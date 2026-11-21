#!/usr/bin/env python3
"""Calibration helpers for probe_frame. No camera, ONNX, or MediaPipe."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import shutil
import socket
import sys
import tempfile
import types
import unittest
from pathlib import Path
from typing import get_args, get_type_hints
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


class FakeFileCapture:
    """Finite video file: yields each frame once, then reports no frame."""

    instances = []
    frames = None

    def __init__(self, source):
        self.source = source
        self.index = 0
        self.reads = 0
        self.released = False
        FakeFileCapture.instances.append(self)

    def isOpened(self):
        return True

    def read(self):
        self.reads += 1
        if self.index >= len(self.frames):
            return False, None
        frame = self.frames[self.index]
        self.index += 1
        return True, frame

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
def synthetic_video_modules(frames):
    """Install the synthetic finite-file capture over the fake cv2 module."""
    FakeFileCapture.instances.clear()
    FakeFileCapture.frames = frames
    with synthetic_probe_modules():
        sys.modules["cv2"].VideoCapture = FakeFileCapture
        yield


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
        self.root = root
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

    def test_ultralytics_runtime_creates_no_ort_session(self):
        yolo_pt = self.yolo.with_suffix(".pt")
        yolo_pt.touch()
        args = probe_frame.build_parser().parse_args(
            [
                "--labels", str(self.labels),
                "--yolo", str(yolo_pt),
                "--yolo-runtime", "ultralytics",
                "--fov",
            ]
        )
        labels, mean, std, pad, resources = probe_frame.prepare(args)
        sessions_seen = []

        def fake_detect(_frame, _args, _labels, _affine, _notes, session):
            sessions_seen.append(session)
            return []

        with (
            synthetic_probe_modules(),
            patch.object(probe_frame, "detect", side_effect=fake_detect),
            resources,
        ):
            self.assertIsNone(resources.yolo_session())
            probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual(sessions_seen, [None])
        self.assertEqual(FakeInferenceSession.created, [])

    def test_prepare_annotation_matches_return(self):
        args = self.make_args()
        result = probe_frame.prepare(args)
        annotation = get_type_hints(probe_frame.prepare)["return"]

        self.assertEqual(len(get_args(annotation)), len(result))
        self.assertIs(get_args(annotation)[-1], probe_frame.ProbeResources)
        self.assertIsInstance(result[-1], probe_frame.ProbeResources)

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

    def test_probe_once_jpeg_only_when_requested(self):
        args = self.make_args()
        labels, mean, std, pad, resources = probe_frame.prepare(args)
        jpeg = b"\xff\xd8preview"
        encode_calls = []

        def fake_encode(frame, width, quality):
            encode_calls.append((frame.shape, width, quality))
            return jpeg

        with (
            synthetic_probe_modules(),
            self.fake_model_calls(),
            patch.object(probe_frame, "encode_preview", side_effect=fake_encode),
            resources,
        ):
            without = probe_frame.probe_once(args, labels, mean, std, pad, resources)
            with_jpeg = probe_frame.probe_once(
                args, labels, mean, std, pad, resources, want_jpeg=True
            )

        self.assertNotIn("jpeg", without)
        self.assertNotIn("jpeg", without["timings_ms"])
        self.assertEqual(with_jpeg["jpeg"], jpeg)
        self.assertIsInstance(with_jpeg["timings_ms"]["jpeg"], float)
        self.assertGreaterEqual(with_jpeg["timings_ms"]["jpeg"], 0.0)
        self.assertEqual(encode_calls, [((480, 640, 3), 320, 60)])

    def test_probe_once_cycle_includes_jpeg_encoding_time(self):
        args = self.make_args()
        labels, mean, std, pad, resources = probe_frame.prepare(args)
        clock = {"ns": 0}

        def tick():
            clock["ns"] += 1_000  # 1 us per measured stage
            return clock["ns"]

        def fake_encode(_frame, _width, _quality):
            clock["ns"] += 50_000_000  # 50 ms spent inside the encoder
            return b"\xff\xd8slow"

        with (
            synthetic_probe_modules(),
            self.fake_model_calls(),
            patch.object(probe_frame.time, "perf_counter_ns", side_effect=tick),
            patch.object(probe_frame, "encode_preview", side_effect=fake_encode),
            resources,
        ):
            probe = probe_frame.probe_once(
                args, labels, mean, std, pad, resources, want_jpeg=True
            )

        self.assertGreaterEqual(probe["timings_ms"]["jpeg"], 50.0)
        self.assertGreaterEqual(
            probe["timings_ms"]["cycle"], probe["timings_ms"]["jpeg"]
        )

    def test_video_is_mutually_exclusive_with_image(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                probe_frame.build_parser().parse_args(
                    ["--video", "clip.mp4", "--image", "still.jpg"]
                )

    def test_video_frames_have_per_frame_ids_and_end_at_eof(self):
        video = self.root / "clip.mp4"
        video.touch()
        args = self.make_args("--video", str(video), "--warmup", "3")
        labels, mean, std, pad, resources = probe_frame.prepare(args)
        capture_times = [100, 200, 300]
        frames = [
            np.full((480, 640, 3), index + 1, dtype=np.uint8)
            for index in range(len(capture_times))
        ]

        with (
            synthetic_video_modules(frames),
            self.fake_model_calls(),
            patch.object(probe_frame.time, "monotonic_ns", side_effect=capture_times),
            resources,
        ):
            probes = [
                probe_frame.probe_once(args, labels, mean, std, pad, resources)
                for _ in capture_times
            ]
            self.assertIsNone(
                probe_frame.probe_once(args, labels, mean, std, pad, resources)
            )
            cap = FakeFileCapture.instances[0]
            self.assertEqual(cap.reads, len(capture_times) + 1)  # no warmup reads
            self.assertFalse(cap.released)

        self.assertEqual([probe["t_ns"] for probe in probes], capture_times)
        self.assertEqual([probe["frame_id"] for probe in probes], capture_times)
        self.assertEqual(len(FakeFileCapture.instances), 1)
        self.assertEqual(FakeFileCapture.instances[0].source, str(video))
        self.assertTrue(FakeFileCapture.instances[0].released)

    def test_emit_lines_ends_at_video_eof_with_ordered_records(self):
        video = self.root / "clip.mp4"
        video.touch()
        args = probe_to_world_module.build_parser().parse_args(
            [
                "--labels", str(self.labels),
                "--yolo", str(self.yolo),
                "--depth", str(self.depth),
                "--video", str(video),
                "--out", "-",
            ]
        )
        prepared = probe_frame.prepare(args)
        capture_times = [1_000, 2_000, 3_000]
        frames = [
            np.full((480, 640, 3), index + 1, dtype=np.uint8)
            for index in range(len(capture_times))
        ]

        with (
            synthetic_video_modules(frames),
            self.fake_model_calls(),
            patch.object(probe_frame.time, "monotonic_ns", side_effect=capture_times),
            patch.object(probe_frame, "prepare", return_value=prepared),
        ):
            worlds = list(probe_to_world_module.emit_lines(args))

        self.assertEqual([world["t_ns"] for world in worlds], capture_times)
        self.assertEqual(
            [world["objects"][0]["frame_id"] for world in worlds], capture_times
        )
        self.assertEqual([world["seq"]["percept"] for world in worlds], [0, 2, 4])

    def test_video_and_jpeg_emit_world_and_preview_until_eof(self):
        video = self.root / "clip.mp4"
        video.touch()
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver.bind(("127.0.0.1", 0))
        receiver.settimeout(5.0)
        self.addCleanup(receiver.close)
        target = f"127.0.0.1:{receiver.getsockname()[1]}"
        argv = [
            "--labels", str(self.labels),
            "--yolo", str(self.yolo),
            "--depth", str(self.depth),
            "--hands", "--hand-model", str(self.hand),
            "--fov",
            "--video", str(video),
            "--udp", target,
            "--jpeg", "--jpeg-every", "2",
        ]
        prepared = probe_frame.prepare(probe_to_world_module.build_parser().parse_args(argv))
        frames = [
            np.full((480, 640, 3), index + 1, dtype=np.uint8) for index in range(3)
        ]
        previews = [b"\xff\xd8frame0", b"\xff\xd8frame2"]

        with (
            synthetic_video_modules(frames),
            self.fake_model_calls(),
            patch.object(probe_frame, "prepare", return_value=prepared),
            patch.object(
                probe_frame, "encode_preview", side_effect=previews
            ) as encode_mock,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(probe_to_world_module.main(argv), 0)

        payloads = [receiver.recvfrom(65535)[0] for _ in range(5)]
        self.assertEqual(payloads[1], previews[0])
        self.assertEqual(payloads[4], previews[1])
        worlds = [json.loads(payloads[index]) for index in (0, 2, 3)]
        self.assertEqual(
            [world["seq"]["percept"] for world in worlds], [0, 2, 4]
        )
        self.assertEqual(
            [world["objects"][0]["frame_id"] for world in worlds],
            [world["t_ns"] for world in worlds],
        )
        self.assertEqual(encode_mock.call_count, 2)
        self.assertTrue(FakeFileCapture.instances[0].released)
        receiver.settimeout(0.05)
        with self.assertRaises(socket.timeout):
            receiver.recvfrom(65535)

    def test_stabiliser_settings_recorded(self):
        args = self.make_args(
            "--depth-window", "7",
            "--depth-jump", "0.4",
            "--depth-evict", "12",
            "--depth-recover", "4",
        )
        labels, mean, std, pad, resources = probe_frame.prepare(args)

        with synthetic_probe_modules(), self.fake_model_calls(), resources:
            probe = probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual(
            probe["depth_stabiliser"],
            {"window": 7, "jump": 0.4, "evict": 12, "recover": 4},
        )
        self.assertTrue(any("depth stabiliser" in note for note in probe["notes"]))

    def test_depth_scale_applies_to_raw_and_smoothed_once(self):
        args = self.make_args("--depth-scale", "0.25")
        labels, mean, std, pad, resources = probe_frame.prepare(args)
        depth_values = iter((8.0, 14.0))  # scaled: 2.0 then a rejected 3.5

        def scaled_depth(_frame, _session, affine, *_rest):
            return np.full(
                (affine.net_h, affine.net_w), next(depth_values), dtype=np.float32
            )

        with (
            synthetic_probe_modules(),
            self.fake_model_calls(),
            patch.object(probe_frame, "predict_depth", side_effect=scaled_depth),
            patch.object(probe_frame, "unproject", wraps=probe_frame.unproject) as spy,
            resources,
        ):
            first = probe_frame.probe_once(args, labels, mean, std, pad, resources)
            second = probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual(first["detections"][0]["z_raw"], 2.0)
        self.assertEqual(first["detections"][0]["Z_m"], 2.0)
        self.assertEqual(second["detections"][0]["z_raw"], 3.5)
        self.assertEqual(second["detections"][0]["Z_m"], 2.0)
        self.assertTrue(second["detections"][0]["z_rejected"])
        self.assertEqual([call.args[2] for call in spy.call_args_list], [2.0, 2.0])

    def patch_same_name_frames(self, frames):
        """Patch detection and depth with per-frame same-name boxes and depths."""
        frames = [list(depths) for depths in frames]
        frame_depths = iter(frames)
        flat_depths = iter([z for depths in frames for z in depths])

        def fake_detect(_frame, _args, _labels, _affine, _notes, *_rest):
            depths = next(frame_depths)
            return [
                {
                    "name": "chair",
                    "conf": 0.9,
                    "bbox_px": [index * 50.0, 100.0, index * 50.0 + 30.0, 140.0],
                    "center_px": [index * 50.0 + 15.0, 120.0],
                    "center_net": [index * 25.0, 60.0],
                }
                for index in range(len(depths))
            ]

        def fake_predict_depth(_frame, _session, affine, *_rest):
            return np.full((affine.net_h, affine.net_w), 1.0, dtype=np.float32)

        return (
            patch.object(probe_frame, "detect", side_effect=fake_detect),
            patch.object(probe_frame, "predict_depth", side_effect=fake_predict_depth),
            patch.object(
                probe_frame, "depth_at_box", side_effect=lambda *_args: next(flat_depths)
            ),
        )

    def test_missing_sample_omits_geometry(self):
        args = self.make_args()
        labels, mean, std, pad, resources = probe_frame.prepare(args)

        with (
            synthetic_probe_modules(),
            self.fake_model_calls(),
            patch.object(probe_frame, "depth_at_box", side_effect=[2.0, None]),
            resources,
        ):
            first = probe_frame.probe_once(args, labels, mean, std, pad, resources)
            second = probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual(first["detections"][0]["Z_m"], 2.0)
        self.assertIn("xyz_cam", first["detections"][0])
        self.assertIsNone(second["detections"][0]["Z_m"])
        self.assertIsNone(second["detections"][0]["z_raw"])
        self.assertTrue(second["detections"][0]["z_rejected"])
        self.assertNotIn("xyz_cam", second["detections"][0])
        with patch.object(
            probe_to_world_module.time, "monotonic_ns", return_value=second["t_ns"]
        ):
            world = probe_to_world_module.probe_to_world(second, t_ns=second["t_ns"])
        self.assertNotIn("xyz_cam", world["objects"][0])

    def test_two_same_class_objects_do_not_share_median(self):
        args = self.make_args()
        labels, mean, std, pad, resources = probe_frame.prepare(args)
        detect_patch, grid_patch, depth_patch = self.patch_same_name_frames([[2.0, 4.0]])

        with synthetic_probe_modules(), detect_patch, grid_patch, depth_patch, resources:
            probe = probe_frame.probe_once(args, labels, mean, std, pad, resources)

        detections = probe["detections"]
        self.assertEqual([d["z_raw"] for d in detections], [2.0, 4.0])
        self.assertEqual([d["Z_m"] for d in detections], [2.0, 4.0])
        self.assertTrue(all(d.get("z_ambiguous") for d in detections))
        self.assertEqual([d["xyz_cam"][2] for d in detections], [2.0, 4.0])

    def test_same_class_group_does_not_poison_history(self):
        args = self.make_args()
        labels, mean, std, pad, resources = probe_frame.prepare(args)
        detect_patch, grid_patch, depth_patch = self.patch_same_name_frames(
            [[2.0, 4.0], [4.0]]
        )

        with synthetic_probe_modules(), detect_patch, grid_patch, depth_patch, resources:
            first = probe_frame.probe_once(args, labels, mean, std, pad, resources)
            second = probe_frame.probe_once(args, labels, mean, std, pad, resources)

        self.assertEqual([d["Z_m"] for d in first["detections"]], [2.0, 4.0])
        self.assertEqual(second["detections"][0]["Z_m"], 4.0)
        self.assertFalse(second["detections"][0]["z_rejected"])
        self.assertFalse(second["detections"][0].get("z_ambiguous", False))

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


class DepthStabiliserTest(unittest.TestCase):
    """Per-id depth smoothing; synthetic series only, no camera or models."""

    def test_single_spike_rejected(self):
        stabiliser = probe_frame.DepthStabiliser()
        samples = [
            stabiliser.update("chair", z)
            for z in (2.0, 2.1, 2.0, 8.0, 2.05)
        ]

        self.assertNotIn(8.0, [sample["Z_m"] for sample in samples])
        self.assertTrue(samples[3]["z_rejected"])
        self.assertEqual(samples[3]["z_raw"], 8.0)
        self.assertLess(abs(samples[3]["Z_m"] - 2.0), 0.01)
        self.assertFalse(samples[4]["z_rejected"])

    def test_slow_ramp_tracked(self):
        stabiliser = probe_frame.DepthStabiliser()
        smoothed = [
            stabiliser.update("laptop", 1.0 + index / 9.0)["Z_m"]
            for index in range(10)
        ]

        self.assertGreater(smoothed[-1], 1.75)
        self.assertLess(abs(smoothed[-1] - 2.0), 0.25)
        for before, after in zip(smoothed, smoothed[1:]):
            self.assertGreaterEqual(after, before)

    def test_new_object_uses_first_sample(self):
        stabiliser = probe_frame.DepthStabiliser()
        first = stabiliser.update("mouse", 3.7)

        self.assertEqual(first["Z_m"], 3.7)
        self.assertEqual(first["z_raw"], 3.7)
        self.assertFalse(first["z_rejected"])

    def test_consecutive_disagreement_adopted(self):
        stabiliser = probe_frame.DepthStabiliser(recover=3)
        for z in (2.0, 2.05, 2.0, 2.1, 2.0):
            stabiliser.update("cup", z)
        rejected = [stabiliser.update("cup", 5.0) for _ in range(3)]

        self.assertTrue(all(sample["z_rejected"] for sample in rejected[:2]))
        self.assertAlmostEqual(rejected[-1]["Z_m"], 5.0, places=5)
        self.assertFalse(rejected[-1]["z_rejected"])

    def test_eviction_after_gap(self):
        stabiliser = probe_frame.DepthStabiliser(window=3, evict=2)
        for z in (2.0, 2.0, 2.0):
            stabiliser.update("bottle", z)
        for _ in range(3):
            stabiliser.advance()

        fresh = stabiliser.update("bottle", 8.0)
        self.assertEqual(fresh["Z_m"], 8.0)
        self.assertEqual(fresh["z_raw"], 8.0)
        self.assertFalse(fresh["z_rejected"])

    def test_missing_sample_does_not_block_eviction(self):
        stabiliser = probe_frame.DepthStabiliser(evict=2)
        for z in (2.0, 2.05, 2.0):
            stabiliser.update("keys", z)
        for _ in range(3):
            missing = stabiliser.update("keys", None)
            self.assertIsNone(missing["Z_m"])
            self.assertTrue(missing["z_rejected"])
            stabiliser.advance()

        fresh = stabiliser.update("keys", 4.0)
        self.assertEqual(fresh["Z_m"], 4.0)
        self.assertFalse(fresh["z_rejected"])

    def test_depth_stabiliser_flags_and_validation(self):
        defaults = probe_frame.build_parser().parse_args([])
        self.assertEqual(
            (
                defaults.depth_window,
                defaults.depth_jump,
                defaults.depth_evict,
                defaults.depth_recover,
            ),
            (5, 0.6, 10, 3),
        )
        for flag, value in (
            ("--depth-window", "0"),
            ("--depth-jump", "0"),
            ("--depth-evict", "0"),
            ("--depth-recover", "0"),
        ):
            with self.subTest(flag=flag):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        probe_frame.build_parser().parse_args([flag, value])


class PreviewEncodeTest(unittest.TestCase):
    """JPEG preview encoding with a fake cv2; no camera or real OpenCV."""

    def test_encode_preview_resizes_to_width_and_sets_quality(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        small = np.zeros((240, 320, 3), dtype=np.uint8)
        calls = {}
        fake_cv2 = types.ModuleType("cv2")
        fake_cv2.INTER_AREA = 3
        fake_cv2.IMWRITE_JPEG_QUALITY = 2

        def record_resize(image, size, interpolation=None):
            calls["resize"] = (image is frame, size, interpolation)
            return small

        def record_encode(ext, image, params):
            calls["encode"] = (ext, image is small, params)
            return True, types.SimpleNamespace(tobytes=lambda: b"\xff\xd8jpeg")

        fake_cv2.resize = record_resize
        fake_cv2.imencode = record_encode

        with patch.dict(sys.modules, {"cv2": fake_cv2}):
            encoded = probe_frame.encode_preview(frame, 320, 55)

        self.assertEqual(encoded, b"\xff\xd8jpeg")
        self.assertEqual(calls["resize"], (True, (320, 240), fake_cv2.INTER_AREA))
        self.assertEqual(calls["encode"], (".jpg", True, [2, 55]))

    def test_encode_preview_does_not_upscale_narrow_frames(self):
        frame = np.zeros((240, 160, 3), dtype=np.uint8)
        sizes = []
        fake_cv2 = types.ModuleType("cv2")
        fake_cv2.INTER_AREA = 3
        fake_cv2.IMWRITE_JPEG_QUALITY = 2
        fake_cv2.resize = lambda image, size, interpolation=None: sizes.append(size) or image
        fake_cv2.imencode = lambda *_args: (True, types.SimpleNamespace(tobytes=lambda: b"jpeg"))

        with patch.dict(sys.modules, {"cv2": fake_cv2}):
            self.assertEqual(probe_frame.encode_preview(frame, 320, 60), b"jpeg")

        self.assertEqual(sizes, [(160, 240)])

    def test_encode_preview_returns_none_when_encoding_fails(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        fake_cv2 = types.ModuleType("cv2")
        fake_cv2.INTER_AREA = 3
        fake_cv2.IMWRITE_JPEG_QUALITY = 2
        fake_cv2.resize = lambda image, _size, interpolation=None: image
        fake_cv2.imencode = lambda *_args: (False, None)

        with patch.dict(sys.modules, {"cv2": fake_cv2}):
            self.assertIsNone(probe_frame.encode_preview(frame, 320, 60))


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

    def test_patch_rejects_pad_and_outside_grid_centres(self):
        metres = np.full((self.affine.net_h, self.affine.net_w), 3.0, dtype=np.float32)
        # Both centres have valid neighbours; only the centre cell is invalid.
        self.assertTrue(self.affine.net_to_full(105, 27)[2])  # below the pad landmark
        self.assertTrue(self.affine.net_to_full(209, 105)[2])  # left of the edge landmark
        for u, v in ((320.0, -0.15), (639.0, 240.0)):
            with self.subTest(landmark=(u, v)):
                self.assertIsNone(
                    probe_frame.depth_at_patch(metres, self.affine, u, v, 1.0)
                )

    def test_box_integer_edge_excludes_wholly_outside_cell(self):
        u2, v2 = 128.0, 176.0
        x2, y2 = self.affine.full_to_net(u2, v2)
        self.assertEqual((x2, y2), (42.0, 84.0))

        metres = np.full((self.affine.net_h, self.affine.net_w), 999.0, dtype=np.float32)
        for y in range(82, 84):
            for x in range(40, 42):
                metres[y, x] = 2.0
        # Cell (84, 42) spans net [42, 43) x [84, 85); it is wholly outside
        # a box ending at net (42, 84) and must not contribute to the median.
        self.assertAlmostEqual(
            probe_frame.depth_at_box(
                metres, self.affine, [122.0, 170.0, u2, v2], 1.0
            ),
            2.0,
        )

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
