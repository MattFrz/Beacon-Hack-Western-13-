#!/usr/bin/env python3
"""live_probe.py: the percept loop driven by the QNX camera.

A grabber (``ingest/tools/beacon_grab.c``) keeps the newest C270 frame in a file.
This reads that file once per cycle, runs YOLOE and metric depth on **that same
array**, and puts the record on the wire:

    beacon_grab -w  ->  latest.jpg  ->  live_probe.py  ->  UDP 5006 -> ingest
                                                       \\-> UDP 5005 -> bridge

One frame in, one frame out: both nets see the same pixels with the same
``frame_id``, so a box unprojects through its own depth and nothing else. The
cycle is one frame at a time on purpose; a threaded grabber that fed YOLO and
depth from different frames would silently produce wrong metres.

Everything below the camera is the team's code: the parser, the per-frame probe
and the record builder are imported from ``probe_frame``/``probe_to_world``, and
the LIVE/HOLD/LOST bookkeeping mirrors ``probe_to_world.emit_lines`` exactly.

Usage (on the Pi, from the percept checkout):
    python3 percept/tools/live_probe.py --grab-file /tmp/live/latest.jpg \
        --udp 127.0.0.1:5006 --video-udp 10.80.55.91:5005 \
        --labels models/labels.txt --yolo models/yoloe26n_320.onnx \
        --depth models/depth_anything_v2_metric_indoor_small.onnx \
        --depth-scale 1.0 --fov 60 --conf 0.15 --ort-intra 3
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import socket
import threading
import sys
import time
from pathlib import Path
from collections import deque
from typing import Any, Dict, List, Optional, Sequence

# QNX's packaged onnxruntime ships the C library but not the pybind extension,
# so `import onnxruntime` raises. Install the ctypes shim before probe_frame
# imports it; on a normal host this is a no-op. The shim lives one level up
# (percept/ort_shim.py), so the checkout root has to be importable too.
# parents[0] is percept/tools, parents[1] is percept/, parents[2] is the root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
# This file's own directory goes on top: it holds the canonical probe_frame and
# probe_to_world. A stale copy of those at the checkout root must not win.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from percept import ort_shim  # noqa: E402

ort_shim.install()

import cv2  # noqa: E402  (probe_frame needs it too; VO uses it for gray frames)

import probe_frame  # noqa: E402
import probe_to_world as ptw  # noqa: E402
import vo_core  # noqa: E402
import hand_landmarks  # noqa: E402

IDENTITY_T = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]

# probe_once runs metric depth per frame but keeps the metres array local, so
# it never reaches this caller. VO needs exactly that array: its keyframes are
# depth-backed, and re-running the ~450 ms model on a second copy of the same
# pixels would halve the cycle rate. Wrapping the module attribute at runtime
# (not the file) captures the frame and the metres with zero extra cost, and
# keeps the one-frame rule: YOLO, depth and VO all see this cycle's pixels.
_DEPTH_CAPTURE: Dict[str, Any] = {}


def _install_depth_capture() -> None:
    """Capture (frame, metres) from each predict_depth call, once per process."""
    original = probe_frame.predict_depth
    if getattr(original, "_beacon_captured", False):
        return

    def _capturing(frame, *call_args, **call_kwargs):
        metres = original(frame, *call_args, **call_kwargs)
        _DEPTH_CAPTURE["frame"] = frame
        _DEPTH_CAPTURE["metres"] = metres
        return metres

    _capturing._beacon_captured = True  # type: ignore[attr-defined]
    probe_frame.predict_depth = _capturing


_FRAME_CAPTURE: Dict[str, Any] = {}


def _install_frame_capture() -> None:
    """Keep this cycle's frame, so the hand landmarker sees the same pixels.

    probe_once owns the frame and does not return it (it is large, and the
    record is serialised). Wrapping read_frame at runtime, the same way the
    depth capture works, keeps the one-frame rule: detection, depth, VO and the
    hand all read this cycle's array and nothing else.
    """
    original = probe_frame.ProbeResources.read_frame
    if getattr(original, "_beacon_captured", False):
        return

    def _capturing(resources):
        frame, frame_id, t_ns = original(resources)
        _FRAME_CAPTURE["frame"] = frame
        _FRAME_CAPTURE["frame_id"] = frame_id
        return frame, frame_id, t_ns

    _capturing._beacon_captured = True  # type: ignore[attr-defined]
    probe_frame.ProbeResources.read_frame = _capturing


def stamp_pose(world: Dict[str, Any], T: List[List[float]], valid: bool,
               step_t_ns: int, epoch: int) -> Dict[str, Any]:
    """Replace the phase-A identity pose with whatever VO last measured.

    probe_to_world stamps a *valid identity* pose because Phase A has no VO.
    Left alone it is worse than silence: guided's memory bearing freezes at
    the bind-time bearing, so after the wearer turns the voice keeps pointing
    where the target used to be. The honest pose is the last VO measurement,
    valid only while VO trusts it, aged from the step's own time so guided's
    freshness gate decides what is still trustworthy.
    """
    now_ns = int(world.get("t_ns") or 0)
    step_t = int(step_t_ns or 0)
    stamped = dict(world)
    stamped["pose"] = {
        "valid": bool(valid),
        "pose_epoch": int(epoch),
        "t_ns": step_t,
        "age_ns": (now_ns - step_t) if now_ns > step_t else 0,
        "T_world_from_cam": [[float(v) for v in row] for row in T],
    }
    return stamped


def _project_vec(vec: Sequence[float], T: List[List[float]]) -> List[float]:
    x, y, z = (float(v) for v in vec)
    return [
        T[0][0] * x + T[0][1] * y + T[0][2] * z + T[0][3],
        T[1][0] * x + T[1][1] * y + T[1][2] * z + T[1][3],
        T[2][0] * x + T[2][1] * y + T[2][2] * z + T[2][3],
    ]


def project_rows(world: Dict[str, Any], T: List[List[float]]) -> Dict[str, Any]:
    """Fresh rows carry their world position: xyz_world = T_world_from_cam @ xyz_cam.

    Remembered rows (in_latest_boxes false) keep the position baked at their
    sighting -- world coordinates do not move when the camera does. The hand is
    always a fresh sighting (it only exists while in frame) and projects the
    same way. `T` is a row-major 4x4 nested list.
    """
    projected = dict(world)
    objects: List[Dict[str, Any]] = []
    for row in world.get("objects") or []:
        if (isinstance(row, dict) and row.get("in_latest_boxes")
                and isinstance(row.get("xyz_cam"), (list, tuple))):
            row = dict(row)
            row["xyz_world"] = _project_vec(row["xyz_cam"], T)
        objects.append(row)
    projected["objects"] = objects
    hand = world.get("hand")
    if isinstance(hand, dict) and isinstance(hand.get("xyz_cam"), (list, tuple)):
        hand = dict(hand)
        hand["xyz_world"] = _project_vec(hand["xyz_cam"], T)
        projected["hand"] = hand
    target = world.get("target")
    if (isinstance(target, dict) and target.get("in_latest_boxes")
            and isinstance(target.get("xyz_cam"), (list, tuple))):
        target = dict(target)
        target["xyz_world"] = _project_vec(target["xyz_cam"], T)
        projected["target"] = target
    return projected


def capture_memory(world: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Deep copy of the rows we stand behind, marked not-in-latest-boxes.

    These are what a late FIND binds to: each row keeps its true last_seen_ns
    (guided ages it), its baked world position, and the not-in-latest flag so
    nothing treats it as currently visible.
    """
    rows = copy.deepcopy(world.get("objects") or [])
    for row in rows:
        if isinstance(row, dict):
            row["in_latest_boxes"] = False
    return rows


