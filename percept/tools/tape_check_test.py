#!/usr/bin/env python3
"""CLI tape-check tests. Stdlib only; no camera, models, or live bridge."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import tape_check as tape  # noqa: E402


def range_record(xyz, name="bottle"):
    return {"objects": [{"name": name, "xyz_cam": list(xyz)}]}


def expected_result(kind, name, pred_m, tape_m, error_pct, passed, limit=0.3):
    return {
        "kind": kind,
        "name": name,
        "pred_m": pred_m,
        "tape_m": tape_m,
        "error": abs(pred_m - tape_m),
        "error_pct": error_pct,
        "limit": limit,
        "pass": passed,
    }


class TapeCheckTest(unittest.TestCase):
    def run_cli(self, payload, *args, stdin=False, suffix=".json"):
        """Run the CLI against a temporary record and capture both streams."""
        text = payload if isinstance(payload, str) else json.dumps(payload)
        stdout, stderr = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            source = "-"
            if not stdin:
                path = Path(directory) / ("world" + suffix)
                path.write_text(text, encoding="utf-8")
                source = str(path)
            stdin_patch = (
                patch.object(sys, "stdin", io.StringIO(text)) if stdin else contextlib.nullcontext()
            )
            with stdin_patch, contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = tape.main(["--json", source, *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def assertResult(self, stdout, expected):
        result = json.loads(stdout)
        self.assertEqual(set(result), set(expected))
        for key, value in expected.items():
            if isinstance(value, float):
                self.assertAlmostEqual(result[key], value, places=9, msg=key)
            else:
                self.assertEqual(result[key], value, key)
        return result

    def test_range_mode_uses_xyz_cam_norm_and_passes_at_threshold(self):
        code, stdout, stderr = self.run_cli(
            range_record([0.0, 0.0, 1.0]), "--tape-m", "1.0", "--name", "bottle"
        )

        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 1.0, 1.0, 0.0, True)
        )

    def test_range_mode_fails_when_error_exceeds_30_percent(self):
        code, stdout, stderr = self.run_cli(
            range_record([0.0, 1.4, 0.0]), "--tape-m", "1.0", "--name", "bottle"
        )

        self.assertEqual((code, stderr), (1, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 1.4, 1.0, 40.0, False)
        )

    def test_range_mode_passes_at_20_percent_error(self):
        code, stdout, stderr = self.run_cli(
            range_record([0.0, 0.0, 1.2]), "--tape-m", "1.0", "--name", "bottle"
        )

        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 1.2, 1.0, 20.0, True)
        )

    def test_d_m_mode_compares_same_frame_distance_to_tape(self):
        code, stdout, stderr = self.run_cli(
            {"d_m": 0.198, "objects": []}, "--tape-m", "0.2", "--kind", "d_m"
        )

        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(stdout, expected_result("d_m", None, 0.198, 0.2, 1.0, True))

    def test_missing_d_m_is_an_error_not_zero(self):
        code, stdout, stderr = self.run_cli(
            {"objects": range_record([0.0, 0.0, 1.0])["objects"]},
            "--tape-m",
            "0.2",
            "--kind",
            "d_m",
        )

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("d_m", stderr)

    def test_missing_xyz_cam_is_an_error_not_zero_range(self):
        record = {
            "target": {"name": "keys", "conf": 0.8},
            "objects": [{"name": "keys", "bbox_px": [1, 2, 3, 4]}],
        }
        code, stdout, stderr = self.run_cli(record, "--tape-m", "1.0")

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("xyz_cam", stderr)

    def test_named_object_without_xyz_is_an_error(self):
        record = {
            "target": {"name": "keys", "xyz_cam": [0, 0, 1.0]},
            "objects": [{"name": "bottle"}, {"name": "keys", "xyz_cam": [0, 0, 1.0]}],
        }
        code, stdout, stderr = self.run_cli(
            record, "--tape-m", "1.0", "--name", "bottle"
        )

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("xyz_cam", stderr)

    def test_malformed_objects_does_not_traceback(self):
        record = {"objects": 5, "target": {"name": "bottle", "xyz_cam": [0, 0, 1.0]}}
        code, stdout, stderr = self.run_cli(record, "--tape-m", "1.0")

        self.assertEqual((code, stderr), (0, ""))
        self.assertNotIn("Traceback", stderr)
        self.assertResult(
            stdout, expected_result("range", "bottle", 1.0, 1.0, 0.0, True)
        )

        code, stdout, stderr = self.run_cli({"objects": 5}, "--tape-m", "1.0")
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertNotIn("Traceback", stderr)
        self.assertIn("xyz_cam", stderr)

    def test_unmatched_name_falls_through_to_target(self):
        record = {
            "target": {"name": "keys", "xyz_cam": [0.0, 0.0, 1.0]},
            "objects": [{"name": "bottle", "xyz_cam": [0.0, 0.0, 2.0]}],
        }
        code, stdout, stderr = self.run_cli(
            record, "--tape-m", "1.0", "--name", "wallet"
        )

        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(stdout, expected_result("range", "keys", 1.0, 1.0, 0.0, True))

    def test_default_limit_applies_at_other_tape_distances(self):
        code, stdout, stderr = self.run_cli(
            range_record([0.0, 0.0, 2.7]), "--tape-m", "2.0"
        )
        self.assertEqual((code, stderr), (1, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 2.7, 2.0, 35.0, False)
        )

        code, stdout, stderr = self.run_cli(
            range_record([0.0, 0.0, 2.2]), "--tape-m", "2.0"
        )
        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 2.2, 2.0, 10.0, True)
        )

    def test_explicit_limit_can_allow_a_larger_error(self):
        code, stdout, stderr = self.run_cli(
            range_record([0.0, 0.0, 1.4]), "--tape-m", "1.0", "--limit", "0.5"
        )

        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 1.4, 1.0, 40.0, True, limit=0.5)
        )

    def test_nonpositive_tape_is_rejected(self):
        for tape_m in ("0", "-1.0"):
            with self.subTest(tape_m=tape_m):
                code, stdout, stderr = self.run_cli(
                    range_record([0.0, 0.0, 1.0]), "--tape-m", tape_m
                )
                self.assertEqual(code, 2)
                self.assertEqual(stdout, "")
                self.assertIn("tape", stderr)

    def test_target_and_first_object_are_range_fallbacks(self):
        record = {
            "target": {"name": "keys", "xyz_cam": [0.0, 0.3, 0.4]},
            "objects": [
                {"name": "unknown"},
                {"name": "bottle", "xyz_cam": [0.0, 0.0, 1.3]},
            ],
        }
        code, stdout, stderr = self.run_cli(record, "--tape-m", "0.5")
        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(stdout, expected_result("range", "keys", 0.5, 0.5, 0.0, True))

        record["target"] = {"name": "keys"}
        code, stdout, stderr = self.run_cli(record, "--tape-m", "1.3")
        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 1.3, 1.3, 0.0, True)
        )

    def test_jsonl_uses_last_nonempty_line(self):
        lines = [
            json.dumps(range_record([0, 0, 9.0])),
            "",
            json.dumps(range_record([0, 0, 1.0])),
            "   ",
        ]
        code, stdout, stderr = self.run_cli(
            "\n".join(lines), "--tape-m", "1.0", "--name", "bottle", suffix=".jsonl"
        )

        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 1.0, 1.0, 0.0, True)
        )

    def test_stdin_record_is_read_from_dash(self):
        code, stdout, stderr = self.run_cli(
            range_record([0.0, 0.0, 1.0]),
            "--tape-m",
            "1.0",
            "--name",
            "bottle",
            stdin=True,
        )

        self.assertEqual((code, stderr), (0, ""))
        self.assertResult(
            stdout, expected_result("range", "bottle", 1.0, 1.0, 0.0, True)
        )

    def test_cli_help_exposes_options(self):
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stdout(stdout):
            tape.build_parser().parse_args(["--help"])

        self.assertEqual(caught.exception.code, 0)
        text = stdout.getvalue()
        for flag in ("--json", "--tape-m", "--kind", "--name", "--limit"):
            self.assertIn(flag, text)
        self.assertIn("range", text)
        self.assertIn("d_m", text)


if __name__ == "__main__":
    unittest.main()
