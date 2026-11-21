#!/usr/bin/env python3
"""Tests for the laptop chessboard calibrator. Synthetic views only; no camera."""

from __future__ import annotations

import contextlib
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import calibrate_camera as cam  # noqa: E402
from percept.tools import probe_frame  # noqa: E402

COLS, ROWS = 9, 6
SQUARE_M = 0.025
WIDTH, HEIGHT = 640, 480
TRUE_FX, TRUE_FY = 800.0, 800.0
TRUE_CX, TRUE_CY = 320.0, 240.0

# (rotation vector, translation) pairs for the synthetic board views. The
# x/y translation centres the inner-corner grid on the principal point.
POSES = (
    ((0.00, 0.00, 0.00), (-0.1000, -0.0625, 0.55)),
    ((0.06, -0.05, 0.03), (-0.0700, -0.0425, 0.60)),
    ((-0.05, 0.07, -0.04), (-0.1400, -0.0525, 0.65)),
    ((0.10, 0.02, 0.08), (-0.0500, -0.0925, 0.70)),
    ((-0.08, -0.09, -0.06), (-0.1200, -0.0225, 0.75)),
    ((0.03, 0.12, 0.02), (-0.0800, -0.1125, 0.80)),
    ((-0.12, 0.04, 0.10), (-0.1500, -0.0825, 0.85)),
    ((0.05, -0.11, -0.09), (-0.0600, -0.0125, 0.90)),
    ((0.00, 0.00, 0.05), (-0.1000, -0.0625, 0.50)),
)


def synthetic_view(rvec, tvec, cell=40):
    """Render a posed chessboard through a known pinhole camera."""
    import cv2
    import numpy as np

    board = np.full(((ROWS + 1) * cell, (COLS + 1) * cell), 255, dtype=np.uint8)
    for j in range(ROWS + 1):
        for i in range(COLS + 1):
            if (i + j) % 2:
                board[j * cell : (j + 1) * cell, i * cell : (i + 1) * cell] = 0

    k_matrix = np.array(
        [[TRUE_FX, 0.0, TRUE_CX], [0.0, TRUE_FY, TRUE_CY], [0.0, 0.0, 1.0]]
    )
    rotation, _ = cv2.Rodrigues(np.asarray(rvec, dtype=np.float64))
    translation = np.asarray(tvec, dtype=np.float64).reshape(3, 1)

    def project(px, py):
        x = (px / cell - 1.0) * SQUARE_M
        y = (py / cell - 1.0) * SQUARE_M
        point = rotation @ np.array([[x], [y], [0.0]]) + translation
        uv = k_matrix @ point
        return (uv[0, 0] / uv[2, 0], uv[1, 0] / uv[2, 0])

    src = np.array(
        [
            [0.0, 0.0],
            [board.shape[1] - 1.0, 0.0],
            [board.shape[1] - 1.0, board.shape[0] - 1.0],
            [0.0, board.shape[0] - 1.0],
        ],
        dtype=np.float32,
    )
    dst = np.array([project(px, py) for px, py in src], dtype=np.float32)
    homography = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(
        board, homography, (WIDTH, HEIGHT), flags=cv2.INTER_AREA, borderValue=255
    )
    return cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)


def write_synthetic_views(directory, poses=POSES):
    import cv2

    paths = []
    for index, (rvec, tvec) in enumerate(poses):
        path = Path(directory) / f"board_{index:02d}.png"
        if not cv2.imwrite(str(path), synthetic_view(rvec, tvec)):
            raise AssertionError(f"could not write {path}")
        paths.append(path)
    return paths