def inject_memory(world: Dict[str, Any], rows: List[Dict[str, Any]], seen_ns: int,
                  memory_s: float, now_ns: int) -> tuple[Dict[str, Any], bool]:
    """Carry remembered rows on a LOST record so a late FIND can bind (§9, 20 s).

    The wire's mode stays LOST -- the target is genuinely not visible; guided
    recomputes its own mode from the bound target and only uses these rows for
    binding and the remembered bearing. Rows expire with --memory-s, which must
    match BEACON_MEMORY_BIND_MAX_NS in guided.
    """
    if not rows:
        return world, False
    age_ns = now_ns - int(seen_ns) if now_ns > int(seen_ns) else 0
    if age_ns >= memory_s * 1_000_000_000:
        return world, False
    merged = dict(world)
    merged["objects"] = copy.deepcopy(rows) + list(world.get("objects") or [])
    return merged, True


# The dashboard's hand colour (#ff5fa2), so the drawn skeleton matches the 3D marker.
HAND_PREVIEW_BGR = (162, 95, 255)


def annotate_hand_preview(jpeg: bytes, hand: Dict[str, Any], frame_w: int,
                          frame_h: int, quality: int = 60) -> bytes:
    """Draw the landmark hand on the preview JPEG the dashboard already shows.

    The composite is the RGB panel on top (boxes, labels, ranges) and the depth
    map below it, both at the preview's width, so the landmarks -- full-frame
    pixels -- scale by panel width over frame width and land on the top panel.

    This exists because the hand is the one thing on the wire with no box in
    shared memory (beacon_hand_t carries a point, not a rectangle), so the
    dashboard cannot overlay it from telemetry the way it does for objects. The
    skeleton goes into the pixels instead: 21 dots, the palm box, the index
    fingertip and the distance, which is enough to see whether the hand is being
    tracked and where the wearer's own reach is being measured from.

    Returns the JPEG unchanged when it cannot be decoded or has no landmarks.
    """
    import cv2
    import numpy as np

    points = hand.get("landmarks_px") or []
    if not points or frame_w <= 0 or frame_h <= 0:
        return jpeg
    image = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return jpeg

    preview_h, preview_w = image.shape[:2]
    panel_h = max(1, min(preview_h, round(frame_h * preview_w / float(frame_w))))
    panel = image[:panel_h]  # a view: drawing on it draws on the composite
    sx = preview_w / float(frame_w)
    sy = panel_h / float(frame_h)
    scale = lambda u, v: (int(round(float(u) * sx)), int(round(float(v) * sy)))

    box = hand.get("bbox_px")
    if isinstance(box, (list, tuple)) and len(box) >= 4:
        cv2.rectangle(panel, scale(box[0], box[1]), scale(box[2], box[3]),
                      HAND_PREVIEW_BGR, 2)
    drawn = [scale(u, v) for u, v in points if len(tuple((u, v))) == 2]
    for point in drawn:
        cv2.circle(panel, point, 3, HAND_PREVIEW_BGR, -1)
    tip = hand.get("tip_px")
    if isinstance(tip, (list, tuple)) and len(tip) >= 2:
        cv2.circle(panel, scale(tip[0], tip[1]), 5, (0, 255, 255), 2)

    label = "hand"
    xyz = hand.get("xyz_cam")
    if isinstance(xyz, (list, tuple)) and len(xyz) == 3:
        label = f"hand {float(xyz[2]):.2f}m"
    origin = drawn[0]
    cv2.putText(panel, label, (max(0, origin[0] - 8), max(10, origin[1] - 6)),
                getattr(cv2, "FONT_HERSHEY_SIMPLEX", 0), 0.4, HAND_PREVIEW_BGR, 1)

    ok, encoded = cv2.imencode(
        ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    )
    return encoded.tobytes() if ok else jpeg


HAND_STATE_PATH = Path("/tmp/live/hand.json")


