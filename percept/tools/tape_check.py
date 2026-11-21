#!/usr/bin/env python3
"""Compare a recorded camera distance with a human tape measurement.

This is a measurement gate for Range 1: it reads a world/probe JSON record,
computes |xyz_cam| or the same-frame d_m, and reports the error against tape.
It does not run a camera, estimate pose, or speak metres.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

DEFAULT_LIMIT = 0.30


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", required=True, help="JSON path, or - for stdin; JSONL uses the last record"
    )
    parser.add_argument("--tape-m", required=True, type=float, help="human-measured metres")
    parser.add_argument(
        "--kind",
        choices=("range", "d_m"),
        default="range",
        help="range uses |xyz_cam|; d_m uses the record's same-frame distance",
    )
    parser.add_argument("--name", help="optional object name to select for range")
    parser.add_argument(
        "--limit",
        type=float,
        default=DEFAULT_LIMIT,
        help=f"maximum allowed error fraction (default {DEFAULT_LIMIT})",
    )
    return parser


def _number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _vec3(value: Any) -> Optional[Tuple[float, float, float]]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    xyz = tuple(_number(component) for component in value)
    if any(component is None for component in xyz):
        return None
    return xyz  # type: ignore[return-value]


def load_record(source: str) -> Mapping[str, Any]:
    """Read a JSON object from a path or stdin, or the last JSONL record."""
    text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("empty JSON input")
    try:
        record = json.loads(text)
    except json.JSONDecodeError:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError("empty JSON input")
        record = json.loads(lines[-1])
    if not isinstance(record, dict):
        raise ValueError("expected a JSON object record")
    return record


def _range_prediction(
    record: Mapping[str, Any], name: Optional[str]
) -> Tuple[float, Optional[str]]:
    raw = record.get("objects")
    objects = (
        [obj for obj in raw if isinstance(obj, Mapping)]
        if isinstance(raw, (list, tuple))
        else []
    )

    if name is not None:
        matches = [obj for obj in objects if obj.get("name") == name]
        if matches:
            xyz = _vec3(matches[0].get("xyz_cam"))
            if xyz is None:
                raise ValueError(f"object {name!r} has no valid xyz_cam")
            return math.sqrt(sum(component * component for component in xyz)), name

    target = record.get("target")
    if isinstance(target, Mapping):
        xyz = _vec3(target.get("xyz_cam"))
        if xyz is not None:
            return math.sqrt(sum(component * component for component in xyz)), target.get("name")

    for obj in objects:
        xyz = _vec3(obj.get("xyz_cam"))
        if xyz is not None:
            return math.sqrt(sum(component * component for component in xyz)), obj.get("name")

    raise ValueError("record has no valid xyz_cam for a range check")


def evaluate(
    record: Mapping[str, Any],
    tape_m: float,
    *,
    kind: str = "range",
    name: Optional[str] = None,
    limit: float = DEFAULT_LIMIT,
) -> Dict[str, Any]:
    """Build the single tape-check result object; never fabricate a prediction."""
    tape = _number(tape_m)
    if tape is None or tape <= 0:
        raise ValueError("--tape-m must be a finite number greater than 0")
    bound = _number(limit)
    if bound is None or bound < 0:
        raise ValueError("--limit must be a finite number at least 0")

    if kind == "d_m":
        pred = _number(record.get("d_m"))
        if pred is None:
            raise ValueError("record has no finite d_m for a same-frame check")
        selected_name = name
    elif kind == "range":
        pred, selected_name = _range_prediction(record, name)
    else:
        raise ValueError(f"unknown check kind {kind!r}")

    error = abs(pred - tape)
    fraction = error / tape
    return {
        "kind": kind,
        "name": selected_name,
        "pred_m": pred,
        "tape_m": tape,
        "error": error,
        "error_pct": 100.0 * fraction,
        "limit": bound,
        "pass": fraction <= bound,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        record = load_record(args.json)
        result = evaluate(
            record, args.tape_m, kind=args.kind, name=args.name, limit=args.limit
        )
    except (OSError, ValueError) as exc:
        print(f"tape check: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, separators=(",", ":"), sort_keys=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
