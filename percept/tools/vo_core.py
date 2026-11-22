#!/usr/bin/env python3
"""VO geometry core: hybrid KLT front-end, depth-backed PnP, ground watchdog.

Spec: docs/superpowers/specs/2026-11-21-vo-integration-design.md. Pure
geometry — no models, no shm, no camera. The depth model, intrinsics, and
tape-gated depth scale arrive as arguments, mirroring the C++ `beacon::Vo`.

Conventions follow the Beacon spec: camera frame is +X right, +Y down,
+Z forward; `T_world_from_cam` is row-major 4x4; OpenCV PnP output is
`T_F_from_K` and the world chain is `T_world_from_K * inv(T_F_from_K)`.
"""

from __future__ import annotations

import math
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence, Tuple

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import probe_frame  # noqa: E402

VO_MAX_DISP_PX = 8.0        # rolling-shutter guard: faster than this is a fast pan
VO_MIN_TRACKS = 60          # below this a step is untrusted
VO_MIN_INLIERS = 15         # solvePnPRansac inlier floor
VO_FB_ERR_PX = 1.0          # forward-backward rejection threshold
VO_WINDOW = 10              # watchdog median window length


@dataclass
class VoConfig:
    h_chest_m: float = 1.4
    max_corners: int = 300
    fb_err_px: float = VO_FB_ERR_PX
    max_disp_px: float = VO_MAX_DISP_PX
    lk_win: Tuple[int, int] = (21, 21)   # wider windows + a taller pyramid let LK
    lk_level: int = 2                    # reach the large per-cycle steps of a
                                         # ~2 Hz live loop; 21/2 is the laptop default
    moved_m: float = 0.10
    rot_deg: float = 15.0
    min_tracks: int = VO_MIN_TRACKS
    min_inliers: int = VO_MIN_INLIERS
    depth_radius: int = 1          # 3x3 patch median at backprojection
    pnp_iterations: int = 200
    pnp_reproj_px: float = 2.0
    pnp_confidence: float = 0.99
    scale_tol: float = 0.25


@dataclass
class PoseResult:
    T_F_from_K: np.ndarray         # row-major 4x4
    inliers: int
    repro_px: float
    inlier_idx: np.ndarray         # indices into the input point arrays


@dataclass
class VoStep:
    valid: bool
    T_world_from_cam: np.ndarray   # row-major 4x4; last pose when invalid
    inliers: int
    h_est: Optional[float]
    scale_mult: float
    median_disp_px: float
    t_ns: int
    n_tracks: int = 0              # surviving LK tracks; 0 also when untrusted


def vo_pts_to_full(pts, vo_w: int, vo_h: int, cam_w: int, cam_h: int) -> np.ndarray:
    """(N,2) VO-scale pixels -> full-frame pixels, linear per axis."""
    pts = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
    return np.column_stack([pts[:, 0] * (cam_w / vo_w), pts[:, 1] * (cam_h / vo_h)])


def lk_track(prev_gray, cur_gray, pts, fb_err_px: float = VO_FB_ERR_PX,
             win: Tuple[int, int] = (21, 21),
             max_level: int = 2) -> Tuple[np.ndarray, np.ndarray, float]:
    """Forward-backward-checked LK tracking.

    Returns (tracked_pts (N,2), ok_mask (N,), median_disp_px over surviving
    tracks). The median is computed before any depth gate (plan ruling).
    """
    pts0 = np.asarray(pts, dtype=np.float32).reshape(-1, 1, 2)
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
    fwd, st_f, _ = cv2.calcOpticalFlowPyrLK(
        prev_gray, cur_gray, pts0, None, winSize=win, maxLevel=max_level,
        criteria=crit)
    back, st_b, _ = cv2.calcOpticalFlowPyrLK(
        cur_gray, prev_gray, fwd, None, winSize=win, maxLevel=max_level,
        criteria=crit)
    orig = pts0.reshape(-1, 2)
    fwd2 = fwd.reshape(-1, 2)
    fb = np.linalg.norm(back.reshape(-1, 2) - orig, axis=1)
    ok = (st_f.reshape(-1).astype(bool) & st_b.reshape(-1).astype(bool)
          & (fb <= fb_err_px))
    if ok.any():
        disp = np.linalg.norm(fwd2[ok] - orig[ok], axis=1)
        med = float(np.median(disp))
    else:
        med = float("inf")
    return fwd2, ok, med


