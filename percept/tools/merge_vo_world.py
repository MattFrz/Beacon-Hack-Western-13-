#!/usr/bin/env python3
"""Merge a probe_to_world JSONL pass with a vo_probe JSONL pass.

Both passes run over the same recording, so their frame ids align: the world
record for frame F gets the newest VO pose at or before F, its objects and
hand are re-projected into the world frame with that pose, and the crumb
trail accumulates from the VO steps (spec §8 gates: >=0.4 s and >=5 cm).

The merged timeline is the frame index at `--fps` (both passes' wall-clock
times are processing time, not capture time), so the bridge replays the walk
at its true pace. Pose honesty is preserved: an untrusted VO step keeps the
last valid pose, flags valid=false, and ages it.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import vo_core  # noqa: E402

IDENTITY_T = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
CRUMB_MIN_DT_NS = 400_000_000
CRUMB_MIN_MOVE_M = 0.05
FRAME_ID_MAX = 10_000  # probe --video frame ids are monotonic ns; ignore those


def read_jsonl(path: Path) -> List[Dict[str, object]]:
    records = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def first_frame_id(record: Dict[str, object]) -> Optional[int]:
    for key in ("target", "hand"):
        part = record.get(key)
        if isinstance(part, dict) and isinstance(part.get("frame_id"), int):
            return part["frame_id"]
    objects = record.get("objects")
    if isinstance(objects, list):
        for obj in objects:
            if isinstance(obj, dict) and isinstance(obj.get("frame_id"), int):
                return obj["frame_id"]
    return None


def usable_frame_id(record: Dict[str, object]) -> Optional[int]:
    """Frame-scale id, or None: probe_to_world --video stamps objects with
    monotonic-ns ids that must never be mistaken for frame indices."""
    fid = first_frame_id(record)
    if fid is None or not (0 < fid < FRAME_ID_MAX):
        return None
    return fid


def translation(T: List[float]):
    return float(T[3]), float(T[7]), float(T[11])


def transform_point(T: List[float], p_cam) -> Optional[List[float]]:
    if not isinstance(p_cam, list) or len(p_cam) < 3:
        return None
    x, y, z = float(p_cam[0]), float(p_cam[1]), float(p_cam[2])
    return [
        T[0] * x + T[1] * y + T[2] * z + T[3],
        T[4] * x + T[5] * y + T[6] * z + T[7],
        T[8] * x + T[9] * y + T[10] * z + T[11],
    ]


def median(values: List[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def build_crumbs(vo_records: List[Dict[str, object]], dt_ns: int):
    """Crumb trail with the frame it belongs to, from valid VO steps."""
    crumbs: List[Dict[str, object]] = []
    last_frame = None
    last_pos = None
    moved_since = 0.0
    for rec in vo_records:
        if not rec.get("valid"):
            continue
        frame = int(rec["frame_id"])
        T = rec["T_world_from_cam"]
        pos = translation(T)
        if last_frame is None:
            crumbs.append({"xyz_world": list(pos), "t_ns": frame * dt_ns,
                           "frame_id": frame})
            last_frame = frame
            last_pos = pos
            continue
        moved_since += math.dist(pos, last_pos)
        now_ns = frame * dt_ns
        if vo_core.crumb_due(last_frame * dt_ns, now_ns, moved_since,
                             CRUMB_MIN_DT_NS, CRUMB_MIN_MOVE_M):
            crumbs.append({"xyz_world": list(pos), "t_ns": now_ns,
                           "frame_id": frame})
            last_frame = frame
            last_pos = pos
            moved_since = 0.0
        else:
            last_pos = pos
    return crumbs


def merge(world_path: Path, vo_path: Path, out_path: Path,
          fps: float = 30.0) -> int:
    if fps <= 0:
        raise SystemExit("--fps must be positive")
    dt_ns = int(round(1e9 / fps))
    world_records = read_jsonl(world_path)
    vo_records = sorted(
        (rec for rec in read_jsonl(vo_path)
         if isinstance(rec.get("frame_id"), int)),
        key=lambda rec: rec["frame_id"])

    offsets = [usable_frame_id(rec) - i for i, rec in enumerate(world_records)
               if usable_frame_id(rec) is not None]
    # A --video world pass emits one record per frame, in order, so the
    # ordinal maps straight onto the 1-based frame index VO uses.
    offset = median(offsets) if offsets else 1

    crumbs = build_crumbs(vo_records, dt_ns)

    last_valid_T = list(IDENTITY_T)
    last_valid_frame: Optional[int] = None
    vo_i = 0  # newest VO record with frame_id <= F
    n_out = 0
    with out_path.open("w", encoding="utf-8") as out:
        for i, rec in enumerate(world_records):
            fid = usable_frame_id(rec)
            F = fid if fid is not None else i + offset
            while (vo_i < len(vo_records)
                   and vo_records[vo_i]["frame_id"] <= F):
                if vo_records[vo_i].get("valid"):
                    last_valid_T = vo_records[vo_i]["T_world_from_cam"]
                    last_valid_frame = vo_records[vo_i]["frame_id"]
                vo_i += 1
            frame_ns = F * dt_ns
            rec["t_ns"] = frame_ns
            rec["frame_id"] = F

            if last_valid_frame is None:
                pose_valid = False
                pose_t_ns = frame_ns
                age_ns = 0
            else:
                newest = vo_records[vo_i - 1] if vo_i > 0 else None
                pose_valid = bool(newest and newest.get("valid")
                                  and newest["frame_id"] == last_valid_frame)
                pose_t_ns = last_valid_frame * dt_ns
                age_ns = frame_ns - pose_t_ns
            rec["pose"] = {
                "valid": pose_valid,
                "pose_epoch": 1,
                "t_ns": pose_t_ns,
                "age_ns": age_ns,
                "T_world_from_cam": list(last_valid_T),
            }

            for key in ("target", "hand"):
                part = rec.get(key)
                if isinstance(part, dict) and "xyz_cam" in part:
                    p_world = transform_point(last_valid_T, part["xyz_cam"])
                    if p_world is not None:
                        part["xyz_world"] = p_world
                if isinstance(part, dict) and "t_ns" in part:
                    part["t_ns"] = frame_ns
                if isinstance(part, dict) and "last_seen_ns" in part:
                    part["last_seen_ns"] = frame_ns
            objects = rec.get("objects")
            if isinstance(objects, list):
                for obj in objects:
                    if isinstance(obj, dict):
                        p_world = (transform_point(last_valid_T, obj["xyz_cam"])
                                   if "xyz_cam" in obj else None)
                        if p_world is not None:
                            obj["xyz_world"] = p_world
                        if "last_seen_ns" in obj:
                            obj["last_seen_ns"] = frame_ns
            rec["crumbs"] = [dict(c) for c in crumbs if c["frame_id"] <= F]
            for c in rec["crumbs"]:
                c.pop("frame_id", None)
            out.write(json.dumps(rec, separators=(",", ":")) + "\n")
            n_out += 1
    return n_out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--world", type=Path, required=True,
                        help="probe_to_world --out JSONL over the same video")
    parser.add_argument("--vo", type=Path, required=True,
                        help="vo_probe --out JSONL over the same video")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fps", type=float, default=30.0,
                        help="recording frame rate for the merged timeline")
    args = parser.parse_args()
    n = merge(args.world, args.vo, args.out, fps=args.fps)
    print(f"merged {n} world records into {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
