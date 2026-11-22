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
        self.last_mtime = 0
        self.latest = None          # {"T", "valid", "t_ns"} of the last step
        self.stop = threading.Event()
        self.steps = 0
        self.valid_steps = 0
        self.bad_streak = 0
        self.last_printed_yaw = 0.0
        self.max_step_ms = 0.0

    def run(self) -> None:
        while not self.stop.is_set():
            try:
                mtime = self.grab_file.stat().st_mtime_ns
            except OSError:
                self.stop.wait(0.05)
                continue
            if mtime == self.last_mtime:
                self.stop.wait(0.03)
                continue
            frame = cv2.imread(str(self.grab_file), cv2.IMREAD_GRAYSCALE)
            if frame is None:
                self.last_mtime = mtime
                continue
            gray = cv2.resize(frame, (self.vo.vo_w, self.vo.vo_h),
                              interpolation=cv2.INTER_AREA)
            self.last_mtime = mtime
            started = time.monotonic_ns()
            with self.lock:
                self.n += 1
                step = self.vo.step(gray, self.n, time.monotonic_ns())
            step_ms = (time.monotonic_ns() - started) / 1e6
            if step_ms > self.max_step_ms:
                self.max_step_ms = step_ms
            if step is None:
                continue
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
        "--vo",
        action="store_true",
        help="track the camera with visual odometry so the dashboard's 3D scene follows it; "
        "needs --fov or --calib. Without it the pose stays identity.",
    )
    parser.add_argument(
        "--h-chest",
        type=float,
        default=0.0,
        help="measured camera height above the floor in metres, for VO's scale watchdog; "
        "0 (default) leaves the scale uncorrected, so distances travelled are approximate",
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
    live_vo = LiveVo(args.depth_scale, args.h_chest) if args.vo else None
    deadline = time.monotonic() + args.max_seconds if args.max_seconds > 0 else None

    seq = 0
    seen = 0
    sent = 0
    world_errors = 0
    dropped_video = 0
    dropped_far = 0
    hands_seen = 0
    warned_vo = False
    max_depth = float(getattr(args, "max_depth", 3.0) or 0.0)
    last_mtime = 0
    last_d_m: Optional[float] = None
    last_seen_ns: Optional[int] = None
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
                try:
                    probe = probe_frame.probe_once(
                        args, labels, mean, std, pad_color, resources,
                        want_jpeg=False, want_preview=True, want_vo=live_vo is not None,
                    )
                except SystemExit as exc:
                    # On Windows (udp_grab.py) the file can vanish for an instant while
                    # the next frame is swapped in; skip that read instead of stopping.
                    if "could not read image" not in str(exc):
                        raise
                    continue
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
                # tracking at about arm's length.
                world, hand_det = lift_hand(world)
                if hand_det is not None:
                    hands_seen += 1
                    print(
                        f"live_probe: HAND conf {float(hand_det.get('conf') or 0.0):.2f} "
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
