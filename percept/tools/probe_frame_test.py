#!/usr/bin/env python3
"""Calibration helpers for probe_frame. No camera, ONNX, or MediaPipe."""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import probe_frame  # noqa: E402
from percept.tools import probe_to_world as probe_to_world_module  # noqa: E402


class GuessCalibrationTest(unittest.TestCase):
    def test_guess_pinhole_centers_and_fx(self):
        cal = probe_frame.guess_calibration(640, 480, 66.0)
        self.assertEqual(cal.cx, 320.0)
        self.assertEqual(cal.cy, 240.0)
        expected_fx = 640.0 / (2.0 * math.tan(math.radians(66.0) / 2.0))
        self.assertAlmostEqual(cal.fx, expected_fx, places=6)
        self.assertAlmostEqual(cal.fy, expected_fx, places=6)
        self.assertEqual(cal.width, 640)
        self.assertEqual(cal.height, 480)

    def test_guess_rejects_bad_fov(self):
        with self.assertRaisesRegex(ValueError, "fov"):
            probe_frame.guess_calibration(640, 480, 0)
        with self.assertRaisesRegex(ValueError, "fov"):
            probe_frame.guess_calibration(640, 480, 180)

    def test_resolve_omits_xyz_without_calib_or_fov(self):
        args = argparse.Namespace(calib=None, fov=None)
        notes = []
        cal = probe_frame.resolve_calibration(args, 640, 480, notes)
        self.assertIsNone(cal)
        self.assertTrue(any("omitted" in note for note in notes))

    def test_resolve_uses_fov_when_calib_missing(self):
        args = argparse.Namespace(calib=None, fov=66.0)
        notes = []
        cal = probe_frame.resolve_calibration(args, 640, 480, notes)
        self.assertIsNotNone(cal)
        self.assertAlmostEqual(cal.cx, 320.0)
        self.assertTrue(any("guessed" in note and "66" in note for note in notes))

    def test_resolve_prefers_calib_over_fov(self):
        guessed = probe_frame.guess_calibration(640, 480, 66.0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calib.json"
            path.write_text(
                json.dumps(
                    {
                        "fx": guessed.fx + 50.0,
                        "fy": guessed.fy + 50.0,
                        "cx": 321.0,
                        "cy": 241.0,
                        "W": 640,
                        "H": 480,
                    }
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(calib=path, fov=66.0)
            notes = []
            cal = probe_frame.resolve_calibration(args, 640, 480, notes)
        self.assertIsNotNone(cal)
        self.assertAlmostEqual(cal.fx, guessed.fx + 50.0)
        self.assertAlmostEqual(cal.cx, 321.0)
        self.assertFalse(any("guessed" in note for note in notes))

    def test_bare_fov_defaults_to_66(self):
        parsed = probe_frame.build_parser().parse_args(["--fov"])
        self.assertEqual(parsed.fov, 66.0)
        omitted = probe_frame.build_parser().parse_args([])
        self.assertIsNone(omitted.fov)

    def test_unproject_centre_stays_on_optical_axis(self):
        cal = probe_frame.guess_calibration(640, 480, 66.0)
        xyz = probe_frame.unproject(320.0, 240.0, 1.0, cal)
        self.assertAlmostEqual(xyz[0], 0.0, places=6)
        self.assertAlmostEqual(xyz[1], 0.0, places=6)
        self.assertAlmostEqual(xyz[2], 1.0, places=6)


class FakeCapture:
    """Synthetic webcam; one instance per open, closed only by release()."""

    instances = []
    clock = None
    read_ns = None

    def __init__(self, camera):
        self.camera = camera
        self.reads = 0
        self.released = False
        FakeCapture.instances.append(self)

    def isOpened(self):
        return True

    def read(self):
        self.reads += 1
        if FakeCapture.clock is not None and FakeCapture.read_ns is not None:
            FakeCapture.clock["ns"] = FakeCapture.read_ns
        return True, np.zeros((480, 640, 3), dtype=np.uint8)

    def release(self):
        self.released = True


class FakeSessionOptions:
    def __init__(self):
        self.intra_op_num_threads = None
        self.execution_mode = None


class FakeInferenceSession:
    created = []

    def __init__(self, path, providers=None, sess_options=None):
        self.path = path
        self.providers = providers
        self.sess_options = sess_options
        self.runs = 0
        FakeInferenceSession.created.append(self)

    def get_inputs(self):
        return [types.SimpleNamespace(name="input")]

    def run(self, _names, _feed):
        self.runs += 1
        return [np.zeros((1, 5, 1), dtype=np.float32)]


class FakeLandmarker:
    created = []

    def __init__(self):
        self.detects = 0
        self.closed = False

    @classmethod
    def create_from_options(cls, _options):
        landmarker = cls()
        cls.created.append(landmarker)
        return landmarker

    def detect(self, _image):
        self.detects += 1
        return types.SimpleNamespace(hand_landmarks=[])

    def close(self):
        self.closed = True


@contextlib.contextmanager
def synthetic_probe_modules():
    """Install fake cv2/ORT/MediaPipe modules; never touch camera or models."""
    FakeCapture.instances.clear()
    FakeCapture.clock = None
    FakeCapture.read_ns = None
    FakeInferenceSession.created.clear()
    FakeLandmarker.created.clear()

    fake_cv2 = types.ModuleType("cv2")
    fake_cv2.VideoCapture = FakeCapture
    fake_cv2.IMREAD_COLOR = 1
    fake_cv2.COLOR_BGR2RGB = 4
    fake_cv2.INTER_AREA = 3
    fake_cv2.INTER_LINEAR = 2
    fake_cv2.resize = lambda frame, _size, interpolation=None: frame
    fake_cv2.cvtColor = lambda frame, _code: frame
    fake_cv2.dnn = types.SimpleNamespace(NMSBoxes=lambda *_args: [])

    fake_ort = types.ModuleType("onnxruntime")
    fake_ort.SessionOptions = FakeSessionOptions
    fake_ort.ExecutionMode = types.SimpleNamespace(ORT_PARALLEL="parallel")
    fake_ort.InferenceSession = FakeInferenceSession

    fake_mp = types.ModuleType("mediapipe")
    fake_mp.ImageFormat = types.SimpleNamespace(SRGB=1)
    fake_mp.Image = lambda image_format, data: types.SimpleNamespace(
        image_format=image_format, data=data
    )
    fake_tasks = types.ModuleType("mediapipe.tasks")
    fake_python = types.ModuleType("mediapipe.tasks.python")
    fake_vision = types.ModuleType("mediapipe.tasks.python.vision")
    fake_vision.HandLandmarker = FakeLandmarker
    fake_vision.RunningMode = types.SimpleNamespace(IMAGE=0)
    fake_vision.HandLandmarkerOptions = lambda **kwargs: types.SimpleNamespace(**kwargs)
    fake_python.vision = fake_vision
    fake_python.BaseOptions = lambda model_asset_path: types.SimpleNamespace(
        model_asset_path=model_asset_path
    )
    fake_tasks.python = fake_python
    fake_mp.tasks = fake_tasks

    with patch.dict(
        sys.modules,
        {
            "cv2": fake_cv2,
            "onnxruntime": fake_ort,
            "mediapipe": fake_mp,
            "mediapipe.tasks": fake_tasks,
            "mediapipe.tasks.python": fake_python,
            "mediapipe.tasks.python.vision": fake_vision,
        },
    ):
        yield


class ProbeRuntimeTest(unittest.TestCase):
    """Cadence and honesty tests; all models and devices are synthetic."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.labels = root / "labels.txt"
        self.labels.write_text("keys\nkeychain\nbottle\ncup\n", encoding="utf-8")
        self.yolo = root / "yolo.onnx"
        self.depth = root / "depth.onnx"
        self.hand = root / "hand.task"
        for path in (self.yolo, self.depth, self.hand):
            path.touch()

    def make_args(self, *extra):
        return probe_frame.build_parser().parse_args(
            [
                "--labels", str(self.labels),
                "--yolo", str(self.yolo),
                "--depth", str(self.depth),
                "--hands", "--hand-model", str(self.hand),
                "--fov",
                *extra,
            ]
        )

    @contextlib.contextmanager
    def fake_model_calls(self):
        def fake_detect(_frame, _args, _labels, _affine, _notes, *_rest):
            return [
                {
                    "name": "keys",
                    "conf": 0.9,
                    "bbox_px": [300.0, 220.0, 340.0, 260.0],
                    "center_px": [320.0, 240.0],
                    "center_net": [160.0, 160.0],
                }
            ]

        def fake_predict_depth(_frame, _session, affine, *_rest):
            return np.full((affine.net_h, affine.net_w), 1.0, dtype=np.float32)

        with patch.object(probe_frame, "detect", side_effect=fake_detect), patch.object(
            probe_frame, "predict_depth", side_effect=fake_predict_depth
        ):
            yield

    def test_sessions_created_once(self):
        args = self.make_args()
        labels, mean, std, pad, resources = probe_frame.prepare(args)

        with synthetic_probe_modules(), self.fake_model_calls(), resources:
            probes = [
                probe_frame.probe_once(args, labels, mean, std, pad, resources)
                for _ in range(3)
            ]

        self.assertEqual(len(probes), 3)
        self.assertEqual(len(FakeInferenceSession.created), 2)
        self.assertEqual(
            sorted(Path(session.path).name for session in FakeInferenceSession.created),
            ["depth.onnx", "yolo.onnx"],
        )

    def test_camera_opened_once(self):
        args = self.make_args("--warmup", "2")
        labels, mean, std, pad, resources = probe_frame.prepare(args)

        with synthetic_probe_modules(), self.fake_model_calls(), resources:
            for _ in range(3):
                probe_frame.probe_once(args, labels, mean, std, pad, resources)
            self.assertEqual(len(FakeCapture.instances), 1)
            self.assertFalse(FakeCapture.instances[0].released)

        cap = FakeCapture.instances[0]
        self.assertEqual(cap.reads, 2 + 3)
        self.assertTrue(cap.released)

    def test_landmarker_created_once(self):
        args = self.make_args()
        labels, mean, std, pad, resources = probe_frame.prepare(args)

        with synthetic_probe_modules(), self.fake_model_calls(), resources:
            for _ in range(3):
                probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual(len(FakeLandmarker.created), 1)
        self.assertEqual(FakeLandmarker.created[0].detects, 3)
        self.assertTrue(FakeLandmarker.created[0].closed)

    def test_t_ns_is_capture_time(self):
        args = self.make_args("--warmup", "0")
        labels, mean, std, pad, resources = probe_frame.prepare(args)
        clock = {"ns": 0}
        capture_ns = 1_700_000_000
        publish_ns = 9_000_000_000

        with (
            synthetic_probe_modules(),
            self.fake_model_calls(),
            patch.object(probe_frame.time, "monotonic_ns", side_effect=lambda: clock["ns"]),
            patch.object(probe_frame.time, "time_ns", return_value=publish_ns),
            resources,
        ):
            FakeCapture.clock = clock
            FakeCapture.read_ns = capture_ns
            probe = probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual(probe["t_ns"], capture_ns)
        with patch.object(
            probe_to_world_module.time, "monotonic_ns", return_value=publish_ns
        ):
            world = probe_to_world_module.probe_to_world(
                probe, t_ns=probe.get("t_ns")
            )
            reused = probe_to_world_module.probe_to_world(
                probe, t_ns=probe.get("t_ns"), seq=2
            )

        for record in (world, reused):
            self.assertEqual(record["t_ns"], capture_ns)
            self.assertEqual(record["target"]["last_seen_ns"], capture_ns)
            self.assertEqual(record["objects"][0]["frame_id"], probe["frame_id"])

        prepared = (labels, mean, std, pad, contextlib.nullcontext())
        args.once = True
        with (
            patch.object(probe_frame, "prepare", return_value=prepared),
            patch.object(probe_frame, "probe_once", side_effect=[probe]),
            patch.object(
                probe_to_world_module.time, "monotonic_ns", return_value=publish_ns
            ),
        ):
            emitted = next(probe_to_world_module.emit_lines(args))
        self.assertEqual(emitted["t_ns"], capture_ns)

    def test_ort_options_flag(self):
        args = self.make_args("--ort-intra", "3", "--ort-parallel")
        self.assertEqual(args.ort_intra, 3)
        self.assertTrue(args.ort_parallel)
        labels, mean, std, pad, resources = probe_frame.prepare(args)

        with synthetic_probe_modules(), self.fake_model_calls(), resources:
            probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual(len(FakeInferenceSession.created), 2)
        for session in FakeInferenceSession.created:
            self.assertEqual(session.sess_options.intra_op_num_threads, 3)
            self.assertEqual(session.sess_options.execution_mode, "parallel")
            self.assertEqual(session.providers, ["CPUExecutionProvider"])
        default_args = self.make_args()
        self.assertEqual(default_args.ort_intra, 4)
        self.assertFalse(default_args.ort_parallel)

    def test_health_fields(self):
        args = self.make_args()
        labels, mean, std, pad, resources = probe_frame.prepare(args)

        with synthetic_probe_modules(), self.fake_model_calls(), resources:
            with_hands = probe_frame.probe_once(
                args, labels, mean, std, pad, resources
            )
            args.hands = False
            without_hands = probe_frame.probe_once(
                args, labels, mean, std, pad, resources
            )

        for probe in (with_hands, without_hands):
            timings = probe["timings_ms"]
            for key in ("yolo", "depth", "cycle"):
                self.assertIsInstance(timings[key], float)
                self.assertGreaterEqual(timings[key], 0.0)
        self.assertIsInstance(with_hands["timings_ms"]["hands"], float)
        self.assertIsNone(without_hands["timings_ms"]["hands"])

        with patch.object(
            probe_to_world_module.time, "monotonic_ns", return_value=9_000_000_000
        ):
            world = probe_to_world_module.probe_to_world(
                with_hands, t_ns=with_hands["t_ns"]
            )
            no_hands = probe_to_world_module.probe_to_world(
                without_hands, t_ns=without_hands["t_ns"]
            )
        self.assertEqual(
            world["health"]["last_hands_ms"], with_hands["timings_ms"]["hands"]
        )
        self.assertEqual(
            world["health"]["last_cycle_ms"], with_hands["timings_ms"]["cycle"]
        )
        self.assertIsNone(no_hands["health"]["last_hands_ms"])


if __name__ == "__main__":
    unittest.main()
