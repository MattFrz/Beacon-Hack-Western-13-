#!/usr/bin/env python3
"""Conversion tests for probe_to_world. No models, camera, or MediaPipe."""

from __future__ import annotations

import contextlib
import io
import json
import math
import socket
import sys
import tempfile
import unittest
from itertools import islice
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import probe_frame  # noqa: E402
from percept.tools import probe_to_world as probe_to_world_module  # noqa: E402
from percept.tools.probe_to_world import (  # noqa: E402
    build_parser,
    emit_lines,
    format_readout,
    probe_to_world,
)

T_NS = 1_234_000_000
FRAME_ID = 7
JPEG = b"\xff\xd8\xff\xe0" + b"fake preview bytes"
IDENTITY_T = [
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1,
]


def make_detection(name: str, xyz=None, frame_id: int = FRAME_ID, conf: float = 0.8):
    detection = {
        "name": name,
        "conf": conf,
        "bbox_px": [10, 20, 30, 40],
        "center_px": [20, 30],
        "frame_id": frame_id,
    }
    if xyz is not None:
        detection["xyz_cam"] = list(xyz)
    return detection


def make_probe(detections=None, hand=None, timings_ms=None, t_ns=None):
    probe = {
        "frame_id": FRAME_ID,
        "W": 640,
        "H": 480,
        "detections": [] if detections is None else detections,
        "hand": hand,
    }
    if timings_ms is not None:
        probe["timings_ms"] = timings_ms
    if t_ns is not None:
        probe["t_ns"] = t_ns
    return probe


def make_last_bottle():
    live = probe_to_world(
        make_probe([make_detection("bottle", [0.0, 0.0, 1.0])]),
        t_ns=T_NS - 1_000_000_000,
    )
    return live["objects"], live["target"]