def publish_hand_state(hand: Optional[Dict[str, Any]], frame_w: int, frame_h: int) -> None:
    """Drop the landmark hand where the 24 fps preview can pick it up.

    The dashboard's camera is live_preview's stream, not this record cadence, and
    shared memory carries a hand point rather than a rectangle -- so the only way
    to draw a skeleton on the smooth video without touching beacon.h is to leave
    the landmarks in a file both processes already share (/tmp/live). Stale or
    absent, live_preview stops drawing: a hand that is no longer seen must not
    linger on the monitor.

    Never raises: a monitor preview must not be able to stop perception.
    """
    try:
        if hand is None or not hand.get("landmarks_px"):
            HAND_STATE_PATH.unlink(missing_ok=True)
            return
        payload = {
            "mono_ns": time.monotonic_ns(),
            "t_ns": hand.get("t_ns"),
            "W": int(frame_w),
            "H": int(frame_h),
            "conf": hand.get("conf"),
            "presence": hand.get("presence"),
            "bbox_px": hand.get("bbox_px"),
            "landmarks_px": hand.get("landmarks_px"),
            "tip_px": hand.get("tip_px"),
            "xyz_cam": hand.get("xyz_cam"),
        }
        HAND_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        HAND_STATE_PATH.write_text(json.dumps(payload, separators=(",", ":")))
    except (OSError, TypeError, ValueError):
        pass


class VoRunner:
    """VO stepping on the grabber's cadence, in a daemon thread.

    The probe cycle is depth-bound (~0.6 s): stepping VO only inside it made
    every step three to five native frames of motion, and measured turns
    collapsed LK (28-135 px steps, 1-25 surviving tracks). At the grabber's
    ~5 Hz the same turn is 6-10 px per step -- the regime the offline clips
    validated. The main thread still stages every keyframe from the record's
    own captured frame + metres (one-frame rule); this thread only steps.
    """

    def __init__(self, vo, grab_file: Path):
        self.vo = vo
        self.grab_file = grab_file
        self.lock = threading.Lock()
        self.n = 0
        self._last_fp: Optional[bytes] = None
        self.latest = None          # {"T", "valid", "t_ns"} of the last step
        self.stop = threading.Event()
        self.steps = 0
        self.valid_steps = 0
        self.bad_streak = 0
        self.last_printed_yaw = 0.0
        self.max_step_ms = 0.0

    # JPEG headers are fixed per camera; the scan data differs early, so a
    # few kilobytes past the headers identify a new frame.
    FRAME_SKIP_BYTES = 512
    FRAME_PROBE_BYTES = 4096

    def _frame_fingerprint(self) -> Optional[bytes]:
        """Content fingerprint of the grab file; None when unreadable.

        On QNX the file's mtime ticks only about once per second while the
        grabber writes ~20 fps, so mtime cannot be the new-frame signal
        (measured on the Pi, 2026-11-22: mtime-triggered VO stepped ~1 Hz and
        a natural turn was 28-105 px per step). The content probe is a few
        kilobytes per poll, ~20-30 polls/s.
        """
        try:
            with self.grab_file.open("rb") as fh:
                fh.seek(self.FRAME_SKIP_BYTES)
                return fh.read(self.FRAME_PROBE_BYTES)
        except OSError:
            return None

    def _poll_once(self) -> bool:
        """Step on a new grab frame; False when nothing new arrived."""
        fp = self._frame_fingerprint()
        if fp is None:
            self.stop.wait(0.05)
            return False
        if fp == self._last_fp:
            self.stop.wait(0.03)
            return False
        self._last_fp = fp
        frame = cv2.imread(str(self.grab_file), cv2.IMREAD_GRAYSCALE)
        if frame is None:
            return False  # corrupt frame consumed; wait for the next
        gray = cv2.resize(frame, (self.vo.vo_w, self.vo.vo_h),
                          interpolation=cv2.INTER_AREA)
        started = time.monotonic_ns()
        with self.lock:
            self.n += 1
            step = self.vo.step(gray, self.n, time.monotonic_ns())
        step_ms = (time.monotonic_ns() - started) / 1e6
        if step_ms > self.max_step_ms:
            self.max_step_ms = step_ms
        if step is None:
            return True
        self.steps += 1
        self.latest = {
            "T": step.T_world_from_cam.tolist(),
            "valid": bool(step.valid),
            "t_ns": int(step.t_ns),
        }
        yaw = math.degrees(math.atan2(
            step.T_world_from_cam[0][2], step.T_world_from_cam[2][2]))
        if step.valid:
            self.valid_steps += 1
            if self.bad_streak >= 3:
                print("live_probe: VO recovered",
                      file=sys.stderr, flush=True)
            self.bad_streak = 0
            if (self.valid_steps % 25 == 1
                    or abs(yaw - self.last_printed_yaw) >= 2.0):
                t = step.T_world_from_cam[:3, 3]
                print(
                    f"live_probe: VO ok #{self.valid_steps} "
                    f"yaw {yaw:+.1f} deg "
                    f"t=[{t[0]:.2f},{t[1]:.2f},{t[2]:.2f}] "
                    f"inliers {step.inliers}/{step.n_tracks} "
                    f"disp {step.median_disp_px:.0f} px "
                    f"step {step_ms:.0f}ms max {self.max_step_ms:.0f}ms",
                    file=sys.stderr, flush=True)
                self.last_printed_yaw = yaw
        else:
            self.bad_streak += 1
            reason = ("fast pan" if step.median_disp_px > self.vo.cfg.max_disp_px
                      else "too few tracks" if step.n_tracks < self.vo.cfg.min_tracks
                      else "pnp failed")
            print(
                f"live_probe: VO untrusted ({reason}: disp "
                f"{step.median_disp_px:.0f} px, tracks "
                f"{step.n_tracks}, inliers {step.inliers}) "
                f"yaw {yaw:+.1f} deg",
                file=sys.stderr, flush=True)
        return True

    def run(self) -> None:
        while not self.stop.is_set():
            self._poll_once()

