#!/usr/bin/env python3
"""Turn laptop probe frames into world JSONL lines for the dashboard.

This is a thin wrapper around probe_frame.py: detection, depth, and hand work
stays there. Phase A has no VO, so xyz_world is xyz_cam, the camera pose is
identity, and crumbs stay empty. Without --calib, probe frames have no xyz_cam
and this tool emits boxes only, as expected. Each record can also go out as one
UDP datagram to the laptop bridge.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import socket
import sys
import time
import zlib
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import probe_frame  # noqa: E402

TARGET_NAMES: Tuple[str, ...] = (
    "keys",
    "keychain",
    "bottle",
    "laptop",
    "keyboard",
    "mouse",
    "headphones",
    "charger",
    "badge",
    "lanyard",
    "wallet",
    "glasses",
    "phone",
)
POSE_EPOCH = 1
IDENTITY_T_WORLD_FROM_CAM: Tuple[int, ...] = (
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1,
)
TARGET_KEYS = ("id", "name", "xyz_cam", "xyz_world", "conf", "last_seen_ns", "frame_id", "pose_epoch")
DEFAULT_UDP_TARGET = "127.0.0.1:5005"


def _vec3(value: Any) -> Optional[Tuple[float, float, float]]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    try:
        xyz = (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError):
        return None
    return xyz if all(math.isfinite(v) for v in xyz) else None


def _number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def _timing(timings: Mapping[str, Any], keys: Sequence[str]) -> Optional[float]:
    for key in keys:
        value = _number(timings.get(key))
        if value is not None:
            return value
    return None


def _stable_id(name: str) -> int:
    return 1 + (zlib.crc32(name.encode("utf-8")) & 0x7FFFFFFF)


def probe_to_world(
    probe: Mapping[str, Any],
    *,
    t_ns: Optional[int] = None,
    seq: int = 0,
    last_d_m: Optional[float] = None,
) -> Dict[str, Any]:
    """Convert one probe_frame result into one world JSONL record."""
    now_ns = time.monotonic_ns() if t_ns is None else int(t_ns)
    detections = list(probe.get("detections") or [])
    probe_frame_id = probe.get("frame_id")

    objects: List[Dict[str, Any]] = []
    for detection in detections:
        obj: Dict[str, Any] = {
            "id": _stable_id(str(detection.get("name", "unknown"))),
            "name": detection.get("name"),
            "bbox_px": detection.get("bbox_px"),
            "conf": detection.get("conf"),
            "last_seen_ns": now_ns,
            "frame_id": detection.get("frame_id", probe_frame_id),
            "pose_epoch": POSE_EPOCH,
            "in_latest_boxes": True,
        }
        xyz_cam = _vec3(detection.get("xyz_cam"))
        if xyz_cam is not None:
            obj["xyz_cam"] = detection["xyz_cam"]
            obj["xyz_world"] = detection["xyz_cam"]
        objects.append(obj)

    target_obj: Optional[Dict[str, Any]] = None
    for name in TARGET_NAMES:
        for detection, obj in zip(detections, objects):
            if detection.get("name") == name:
                target_obj = obj
                break
        if target_obj is not None:
            break
    target = (
        {key: target_obj[key] for key in TARGET_KEYS if key in target_obj}
        if target_obj is not None
        else None
    )

    hand_probe = probe.get("hand")
    hand: Optional[Dict[str, Any]] = None
    if isinstance(hand_probe, Mapping):
        hand = {
            "t_ns": now_ns,
            "frame_id": hand_probe.get("frame_id", probe_frame_id),
        }
        if "conf" in hand_probe:
            hand["conf"] = hand_probe["conf"]
        hand_xyz = _vec3(hand_probe.get("xyz_cam"))
        if hand_xyz is not None:
            hand["xyz_cam"] = hand_probe["xyz_cam"]
            hand["xyz_world"] = hand_probe["xyz_cam"]

    d_m: Optional[float] = None
    if target is not None and hand is not None:
        hand_xyz = _vec3(hand.get("xyz_cam"))
        target_xyz = _vec3(target.get("xyz_cam"))
        if (
            hand_xyz is not None
            and target_xyz is not None
            and hand.get("frame_id") is not None
            and target.get("frame_id") is not None
            and hand["frame_id"] == target["frame_id"]
        ):
            d_m = math.dist(hand_xyz, target_xyz)
    if d_m is None and last_d_m is not None:
        held = _number(last_d_m)
        if held is not None:
            d_m = held

    timings = probe.get("timings_ms") or probe.get("timings") or {}
    health = {
        "last_yolo_ms": _timing(timings, ("yolo", "last_yolo_ms")),
        "last_depth_ms": _timing(timings, ("depth", "last_depth_ms")),
    }

    world: Dict[str, Any] = {
        "v": 1,
        "t_ns": now_ns,
        "seq": {"percept": int(seq), "voiced": None, "guided": None},
        "mode": "LIVE" if detections else "HOLD",
        "law": "NONE",
        "cue": None,
        "intent": None,
        "target": target,
        "hand": hand,
        "objects": objects,
        "pose": {
            "valid": True,
            "pose_epoch": POSE_EPOCH,
            "t_ns": now_ns,
            "age_ns": 0,
            "T_world_from_cam": list(IDENTITY_T_WORLD_FROM_CAM),
        },
        "pose_epoch": POSE_EPOCH,
        "crumbs": [],
        "health": health,
    }
    if d_m is not None:
        world["d_m"] = d_m
    return world


def parse_udp_target(value: str) -> Tuple[str, int]:
    """Parse --udp HOST:PORT into a UDP address; no name resolution here."""
    host, sep, port_text = str(value).rpartition(":")
    if not sep or not host or ":" in host:
        raise ValueError(f"--udp must be HOST:PORT (got {value!r})")
    if not port_text.isdecimal():
        raise ValueError(f"--udp port must be a number 1-65535 (got {value!r})")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise ValueError(f"--udp port must be 1-65535 (got {value!r})")
    return host, port


def build_parser() -> argparse.ArgumentParser:
    parser = probe_frame.build_parser()
    parser.add_argument("--out", help="JSONL path, or - for stdout")
    parser.add_argument(
        "--udp",
        nargs="?",
        const=DEFAULT_UDP_TARGET,
        help="send each world object as one UDP datagram to HOST:PORT "
        f"(bare flag uses {DEFAULT_UDP_TARGET}); default none",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="capture one frame; images are always once, cameras loop until SIGINT",
    )
    return parser


def _output(path: str) -> contextlib.AbstractContextManager:
    if path == "-":
        return contextlib.nullcontext(sys.stdout)
    return Path(path).open("w", encoding="utf-8")


def emit_lines(args: argparse.Namespace) -> Iterator[Dict[str, Any]]:
    """Yield world records from an already-prepared probe_frame CLI."""
    labels, mean, std, pad_color = probe_frame.prepare(args)
    stop_after_one = args.once or args.image is not None
    seq = 0
    last_d_m: Optional[float] = None

    while True:
        probe = probe_frame.probe_once(args, labels, mean, std, pad_color)
        world = probe_to_world(probe, seq=seq, last_d_m=last_d_m)
        if "d_m" in world:
            last_d_m = world["d_m"]
        yield world
        seq += 2
        if stop_after_one:
            return


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.out is None and args.udp is None:
        parser.error("one of --out or --udp is required")
    udp_target: Optional[Tuple[str, int]] = None
    if args.udp is not None:
        try:
            udp_target = parse_udp_target(args.udp)
        except ValueError as exc:
            parser.error(str(exc))

    try:
        with contextlib.ExitStack() as stack:
            out = stack.enter_context(_output(str(args.out))) if args.out is not None else None
            sock = (
                stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
                if udp_target is not None
                else None
            )
            for world in emit_lines(args):
                line = json.dumps(world, separators=(",", ":"), sort_keys=False)
                if out is not None:
                    out.write(line)
                    out.write("\n")
                    out.flush()
                if sock is not None:
                    sock.sendto(line.encode("utf-8"), udp_target)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