class ProbeToWorldTest(unittest.TestCase):
    def test_detection_xyz_cam_copies_to_xyz_world(self):
        xyz = [0.12, 0.15, 0.55]
        world = probe_to_world(
            make_probe([make_detection("keys", xyz)]), t_ns=T_NS, seq=0
        )

        obj = world["objects"][0]
        self.assertEqual(obj["xyz_cam"], xyz)
        self.assertEqual(obj["xyz_world"], xyz)
        self.assertEqual(world["target"]["xyz_world"], xyz)
        self.assertEqual(world["seq"]["percept"], 0)
        self.assertEqual(world["mode"], "LIVE")

    def test_target_uses_first_in_view_label_in_priority_order(self):
        keys = make_detection("keys", [0.1, 0.2, 0.5])
        mouse = make_detection("mouse", [0.0, 0.1, 0.6])
        bottle = make_detection("bottle", [-0.4, -0.2, 1.3])

        first = probe_to_world(make_probe([bottle, mouse, keys]), t_ns=T_NS)
        self.assertEqual(first["target"]["name"], "keys")

        second = probe_to_world(make_probe([bottle, mouse]), t_ns=T_NS)
        self.assertEqual(second["target"]["name"], "bottle")

        third = probe_to_world(make_probe([mouse]), t_ns=T_NS)
        self.assertEqual(third["target"]["name"], "mouse")

    def test_box_is_target_when_only_baked_name_in_view(self):
        world = probe_to_world(
            make_probe([make_detection("box", [0.1, 0.2, 0.7])]), t_ns=T_NS
        )

        self.assertEqual(world["target"]["name"], "box")

    def test_bottle_beats_box_when_both_are_in_view(self):
        box = make_detection("box", [0.1, 0.2, 0.7])
        bottle = make_detection("bottle", [-0.2, 0.1, 1.1])

        world = probe_to_world(make_probe([box, bottle]), t_ns=T_NS)
        self.assertEqual(world["target"]["name"], "bottle")

    def test_load_target_names_skips_comments_and_blanks_keeping_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.txt"
            path.write_text(
                "# baked nouns\n\n  keys  \n\n# more names\n keychain \nbottle\n"
                "  cup \n",
                encoding="utf-8",
            )

            names = probe_to_world_module.load_target_names(path)

        self.assertEqual(names, ("keys", "keychain", "bottle", "cup"))

    def test_load_target_names_errors_on_missing_or_short_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.txt"
            with self.assertRaises(OSError):
                probe_to_world_module.load_target_names(path)

            path.write_text(
                "keys\n\n# needs at least three\nkeychain\n", encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                probe_to_world_module.load_target_names(path)

    def test_frames_dir_writes_one_preview_per_record(self):
        """--frames-dir: one composite JPEG per emitted record, named by ordinal,
        so the bridge pairs frame i with replay record i."""
        tmp = Path(tempfile.mkdtemp())
        labels = tmp / "labels.txt"
        labels.write_text("keys\nkeychain\nbottle\n", encoding="utf-8")
        frames = tmp / "frames"
        asked_preview = []
        counter = {"n": 0}

        def fake_probe_once(_args, *_a, want_preview=False, **_k):
            counter["n"] += 1
            asked_preview.append(want_preview)
            idx = counter["n"]
            return {
                "frame_id": idx, "t_ns": idx, "W": 64, "H": 48,
                "detections": [], "hand": None, "notes": [],
                "timings_ms": {}, "depth_grid": None,
                "preview": b"\xff\xd8preview" if want_preview else None,
            }

        def fake_convert(probe, **_k):
            return {"t_ns": probe["t_ns"], "mode": "LIVE", "objects": [],
                    "target": None}

        args = probe_to_world_module.build_parser().parse_args(
            ["--image", "x.png", "--labels", str(labels),
             "--frames-dir", str(frames), "--out", "-"])
        with patch.object(probe_to_world_module.probe_frame, "prepare",
                          return_value=(("keys", "keychain", "bottle"),
                                        (0.0, 0.0, 0.0), (1.0, 1.0, 1.0),
                                        (0, 0, 0), MagicMock())), \
             patch.object(probe_to_world_module.probe_frame, "probe_once",
                          side_effect=fake_probe_once), \
             patch.object(probe_to_world_module, "probe_to_world",
                          side_effect=fake_convert):
            records = list(probe_to_world_module.emit_lines(args))

        files = sorted(frames.glob("*.jpg"))
        self.assertEqual(len(files), len(records))
        self.assertEqual([f.name for f in files], ["000000.jpg"])
        self.assertEqual(files[0].read_bytes(), b"\xff\xd8preview")
        self.assertEqual(asked_preview, [True])

    def test_module_target_names_cover_repo_labels_with_priority_first(self):
        labels_path = probe_to_world_module.REPO_ROOT / "models" / "labels.txt"
        baked = tuple(
            line.strip()
            for line in labels_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
        priority = ("keys", "phone", "bottle", "can", "box", "mouse")
        expected = priority + tuple(name for name in baked if name not in priority)

        self.assertEqual(probe_to_world_module.TARGET_NAMES, expected)
        self.assertEqual(probe_to_world_module.TARGET_NAMES[:6], priority)
        self.assertEqual(probe_to_world_module.TARGET_NAMES, expected)

    def test_distance_uses_same_frame_xyz_only(self):
        hand = {
            "frame_id": FRAME_ID,
            "fingertip_px": [1, 2],
            "xyz_cam": [0.2, 0.1, 0.3],
            "conf": 0.9,
        }
        target = make_detection("keys", [0.1, 0.2, 0.5])
        world = probe_to_world(make_probe([target], hand), t_ns=T_NS)

        self.assertAlmostEqual(world["d_m"], math.sqrt(0.06))

        other_frame = dict(hand, frame_id=FRAME_ID + 1)
        world = probe_to_world(make_probe([target], other_frame), t_ns=T_NS)
        self.assertNotIn("d_m", world)

        no_xyz_target = make_detection("keys")
        world = probe_to_world(make_probe([no_xyz_target], hand), t_ns=T_NS)
        self.assertNotIn("d_m", world)

    def test_baked_name_in_latest_boxes_is_live(self):
        world = probe_to_world(make_probe([make_detection("keys")]), t_ns=T_NS)

        self.assertEqual(world["mode"], "LIVE")
        self.assertTrue(world["objects"][0]["in_latest_boxes"])

    def test_live_without_hand_omits_d_m_even_with_last(self):
        hand = {"frame_id": FRAME_ID + 1, "xyz_cam": [0.2, 0.1, 0.3]}
        target = make_detection("keys", [0.1, 0.2, 0.5])
        probe = make_probe([target], hand)

        self.assertNotIn("d_m", probe_to_world(probe, t_ns=T_NS))
        self.assertNotIn(
            "d_m", probe_to_world(probe, t_ns=T_NS, last_d_m=1.25)
        )
        no_hand = probe_to_world(make_probe([target]), t_ns=T_NS, last_d_m=1.25)
        self.assertEqual(no_hand["mode"], "LIVE")
        self.assertNotIn("d_m", no_hand)

    def test_held_d_m_applies_only_to_hold_not_live_or_lost(self):
        target = make_detection("keys", [0.1, 0.2, 0.5])
        live = probe_to_world(
            make_probe([target]), t_ns=T_NS, last_d_m=0.2
        )
        hold = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_000_000_000,
            last_d_m=0.2,
        )
        lost = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_600_000_000,
            last_d_m=0.2,
        )

        self.assertEqual(live["mode"], "LIVE")
        self.assertNotIn("d_m", live)
        self.assertEqual(hold["mode"], "HOLD")
        self.assertEqual(hold["d_m"], 0.2)
        self.assertEqual(lost["mode"], "LOST")
        self.assertNotIn("d_m", lost)

    def test_phase_a_pose_is_identity_with_no_crumbs(self):
        world = probe_to_world(
            make_probe([make_detection("keys", [0.1, 0.2, 0.5])]), t_ns=T_NS
        )

        self.assertEqual(
            world["pose"],
            {
                "valid": True,
                "pose_epoch": 1,
                "t_ns": T_NS,
                "age_ns": 0,
                "T_world_from_cam": IDENTITY_T,
            },
        )
        self.assertEqual(world["pose_epoch"], 1)
        self.assertEqual(world["crumbs"], [])
        self.assertEqual(world["law"], "NONE")

    def test_detection_without_xyz_omits_camera_and_world_coordinates(self):
        world = probe_to_world(make_probe([make_detection("keys")]), t_ns=T_NS)

        obj = world["objects"][0]
        for key in ("name", "bbox_px", "conf", "frame_id", "in_latest_boxes"):
            self.assertIn(key, obj)
        self.assertTrue(obj["in_latest_boxes"])
        self.assertNotIn("xyz_cam", obj)
        self.assertNotIn("xyz_world", obj)
        self.assertNotIn("xyz_world", world["target"])

    def test_health_timings_are_numbers_when_provided(self):
        world = probe_to_world(
            make_probe(
                timings_ms={
                    "yolo": 12.5,
                    "depth": 34,
                    "hands": 5.5,
                    "cycle": 61.0,
                }
            ),
            t_ns=T_NS,
        )
        self.assertEqual(world["health"]["last_yolo_ms"], 12.5)
        self.assertEqual(world["health"]["last_depth_ms"], 34)
        self.assertEqual(world["health"]["last_hands_ms"], 5.5)
        self.assertEqual(world["health"]["last_cycle_ms"], 61.0)

        unknown = probe_to_world(make_probe(), t_ns=T_NS)
        self.assertIsNone(unknown["health"]["last_yolo_ms"])
        self.assertIsNone(unknown["health"]["last_depth_ms"])
        self.assertIsNone(unknown["health"]["last_hands_ms"])
        self.assertIsNone(unknown["health"]["last_cycle_ms"])

    def test_no_detections_without_history_is_lost_with_null_hand(self):
        world = probe_to_world(make_probe(), t_ns=T_NS)

        self.assertEqual(world["mode"], "LOST")
        self.assertEqual(world["objects"], [])
        self.assertIsNone(world["target"])
        self.assertIsNone(world["hand"])
        self.assertNotIn("d_m", world)

    def test_recent_missing_target_is_hold_with_held_distance(self):
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_000_000_000,
            last_d_m=0.2,
        )

        self.assertEqual(world["mode"], "HOLD")
        self.assertEqual(world["d_m"], 0.2)
        self.assertIsNone(world["target"])
        self.assertEqual(world["objects"], [])

    def test_hold_replays_last_live_objects_and_target_faded(self):
        last_objects, last_target = make_last_bottle()
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_000_000_000,
            last_d_m=0.2,
            last_objects=last_objects,
            last_target=last_target,
        )

        self.assertEqual(world["mode"], "HOLD")
        self.assertEqual(world["d_m"], 0.2)
        self.assertEqual(world["target"]["name"], "bottle")
        self.assertIs(world["target"]["in_latest_boxes"], False)
        self.assertEqual(len(world["objects"]), 1)
        self.assertIs(world["objects"][0]["in_latest_boxes"], False)
        self.assertEqual(world["objects"][0]["xyz_cam"], [0.0, 0.0, 1.0])

    def test_hold_derived_target_without_last_target_is_faded(self):
        last_objects, _last_target = make_last_bottle()
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_000_000_000,
            last_d_m=0.2,
            last_objects=last_objects,
        )

        self.assertEqual(world["mode"], "HOLD")
        self.assertEqual(world["target"]["name"], "bottle")
        self.assertIs(world["target"]["in_latest_boxes"], False)
        self.assertIs(world["objects"][0]["in_latest_boxes"], False)

    def test_hold_does_not_alias_last_live_objects_or_target(self):
        last_objects, last_target = make_last_bottle()
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_000_000_000,
            last_d_m=0.2,
            last_objects=last_objects,
            last_target=last_target,
        )

        world["objects"][0]["xyz_cam"][2] = 99.0
        world["objects"][0]["name"] = "cup"
        world["target"]["xyz_cam"][2] = 99.0

        self.assertEqual(last_objects[0]["xyz_cam"], [0.0, 0.0, 1.0])
        self.assertEqual(last_objects[0]["name"], "bottle")
        self.assertIs(last_objects[0]["in_latest_boxes"], True)
        self.assertEqual(last_target["xyz_cam"], [0.0, 0.0, 1.0])

    def test_lost_ignores_last_live_objects_and_target(self):
        last_objects, last_target = make_last_bottle()
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_500_000_000,
            last_d_m=0.2,
            last_objects=last_objects,
            last_target=last_target,
        )

        self.assertEqual(world["mode"], "LOST")
        self.assertNotIn("d_m", world)
        self.assertEqual(world["objects"], [])
        self.assertIsNone(world["target"])

    def test_exactly_hold_max_age_is_lost_without_distance(self):
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_500_000_000,
            last_d_m=0.2,
        )

        self.assertEqual(world["mode"], "LOST")
        self.assertNotIn("d_m", world)

    def test_exact_hold_max_age_stays_lost_above_float53(self):
        now_ns = (1 << 53) + 1
        world = probe_to_world(
            make_probe(),
            t_ns=now_ns,
            last_seen_ns=now_ns - 1_500_000_000,
            last_d_m=0.2,
        )

        self.assertEqual(world["mode"], "LOST")
        self.assertNotIn("d_m", world)

    def test_older_than_hold_max_age_is_lost_without_distance(self):
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            last_seen_ns=T_NS - 1_600_000_000,
            last_d_m=0.2,
        )

        self.assertEqual(world["mode"], "LOST")
        self.assertNotIn("d_m", world)

    def test_hand_world_is_identity_and_conf_is_optional(self):
        hand = {
            "frame_id": FRAME_ID,
            "xyz_cam": [0.22, 0.13, 0.38],
            "conf": 0.9,
        }
        world = probe_to_world(make_probe(hand=hand), t_ns=T_NS)
        self.assertEqual(world["hand"]["xyz_cam"], hand["xyz_cam"])
        self.assertEqual(world["hand"]["xyz_world"], hand["xyz_cam"])
        self.assertEqual(world["hand"]["conf"], 0.9)
        self.assertEqual(world["hand"]["t_ns"], T_NS)
        self.assertEqual(world["hand"]["frame_id"], FRAME_ID)

        hand_without_xyz = {"frame_id": FRAME_ID, "conf": 0.7}
        world = probe_to_world(make_probe(hand=hand_without_xyz), t_ns=T_NS)
        self.assertNotIn("xyz_cam", world["hand"])
        self.assertNotIn("xyz_world", world["hand"])

    def test_seq_percept_even_increment(self):
        first = probe_to_world(make_probe(), t_ns=T_NS, seq=0)
        second = probe_to_world(make_probe(), t_ns=T_NS + 1, seq=2)
        self.assertEqual(first["seq"]["percept"], 0)
        self.assertEqual(second["seq"]["percept"], 2)

    def test_emit_lines_increments_seq_and_omits_stale_live_distance(self):
        hand = {
            "frame_id": FRAME_ID,
            "xyz_cam": [0.2, 0.1, 0.3],
            "conf": 0.9,
        }
        target = make_detection("keys", [0.1, 0.2, 0.5])
        probes = [
            make_probe([target], hand),
            make_probe([target], dict(hand, frame_id=FRAME_ID + 1)),
        ]
        args = build_parser().parse_args(["--out", "-"])
        prepared = (
            [], (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0, 0, 0),
            contextlib.nullcontext(),
        )
        probe_iter = iter(probes)

        with patch.object(probe_frame, "prepare", return_value=prepared), patch.object(
            probe_frame, "probe_once", side_effect=lambda *_a, **_k: next(probe_iter)
        ) as probe_once:
            lines = list(islice(emit_lines(args), 2))

        self.assertEqual([line["seq"]["percept"] for line in lines], [0, 2])
        self.assertAlmostEqual(lines[0]["d_m"], math.sqrt(0.06))
        self.assertNotIn("d_m", lines[1])
        self.assertEqual(probe_once.call_count, 2)

    def test_emit_lines_tracks_live_hold_lost_and_clears_distance(self):
        hand = {
            "frame_id": FRAME_ID,
            "xyz_cam": [0.2, 0.1, 0.3],
            "conf": 0.9,
        }
        target = make_detection("bottle", [0.0, 0.0, 1.0])
        probes = [
            make_probe([target], hand, t_ns=T_NS),
            make_probe(t_ns=T_NS + 1_000_000_000),
            make_probe(t_ns=T_NS + 1_600_000_000),
            make_probe(t_ns=T_NS + 1_700_000_000),
        ]
        args = build_parser().parse_args(["--out", "-"])
        prepared = (
            [], (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0, 0, 0),
            contextlib.nullcontext(),
        )
        probe_iter = iter(probes)

        with patch.object(probe_frame, "prepare", return_value=prepared), patch.object(
            probe_frame, "probe_once", side_effect=lambda *_a, **_k: next(probe_iter)
        ):
            stream = emit_lines(args)
            lines = [next(stream)]
            lines[0]["objects"][0]["xyz_cam"][2] = 99.0
            lines.extend(islice(stream, len(probes) - 1))

        self.assertEqual(
            [line["t_ns"] for line in lines],
            [
                T_NS,
                T_NS + 1_000_000_000,
                T_NS + 1_600_000_000,
                T_NS + 1_700_000_000,
            ],
        )
        self.assertEqual(
            [line["mode"] for line in lines], ["LIVE", "HOLD", "LOST", "LOST"]
        )
        self.assertTrue(lines[0]["objects"][0]["in_latest_boxes"])
        self.assertAlmostEqual(lines[0]["d_m"], math.sqrt(0.54))
        self.assertEqual(lines[1]["objects"][0]["name"], "bottle")
        self.assertIs(lines[1]["objects"][0]["in_latest_boxes"], False)
        self.assertEqual(lines[1]["objects"][0]["xyz_cam"], [0.0, 0.0, 1.0])
        self.assertEqual(lines[1]["target"]["name"], "bottle")
        self.assertIs(lines[1]["target"]["in_latest_boxes"], False)
        self.assertEqual(lines[1]["d_m"], lines[0]["d_m"])
        self.assertEqual(lines[2]["objects"], [])
        self.assertIsNone(lines[2]["target"])
        self.assertNotIn("d_m", lines[2])
        self.assertEqual(lines[3]["objects"], [])
        self.assertIsNone(lines[3]["target"])
        self.assertNotIn("d_m", lines[3])

    def test_parser_has_world_cli_flags(self):
        parser = build_parser()
        args = parser.parse_args(["--out", "-", "--once"])
        self.assertEqual(str(args.out), "-")
        self.assertTrue(args.once)
        self.assertIsNone(args.calib)
        self.assertEqual(args.camera, 0)

    def test_parser_has_jpeg_flags_with_defaults(self):
        args = build_parser().parse_args(["--udp", "127.0.0.1:5005", "--jpeg"])
        self.assertTrue(args.jpeg)
        self.assertEqual(args.jpeg_width, 320)
        self.assertEqual(args.jpeg_quality, 60)
        self.assertEqual(args.jpeg_every, 1)

        tuned = build_parser().parse_args(
            [
                "--jpeg", "--udp", "127.0.0.1:5005",
                "--jpeg-width", "240", "--jpeg-quality", "45",
                "--jpeg-every", "3",
            ]
        )
        self.assertEqual(tuned.jpeg_width, 240)
        self.assertEqual(tuned.jpeg_quality, 45)
        self.assertEqual(tuned.jpeg_every, 3)

    def test_jpeg_requires_udp(self):
        with patch.object(probe_to_world_module, "emit_lines") as emit_lines_mock:
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    probe_to_world_module.main(["--out", "-", "--jpeg"])
        emit_lines_mock.assert_not_called()
        self.assertIn("--jpeg", stderr.getvalue())
        self.assertIn("--udp", stderr.getvalue())

    def test_jpeg_bytes_never_enter_world_dict(self):
        probe = make_probe()
        probe["jpeg"] = JPEG
        world = probe_to_world(probe, t_ns=T_NS)

        self.assertNotIn("jpeg", world)
        self.assertNotIn(JPEG, json.dumps(world, separators=(",", ":")).encode("utf-8"))


