import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_vo import LiveVo, apply_pose  # noqa: E402
from percept.tools import probe_frame  # noqa: E402


class FollowsCamera(unittest.TestCase):
    def test_pan_right_moves_pose_right(self):
        rng = np.random.default_rng(1)
        base = cv2.GaussianBlur(rng.integers(0, 255, (480, 900), dtype=np.uint8), (0, 0), 2)
        calib = probe_frame.Calibration(fx=554.0, fy=554.0, cx=320.0, cy=240.0)
        affine = probe_frame.make_affine(640, 480, 105, 105)
        flat = np.full((105, 105), 2.0, dtype=np.float32)  # a wall 2 m away
        vo = LiveVo(depth_scale=1.0)
        for i in range(8):
            # the camera slides right: the scene slides left 2 px per frame
            gray = base[:480, 2 * i : 2 * i + 640]
            probe = {"frame_id": i + 1, "t_ns": i * 33_000_000, "_vo_input": {
                "frame": cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), "depth": flat,
                "depth_affine": affine, "calibration": calib}}
            self.assertTrue(vo.update(probe))
        self.assertTrue(vo.valid)
        self.assertGreater(vo.pose[0, 3], 0.02)  # about 14 px * 2 m / 554 = 0.05 m right
        self.assertLess(abs(vo.pose[1, 3]), 0.02)


class ApplyPose(unittest.TestCase):
    def test_moves_fresh_points_and_keeps_held_ones(self):
        T = np.eye(4)
        T[:3, 3] = (1.0, 0.0, 2.0)  # camera stepped 1 m right, 2 m forward
        world = {
            "objects": [
                {"in_latest_boxes": True, "xyz_cam": [0, 0, 1], "xyz_world": [0, 0, 1]},
                {"in_latest_boxes": False, "xyz_cam": [0, 0, 1], "xyz_world": [9, 9, 9]},
            ],
            "target": {"xyz_cam": [0, 0, 1], "xyz_world": [0, 0, 1]},
            "hand": {"xyz_cam": [1, 0, 0], "xyz_world": [1, 0, 0]},
            "pose": {"valid": True, "T_world_from_cam": []},
        }
        apply_pose(world, T, valid=False)
        self.assertEqual(world["objects"][0]["xyz_world"], [1.0, 0.0, 3.0])
        self.assertEqual(world["objects"][1]["xyz_world"], [9, 9, 9])
        self.assertEqual(world["target"]["xyz_world"], [1.0, 0.0, 3.0])
        self.assertEqual(world["hand"]["xyz_world"], [2.0, 0.0, 2.0])
        self.assertEqual(world["pose"]["T_world_from_cam"][3], 1.0)
        self.assertFalse(world["pose"]["valid"])


if __name__ == "__main__":
    unittest.main()
