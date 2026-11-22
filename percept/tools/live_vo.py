"""live_vo.py: camera pose from the live frames, so the 3D scene follows the camera.

live_probe runs YOLOE and depth on one frame. This feeds that same frame and depth
grid to vo_core.Vo and stamps the result on the world record: `pose.T_world_from_cam`
moves with the wearer, and every freshly seen point is moved from camera space to
world space (`xyz_world = T @ xyz_cam`). Points held from earlier frames are already
in world space and are left alone.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import cv2
import numpy as np

from percept.tools import vo_core

VO_WIDTH = 320
# The fast-pan guard is "~8 px per camera frame" (vo_core). Detection + depth run at
# ~8 Hz on a ~24-30 fps camera, so one step spans ~3-4 camera frames of motion; scale
# the guard like vo_probe.py does for --stride.
FRAMES_PER_STEP = 4


class LiveVo:
    """Stateful wrapper: one `update(probe)` per processed frame."""

    def __init__(self, depth_scale: float, h_chest: float = 0.0):
        self.depth_scale = float(depth_scale)
        # h_chest 0 turns the ground-height scale watchdog off (no measured height yet).
        self.h_chest = float(h_chest)
        self._vo: Optional[vo_core.Vo] = None
        self.pose = np.eye(4)
        self.valid = True  # identity until tracking starts: the Phase A pose

    def update(self, probe: Dict[str, Any]) -> bool:
        """Advance on this frame's pixels and depth; False when VO cannot run on them."""
        src = probe.get("_vo_input") or {}
        frame, depth, calib = src.get("frame"), src.get("depth"), src.get("calibration")
        if frame is None or depth is None or calib is None:
            return False
        h, w = frame.shape[:2]
        if self._vo is None:
            vo_h = max(48, int(round(h * VO_WIDTH / w)))
            cfg = vo_core.VoConfig()
            cfg.max_disp_px *= FRAMES_PER_STEP
            self._vo = vo_core.Vo(calib, self.depth_scale, self.h_chest, w, h, VO_WIDTH, vo_h, cfg)
        vo = self._vo
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (vo.vo_w, vo.vo_h),
                          interpolation=cv2.INTER_AREA)
        fid, t_ns = int(probe["frame_id"]), int(probe["t_ns"])
        vo.on_depth_frame(gray, depth, src["depth_affine"], fid, t_ns)
        step = vo.step(gray, fid, t_ns)
        if step is not None:
            self.pose, self.valid = step.T_world_from_cam, step.valid
            self.last_step = step
        return True


def _to_world(T: np.ndarray, xyz) -> list:
    return [float(v) for v in (T @ np.array([*xyz, 1.0]))[:3]]


def apply_pose(world: Dict[str, Any], T: np.ndarray, valid: bool) -> Dict[str, Any]:
    """Put T in the record's pose and move this frame's camera-space points to world space."""
    for obj in world.get("objects") or []:
        if obj.get("in_latest_boxes") and obj.get("xyz_cam"):
            obj["xyz_world"] = _to_world(T, obj["xyz_cam"])
    target = world.get("target")
    if target and target.get("in_latest_boxes") is not False and target.get("xyz_cam"):
        target["xyz_world"] = _to_world(T, target["xyz_cam"])
    hand = world.get("hand")
    if hand and hand.get("xyz_cam"):
        hand["xyz_world"] = _to_world(T, hand["xyz_cam"])
    world["pose"]["T_world_from_cam"] = [float(v) for v in T.reshape(-1)]
    world["pose"]["valid"] = bool(valid)
    return world
