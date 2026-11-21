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

Static objects persist as anchors: each sighting within a 1.5 m same-class
gate updates an anchor whose emitted position is the component-wise median
of its sightings, so pose/depth jitter averages out and objects stay put
(faded) even when not currently detected. People stay live-only.
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
ANCHOR_GATE_M = 1.5     # association radius: sighting -> same-class anchor
ANCHOR_MAX_OBS = 120    # robust position window per anchor
LIVE_ONLY_NAMES = {"person"}  # people move; anchoring them pins a ghost
INTERP_MAX_GAP_NS = 2_000_000_000  # bridge refused gaps up to 2 s for display


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


def component_median(obs: List[List[float]]) -> List[float]:
    """Robust anchor position: per-axis median of the sighting window."""
    return [sorted(c)[len(c) // 2] for c in zip(*obs)]


class Anchor:
    """A persistent world object: every sighting within the gate updates the
    window; the emitted position is its component-wise median, so pose and
    depth jitter average out instead of teleporting the marker."""

    def __init__(self, name: str, world: List[float], frame_ns: int,
                 frame_id: int):
        self.name = name
        self.id = name
        self.obs: List[List[float]] = [world]
        self.last_seen_ns = frame_ns
        self.last_frame_id = frame_id
        self.latest_cam: Optional[List[float]] = None
        self.latest_bbox: Optional[List[float]] = None
        self.latest_conf: Optional[float] = None

    def position(self) -> List[float]:
        return component_median(self.obs[-ANCHOR_MAX_OBS:])

    def update(self, world: List[float], frame_ns: int, frame_id: int):
        self.obs.append(world)
        if len(self.obs) > ANCHOR_MAX_OBS:
            del self.obs[:len(self.obs) - ANCHOR_MAX_OBS]
        self.last_seen_ns = frame_ns
        self.last_frame_id = frame_id

    def emit(self, in_latest_boxes: bool) -> Dict[str, object]:
        out: Dict[str, object] = {
            "id": self.id, "name": self.name,
            "xyz_world": self.position(),
            "last_seen_ns": self.last_seen_ns,
            "frame_id": self.last_frame_id,
            "pose_epoch": 1, "in_latest_boxes": in_latest_boxes,
        }
        if self.latest_cam is not None:
            out["xyz_cam"] = self.latest_cam
        if self.latest_bbox is not None:
            out["bbox_px"] = self.latest_bbox
        if self.latest_conf is not None:
            out["conf"] = self.latest_conf
        return out


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


def blend_pose(Ta: List[float], Tb: List[float], alpha: float) -> List[float]:
    """Display-side bridge across a refused gap: translation lerps, rotation
    lerps then is re-orthonormalized (Gram-Schmidt on the columns)."""
    cols = [[Ta[c] + alpha * (Tb[c] - Ta[c]),
             Ta[4 + c] + alpha * (Tb[4 + c] - Ta[4 + c]),
             Ta[8 + c] + alpha * (Tb[8 + c] - Ta[8 + c])] for c in range(3)]
    for i in range(3):
        for j in range(i):
            d = sum(cols[i][k] * cols[j][k] for k in range(3))
            cols[i] = [cols[i][k] - d * cols[j][k] for k in range(3)]
        norm = math.sqrt(sum(v * v for v in cols[i])) or 1.0
        cols[i] = [v / norm for v in cols[i]]
    return [
        cols[0][0], cols[1][0], cols[2][0],
        Ta[3] + alpha * (Tb[3] - Ta[3]),
        cols[0][1], cols[1][1], cols[2][1],
        Ta[7] + alpha * (Tb[7] - Ta[7]),
        cols[0][2], cols[1][2], cols[2][2],
        Ta[11] + alpha * (Tb[11] - Ta[11]),
        0, 0, 0, 1,
    ]


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
    anchors: List[Anchor] = []           # persistent world-object map
    anchor_counters: Dict[str, int] = {}
    persistent_target: Optional[Anchor] = None  # homing marker through gaps
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
            pose_T = list(last_valid_T)
            interpolated = False
            if not pose_valid and last_valid_frame is not None:
                # Display-side bridge: offline the whole VO timeline is known,
                # so a refused gap can be bridged to the next valid pose
                # within the horizon instead of freezing the wearer marker.
                next_valid = None
                j = vo_i
                while j < len(vo_records):
                    if vo_records[j].get("valid"):
                        next_valid = vo_records[j]
                        break
                    j += 1
                if (next_valid is not None
                        and (next_valid["frame_id"] - F) * dt_ns
                        <= INTERP_MAX_GAP_NS):
                    denom = next_valid["frame_id"] - last_valid_frame
                    if denom > 0:
                        alpha = (F - last_valid_frame) / denom
                        pose_T = blend_pose(last_valid_T,
                                            next_valid["T_world_from_cam"],
                                            alpha)
                        pose_valid = True
                        interpolated = True
                        pose_t_ns = frame_ns
                        age_ns = 0
            rec["pose"] = {
                "valid": pose_valid,
                "interpolated": interpolated,
                "pose_epoch": 1,
                "t_ns": pose_t_ns,
                "age_ns": age_ns,
                "T_world_from_cam": pose_T,
            }

            part = rec.get("hand")
            if isinstance(part, dict):
                if "xyz_cam" in part:
                    p_world = transform_point(pose_T, part["xyz_cam"])
                    if p_world is not None:
                        part["xyz_world"] = p_world
                if "t_ns" in part:
                    part["t_ns"] = frame_ns
                if "last_seen_ns" in part:
                    part["last_seen_ns"] = frame_ns
            objects = rec.get("objects")
            live_objects: List[Dict[str, object]] = []
            seen_anchors: set = set()
            if isinstance(objects, list):
                counters: Dict[str, int] = anchor_counters
                for obj in objects:
                    if not isinstance(obj, dict) or "xyz_cam" not in obj:
                        continue
                    p_world = transform_point(pose_T, obj["xyz_cam"])
                    if p_world is None:
                        continue
                    name = obj.get("name") if isinstance(obj.get("name"), str) else None
                    if name is None or name in LIVE_ONLY_NAMES:
                        # live-only: rendered exactly when detected, never anchored
                        obj["xyz_world"] = p_world
                        obj["last_seen_ns"] = frame_ns
                        live_objects.append(obj)
                        continue
                    # associate to the nearest same-class anchor within the gate
                    best: Optional[Anchor] = None
                    best_d = ANCHOR_GATE_M
                    for anchor in anchors:
                        if anchor.name != name:
                            continue
                        d = math.dist(anchor.position(), p_world)
                        if d <= best_d:
                            best, best_d = anchor, d
                    if best is None:
                        best = Anchor(name, p_world, frame_ns, F)
                        counters[name] = counters.get(name, 0) + 1
                        best.id = name + '-' + str(counters[name])
                        anchors.append(best)
                    else:
                        best.update(p_world, frame_ns, F)
                    best.latest_cam = list(obj["xyz_cam"])
                    best.latest_bbox = obj.get("bbox_px")
                    best.latest_conf = obj.get("conf")
                    seen_anchors.add(best)
            rec["objects"] = ([a.emit(a in seen_anchors) for a in anchors]
                              + live_objects)

            # Target: live camera-space precision while in frame; the anchor's
            # median position (faded) while out of frame, so the dashboard
            # keeps a homing marker through detection gaps.
            target = rec.get("target")
            if isinstance(target, dict):
                p_world = (transform_point(pose_T, target["xyz_cam"])
                           if isinstance(target.get("xyz_cam"), list) else None)
                if p_world is not None:
                    target["xyz_world"] = p_world
                if "t_ns" in target:
                    target["t_ns"] = frame_ns
                if "last_seen_ns" in target:
                    target["last_seen_ns"] = frame_ns
                name = target.get("name")
                if (isinstance(name, str) and p_world is not None
                        and isinstance(target.get("xyz_cam"), list)):
                    cam = target["xyz_cam"]
                    match = next((a for a in anchors
                                  if a.name == name and a.latest_cam == cam), None)
                    if match is None:
                        best_d = ANCHOR_GATE_M
                        for a in anchors:
                            if a.name != name:
                                continue
                            d = math.dist(a.position(), p_world)
                            if d <= best_d:
                                match, best_d = a, d
                    if match is not None:
                        persistent_target = match
            elif persistent_target is not None:
                held = persistent_target.emit(False)
                if persistent_target.latest_cam is not None:
                    held["xyz_cam"] = persistent_target.latest_cam
                rec["target"] = held
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