class ReadoutTest(unittest.TestCase):
    def test_readout_reports_norm_and_record_identity(self):
        world = probe_to_world(
            make_probe([make_detection("bottle", [0, 0, 1.0])]), t_ns=T_NS, seq=0
        )

        line = format_readout(world)
        self.assertNotIn("\n", line)
        self.assertIn("seq=0", line)
        self.assertIn("mode=LIVE", line)
        self.assertIn("name=bottle", line)
        self.assertRegex(line, r"\brange_m=1(?:\.0+)?(?:\s|$)")
        self.assertIn("objects=1", line)

        lateral = probe_to_world(
            make_probe([make_detection("bottle", [3.0, 4.0, 0.0])]), t_ns=T_NS, seq=0
        )
        self.assertIn("range_m=5.000", format_readout(lateral))

    def test_readout_includes_finite_distance(self):
        world = probe_to_world(
            make_probe([make_detection("bottle", [0, 0, 1.0])]), t_ns=T_NS, seq=0
        )
        world["d_m"] = 0.2

        line = format_readout(world)
        self.assertRegex(line, r"\brange_m=1(?:\.0+)?(?:\s|$)")
        self.assertRegex(line, r"\bd_m=0\.2(?:0+)?(?:\s|$)")

    def test_readout_omits_range_when_target_has_no_xyz(self):
        world = probe_to_world(make_probe([make_detection("keys")]), t_ns=T_NS, seq=2)

        line = format_readout(world)
        self.assertIn("name=keys", line)
        self.assertNotIn("range_m=", line)

    def test_hold_without_distance_omits_range_and_distance(self):
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            seq=4,
            last_seen_ns=T_NS - 1_000_000_000,
        )

        line = format_readout(world)
        self.assertIn("mode=HOLD", line)
        self.assertNotIn("range_m=", line)
        self.assertNotIn("d_m=", line)

    def test_hold_readout_shows_held_name_range_and_distance(self):
        last_objects, last_target = make_last_bottle()
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            seq=6,
            last_seen_ns=T_NS - 1_000_000_000,
            last_d_m=0.2,
            last_objects=last_objects,
            last_target=last_target,
        )

        line = format_readout(world)
        self.assertIn("mode=HOLD", line)
        self.assertIn("name=bottle", line)
        self.assertRegex(line, r"\brange_m=1(?:\.0+)?(?:\s|$)")
        self.assertRegex(line, r"\bd_m=0\.2(?:0+)?(?:\s|$)")
        self.assertIn("objects=1", line)

    def test_lost_readout_omits_range_and_distance(self):
        last_objects, last_target = make_last_bottle()
        world = probe_to_world(
            make_probe(),
            t_ns=T_NS,
            seq=8,
            last_seen_ns=T_NS - 1_600_000_000,
            last_d_m=0.2,
            last_objects=last_objects,
            last_target=last_target,
        )

        line = format_readout(world)
        self.assertIn("mode=LOST", line)
        self.assertNotIn("range_m=", line)
        self.assertNotIn("d_m=", line)

    def test_main_sends_readout_to_stderr_and_jsonl_to_stdout(self):
        world = probe_to_world(
            make_probe([make_detection("bottle", [0, 0, 1.0])]), t_ns=T_NS, seq=0
        )
        world["d_m"] = 0.2

        with patch.object(
            probe_to_world_module, "emit_lines", return_value=[world]
        ), contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(
            io.StringIO()
        ) as stderr:
            self.assertEqual(probe_to_world_module.main(["--out", "-"]), 0)

        stdout_lines = stdout.getvalue().splitlines()
        stderr_lines = stderr.getvalue().splitlines()
        self.assertEqual(len(stdout_lines), 1)
        self.assertEqual(json.loads(stdout_lines[0]), world)
        self.assertEqual(len(stderr_lines), 1)
        self.assertIn("mode=LIVE", stderr_lines[0])
        self.assertIn("range_m=", stderr_lines[0])
        self.assertIn("d_m=", stderr_lines[0])
        self.assertNotIn(stderr_lines[0], stdout.getvalue())


