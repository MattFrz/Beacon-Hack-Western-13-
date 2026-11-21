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
    return {
        "v": 1, "t_ns": 999_999_999, "seq": {"percept": frame_id},
        "mode": "LIVE", "law": "NONE", "cue": None, "intent": None,
        "target": None, "hand": None,
        "objects": [{
            "id": 7, "name": "bottle", "bbox_px": [1, 2, 3, 4], "conf": 0.9,
            "xyz_cam": list(xyz_cam), "xyz_world": list(xyz_cam),
            "last_seen_ns": 999_999_999, "frame_id": frame_id,
            "pose_epoch": 1, "in_latest_boxes": True,
        }],
        "pose": {"valid": True, "pose_epoch": 1, "t_ns": 999_999_999,
                 "age_ns": 0, "T_world_from_cam": T(0)},
        "crumbs": [], "health": {},
    }


def vo_record(frame_id: int, valid: bool, tx: float):
    return {"frame_id": frame_id, "valid": valid, "inliers": 100,
            "median_disp_px": 2.0, "h_est": None, "scale_mult": 1.0,
            "t": [tx, 0.0, 0.0], "T_world_from_cam": T(tx)}


class MergeTests(unittest.TestCase):
    def run_merge(self, world_records, vo_records):
        with tempfile.TemporaryDirectory() as tmp:
            world = write_jsonl(Path(tmp) / "w.jsonl", world_records)
            vo = write_jsonl(Path(tmp) / "vo.jsonl", vo_records)
            out = Path(tmp) / "merged.jsonl"
            merge_vo_world.merge(world, vo, out, fps=FPS)
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