def _make_vo(args: argparse.Namespace, frame_w: int, frame_h: int):
    """Build the VO step machine; None (with a warning) when there are no intrinsics."""
    notes: List[str] = []
    calibration = probe_frame.resolve_calibration(args, frame_w, frame_h, notes)
    if calibration is None:
        print("live_probe: VO off: no camera intrinsics (--fov or --calib)",
              file=sys.stderr, flush=True)
        return None
    vo_w = max(64, int(getattr(args, "vo_width", 320)))
    vo_h = max(48, int(round(frame_h * vo_w / max(1, frame_w))))
    cfg = vo_core.VoConfig(h_chest_m=float(getattr(args, "h_chest", 1.4)))
    # The spec guard is ~8 px per *native camera frame*; this loop consumes
    # frames at its own slower cadence, so the per-step threshold is a flag.
    cfg.max_disp_px = float(getattr(args, "vo_max_disp", 60.0))
    # Device reality: MJPEG frames through the sensor framework are noisier
    # than the laptop webcam LK was tuned on, and the forward-backward check
    # starved tracks right at the 60-floor even on static scenes (measured:
    # 54-59 surviving vs 60 required). More corners in the pool, a slightly
    # looser FB gate, and a floor above PnP's real needs (15 inliers).
    cfg.max_corners = int(getattr(args, "vo_max_corners", 500))
    cfg.fb_err_px = float(getattr(args, "vo_fb_err", 1.5))
    cfg.min_tracks = int(getattr(args, "vo_min_tracks", 40))
    cfg.lk_win = (int(getattr(args, "vo_win", 31)),) * 2
    cfg.lk_level = int(getattr(args, "vo_levels", 4))
    return vo_core.Vo(
        calibration, scale=float(args.depth_scale),
        h_chest=float(getattr(args, "h_chest", 1.4)),
        cam_w=frame_w, cam_h=frame_h, vo_w=vo_w, vo_h=vo_h, cfg=cfg,
    )


def build_parser() -> argparse.ArgumentParser:
    """The team's flags, plus the ones that describe where live frames come from."""
    parser = ptw.build_parser()
    parser.add_argument(
        "--grab-file",
        type=Path,
        default=Path("/tmp/live/latest.jpg"),
        help="newest camera frame written by beacon_grab (default /tmp/live/latest.jpg)",
    )
    parser.add_argument(
        "--video-udp",
        nargs="?",
        const="",
        default=None,
        help="send the downscaled preview JPEG to HOST:PORT (the bridge on the laptop); "
        "bare flag uses the --udp host",
    )
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=0.0,
        help="stop after this long; 0 runs until SIGINT (default 0)",
    )
    parser.add_argument(
        "--max-depth",
        type=float,
        default=3.0,
        help="only report objects whose measured forward distance is within this many "
        "metres (default 3.0); 0 disables the gate. The metric depth model is not yet "
        "tape-calibrated, so this gates on the model's own metres -- see docs/pi-bringup.md.",
    )
    parser.add_argument(
        "--publish-every",
        type=int,
        default=1,
        help="send one record every N processed frames (default 1)",
    )
    parser.add_argument(
        "--vo", action=argparse.BooleanOptionalAction, default=True,
        help="run visual odometry on the same frames as YOLO and depth "
             "(default on; needs --depth)",
    )
    parser.add_argument(
        "--h-chest", type=float, default=1.4, metavar="M",
        help="camera height above the floor for the VO watchdog (default 1.4 m; "
             "tape-measure it before trusting metres)",
    )
    parser.add_argument(
        "--vo-width", type=int, default=320,
        help="VO gray working width in px (default 320)",
    )
    parser.add_argument(
        "--vo-max-disp", type=float, default=60.0, metavar="PX",
        help="refuse a VO step whose motion exceeds this many px per probe cycle "
             "(default 60). The spec guard is ~8 px per native camera frame; this "
             "loop consumes frames near 2 Hz, so the threshold is per cycle. Turn "
             "slowly: a 180 deg turn should take ten seconds or more.",
    )
    parser.add_argument(
        "--vo-max-corners", type=int, default=500,
        help="goodFeaturesToTrack pool size for VO (default 500 on device)",
    )
    parser.add_argument(
        "--vo-fb-err", type=float, default=1.5, metavar="PX",
        help="forward-backward LK rejection threshold (default 1.5 px; "
             "1.0 starved tracks on MJPEG frames)",
    )
    parser.add_argument(
        "--vo-min-tracks", type=int, default=40,
        help="untrusted step below this many surviving tracks (default 40; "
             "PnP only needs 15 inliers)",
    )
    parser.add_argument(
        "--vo-win", type=int, default=31, metavar="PX",
        help="LK window side (default 31; 21 is the offline-tuning default, "
             "too small for per-cycle steps at a ~2 Hz live loop)",
    )
    parser.add_argument(
        "--vo-levels", type=int, default=4,
        help="LK pyramid levels (default 4; reaches ~150 px steps)",
    )
    # The YOLO `hand` class is the fallback path, and on-device it scores
    # 0.05-0.25, so live_probe lowers only that class's bar. probe_frame owns the
    # flag; this only changes its default.
    parser.set_defaults(yolo_hand_conf=0.05)
    parser.add_argument(
        "--memory-s", type=float, default=20.0, metavar="S",
        help="carry remembered rows on LOST records so a late FIND can bind, in "
             "seconds (default 20; must match BEACON_MEMORY_BIND_MAX_NS in guided)",
    )
    return parser


