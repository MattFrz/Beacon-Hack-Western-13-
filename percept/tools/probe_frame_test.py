#!/usr/bin/env python3
"""Calibration helpers for probe_frame. No camera, ONNX, or MediaPipe."""

from __future__ import annotations

import argparse
import math
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import probe_frame  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
