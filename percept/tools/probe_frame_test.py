#!/usr/bin/env python3
"""Calibration helpers for probe_frame. No camera, ONNX, or MediaPipe."""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import shutil
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
    def fake_model_calls(self, depth_value=1.0):
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
            return np.full((affine.net_h, affine.net_w), depth_value, dtype=np.float32)

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

    def test_probe_unproject_receives_scaled_z_once(self):
        args = self.make_args("--depth-scale", "0.5")
        labels, mean, std, pad, resources = probe_frame.prepare(args)

        def spiky_depth(_frame, _session, affine, *_rest):
            grid = np.full((affine.net_h, affine.net_w), 4.0, dtype=np.float32)
            grid[105, 105] = 100.0  # one bad centre cell must not set Z
            return grid

        with (
            synthetic_probe_modules(),
            self.fake_model_calls(),
            patch.object(probe_frame, "predict_depth", side_effect=spiky_depth),
            patch.object(probe_frame, "unproject", wraps=probe_frame.unproject) as spy,
            resources,
        ):
            probe = probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual(probe["detections"][0]["Z_m"], 2.0)
        self.assertEqual(len(spy.call_args_list), 1)
        self.assertEqual(spy.call_args_list[0].args[2], 2.0)


class DepthSamplingTest(unittest.TestCase):
    """Synthetic grids and affines: no camera, ONNX, or MediaPipe."""

    def setUp(self):
        self.affine = probe_frame.make_affine(640, 480, 210, 210)

    def test_affine_roundtrip_no_flip(self):
        affine = self.affine
        rng = np.random.default_rng(7)
        for u, v in zip(rng.uniform(0.0, 639.0, 200), rng.uniform(0.0, 479.0, 200)):
            u_net, v_net = affine.full_to_net(float(u), float(v))
            u_back, v_back, valid = affine.net_to_full(u_net, v_net)
            self.assertTrue(valid)
            self.assertLessEqual(abs(u_back - u), 1.0)
            self.assertLessEqual(abs(v_back - v), 1.0)

        u_net, v_net = affine.full_to_net(0.0, 0.0)
        u_back, v_back, valid = affine.net_to_full(u_net, v_net)
        self.assertTrue(valid)
        self.assertAlmostEqual(u_back, 0.0, places=6)
        self.assertAlmostEqual(v_back, 0.0, places=6)
        u_net, v_net = affine.full_to_net(639.0, 479.0)
        u_back, v_back, valid = affine.net_to_full(u_net, v_net)
        self.assertTrue(valid)
        self.assertLessEqual(abs(u_back - 639.0), 1.0)
        self.assertLessEqual(abs(v_back - 479.0), 1.0)

        self.assertFalse(affine.net_to_full(5, 5)[2])  # letterbox pad
        self.assertTrue(affine.net_to_full(105, 105)[2])

    def test_synthetic_gradient_orientation(self):
        rows, cols = np.arange(self.affine.net_h), np.arange(self.affine.net_w)
        metres = 1.0 + 0.02 * cols[None, :] + 0.01 * rows[:, None]
        z_left = probe_frame.depth_at_box(
            metres, self.affine, [100.0, 200.0, 140.0, 240.0], 1.0
        )
        z_right = probe_frame.depth_at_box(
            metres, self.affine, [400.0, 200.0, 440.0, 240.0], 1.0
        )
        z_top = probe_frame.depth_at_box(
            metres, self.affine, [200.0, 100.0, 240.0, 140.0], 1.0
        )
        z_bottom = probe_frame.depth_at_box(
            metres, self.affine, [200.0, 300.0, 240.0, 340.0], 1.0
        )
        self.assertGreater(z_right, z_left)
        self.assertGreater(z_bottom, z_top)

    def test_box_median_beats_center_pixel(self):
        metres = np.full((self.affine.net_h, self.affine.net_w), 8.0, dtype=np.float32)
        rows, cols = np.arange(self.affine.net_h), np.arange(self.affine.net_w)
        disc = (cols[None, :] - 105.0) ** 2 + (rows[:, None] - 105.0) ** 2 <= 20.0**2
        metres[disc] = 2.0
        metres[105, 105] = 8.0  # box centre cell on background, interior on disc

        bbox = [259.0, 179.0, 381.0, 301.0]
        self.assertAlmostEqual(
            probe_frame.depth_at_full(metres, self.affine, 320.0, 240.0, 1.0), 8.0
        )
        self.assertAlmostEqual(
            probe_frame.depth_at_box(metres, self.affine, bbox, 1.0), 2.0, places=5
        )

    def test_box_sampling_excludes_padding_and_clipped_boxes(self):
        metres = np.full((self.affine.net_h, self.affine.net_w), 999.0, dtype=np.float32)
        for y in range(self.affine.net_h):
            for x in range(self.affine.net_w):
                if self.affine.net_to_full(x, y)[2]:
                    metres[y, x] = 2.0

        straddling_pad = probe_frame.depth_at_box(
            metres, self.affine, [100.0, -100.0, 200.0, 20.0], 1.0
        )
        self.assertAlmostEqual(straddling_pad, 2.0, places=5)

        fully_invalid = probe_frame.depth_at_box(
            metres, self.affine, [100.0, -400.0, 200.0, -350.0], 1.0
        )
        self.assertIsNone(fully_invalid)

    def test_depth_scale_applied_exactly_once(self):
        metres = np.full((self.affine.net_h, self.affine.net_w), 4.0, dtype=np.float32)
        self.assertAlmostEqual(
            probe_frame.depth_at_box(
                metres, self.affine, [300.0, 220.0, 340.0, 260.0], 0.5
            ),
            2.0,
        )
        self.assertAlmostEqual(
            probe_frame.depth_at_patch(metres, self.affine, 320.0, 240.0, 0.5), 2.0
        )

    def test_preprocessing_contract(self):
        args = probe_frame.build_parser().parse_args([])
        mean = probe_frame.parse_csv3(args.depth_mean, "--depth-mean")
        std = probe_frame.parse_csv3(args.depth_std, "--depth-std")
        pad = probe_frame.parse_csv3(args.depth_pad, "--depth-pad")
        affine = probe_frame.make_affine(4, 4, 4, 4)
        frame = np.full((4, 4, 3), [10, 100, 200], dtype=np.uint8)

        class RecordingSession:
            def __init__(self):
                self.tensor = None

            def get_inputs(self):
                return [types.SimpleNamespace(name="input")]

            def run(self, _names, feed):
                self.tensor = feed["input"]
                return [np.zeros((1, 1, 4, 4), dtype=np.float32)]

        session = RecordingSession()
        with synthetic_probe_modules():
            fake_cv2 = sys.modules["cv2"]
            with patch.object(
                fake_cv2,
                "cvtColor",
                lambda image, code: image[..., ::-1]
                if code == fake_cv2.COLOR_BGR2RGB
                else image,
            ):
                probe_frame.predict_depth(
                    frame, session, affine, args, mean, std, tuple(int(v) for v in pad)
                )

        tensor = session.tensor
        self.assertEqual(tensor.shape, (1, 3, 4, 4))
        self.assertEqual(tensor.dtype, np.float32)
        rgb = np.array([200.0, 100.0, 10.0], dtype=np.float32) / 255.0
        expected = (rgb - np.asarray(mean, dtype=np.float32)) / np.asarray(
            std, dtype=np.float32
        )
        for channel in range(3):
            np.testing.assert_allclose(tensor[0, channel], expected[channel], atol=1e-6)

    def test_probe_json_records_sampler(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        labels = root / "labels.txt"
        labels.write_text("keys\n", encoding="utf-8")
        depth = root / "depth.onnx"
        depth.touch()
        args = probe_frame.build_parser().parse_args(
            ["--labels", str(labels), "--depth", str(depth), "--depth-scale", "0.5"]
        )
        resources = probe_frame.ProbeResources(args)
        with (
            synthetic_probe_modules(),
            patch.object(
                probe_frame,
                "predict_depth",
                return_value=np.full((210, 210), 1.0, dtype=np.float32),
            ),
            resources,
        ):
            probe = probe_frame.probe_once(
                args,
                ["keys"],
                (0.485, 0.456, 0.406),
                (0.229, 0.224, 0.225),
                (114, 114, 114),
                resources,
            )

        self.assertEqual(probe["depth_grid"]["sampler"], "box_median")
        self.assertEqual(probe["depth_grid"]["depth_scale"], 0.5)


if __name__ == "__main__":
    unittest.main()