def backproject(pts_full, metres, affine, calib,
                scale: float, depth_radius: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    """Full-frame pixels -> 3D camera-frame points via the depth grid.

    Per-point depth is probe_frame.depth_at_patch (3x3 median by default,
    letterbox-aware). Invalid cells (NaN / <= 0 / pad) yield mask 0.
    """
    pts_full = np.asarray(pts_full, dtype=np.float64).reshape(-1, 2)
    n = len(pts_full)
    pts3d = np.full((n, 3), np.nan, dtype=np.float64)
    mask = np.zeros(n, dtype=bool)
    for i in range(n):
        z = probe_frame.depth_at_patch(metres, affine, float(pts_full[i, 0]),
                                       float(pts_full[i, 1]), scale,
                                       radius=depth_radius)
        if z is None:
            continue
        x, y, zc = probe_frame.unproject(float(pts_full[i, 0]), float(pts_full[i, 1]),
                                         z, calib)
        pts3d[i] = (x, y, zc)
        mask[i] = True
    return pts3d, mask


def _camera_matrix(calib) -> np.ndarray:
    return np.array([[calib.fx, 0.0, calib.cx],
                      [0.0, calib.fy, calib.cy],
                      [0.0, 0.0, 1.0]], dtype=np.float64)


def solve_pose(pts3d, pts2d, calib,
               cfg: Optional[VoConfig] = None) -> Optional[PoseResult]:
    """solvePnPRansac on 3D-in-K / 2D-in-F. None below the inlier floor."""
    cfg = cfg or VoConfig()
    pts3d = np.asarray(pts3d, dtype=np.float64).reshape(-1, 3)
    pts2d = np.asarray(pts2d, dtype=np.float64).reshape(-1, 2)
    if len(pts3d) < 4 or len(pts3d) != len(pts2d):
        return None
    K = _camera_matrix(calib)
    ok, rvec, tvec, inl = cv2.solvePnPRansac(
        pts3d, pts2d, K, None,
        iterationsCount=cfg.pnp_iterations,
        reprojectionError=cfg.pnp_reproj_px,
        confidence=cfg.pnp_confidence,
        flags=cv2.SOLVEPNP_EPNP)
    if not ok:
        return None
    inl = np.asarray(inl).reshape(-1)
    if len(inl) < cfg.min_inliers:
        return None
    R, _ = cv2.Rodrigues(rvec)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = np.asarray(tvec, dtype=np.float64).reshape(3)
    proj, _ = cv2.projectPoints(pts3d[inl], rvec, tvec, K, None)
    repro = float(np.mean(np.linalg.norm(proj.reshape(-1, 2) - pts2d[inl], axis=1)))
    return PoseResult(T_F_from_K=T, inliers=int(len(inl)), repro_px=repro,
                     inlier_idx=inl)


def chain(T_world_from_K, T_F_from_K) -> np.ndarray:
    """T_world_from_F = T_world_from_K * inv(T_F_from_K) (spec §8)."""
    return np.asarray(T_world_from_K, dtype=np.float64) @ np.linalg.inv(
        np.asarray(T_F_from_K, dtype=np.float64))


def fit_ground_height(pts3d_cam, calib, min_pts: int = 20,
                      up_tol_deg: float = 30.0) -> Optional[float]:
    """Camera height above the ground plane fitted to below-horizon points.

    Returns None when the plane is not fittable: too few candidates, a
    degenerate fit, or a normal too far from up. `calib` is reserved for
    horizon banding that needs intrinsics; selection is Y > 0 (below the
    camera level) today.
    """
    pts = np.asarray(pts3d_cam, dtype=np.float64).reshape(-1, 3)
    cand = pts[pts[:, 1] > 0.0]
    if len(cand) < min_pts:
        return None
    centroid = cand.mean(axis=0)
    A = cand - centroid
    try:
        _, _, vt = np.linalg.svd(A, full_matrices=False)
    except np.linalg.LinAlgError:
        return None
    n = vt[-1]
    if n[1] > 0.0:
        n = -n
    n_norm = float(np.linalg.norm(n))
    if n_norm < 1e-9:
        return None
    n = n / n_norm
    angle_to_up = math.degrees(math.acos(max(-1.0, min(1.0, -n[1]))))
    if angle_to_up > up_tol_deg:
        return None
    return abs(float(np.dot(n, centroid)))


def scale_correction(h_est: Optional[float], h_chest: float, window: deque,
                     tol: float = 0.25) -> float:
    """Ground-height watchdog: translation-length multiplier for this step.

    Appends h_est to the window; when the latest h_est deviates from the
    measured chest height by more than tol, returns h_chest / median(window);
    otherwise 1.0. h_est None (floor not visible) leaves the window untouched
    and returns 1.0.
    """
    if h_est is None or not math.isfinite(h_est) or h_chest <= 0.0 or h_est <= 0.0:
        return 1.0
    window.append(float(h_est))
    if abs(h_est / h_chest - 1.0) <= tol:
        return 1.0
    med = float(np.median(window))
    if med <= 0.0:
        return 1.0
    return float(h_chest / med)


def keyframe_due(T_rel, n_tracks: int, moved_m: float = 0.10,
                 rot_deg: float = 15.0,
                 min_tracks: int = VO_MIN_TRACKS) -> bool:
    """True when the K->F motion or track starvation demands a new keyframe."""
    T = np.asarray(T_rel, dtype=np.float64)
    moved = float(np.linalg.norm(T[:3, 3]))
    cos = (np.trace(T[:3, :3]) - 1.0) / 2.0
    rot = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
    return moved >= moved_m or rot >= rot_deg or n_tracks < min_tracks


def crumb_due(last_crumb_ns: int, now_ns: int, moved_since_crumb_m: float,
              min_dt_ns: int = 400_000_000,
              min_move_m: float = 0.05) -> bool:
    """Crumb only after both the time and the distance gates pass (spec §8)."""
    return (now_ns - last_crumb_ns) >= min_dt_ns and moved_since_crumb_m >= min_move_m


class Vo:
    """Stateful VO step machine: keyframe in, pose steps out.

    `on_depth_frame` receives percept's in-process copy of a depth-complete
    frame (spec F9: never re-read the ring for keyframe material) and either
    promotes it as the first keyframe or holds it as the swap candidate.
    `step` consumes a fresh frame; None means "no step happened" (no
    keyframe, or a stale/repeated frame_id), a VoStep with valid=False means
    "step attempted, untrusted" — the pose never moves and never extrapolates.
    """

    def __init__(self, calibration, scale: float, h_chest: float,
                 cam_w: int, cam_h: int, vo_w: int, vo_h: int,
                 cfg: Optional[VoConfig] = None):
        self.calib = calibration
        self.scale = float(scale)
        self.cfg = cfg or VoConfig()
        self.cfg.h_chest_m = float(h_chest)
        self.cam_w, self.cam_h = int(cam_w), int(cam_h)
        self.vo_w, self.vo_h = int(vo_w), int(vo_h)
        self._window = deque(maxlen=VO_WINDOW)
        self._K = None            # active keyframe dict
        self._candidate = None    # most recent depth-complete frame
        self._last_frame_id = None
        self._pose = np.eye(4)    # world origin: first keyframe
        self._prev_gray = None    # last consumed frame, for the per-frame guard
        self._prev_pts = None

    def on_depth_frame(self, gray_vo, metres, affine, frame_id: int,
                      t_ns: int) -> bool:
        """Stage (and on first call promote) a depth-complete keyframe."""
        if gray_vo is None or metres is None:
            return False
        corners = cv2.goodFeaturesToTrack(
            gray_vo, maxCorners=self.cfg.max_corners, qualityLevel=0.01,
            minDistance=8.0, blockSize=7)
        if corners is None or len(corners) < self.cfg.min_tracks:
            return False
        pts2d_vo = corners.reshape(-1, 2)
        pts_full = vo_pts_to_full(pts2d_vo, self.vo_w, self.vo_h,
                                  self.cam_w, self.cam_h)
        pts3d, mask = backproject(pts_full, metres, affine, self.calib,
                                  self.scale, self.cfg.depth_radius)
        if int(mask.sum()) < self.cfg.min_tracks:
            return False
        self._candidate = {
            "gray": gray_vo, "pts2d_vo": pts2d_vo[mask], "pts3d": pts3d[mask],
            "frame_id": int(frame_id), "t_ns": int(t_ns),
        }
        if self._K is None:
            self._promote(np.eye(4))
        return True

    def _promote(self, T_world_from_K: np.ndarray) -> None:
        c = self._candidate
        self._K = dict(c)
        self._K["T_world_from_K"] = np.asarray(T_world_from_K, dtype=np.float64)
        # The per-frame guard anchors on the promoted keyframe's frame.
        self._prev_gray = self._K["gray"]
        self._prev_pts = self._K["pts2d_vo"]

    def _invalid(self, med_disp: float, t_ns: int, n_tracks: int = 0) -> VoStep:
        # Any untrusted step re-anchors to a newer depth-complete candidate
        # (bounds K->F drift by the depth cadence) but never moves the pose.
        if (self._candidate is not None and self._K is not None
                and self._candidate["frame_id"] > self._K["frame_id"]):
            self._promote(self._pose)
        return VoStep(valid=False, T_world_from_cam=self._pose.copy(),
                      inliers=0, h_est=None, scale_mult=1.0,
                      median_disp_px=med_disp, t_ns=int(t_ns),
                      n_tracks=int(n_tracks))

    def step(self, gray_vo, frame_id: int, t_ns: int) -> Optional[VoStep]:
        if self._K is None:
            return None
        if self._last_frame_id is not None and frame_id <= self._last_frame_id:
            return None
        self._last_frame_id = int(frame_id)
        K = self._K
        ptsF_vo, ok, med_disp = lk_track(K["gray"], gray_vo, K["pts2d_vo"],
                                          self.cfg.fb_err_px, self.cfg.lk_win,
                                          self.cfg.lk_level)
        # Rolling-shutter guard: spec says "~8 px/frame" — per camera frame.
        # Measure prev->F velocity, not K->F accumulation; K->F stays for PnP.
        if self._prev_gray is not None and self._prev_pts is not None \
                and len(self._prev_pts):
            _, ok_prev, med_prev = lk_track(self._prev_gray, gray_vo,
                                            self._prev_pts, self.cfg.fb_err_px,
                                            self.cfg.lk_win, self.cfg.lk_level)
            guard_disp = med_prev
        else:
            guard_disp = med_disp
        if ok.any():
            self._prev_gray = gray_vo
            self._prev_pts = ptsF_vo[ok]
        if guard_disp > self.cfg.max_disp_px:
            return self._invalid(guard_disp, t_ns, int(ok.sum()))   # fast pan: refuse, keep pose
        n_ok = int(ok.sum())
        if n_ok < self.cfg.min_tracks:
            return self._invalid(guard_disp, t_ns, n_ok)
        ptsF_full = vo_pts_to_full(ptsF_vo[ok], self.vo_w, self.vo_h,
                                   self.cam_w, self.cam_h)
        pts3d_ok = K["pts3d"][ok]
        res = solve_pose(pts3d_ok, ptsF_full, self.calib, self.cfg)
        if res is None:
            return self._invalid(guard_disp, t_ns, n_ok)
        h_est = fit_ground_height(pts3d_ok[res.inlier_idx], self.calib)
        mult = scale_correction(h_est, self.cfg.h_chest_m, self._window,
                                self.cfg.scale_tol)
        T_F = res.T_F_from_K.copy()
        T_F[:3, 3] *= mult                          # watchdog rescales translation
        T_world_from_F = chain(K["T_world_from_K"], T_F)
        if (self._candidate is not None
                and self._candidate["frame_id"] > K["frame_id"]
                and keyframe_due(T_F, n_ok, self.cfg.moved_m, self.cfg.rot_deg,
                                 self.cfg.min_tracks)):
            self._promote(T_world_from_F)
        self._pose = T_world_from_F
        return VoStep(valid=True, T_world_from_cam=T_world_from_F,
                      inliers=res.inliers, h_est=h_est, scale_mult=mult,
                      median_disp_px=guard_disp, t_ns=int(t_ns),
                      n_tracks=n_ok)