class CalibrateCameraTest(unittest.TestCase):
    def test_writer_shape(self):
        payload = cam.make_calibration(
            TRUE_FX + 1.5, TRUE_FY + 2.5, TRUE_CX + 1.25, TRUE_CY - 0.25, WIDTH, HEIGHT
        )
        for key in ("fx", "fy", "cx", "cy"):
            self.assertTrue(math.isfinite(payload[key]), key)
        for key in ("W", "H", "width", "height"):
            self.assertIsInstance(payload[key], int)
        self.assertEqual(payload["width"], payload["W"])
        self.assertEqual(payload["height"], payload["H"])

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calib.json"
            cam.write_calibration(path, payload)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), payload)

    def test_synthetic_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = write_synthetic_views(directory)
            result = cam.calibrate_images(
                paths, rows=ROWS, cols=COLS, square_m=SQUARE_M
            )

        self.assertAlmostEqual(result["fx"], TRUE_FX, delta=0.05 * TRUE_FX)
        self.assertAlmostEqual(result["fy"], TRUE_FY, delta=0.05 * TRUE_FY)
        self.assertAlmostEqual(result["cx"], TRUE_CX, delta=15.0)
        self.assertAlmostEqual(result["cy"], TRUE_CY, delta=15.0)

    def test_too_few_boards_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = write_synthetic_views(directory, poses=POSES[:2])
            with self.assertRaisesRegex(ValueError, "at least"):
                cam.calibrate_images(paths, rows=ROWS, cols=COLS, square_m=SQUARE_M)

    def test_boards_without_corners_raise(self):
        import cv2
        import numpy as np

        with tempfile.TemporaryDirectory() as directory:
            blank = np.full((HEIGHT, WIDTH, 3), 255, dtype=np.uint8)
            paths = []
            for index in range(len(POSES)):
                path = Path(directory) / f"blank_{index:02d}.png"
                cv2.imwrite(str(path), blank)
                paths.append(path)
            with self.assertRaisesRegex(ValueError, "no chessboard corners"):
                cam.calibrate_images(paths, rows=ROWS, cols=COLS, square_m=SQUARE_M)

    def test_saved_file_loads_in_probe_frame_at_640x480(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = write_synthetic_views(directory)
            calibration = cam.calibrate_images(
                paths, rows=ROWS, cols=COLS, square_m=SQUARE_M
            )
            out = Path(directory) / "calib.json"
            cam.write_calibration(out, calibration)
            notes = []
            loaded = probe_frame.load_calibration(out, WIDTH, HEIGHT, notes)

        self.assertEqual(notes, [])
        self.assertEqual(loaded.fx, calibration["fx"])
        self.assertEqual(loaded.fy, calibration["fy"])
        self.assertEqual(loaded.cx, calibration["cx"])
        self.assertEqual(loaded.cy, calibration["cy"])
        self.assertEqual(loaded.width, WIDTH)
        self.assertEqual(loaded.height, HEIGHT)

    def test_cli_help_exposes_options(self):
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stdout(stdout):
            cam.build_parser().parse_args(["--help"])
        self.assertEqual(caught.exception.code, 0)
        text = stdout.getvalue()
        for flag in (
            "--images",
            "--rows",
            "--cols",
            "--square-m",
            "--out",
            "--camera",
            "--write-board",
        ):
            self.assertIn(flag, text)
        self.assertEqual(cam.build_parser().get_default("out"), Path("models/calib.json"))

    def test_write_board_is_detectable(self):
        import cv2

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.png"
            cam.write_board(path, rows=ROWS, cols=COLS)
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            self.assertIsNotNone(image)
            corners = cam.find_corners(image, ROWS, COLS)
            self.assertIsNotNone(corners)
            self.assertEqual(len(corners), ROWS * COLS)

    def test_capture_frames_prompts_between_views(self):
        import cv2
        import numpy as np

        class FakeCap:
            def __init__(self):
                self.index = 0

            def isOpened(self):
                return True

            def read(self):
                frame = np.full((HEIGHT, WIDTH, 3), 40 * (self.index + 1), dtype=np.uint8)
                self.index += 1
                return True, frame

            def release(self):
                pass

        prompts = []
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(cv2, "VideoCapture", return_value=FakeCap()):
                paths = cam.capture_frames(
                    0, 2, Path(directory), prompt=prompts.append
                )
            self.assertEqual(len(paths), 2)
            self.assertTrue(all(path.exists() for path in paths))
        self.assertEqual(len(prompts), 1)
        self.assertIn("reposition", prompts[0].lower())

    def test_nonpositive_square_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = write_synthetic_views(directory)
            with self.assertRaisesRegex(ValueError, "square"):
                cam.calibrate_images(paths, rows=ROWS, cols=COLS, square_m=0.0)

    def test_identical_views_raise(self):
        with tempfile.TemporaryDirectory() as directory:
            one = write_synthetic_views(directory, poses=POSES[:1])
            paths = one * cam.MIN_BOARDS
            with self.assertRaisesRegex(ValueError, "too similar"):
                cam.calibrate_images(paths, rows=ROWS, cols=COLS, square_m=SQUARE_M)


if __name__ == "__main__":
    unittest.main()
