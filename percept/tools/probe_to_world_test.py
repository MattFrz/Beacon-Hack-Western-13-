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
from unittest.mock import patch

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


def make_probe(detections=None, hand=None, timings_ms=None):
    probe = {
        "frame_id": FRAME_ID,
        "W": 640,
        "H": 480,
        "detections": [] if detections is None else detections,
        "hand": hand,
    }
    if timings_ms is not None:
        probe["timings_ms"] = timings_ms
    return probe


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
        keychain = make_detection("keychain", [0.0, 0.1, 0.6])
        bottle = make_detection("bottle", [-0.4, -0.2, 1.3])

        first = probe_to_world(make_probe([bottle, keychain, keys]), t_ns=T_NS)
        self.assertEqual(first["target"]["name"], "keys")

        second = probe_to_world(make_probe([bottle, keychain]), t_ns=T_NS)
        self.assertEqual(second["target"]["name"], "keychain")

        third = probe_to_world(make_probe([bottle]), t_ns=T_NS)
        self.assertEqual(third["target"]["name"], "bottle")

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

    def test_missing_same_frame_distance_holds_last_or_is_omitted(self):
        hand = {"frame_id": FRAME_ID + 1, "xyz_cam": [0.2, 0.1, 0.3]}
        target = make_detection("keys", [0.1, 0.2, 0.5])
        probe = make_probe([target], hand)

        self.assertNotIn("d_m", probe_to_world(probe, t_ns=T_NS))
        self.assertEqual(
            probe_to_world(probe, t_ns=T_NS, last_d_m=1.25)["d_m"], 1.25
        )

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
            make_probe(timings_ms={"yolo": 12.5, "depth": 34}), t_ns=T_NS
        )
        self.assertEqual(world["health"]["last_yolo_ms"], 12.5)
        self.assertEqual(world["health"]["last_depth_ms"], 34)

        unknown = probe_to_world(make_probe(), t_ns=T_NS)
        self.assertIsNone(unknown["health"]["last_yolo_ms"])
        self.assertIsNone(unknown["health"]["last_depth_ms"])

    def test_no_detections_is_hold_with_null_hand(self):
        world = probe_to_world(make_probe(), t_ns=T_NS)

        self.assertEqual(world["mode"], "HOLD")
        self.assertEqual(world["objects"], [])
        self.assertIsNone(world["target"])
        self.assertIsNone(world["hand"])

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

    def test_emit_lines_increments_seq_and_holds_distance(self):
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
        prepared = ([], (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0, 0, 0))

        with patch.object(probe_frame, "prepare", return_value=prepared), patch.object(
            probe_frame, "probe_once", side_effect=probes
        ) as probe_once:
            lines = list(islice(emit_lines(args), 2))

        self.assertEqual([line["seq"]["percept"] for line in lines], [0, 2])
        self.assertAlmostEqual(lines[0]["d_m"], math.sqrt(0.06))
        self.assertEqual(lines[1]["d_m"], lines[0]["d_m"])
        self.assertEqual(probe_once.call_count, 2)

    def test_parser_has_world_cli_flags(self):
        parser = build_parser()
        args = parser.parse_args(["--out", "-", "--once"])
        self.assertEqual(str(args.out), "-")
        self.assertTrue(args.once)
        self.assertIsNone(args.calib)
        self.assertEqual(args.camera, 0)


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
        self.assertIn("d_m=0.2", line)

    def test_readout_omits_range_when_target_has_no_xyz(self):
        world = probe_to_world(make_probe([make_detection("keys")]), t_ns=T_NS, seq=2)

        line = format_readout(world)
        self.assertIn("name=keys", line)
        self.assertNotIn("range_m=", line)

    def test_hold_without_distance_omits_range_and_distance(self):
        world = probe_to_world(make_probe(), t_ns=T_NS, seq=4)

        line = format_readout(world)
        self.assertIn("mode=HOLD", line)
        self.assertNotIn("range_m=", line)
        self.assertNotIn("d_m=", line)

    def test_hold_can_show_held_distance_without_range(self):
        world = probe_to_world(make_probe(), t_ns=T_NS, seq=6, last_d_m=0.2)

        line = format_readout(world)
        self.assertIn("mode=HOLD", line)
        self.assertIn("d_m=0.2", line)
        self.assertNotIn("range_m=", line)

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
        self.receiver.settimeout(2.0)
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
        ):
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
