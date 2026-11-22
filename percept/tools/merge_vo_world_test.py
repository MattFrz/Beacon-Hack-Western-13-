#!/usr/bin/env python3
"""merge_vo_world tests: synthetic world + VO JSONL, no camera or models."""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import merge_vo_world  # noqa: E402

FPS = 10.0
DT_NS = 100_000_000


def write_jsonl(path: Path, records) -> Path:
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
    return path


def T(tx: float):
    return [1, 0, 0, tx, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def world_record(frame_id: int, xyz_cam=(1.0, 0.0, 2.0)):
    return record_with(frame_id, [{
        "id": 7, "name": "bottle", "bbox_px": [1, 2, 3, 4], "conf": 0.9,
        "xyz_cam": list(xyz_cam), "xyz_world": list(xyz_cam),
        "last_seen_ns": 999_999_999, "frame_id": frame_id,
        "pose_epoch": 1, "in_latest_boxes": True,
    }])


def record_with(frame_id: int, objects):
    return {
        "v": 1, "t_ns": 999_999_999, "seq": {"percept": frame_id},
        "mode": "LIVE", "law": "NONE", "cue": None, "intent": None,
        "target": None, "hand": None,
        "objects": objects,
        "pose": {"valid": True, "pose_epoch": 1, "t_ns": 999_999_999,
                 "age_ns": 0, "T_world_from_cam": T(0)},
        "crumbs": [], "health": {},
    }


def vo_record(frame_id: int, valid: bool, tx: float):
    return {"frame_id": frame_id, "valid": valid, "inliers": 100,
            "median_disp_px": 2.0, "h_est": None, "scale_mult": 1.0,
            "t": [tx, 0.0, 0.0], "T_world_from_cam": T(tx)}


class MergeTests(unittest.TestCase):
    def run_merge(self, world_records, vo_records, target=None):
        with tempfile.TemporaryDirectory() as tmp:
            world = write_jsonl(Path(tmp) / "w.jsonl", world_records)
            vo = write_jsonl(Path(tmp) / "vo.jsonl", vo_records)
            out = Path(tmp) / "merged.jsonl"
            merge_vo_world.merge(world, vo, out, fps=FPS, target_name=target)
            return [json.loads(line) for line in
                    out.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_pose_and_world_points_follow_vo(self):
        merged = self.run_merge(
            [world_record(5), world_record(11)],
            [vo_record(2, True, 0.0), vo_record(5, True, 1.0),
             vo_record(8, True, 1.5), vo_record(11, True, 2.0)])
        pose = merged[0]["pose"]
        self.assertTrue(pose["valid"])
        self.assertEqual(pose["T_world_from_cam"], T(1.0))
        self.assertEqual(pose["t_ns"], 5 * DT_NS)
        obj = merged[0]["objects"][0]
        self.assertEqual(obj["xyz_world"], [2.0, 0.0, 2.0])  # T(1) . (1,0,2)
        self.assertEqual(merged[0]["t_ns"], 5 * DT_NS)
        self.assertEqual(merged[0]["objects"][0]["last_seen_ns"], 5 * DT_NS)
        self.assertEqual(merged[1]["pose"]["T_world_from_cam"], T(2.0))

    def test_invalid_vo_keeps_last_pose_and_ages_it(self):
        merged = self.run_merge(
            [world_record(5), world_record(9)],
            [vo_record(2, True, 0.0), vo_record(5, True, 1.0),
             vo_record(8, False, 0.0)])
        pose = merged[1]["pose"]
        self.assertFalse(pose["valid"])
        self.assertEqual(pose["T_world_from_cam"], T(1.0))  # kept, not moved
        self.assertEqual(pose["age_ns"], (9 - 5) * DT_NS)

    def test_invalid_gap_pose_is_interpolated_between_valid_steps(self):
        """Offline the whole VO timeline is known: a refused gap gets a bridged
        pose (lerp translation, nearest rotation) flagged interpolated=true,
        instead of freezing the wearer marker with pose lost."""
        merged = self.run_merge(
            [world_record(5), world_record(7), world_record(9)],
            [vo_record(5, True, 1.0), vo_record(7, False, 0.0),
             vo_record(9, True, 2.0)])
        mid = merged[1]["pose"]
        self.assertTrue(mid["valid"])
        self.assertTrue(mid["interpolated"])
        self.assertEqual(mid["T_world_from_cam"][3], 1.5)  # halfway lerp
        self.assertEqual(mid["t_ns"], 7 * DT_NS)
        # the honest endpoints stay honest
        self.assertFalse(merged[0]["pose"].get("interpolated", False))
        self.assertFalse(merged[2]["pose"].get("interpolated", False))

    def test_gap_longer_than_horizon_keeps_pose_lost(self):
        """A long refusal has no trustworthy bridge: keep the held pose and the
        pose-lost flag instead of inventing motion."""
        merged = self.run_merge(
            [world_record(5), world_record(7), world_record(9)],
            [vo_record(5, True, 1.0), vo_record(7, False, 0.0),
             vo_record(50, True, 2.0)])
        mid = merged[1]["pose"]
        self.assertFalse(mid["valid"])
        self.assertFalse(mid.get("interpolated", False))
        self.assertEqual(mid["T_world_from_cam"], T(1.0))  # held
        # the gap is still open at frame 9: held, not bridged
        self.assertFalse(merged[2]["pose"]["valid"])
        self.assertEqual(merged[2]["pose"]["T_world_from_cam"], T(1.0))

    def test_no_vo_yet_means_invalid_identity_pose(self):
        merged = self.run_merge([world_record(1)], [vo_record(4, True, 0.5)])
        pose = merged[0]["pose"]
        self.assertFalse(pose["valid"])
        self.assertEqual(pose["T_world_from_cam"], T(0))

    def test_crumbs_gated_by_time_and_distance(self):
        merged = self.run_merge(
            [world_record(2), world_record(12), world_record(20)],
            [vo_record(2, True, 0.0), vo_record(5, True, 0.05),
             vo_record(12, True, 0.6), vo_record(20, True, 1.2)])
        crumbs = merged[-1]["crumbs"]
        # first valid pose seeds the trail; 5 is under 0.4 s; 12 and 20 pass
        self.assertEqual([c["xyz_world"][0] for c in crumbs],
                         [0.0, 0.6, 1.2])

    def test_ns_scale_frame_ids_are_ignored_for_alignment(self):
        """probe_to_world --video stamps objects with monotonic-ns frame ids;
        those must not be mistaken for frame indices."""
        rec_a = world_record(37835178895452, xyz_cam=(1.0, 0.0, 2.0))
        rec_b = world_record(37841061716173, xyz_cam=(1.0, 0.0, 2.0))
        merged = self.run_merge(
            [rec_a, rec_b],
            [vo_record(1, True, 0.0), vo_record(2, True, 1.0)])
        # ordinal alignment: record 0 -> frame 1 (T 0), record 1 -> frame 2 (T 1)
        self.assertEqual(merged[0]["pose"]["T_world_from_cam"], T(0.0))
        self.assertEqual(merged[1]["pose"]["T_world_from_cam"], T(1.0))
        self.assertEqual(merged[1]["objects"][0]["xyz_world"], [2.0, 0.0, 2.0])

    def test_anchor_persists_through_detection_gap(self):
        merged = self.run_merge(
            [world_record(2), record_with(12, []), record_with(20, [])],
            [vo_record(2, True, 0.0), vo_record(12, True, 0.1),
             vo_record(20, True, 0.2)])
        objs = merged[2]["objects"]
        self.assertEqual(len(objs), 1)
        bottle = objs[0]
        self.assertEqual(bottle["name"], "bottle")
        self.assertEqual(bottle["xyz_world"], [1.0, 0.0, 2.0])
        self.assertEqual(bottle["last_seen_ns"], 2 * DT_NS)
        self.assertFalse(bottle["in_latest_boxes"])  # faded, not dropped

    def test_anchor_median_absorbs_jitter_and_dedupes(self):
        cams = [(1.0, 0.0, 2.0), (1.5, 0.0, 2.5), (1.1, 0.0, 2.1)]
        merged = self.run_merge(
            [world_record(2, xyz_cam=cams[0]),
             world_record(5, xyz_cam=cams[1]),
             world_record(8, xyz_cam=cams[2])],
            [vo_record(2, True, 1.0), vo_record(5, True, 1.0),
             vo_record(8, True, 1.0)])
        # same bottle, jittered sightings within the 1.5 m gate -> one anchor
        objs = merged[2]["objects"]
        self.assertEqual([o["name"] for o in objs], ["bottle"])
        world = [(2.0, 0.0, 2.0), (2.5, 0.0, 2.5), (2.1, 0.0, 2.1)]
        med = [sorted(c)[len(c) // 2] for c in zip(*world)]
        self.assertEqual(objs[0]["xyz_world"], med)
        self.assertTrue(objs[0]["in_latest_boxes"])

    def test_person_stays_live_only(self):
        def person_at(fid, x):
            return record_with(fid, [{
                "id": 1, "name": "person", "bbox_px": [1, 2, 3, 4],
                "conf": 0.9, "xyz_cam": [x, 0.0, 2.0],
                "xyz_world": [x, 0.0, 2.0], "last_seen_ns": 999_999_999,
                "frame_id": fid, "pose_epoch": 1, "in_latest_boxes": True,
            }])
        merged = self.run_merge(
            [person_at(2, 0.0), person_at(5, 0.0), record_with(8, [])],
            [vo_record(2, True, 0.0), vo_record(5, True, 0.0),
             vo_record(8, True, 0.0)])
        self.assertEqual([o["name"] for o in merged[0]["objects"]], ["person"])
        self.assertEqual([o["name"] for o in merged[1]["objects"]], ["person"])
        # no persistent person anchor: gone from the map when not detected
        self.assertEqual(merged[2]["objects"], [])

    def test_gate_splits_distant_same_class_objects(self):
        def chair(i, x):
            return {"id": i, "name": "chair", "bbox_px": [1, 2, 3, 4],
                    "conf": 0.9, "xyz_cam": [x, 0.0, 1.0],
                    "xyz_world": [x, 0.0, 1.0],
                    "last_seen_ns": 999_999_999, "frame_id": 2,
                    "pose_epoch": 1, "in_latest_boxes": True}
        chairs = record_with(2, [chair(1, 0.0), chair(2, 3.0)])
        merged = self.run_merge(
            [chairs, record_with(5, [])],
            [vo_record(2, True, 0.0), vo_record(5, True, 0.0)])
        names = sorted(o["name"] for o in merged[1]["objects"])
        self.assertEqual(names, ["chair", "chair"])
        positions = sorted(o["xyz_world"][0] for o in merged[1]["objects"])
        self.assertEqual(positions, [0.0, 3.0])
        self.assertFalse(any(o["in_latest_boxes"] for o in merged[1]["objects"]))

    def test_target_persists_via_anchor_when_out_of_frame(self):
        first = record_with(2, [{
            "id": 3, "name": "scissors", "bbox_px": [1, 2, 3, 4],
            "conf": 0.9, "xyz_cam": [0.0, 0.0, 2.0],
            "xyz_world": [0.0, 0.0, 2.0], "last_seen_ns": 999_999_999,
            "frame_id": 2, "pose_epoch": 1, "in_latest_boxes": True,
        }])
        first["target"] = {
            "id": 3, "name": "scissors", "xyz_cam": [0.0, 0.0, 2.0],
            "xyz_world": [0.0, 0.0, 2.0], "conf": 0.9,
            "last_seen_ns": 999_999_999, "frame_id": 2,
            "pose_epoch": 1, "in_latest_boxes": True,
        }
        merged = self.run_merge(
            [first, record_with(5, [])],
            [vo_record(2, True, 0.0), vo_record(5, True, 0.5)])
        t0 = merged[0]["target"]
        self.assertEqual(t0["name"], "scissors")
        self.assertEqual(t0["xyz_world"], [0.0, 0.0, 2.0])  # live transform
        self.assertTrue(t0["in_latest_boxes"])
        t1 = merged[1]["target"]
        self.assertIsNotNone(t1)  # faded anchor, not dropped
        self.assertEqual(t1["name"], "scissors")
        self.assertEqual(t1["xyz_world"], [0.0, 0.0, 2.0])  # anchor median
        self.assertFalse(t1["in_latest_boxes"])
        self.assertEqual(t1["last_seen_ns"], 2 * DT_NS)

    def test_named_target_is_sticky_through_retargeting(self):
        """--target scissors: the homing marker sticks to the named item's
        anchor even while the world pass retargets to other visible objects."""
        def rec(fid, name, x):
            return record_with(fid, [{
                "id": 1, "name": name, "bbox_px": [1, 2, 3, 4], "conf": 0.9,
                "xyz_cam": [x, 0.0, 2.0], "xyz_world": [x, 0.0, 2.0],
                "last_seen_ns": 999_999_999, "frame_id": fid,
                "pose_epoch": 1, "in_latest_boxes": True,
            }])
        scissors = rec(2, "scissors", 0.0)
        scissors["target"] = {"id": 1, "name": "scissors",
                               "xyz_cam": [0.0, 0.0, 2.0],
                               "xyz_world": [0.0, 0.0, 2.0], "conf": 0.9,
                               "last_seen_ns": 999_999_999,
                               "frame_id": 2, "pose_epoch": 1}
        bottle = rec(9, "bottle", 1.0)
        bottle["target"] = {"id": 1, "name": "bottle",
                            "xyz_cam": [1.0, 0.0, 2.0],
                            "xyz_world": [1.0, 0.0, 2.0], "conf": 0.9,
                            "last_seen_ns": 999_999_999,
                            "frame_id": 9, "pose_epoch": 1}
        merged = self.run_merge(
            [scissors, bottle],
            [vo_record(2, True, 0.0), vo_record(9, True, 0.5)],
            target="scissors")
        self.assertEqual(merged[0]["target"]["name"], "scissors")
        # frame 9 retargets to bottle; the sticky rule keeps homing to scissors
        t1 = merged[1]["target"]
        self.assertEqual(t1["name"], "scissors")
        self.assertFalse(t1["in_latest_boxes"])
        self.assertEqual(t1["xyz_world"], [0.0, 0.0, 2.0])

    def test_record_without_frame_id_uses_calibrated_ordinal(self):
        blank = world_record(5)
        blank["objects"] = []  # no frame_id anywhere
        merged = self.run_merge(
            [world_record(5), blank, world_record(11)],
            [vo_record(5, True, 1.0), vo_record(11, True, 2.0)])
        # ordinal 1 sits between 5 and 11; the median offset rule gives frame
        # 10, whose newest VO pose is still frame 5
        self.assertEqual(merged[1]["pose"]["T_world_from_cam"], T(1.0))
        self.assertEqual(merged[1]["t_ns"], 10 * DT_NS)


if __name__ == "__main__":
    unittest.main()
