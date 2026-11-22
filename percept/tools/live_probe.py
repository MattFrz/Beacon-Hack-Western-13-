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
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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

import probe_frame  # noqa: E402
import probe_to_world as ptw  # noqa: E402


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
    deadline = time.monotonic() + args.max_seconds if args.max_seconds > 0 else None

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
    last_objects: Optional[List[Dict[str, Any]]] = None
    last_target: Optional[Dict[str, Any]] = None

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
            f"{max_depth:g} m, {hands_seen} hand observation(s)",
            file=sys.stderr,
            flush=True,
        )
    return 0 if seen else 1


if __name__ == "__main__":
    raise SystemExit(main())