def _open_sock(
    target: Optional[str], default_host: Optional[str]
) -> tuple[Optional[socket.socket], Optional[tuple[str, int]]]:
    """Return (socket, address); socket objects have no __dict__, so keep them apart."""
    if target is None:
        return None, None
    if target == "":
        if default_host is None:
            return None, None
        target = default_host
    host, port = ptw.parse_udp_target(target)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # QNX's default UDP send buffer is too small for a preview JPEG and sendto()
    # fails with EMSGSIZE. Ask for a big one; ignore failure and let the per-send
    # guard below report it instead.
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
    except OSError:
        pass
    return sock, (host, port)


def gate_by_depth(
    world: Dict[str, Any], max_depth: float
) -> tuple[Dict[str, Any], int]:
    """Drop objects the depth model places beyond `max_depth` metres ahead.

    A monitor-grade model is confidently wrong at range: a bottle on the desk and
    the far wall of the hall come back with the same order of magnitude. Rather
    than speak a number we do not believe, an object that measures farther than
    the gate is not reported at all -- and if nothing survives, the record says
    LOST instead of claiming a target it cannot locate.

    Returns (world, dropped_count); the input dict is not modified.
    """
    if max_depth <= 0:
        return world, 0

    def forward_m(obj: Dict[str, Any]) -> Optional[float]:
        for key in ("xyz_cam", "xyz_world"):
            vec = obj.get(key)
            if isinstance(vec, (list, tuple)) and len(vec) == 3:
                try:
                    return float(vec[2])
                except (TypeError, ValueError):
                    return None
        return None

    kept: List[Dict[str, Any]] = []
    dropped = 0
    for obj in world.get("objects") or []:
        z = forward_m(obj)
        if z is None or z <= max_depth:
            kept.append(obj)
        else:
            dropped += 1
    if not dropped:
        return world, 0

    gated = dict(world)
    gated["objects"] = kept
    target = gated.get("target")
    if target is not None:
        names = {obj.get("name") for obj in kept}
        if target.get("name") not in names:
            gated["target"] = None
            gated.pop("d_m", None)
    if not kept:
        # Nothing we are willing to stand behind is in range.
        gated["mode"] = "LOST"
        gated["target"] = None
        gated.pop("d_m", None)
    return gated, dropped


HAND_MIN_Z_M = 0.2  # the wearer's own hand, seen from a chest camera, is within arm's reach
HAND_MAX_Z_M = 0.8
# Across-the-knuckles palm width of an adult hand, landmark 5 to landmark 17.
# An anthropometric constant, not a measurement of this wearer: +-20% between
# adults, so a landmark hand's distance is an estimate with that error, which is
# still finer than the 0.2-0.8 m clamp the box path needs.
HAND_PALM_WIDTH_M = 0.085
HAND_PALM_LANDMARKS = (5, 17)


def _boxes_touch(a: Sequence[float], b: Sequence[float], pad: float = 0.15) -> bool:
    """True when box a overlaps box b grown by `pad` of its size on each side."""
    bw, bh = b[2] - b[0], b[3] - b[1]
    return not (a[2] < b[0] - pad * bw or a[0] > b[2] + pad * bw
                or a[3] < b[1] - pad * bh or a[1] > b[3] + pad * bh)


def place_hand(world: Dict[str, Any], frame_w: int, frame_h: int,
               hfov_deg: float) -> Dict[str, Any]:
    """Give the hand a usable 3D point; the depth model cannot measure a hand.

    Measured on the Pi: a hand ~0.3 m away read 0.5-3.7 m, so REACH (d <= 0.5 m)
    never started. Two facts fix it without guessing: (1) a hand whose box
    touches an object's box is at that object, so it takes that object's depth
    (the lateral offset still comes from the boxes, so the ticks still steer);
    (2) otherwise the wearer's own hand is within arm's reach, so its depth is
    clamped to 0.2-0.8 m. The direction from the camera is kept either way.
    Returns a new world dict; unchanged when there is no hand box or geometry.
    """
    hand = world.get("hand")
    if not isinstance(hand, dict) or not hand.get("bbox_px") or frame_w <= 0 or frame_h <= 0:
        return world
    x0, y0, x1, y1 = (float(v) for v in hand["bbox_px"])
    u, v = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    f = frame_w / (2.0 * math.tan(math.radians(hfov_deg) / 2.0))
    z = None
    for obj in world.get("objects") or []:
        if (isinstance(obj, dict) and obj.get("in_latest_boxes") and obj.get("bbox_px")
                and isinstance(obj.get("xyz_cam"), (list, tuple))
                and _boxes_touch((x0, y0, x1, y1), obj["bbox_px"])):
            z = float(obj["xyz_cam"][2])
            break
    if z is None and isinstance(hand.get("palm_width_px"), (int, float)):
        # A landmark hand knows its own palm width in pixels, so the pinhole
        # gives a real distance instead of the clamp: z = f * W_palm / w_px.
        palm_px = float(hand["palm_width_px"])
        if palm_px > 1.0:
            z = f * HAND_PALM_WIDTH_M / palm_px
    if z is None:
        raw = hand.get("xyz_cam")
        z = float(raw[2]) if isinstance(raw, (list, tuple)) and len(raw) == 3 else HAND_MAX_Z_M
    z = min(max(z, HAND_MIN_Z_M), HAND_MAX_Z_M)
    placed = dict(hand)
    placed["xyz_cam"] = [(u - frame_w / 2.0) / f * z, (v - frame_h / 2.0) / f * z, z]
    out = dict(world)
    out["hand"] = placed
    return out