class UdpEmitTest(unittest.TestCase):
    def setUp(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receiver.bind(("127.0.0.1", 0))
        self.receiver.settimeout(5.0)
        self.addCleanup(self.receiver.close)
        self.target = f"127.0.0.1:{self.receiver.getsockname()[1]}"
        self.world = probe_to_world(
            make_probe([make_detection("keys", [0.1, 0.2, 0.5])]), t_ns=T_NS
        )

    def receive_payload(self):
        return self.receiver.recvfrom(65535)[0]

    def run_with_world(self, argv):
        with patch.object(
            probe_to_world_module, "emit_lines", return_value=[self.world]
        ), contextlib.redirect_stderr(io.StringIO()):
            return probe_to_world_module.main(argv)

    def run_with_jpeg(self, argv, jpeg=JPEG, count=1):
        def fake_emit_lines(_args, on_video=None):
            yield self.world
            if on_video is not None:
                for _ in range(count):
                    on_video(jpeg)

        with patch.object(
            probe_to_world_module, "emit_lines", side_effect=fake_emit_lines
        ), contextlib.redirect_stderr(io.StringIO()):
            return probe_to_world_module.main(argv)

    def test_udp_datagram_matches_world_record(self):
        self.assertEqual(self.run_with_world(["--udp", self.target]), 0)

        payload = self.receive_payload()
        self.assertEqual(json.loads(payload), self.world)
        self.assertEqual(
            payload,
            json.dumps(self.world, separators=(",", ":"), sort_keys=False).encode(
                "utf-8"
            ),
        )

    def test_jsonl_and_udp_are_both_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "world.jsonl"
            self.assertEqual(
                self.run_with_world(["--out", str(out), "--udp", self.target]), 0
            )
            lines = out.read_text(encoding="utf-8").splitlines()

        payload = self.receive_payload()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0]), self.world)
        self.assertEqual(payload.decode("utf-8"), lines[0])

    def test_out_is_optional_when_udp_is_set(self):
        args = build_parser().parse_args(["--udp", self.target])
        self.assertIsNone(args.out)
        self.assertEqual(args.udp, self.target)
        self.assertEqual(self.run_with_world(["--udp", self.target]), 0)
        self.assertEqual(json.loads(self.receive_payload()), self.world)

    def test_bare_udp_sends_only_world_datagram(self):
        prepared = (
            [], (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0, 0, 0),
            contextlib.nullcontext(),
        )
        wanted = []

        def fake_probe_once(*_args, **kwargs):
            wanted.append(kwargs.get("want_jpeg", False))
            return make_probe([make_detection("keys", [0.1, 0.2, 0.5])], t_ns=T_NS)

        with patch.object(probe_frame, "prepare", return_value=prepared), patch.object(
            probe_frame, "probe_once", side_effect=fake_probe_once
        ), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(
                probe_to_world_module.main(["--udp", self.target, "--once"]), 0
            )

        self.assertEqual(wanted, [False])
        self.assertEqual(json.loads(self.receive_payload()), self.world)
        self.receiver.settimeout(0.05)
        with self.assertRaises(socket.timeout):
            self.receiver.recvfrom(65535)

    def test_jpeg_every_zero_is_parser_error_with_or_without_jpeg(self):
        for bad in ("0", "-1"):
            for extra in ([], ["--jpeg"]):
                with self.subTest(bad=bad, extra=extra):
                    with patch.object(
                        probe_to_world_module, "emit_lines"
                    ) as emit_lines_mock:
                        with contextlib.redirect_stderr(io.StringIO()) as stderr:
                            with self.assertRaises(SystemExit):
                                probe_to_world_module.main(
                                    [
                                        "--udp", self.target,
                                        "--jpeg-every", bad, *extra,
                                    ]
                                )
                    emit_lines_mock.assert_not_called()
                    self.assertIn("--jpeg-every", stderr.getvalue())

        self.receiver.settimeout(0.05)
        with self.assertRaises(socket.timeout):
            self.receiver.recvfrom(65535)

    def test_missing_out_and_udp_is_error(self):
        with patch.object(probe_to_world_module, "emit_lines") as emit_lines_mock:
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    probe_to_world_module.main([])
        emit_lines_mock.assert_not_called()
        self.assertIn("--out", stderr.getvalue())
        self.assertIn("--udp", stderr.getvalue())

    def test_udp_payload_is_one_json_object_under_60kb(self):
        self.assertEqual(self.run_with_world(["--udp", self.target]), 0)

        payload = self.receive_payload()
        self.assertLess(len(payload), 60000)
        self.assertIsInstance(json.loads(payload), dict)
        self.assertNotIn(b"\n", payload)
        self.receiver.settimeout(0.05)
        with self.assertRaises(socket.timeout):
            self.receiver.recvfrom(65535)

    def test_bare_udp_defaults_to_loopback_5005(self):
        args = build_parser().parse_args(["--udp"])
        self.assertEqual(args.udp, "127.0.0.1:5005")
        self.assertEqual(
            probe_to_world_module.parse_udp_target(args.udp), ("127.0.0.1", 5005)
        )

    def test_jpeg_is_a_separate_raw_datagram(self):
        self.assertEqual(self.run_with_jpeg(["--udp", self.target, "--jpeg"]), 0)

        world_payload = self.receive_payload()
        self.assertEqual(json.loads(world_payload), self.world)

        video_payload = self.receive_payload()
        self.assertTrue(video_payload.startswith(b"\xff\xd8"))
        self.assertEqual(video_payload, JPEG)
        with self.assertRaises(ValueError):
            json.loads(video_payload)
        self.assertNotIn(b"\n", video_payload)
        self.assertLess(len(video_payload), 60_000)

        self.receiver.settimeout(0.05)
        with self.assertRaises(socket.timeout):
            self.receiver.recvfrom(65535)

    def test_jpeg_never_appears_in_out_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "world.jsonl"
            self.assertEqual(
                self.run_with_jpeg(
                    ["--out", str(out), "--udp", self.target, "--jpeg"]
                ),
                0,
            )
            raw = out.read_bytes()
            lines = raw.decode("utf-8").splitlines()

        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0]), self.world)
        self.assertNotIn(JPEG, raw)
        self.assertNotIn(b"jpeg", raw)
        self.assertEqual(json.loads(self.receive_payload()), self.world)
        self.assertTrue(self.receive_payload().startswith(b"\xff\xd8"))

    def test_jpeg_every_controls_video_datagram_count(self):
        args = build_parser().parse_args(
            ["--udp", self.target, "--jpeg", "--jpeg-every", "2"]
        )
        prepared = (
            [], (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0, 0, 0),
            contextlib.nullcontext(),
        )
        # islice bounds the camera loop; no attempt is made to exhaust the fake.
        wanted = []
        collected = []

        def fake_probe_once(*_args, **kwargs):
            index = len(wanted)
            wanted.append(kwargs.get("want_jpeg", False))
            probe = make_probe(t_ns=T_NS + index)
            if index % 2 == 0:
                probe["jpeg"] = JPEG
            return probe

        with patch.object(probe_frame, "prepare", return_value=prepared), patch.object(
            probe_frame, "probe_once", side_effect=fake_probe_once
        ):
            lines = list(islice(emit_lines(args, on_video=collected.append), 6))

        # The last yielded record's post-yield callback runs on the next resume.
        self.assertEqual(len(lines), 6)
        self.assertEqual(
            [line["seq"]["percept"] for line in lines], [0, 2, 4, 6, 8, 10]
        )
        self.assertEqual(wanted, [True, False, True, False, True, False])
        self.assertEqual(collected, [JPEG, JPEG, JPEG])

    def test_oversized_jpeg_dropped_with_one_warning(self):
        oversized = b"\xff\xd8" + b"x" * 60_000

        def fake_emit_lines(_args, on_video=None):
            yield self.world
            on_video(oversized)
            on_video(oversized)

        with patch.object(
            probe_to_world_module, "emit_lines", side_effect=fake_emit_lines
        ), contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(
                probe_to_world_module.main(["--udp", self.target, "--jpeg"]), 0
            )

        self.assertEqual(json.loads(self.receive_payload()), self.world)
        self.receiver.settimeout(0.05)
        with self.assertRaises(socket.timeout):
            self.receiver.recvfrom(65535)
        self.assertEqual(stderr.getvalue().count("60000"), 1)

    def test_invalid_udp_target_errors_without_sending(self):
        for bad in (
            "127.0.0.1", "bad:port", ":5005", "a:b:5005",
            "127.0.0.1:0", "127.0.0.1:70000", "",
        ):
            with self.subTest(bad=bad):
                with patch.object(probe_to_world_module, "emit_lines") as emit_lines_mock:
                    with contextlib.redirect_stderr(io.StringIO()) as stderr:
                        with self.assertRaises(SystemExit):
                            probe_to_world_module.main(["--udp", bad])
                emit_lines_mock.assert_not_called()
                self.assertIn("--udp", stderr.getvalue())

        self.receiver.settimeout(0.05)
        with self.assertRaises(socket.timeout):
            self.receiver.recvfrom(65535)


if __name__ == "__main__":
    unittest.main()
