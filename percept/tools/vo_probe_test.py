#!/usr/bin/env python3
"""vo_probe CLI end-to-end test. Synthetic clip, no camera, no models, no shm."""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE = REPO_ROOT / "percept" / "tools" / "vo_probe.py"

CLIP_W, CLIP_H = 320, 240
CANVAS_W = 640
FRAMES = 40
SHIFT_PX = 4.0
FLAT_Z = 2.0
HFOV = 66.0
STRIDE = 3


def make_clip(path: Path) -> float:
    """Sliding-window random-rectangle texture; returns scripted total |t| in m.

    Non-periodic on purpose: a uniform block grid aliases at displacements
    that are multiples of the block period, and RANSAC rightly refuses
    those steps (watched happen: 40/290 inliers, then 0).
    """
    rng = np.random.default_rng(11)
    canvas = np.zeros((CLIP_H, CANVAS_W), np.uint8)
    for _ in range(240):
        x = int(rng.integers(0, CANVAS_W - 60))
        y = int(rng.integers(0, CLIP_H - 60))
        w, h = int(rng.integers(12, 60)), int(rng.integers(12, 60))
        canvas[y:y + h, x:x + w] = int(rng.integers(40, 255))
    canvas = np.clip(
        canvas.astype(np.int16)
        + rng.integers(0, 24, (CLIP_H, CANVAS_W), dtype=np.uint8),
        0, 255).astype(np.uint8)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 30.0,
                             (CLIP_W, CLIP_H))
    for i in range(FRAMES):
        M = np.float32([[1.0, 0.0, -SHIFT_PX * i], [0.0, 1.0, 0.0]])
        gray = cv2.warpAffine(canvas, M, (CLIP_W, CLIP_H))
        writer.write(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
    writer.release()
    fx = CLIP_W / (2.0 * math.tan(math.radians(HFOV) / 2.0))
    total_px = SHIFT_PX * (FRAMES - 1)
    return total_px * FLAT_Z / fx


class VoProbeTests(unittest.TestCase):
    def test_record_mode_needs_no_h_chest(self):
        """--record is pure capture; the watchdog argument belongs to probing."""
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(PROBE), "--record", str(Path(tmp) / "rec"),
                 "--seconds", "0.01"],
                capture_output=True, text=True, timeout=60, cwd=str(REPO_ROOT))
            self.assertNotIn("--h-chest", proc.stderr,
                             "record mode must not demand the watchdog argument")
            self.assertNotIn("need --depth", proc.stderr,
                             "record mode must not demand a depth source")

    def test_probe_mode_requires_h_chest(self):
        proc = subprocess.run(
            [sys.executable, str(PROBE), "--video", "/nonexistent.avi",
             "--flat-depth", "2.0"],
            capture_output=True, text=True, timeout=60, cwd=str(REPO_ROOT))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--h-chest", proc.stderr)

    def test_recorded_clip_recovers_scripted_translation(self):
        with tempfile.TemporaryDirectory() as tmp:
            avi = Path(tmp) / "walk.avi"
            t_true = make_clip(avi)
            cmd = [sys.executable, str(PROBE),
                   "--video", str(avi),
                   "--flat-depth", str(FLAT_Z),
                   "--h-chest", "1.4",
                   "--fov"]
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=180, cwd=str(REPO_ROOT))
            self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
            summary = json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertGreaterEqual(summary["valid_fraction"], 0.9,
                                    f"too many invalid steps: {summary}")
            self.assertLess(abs(summary["final_t_m"] - t_true), 0.05 * t_true,
                             f"final_t_m={summary['final_t_m']} vs scripted "
                             f"{t_true}")


if __name__ == "__main__":
    unittest.main()