def lift_hand(world: Dict[str, Any]) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Move a `hand` detection out of objects[] into the record's hand field.

    MediaPipe cannot run on QNX (its pybind11 proto caster is broken there), so the
    hand arrives as an ordinary YOLO class instead. The guidance law does not want
    landmarks -- law.c only asks "is the hand converging on the target", which needs
    one point, and a box centroid unprojected through the same depth grid gives it.

    Lifting keeps objects[] meaning "things you can find": a hand is not a target
    and must not win a FIND, nor show up as a findable box on the dashboard. When
    this returns a hand, it has the same shape probe_to_world emits, so ingest and
    guided cannot tell the difference.

    Returns (world, hand); the input dict is not modified.
    """
    objects = world.get("objects") or []
    hand_objs = [
        obj
        for obj in objects
        if isinstance(obj, dict) and str(obj.get("name", "")).lower() == "hand"
    ]
    if not hand_objs:
        return world, None

    best = max(hand_objs, key=lambda obj: float(obj.get("conf") or 0.0))
    hand: Dict[str, Any] = {
        "t_ns": world.get("t_ns"),
        "frame_id": best.get("frame_id"),
    }
    if "conf" in best:
        hand["conf"] = best["conf"]
    if best.get("bbox_px") is not None:
        hand["bbox_px"] = best["bbox_px"]  # so the dashboard can draw the hand on the live video
    if isinstance(best.get("xyz_cam"), (list, tuple)):
        hand["xyz_cam"] = list(best["xyz_cam"])
    if isinstance(best.get("xyz_world"), (list, tuple)):
        hand["xyz_world"] = list(best["xyz_world"])

    lifted = dict(world)
    lifted["objects"] = [
        obj for obj in objects if not isinstance(obj, dict) or str(obj.get("name", "")).lower() != "hand"
    ]
    lifted["hand"] = hand
    target = lifted.get("target")
    if isinstance(target, dict) and str(target.get("name", "")).lower() == "hand":
        lifted["target"] = None
        lifted.pop("d_m", None)
    return lifted, hand


def hand_row_from_landmarks(world: Dict[str, Any], found: Dict[str, Any],
                            frame_id: Any) -> Optional[Dict[str, Any]]:
    """The record's hand{} from 21 landmarks, in the shape the YOLO lift emits.

    The point the law subtracts is the centre of the landmark set, not a box
    centre: the wrist, the knuckles and the fingertips all move during a reach
    while their centroid does not. `tip_px` and the landmarks ride along so the
    dashboard can draw the real hand, and `palm_width_px` gives place_hand a
    geometric distance instead of a clamp.

    Confidence is the palm score times the landmark model's presence score: the
    law gates on one number, and both stages have to agree before the cue moves.
    """
    points = [
        (float(point[0]), float(point[1]))
        for point in (found.get("landmarks_px") or [])
        if isinstance(point, (list, tuple)) and len(point) >= 2
    ]
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    conf = float(found.get("conf") or 0.0) * float(found.get("presence") or 0.0)
    hand: Dict[str, Any] = {
        "t_ns": world.get("t_ns"),
        "frame_id": frame_id,
        "conf": conf,
        "bbox_px": [min(xs), min(ys), max(xs), max(ys)],
        "landmarks_px": [[u, v] for u, v in points],
        "presence": float(found.get("presence") or 0.0),
    }
    tip = found.get("tip_px")
    if isinstance(tip, (list, tuple)) and len(tip) >= 2:
        hand["tip_px"] = [float(tip[0]), float(tip[1])]
    palm = [points[i] for i in HAND_PALM_LANDMARKS if i < len(points)]
    if len(palm) == 2:
        hand["palm_width_px"] = math.dist(palm[0], palm[1])
    return hand


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    grab_file: Path = args.grab_file
    if not grab_file.exists():
        parser.error(f"no camera frame at {grab_file}: start beacon_grab first")

    # read_frame() reads args.image on every call, which is exactly the live
    # behaviour we want: same path, newest bytes, fresh frame_id each cycle.
    args.image = grab_file
    args.once = False
    # Composite previews are stacked (boxes + depth), so keep them small enough
    # to stay in one UDP datagram under the bridge's 60 KB limit.
    args.preview_width = min(int(getattr(args, "preview_width", 320) or 320), 480)
    args.preview_quality = int(getattr(args, "preview_quality", 60) or 60)

    world_sock, world_addr = _open_sock(args.udp, None)
    video_sock, video_addr = _open_sock(getattr(args, "video_udp", None), "127.0.0.1:5005")
    publish_every = max(1, int(getattr(args, "publish_every", 1)))

    labels, mean, std, pad_color, resources = probe_frame.prepare(args)
    deadline = time.monotonic() + args.max_seconds if args.max_seconds > 0 else None

    # The landmark hand replaces the YOLO `hand` class whenever it finds one. It
    # is optional on purpose: a missing TFLite runtime or bundle must not stop
    # perception, it only means the weaker fallback path is all this run has.
    # --hand-model is probe_frame's MediaPipe .task flag; here the same bundle is
    # run through TFLite, because the MediaPipe binding cannot build a
    # HandLandmarker on QNX. --hand-conf is the palm/landmark score floor.
    hand_finder = None
    if getattr(args, "hand_model", None) is not None:
        try:
            hand_finder = hand_landmarks.HandLandmarks(
                args.hand_model, min_score=float(args.hand_conf),
                min_presence=float(args.hand_conf), threads=1
            )
            _install_frame_capture()
            print(
                f"live_probe: hand landmarks armed from {args.hand_model} "
                f"(score >= {args.hand_conf:g})",
                file=sys.stderr, flush=True,
            )
        except Exception as exc:  # missing runtime, bad bundle: fall back
            print(
                f"live_probe: hand landmarks unavailable ({exc}); "
                "falling back to the YOLO `hand` class",
                file=sys.stderr, flush=True,
            )

    seq = 0
    seen = 0
    sent = 0
    world_errors = 0
    dropped_video = 0
    dropped_far = 0
    hands_seen = 0
    max_depth = float(getattr(args, "max_depth", 3.0) or 0.0)
    last_mtime = 0
    last_d_m: Optional[float] = None
    last_seen_ns: Optional[int] = None
    vision_ns: deque = deque(maxlen=60)  # age of vision at refresh, newest 60 records
    prev_frame_ns = 0
    last_objects: Optional[List[Dict[str, Any]]] = None
    last_target: Optional[Dict[str, Any]] = None

    use_vo = bool(getattr(args, "vo", True)) and args.depth is not None
    if use_vo:
        _install_depth_capture()
        print("live_probe: VO armed (depth-backed PnP on the same frames)",
              file=sys.stderr, flush=True)
    vo = None
    vo_runner: Optional[VoRunner] = None
    memory_rows: List[Dict[str, Any]] = []
    memory_seen_ns = 0
    memory_injected = 0
    memory_s = max(0.0, float(getattr(args, "memory_s", 20.0)))

    print(f"live_probe: watching {grab_file}", file=sys.stderr, flush=True)
    try:
        with resources:
            while True:
                if deadline is not None and time.monotonic() > deadline:
                    break

                try:
                    mtime = grab_file.stat().st_mtime_ns
                except OSError:
                    mtime = last_mtime
                if mtime == last_mtime:
                    # No new frame yet. Wait for one instead of reprocessing the
                    # same pixels: a repeated frame would refresh LIVE while the
                    # camera is actually stalled, which is the opposite of the
                    # honesty rule the law is built on.
                    time.sleep(0.02)
                    continue
                last_mtime = mtime

                # want_preview renders the stacked composite: RGB with YOLO boxes,
                # labels and ranges on top, the colourised metric depth map with the
                # same boxes underneath. That is what the monitor should see; the raw
                # camera JPEG would show pixels with nothing drawn on them.
                probe = probe_frame.probe_once(
                    args, labels, mean, std, pad_color, resources,
                    want_jpeg=False, want_preview=True,
                )
                if probe is None:
                    continue
                seen += 1

                world = ptw.probe_to_world(
                    probe,
                    t_ns=probe.get("t_ns"),
                    seq=seq,
                    last_d_m=last_d_m,
                    last_seen_ns=last_seen_ns,
                    last_objects=last_objects,
                    last_target=last_target,
                )
                # bbox_px is in full-frame pixels; the dashboard scales the boxes onto
                # the 24 fps camera feed (which may be downscaled) with this size.
                if probe.get("W") and probe.get("H"):
                    world["frame_wh"] = [int(probe["W"]), int(probe["H"])]

                # A YOLO `hand` is not a findable object; it belongs in hand{},
                # where the law and the dashboard already look for it. Lift before
                # the depth gate: the gate is a claim about *things we name a
                # distance for*, and the hand is the user's own hand -- with the
                # depth model's known far-bias, gating it would silently kill hand
                # tracking at about arm's length. Lifting also sanitises objects[]
                # even when the landmarker wins, so a stale hand row can never be
                # bound as a FIND target.
                world, hand_det = lift_hand(world)
                hand_source = "yolo" if hand_det is not None else None
                if hand_finder is not None:
                    # A landmarker replaces the YOLO class outright rather than
                    # merging with it: on the Pi the class scores 0.05-0.25 on
                    # whatever is in frame (70 hits against 25 real landmark
                    # hands in one live session), and a 0.16 box must not
                    # masquerade as the wearer's hand while the landmarks are
                    # honest. The fallback stays for a run with no bundle.
                    hand_det = None
                    hand_source = None
                    frame = _FRAME_CAPTURE.get("frame")
                    found = hand_finder.find(frame) if frame is not None else None
                    landmark_hand = (
                        hand_row_from_landmarks(world, found, probe.get("frame_id"))
                        if found is not None else None
                    )
                    if landmark_hand is not None:
                        world = dict(world)
                        world["hand"] = landmark_hand
                        hand_det = landmark_hand
                        hand_source = "landmarks"
                if hand_det is not None and probe.get("W") and probe.get("H"):
                    world = place_hand(world, int(probe["W"]), int(probe["H"]),
                                       float(getattr(args, "fov", None) or 60.0))
                    hand_det = world["hand"]
                # The dashboard reads the preview pixels, not the hand row: see
                # annotate_hand_preview. Cheap at the record cadence, and it must
                # never stop perception, so a failure keeps the plain preview.
                if (hand_det is not None and probe.get("preview")
                        and probe.get("W") and probe.get("H")):
                    try:
                        probe["preview"] = annotate_hand_preview(
                            probe["preview"], hand_det,
                            int(probe["W"]), int(probe["H"]),
                        )
                    except Exception as exc:
                        print(f"live_probe: hand preview skipped ({exc})",
                              file=sys.stderr, flush=True)
                if probe.get("W") and probe.get("H"):
                    publish_hand_state(hand_det, int(probe["W"]), int(probe["H"]))
                if hand_det is not None:
                    hands_seen += 1
                    print(
                        f"live_probe: HAND ({hand_source}) "
                        f"conf {float(hand_det.get('conf') or 0.0):.2f} "
                        f"xyz_cam {[round(float(v), 2) for v in hand_det.get('xyz_cam', [])]}",
                        file=sys.stderr,
                        flush=True,
                    )

                # Only stand behind what is measurably close. Objects the depth
                # model places beyond --max-depth are dropped here, before the
                # state machine, so the wire never carries a far-away "target".
                world, gated_away = gate_by_depth(world, max_depth)
                if gated_away:
                    dropped_far += gated_away

                # Live VO: the daemon thread steps on every new grab frame;
                # the main thread stages each keyframe from the record's own
                # captured frame + metres (one-frame rule for depth), then
                # stamps the newest pose on this record.
                if use_vo and vo is None:
                    vo = _make_vo(args, int(probe["W"]), int(probe["H"]))
                    if vo is None:
                        use_vo = False
                    else:
                        vo_runner = VoRunner(vo, grab_file)
                        threading.Thread(
                            target=vo_runner.run, daemon=True,
                            name="vo-runner").start()
                if use_vo and vo is not None and vo_runner is not None:
                    frame_cap = _DEPTH_CAPTURE.get("frame")
                    metres_cap = _DEPTH_CAPTURE.get("metres")
                    if frame_cap is not None and metres_cap is not None:
                        gray = cv2.resize(
                            cv2.cvtColor(frame_cap, cv2.COLOR_BGR2GRAY),
                            (vo.vo_w, vo.vo_h), interpolation=cv2.INTER_AREA)
                        depth_affine = probe_frame.make_affine(
                            int(probe["W"]), int(probe["H"]),
                            int(args.depth_size), int(args.depth_size))
                        with vo_runner.lock:
                            vo_runner.vo.on_depth_frame(
                                gray, metres_cap, depth_affine,
                                vo_runner.n, int(probe["t_ns"]))
                    # A phase-A identity pose marked valid would freeze guided's
                    # memory bearing at the bind-time bearing and keep "guiding"
                    # after the wearer turns. Replace it with what VO last
                    # measured, honestly invalid until the first keyframe.
                    with vo_runner.lock:
                        latest = vo_runner.latest
                    if latest is not None:
                        world = stamp_pose(world, latest["T"], latest["valid"],
                                           latest["t_ns"], ptw.POSE_EPOCH)
                        world = project_rows(world, latest["T"])
                    else:
                        world = stamp_pose(world, IDENTITY_T, False, 0,
                                           ptw.POSE_EPOCH)

                # Remembered rows keep a late FIND bindable after the turn: the
                # wire's mode stays honest (LOST), guided recomputes its own.
                now_ns = int(world["t_ns"])
                if world["mode"] == "LIVE":
                    memory_rows = capture_memory(world)
                    memory_seen_ns = now_ns
                elif world["mode"] == "LOST" and memory_rows:
                    world, injected = inject_memory(
                        world, memory_rows, memory_seen_ns, memory_s, now_ns)
                    if injected:
                        memory_injected += 1

                # Mirror emit_lines' state machine so LIVE/HOLD/LOST agree.
                if world["mode"] == "LIVE":
                    last_seen_ns = int(world["t_ns"])
                    last_objects = copy.deepcopy(world["objects"])
                    last_target = copy.deepcopy(world["target"])
                if world["mode"] == "LOST":
                    last_objects = None
                    last_target = None
                    last_d_m = None
                elif "d_m" in world:
                    last_d_m = world["d_m"]

                # p95_vision_ns (spec: LIVE lasts max(1 s, 2 x p95)). Without it guided
                # assumes 1 s and the ~1 s on-device cycle drops the target to LOST
                # between records. Measured as how old the previous record's frame is
                # when this one replaces it (latency + cycle), i.e. the oldest vision
                # guided normally holds; capture->publish alone (~0.9 s) is too short
                # here because the cycle (~1.1 s) is longer than the latency.
                now_ns = time.monotonic_ns()
                if prev_frame_ns:
                    vision_ns.append(now_ns - prev_frame_ns)
                prev_frame_ns = int(world.get("t_ns") or 0)
                ranked = sorted(v for v in vision_ns if 0 < v < 10_000_000_000)
                if ranked:
                    world.setdefault("health", {})["p95_vision_ns"] = ranked[int(0.95 * (len(ranked) - 1))]

                if seen % publish_every == 0:
                    line = json.dumps(world, separators=(",", ":"))
                    if world_sock is not None and world_addr is not None:
                        try:
                            world_sock.sendto(line.encode("utf-8"), world_addr)
                        except OSError as exc:
                            world_errors += 1
                            if world_errors == 1:
                                print(
                                    f"live_probe: world send to {world_addr} failed: {exc} "
                                    "(perception continues)",
                                    file=sys.stderr,
                                    flush=True,
                                )
                        else:
                            sent += 1
                    print(ptw.format_readout(world), file=sys.stderr, flush=True)

                jpeg = probe.get("preview") or probe.get("jpeg")
                if video_sock is not None and video_addr is not None and jpeg is not None:
                    if len(jpeg) > ptw.MAX_VIDEO_BYTES:
                        dropped_video += 1
                    else:
                        # A monitor preview must never be able to stop perception:
                        # the wearer keeps hearing even if the network misbehaves.
                        try:
                            video_sock.sendto(jpeg, video_addr)
                        except OSError as exc:
                            dropped_video += 1
                            if dropped_video == 1:
                                print(
                                    f"live_probe: preview send to {video_addr} failed "
                                    f"({len(jpeg)} bytes): {exc} (perception continues)",
                                    file=sys.stderr,
                                    flush=True,
                                )

                seq += 2
    except KeyboardInterrupt:
        print("live_probe: interrupted", file=sys.stderr, flush=True)
    finally:
        for sock in (world_sock, video_sock):
            if sock is not None:
                sock.close()
        print(
            f"live_probe: {seen} frame(s) processed, {sent} record(s) sent, "
            f"{dropped_video} preview(s) oversized, {dropped_far} object(s) beyond "
            f"{max_depth:g} m, {hands_seen} hand observation(s)"
            + (f", VO {getattr(vo_runner, 'valid_steps', 0)}/"
               f"{getattr(vo_runner, 'steps', 0)} valid, "
               f"{memory_injected} LOST record(s) carried remembered row(s)"
               if (vo_runner is not None or memory_injected) else ""),
            file=sys.stderr,
            flush=True,
        )
    return 0 if seen else 1


if __name__ == "__main__":
    raise SystemExit(main())
