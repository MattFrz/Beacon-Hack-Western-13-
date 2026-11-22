#!/usr/bin/env python3
"""VO geometry core tests. Synthetic frames only; no camera, models, or shm.

Every motion here is an exact homography warp of a synthetic textured frame,
so the true relative pose is known analytically: a fronto-parallel plane at
depth d under camera translation t maps by H = K (I - t n^T / d) K^-1, and a
camera rotation R (about the camera centre) maps by H = K R K^-1.
"""

from __future__ import annotations

import math
import sys
import unittest
from collections import deque
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import vo_core  # noqa: E402
from percept.tools.probe_frame import guess_calibration, make_affine  # noqa: E402

VO_W, VO_H = 320, 240          # tests run with VO scale == full frame scale
CAM_W, CAM_H = VO_W, VO_H
HFOV_DEG = 66.0
PLANE_Z = 2.0                  # metres, fronto-parallel synthetic scene
DEPTH_GRID = 105               # metres grid is 105 x 105 for every keyframe


def make_texture(seed: int = 7) -> np.ndarray:
    """Block noise: strong corner structure that LK actually tracks."""
    rng = np.random.default_rng(seed)
    blocks = rng.integers(0, 255, (VO_H // 8, VO_W // 8), dtype=np.uint8)
    coarse = np.kron(blocks, np.ones((8, 8), dtype=np.uint8))
    fine = rng.integers(0, 32, (VO_H, VO_W), dtype=np.uint8)
    return np.clip(coarse.astype(np.int16) + fine, 0, 255).astype(np.uint8)


def camera_matrix(calib) -> np.ndarray:
    return np.array(
        [[calib.fx, 0.0, calib.cx], [0.0, calib.fy, calib.cy], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def warp_for_translation(calib, t_m) -> np.ndarray:
    """H mapping keyframe pixels to frame-F pixels after camera moves t_m."""
    K = camera_matrix(calib)
    t = np.asarray(t_m, dtype=np.float64).reshape(3, 1)
    n = np.array([[0.0], [0.0], [1.0]])
    H = K @ (np.eye(3) - (t @ n.T) / PLANE_Z) @ np.linalg.inv(K)
    return H


def warp_for_rotation(calib, rvec) -> np.ndarray:
    """H mapping keyframe pixels to frame-F pixels after camera rotates."""
    K = camera_matrix(calib)
    R, _ = cv2.Rodrigues(np.asarray(rvec, dtype=np.float64))
    return K @ R @ np.linalg.inv(K)


def make_metres(z_m: float = PLANE_Z, nan_left: bool = False) -> np.ndarray:
    grid = np.full((DEPTH_GRID, DEPTH_GRID), z_m, dtype=np.float32)
    if nan_left:
        grid[:, : DEPTH_GRID // 2] = np.nan
    return grid


def make_vo(h_chest: float = 2.0, metres=None):
    calib = guess_calibration(CAM_W, CAM_H, HFOV_DEG)
    vo = vo_core.Vo(
        calib, scale=1.0, h_chest=h_chest,
        cam_w=CAM_W, cam_h=CAM_H, vo_w=VO_W, vo_h=VO_H,
    )
    affine = make_affine(CAM_W, CAM_H, DEPTH_GRID, DEPTH_GRID)
    gray = make_texture()
    ok = vo.on_depth_frame(gray, metres if metres is not None else make_metres(),
                           affine, frame_id=1, t_ns=0)
    assert ok, "synthetic keyframe must be accepted"
    return vo, calib, gray


def rotation_angle_deg(R: np.ndarray) -> float:
    cos = (np.trace(R[:3, :3]) - 1.0) / 2.0
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


class VoCoreTests(unittest.TestCase):
    def test_pure_translation_recovered(self):
        vo, calib, gray = make_vo()
        t_true = np.array([0.05, 0.0, 0.0])
        frame = cv2.warpPerspective(gray, warp_for_translation(calib, t_true),
                                    (VO_W, VO_H))
        step = vo.step(frame, frame_id=2, t_ns=100_000_000)
        self.assertIsNotNone(step)
        self.assertTrue(step.valid, f"guard fired? disp={step.median_disp_px}")
        t_rec = step.T_world_from_cam[:3, 3]
        self.assertLess(abs(np.linalg.norm(t_rec) - 0.05), 0.05 * 0.05)
        cos_dir = float(np.dot(t_rec, t_true) /
                        (np.linalg.norm(t_rec) * np.linalg.norm(t_true)))
        self.assertLess(math.degrees(math.acos(max(-1.0, min(1.0, cos_dir)))), 5.0)

    def test_pure_rotation_recovered(self):
        # 10 deg total in 1 deg per-frame steps (~30 deg/s at stride 1): the
        # guard measures per-frame velocity, so slow scanning stays valid and
        # K->F accumulation is bounded by the 15 deg keyframe swap.
        vo, calib, gray = make_vo()
        metres = make_metres()
        affine = make_affine(CAM_W, CAM_H, DEPTH_GRID, DEPTH_GRID)
        rvec_step = np.array([0.0, math.radians(1.0), 0.0])
        H = warp_for_rotation(calib, rvec_step)
        frame = gray
        fid = 1
        for _ in range(10):
            frame = cv2.warpPerspective(frame, H, (VO_W, VO_H))
            fid += 1
            ok = vo.on_depth_frame(frame, metres, affine, frame_id=fid,
                                  t_ns=fid * 100_000_000)
            self.assertTrue(ok)
            step = vo.step(frame, frame_id=fid, t_ns=fid * 100_000_000)
            self.assertIsNotNone(step)
        self.assertTrue(step.valid, f"final step must be valid: "
                          f"disp={step.median_disp_px}")
        R_expected, _ = cv2.Rodrigues(np.array([0.0, math.radians(10.0), 0.0]))
        R_rec = step.T_world_from_cam[:3, :3]
        dR = R_rec @ R_expected   # R_rec is the world pose: inv(R_expected)
        self.assertLess(rotation_angle_deg(dR), 2.0)

    def test_step_skips_stale_frame(self):
        vo, calib, gray = make_vo()
        frame = cv2.warpPerspective(
            gray, warp_for_translation(calib, [0.05, 0.0, 0.0]), (VO_W, VO_H))
        first = vo.step(frame, frame_id=2, t_ns=100_000_000)
        self.assertTrue(first.valid)
        again = vo.step(frame, frame_id=2, t_ns=200_000_000)
        self.assertIsNone(again, "repeated frame_id must be a silent no-op")
        older = vo.step(gray, frame_id=1, t_ns=300_000_000)
        self.assertIsNone(older, "older frame_id must be a silent no-op")

    def test_depth_gate_rejects_invalid_cells(self):
        calib = guess_calibration(CAM_W, CAM_H, HFOV_DEG)
        affine = make_affine(CAM_W, CAM_H, DEPTH_GRID, DEPTH_GRID)
        pts_full = np.array([[40.0, 40.0], [280.0, 200.0], [160.0, 120.0]])
        pts3d, mask = vo_core.backproject(pts_full, make_metres(nan_left=True),
                                          affine, calib, 1.0)
        self.assertFalse(bool(mask[0]), "NaN-depth region must be excluded")
        self.assertTrue(bool(mask[1]))
        self.assertTrue(bool(mask[2]))
        # A keyframe whose depth is invalid everywhere must be refused, and
        # with no keyframe there is no pose to invent.
        vo = vo_core.Vo(calib, scale=1.0, h_chest=2.0,
                        cam_w=CAM_W, cam_h=CAM_H, vo_w=VO_W, vo_h=VO_H)
        nan_metres = np.full((DEPTH_GRID, DEPTH_GRID), np.nan, dtype=np.float32)
        ok = vo.on_depth_frame(make_texture(), nan_metres, affine,
                               frame_id=2, t_ns=0)
        self.assertFalse(ok)
        self.assertIsNone(vo.step(make_texture(), frame_id=2, t_ns=0))

    def test_fast_pan_invalidates_pose(self):
        vo, calib, gray = make_vo()
        small = cv2.warpPerspective(
            gray, warp_for_translation(calib, [0.05, 0.0, 0.0]), (VO_W, VO_H))
        good = vo.step(small, frame_id=2, t_ns=100_000_000)
        self.assertTrue(good.valid)
        pose_before = good.T_world_from_cam.copy()
        M = np.float32([[1.0, 0.0, -20.0], [0.0, 1.0, 0.0]])
        pan = cv2.warpAffine(gray, M, (VO_W, VO_H))
        bad = vo.step(pan, frame_id=3, t_ns=200_000_000)
        self.assertIsNotNone(bad, "a guard refusal is a step, not a skip")
        self.assertFalse(bad.valid)
        np.testing.assert_array_equal(bad.T_world_from_cam, pose_before,
                                      err_msg="guard must not move the pose")

    def test_no_floor_no_correction(self):
        calib = guess_calibration(CAM_W, CAM_H, HFOV_DEG)
        pts = np.array([[0.5, -1.0, 2.0], [-0.5, -1.5, 2.5], [0.2, -0.8, 1.8]])
        h = vo_core.fit_ground_height(pts, calib)
        self.assertIsNone(h, "points above the horizon are not a floor")
        window = deque()
        self.assertEqual(vo_core.scale_correction(h, 2.0, window), 1.0)
        self.assertEqual(len(window), 0, "None h_est must not touch the window")

    def test_watchdog_corrects_scale_error(self):
        calib = guess_calibration(CAM_W, CAM_H, HFOV_DEG)
        # A floor reconstructed at 0.5 m below the camera when the chest is
        # 2.0 m up: the classic 4x metric-scale failure.
        rng = np.random.default_rng(3)
        floor = np.column_stack([rng.uniform(-2, 2, 50),
                                 np.full(50, 0.5),
                                 rng.uniform(1.0, 4.0, 50)])
        h = vo_core.fit_ground_height(floor, calib)
        self.assertIsNotNone(h)
        self.assertLess(abs(h - 0.5), 0.05)
        window = deque()
        corr = vo_core.scale_correction(h, 2.0, window)
        self.assertGreater(corr, 4.0 * 0.9)
        self.assertLess(corr, 4.0 * 1.1)

    def test_keyframe_due_thresholds(self):
        ident = np.eye(4)
        moved = np.eye(4); moved[0, 3] = 0.05
        far = np.eye(4); far[0, 3] = 0.20
        R, _ = cv2.Rodrigues(np.array([0.0, math.radians(20.0), 0.0]))
        rot20 = np.eye(4); rot20[:3, :3] = R
        self.assertFalse(vo_core.keyframe_due(ident, n_tracks=100))
        self.assertFalse(vo_core.keyframe_due(moved, n_tracks=100))
        self.assertTrue(vo_core.keyframe_due(far, n_tracks=100))
        self.assertTrue(vo_core.keyframe_due(rot20, n_tracks=100))
        self.assertTrue(vo_core.keyframe_due(ident, n_tracks=30))

    def test_crumb_due_gates(self):
        self.assertTrue(vo_core.crumb_due(0, 500_000_000, 0.06))
        self.assertFalse(vo_core.crumb_due(0, 200_000_000, 0.06),
                         "under 0.4 s: no crumb")
        self.assertFalse(vo_core.crumb_due(0, 500_000_000, 0.03),
                         "under 5 cm: no crumb")


if __name__ == "__main__":
    unittest.main()
