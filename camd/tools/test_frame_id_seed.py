#!/usr/bin/env python3
"""Regression check for camd frame-ID seeding across restarts on Linux.

The normal ring layout puts the highest frame_id in newest_slot, so a simple
stub-then-BMP run cannot distinguish max-across-slots seeding from reading only
the newest slot. This test writes a high id into a non-newest slot, restarts
camd, and checks that the published id is high_id + 1.

Run from the repo root after `make -C camd`:

    python3 camd/tools/test_frame_id_seed.py
"""

from __future__ import annotations

import ctypes
import mmap
import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CAMD = REPO_ROOT / "camd" / "camd"
READ_FRAMES = REPO_ROOT / "camd" / "read-frames"
SHM_PATH = Path("/dev/shm/beacon_frames")

ABI_VERSION = 1
FRAME_SLOTS = 3
FRAME_MAX_BYTES = 1920 * 1080 * 4
PLANTED_ID = 900
NEWEST_SLOT = 0
HIGH_ID_SLOT = 2


class FrameSlot(ctypes.Structure):
    _fields_ = [
        ("seq", ctypes.c_uint32),
        ("_pad0", ctypes.c_uint32),
        ("frame_id", ctypes.c_uint64),
        ("t_ns", ctypes.c_uint64),
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("stride", ctypes.c_uint32),
        ("frametype", ctypes.c_uint32),
        ("bytes_used", ctypes.c_uint32),
        ("_pad1", ctypes.c_uint32),
        ("pixels", ctypes.c_uint8 * FRAME_MAX_BYTES),
    ]


class Frames(ctypes.Structure):
    _fields_ = [
        ("abi", ctypes.c_uint32),
        ("newest_slot", ctypes.c_uint32),
        ("slot", FrameSlot * FRAME_SLOTS),
    ]


def run(cmd: list[Path]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def plant_non_newest_high_id() -> None:
    SHM_PATH.unlink(missing_ok=True)
    run([CAMD, "--stub", "--once"])

    with SHM_PATH.open("r+b") as fp:
        with mmap.mmap(fp.fileno(), ctypes.sizeof(Frames)) as mm:
            frames = Frames.from_buffer(mm)
            frames.abi = ABI_VERSION
            frames.newest_slot = NEWEST_SLOT
            for i, slot in enumerate(frames.slot):
                slot.seq = 2
                slot.frame_id = 1 + i
            high_slot = frames.slot[HIGH_ID_SLOT]
            high_slot.frame_id = PLANTED_ID
            mm.flush()
            del high_slot, slot, frames


def published_frame_id() -> int:
    output = run([READ_FRAMES])
    match = re.search(r"frame_id=(\d+)", output)
    if match is None:
        raise RuntimeError(f"no frame_id in read-frames output: {output!r}")
    return int(match.group(1))


def main() -> None:
    if not CAMD.exists() or not READ_FRAMES.exists():
        raise SystemExit("build camd first: make -C camd")
    if HIGH_ID_SLOT == NEWEST_SLOT:
        raise SystemExit("test setup error: high-id slot must not be newest")

    plant_non_newest_high_id()
    run([CAMD, "--stub", "--once"])
    got = published_frame_id()
    expected = PLANTED_ID + 1
    if got != expected:
        raise SystemExit(f"frame id seed failed: got {got}, expected {expected}")
    print(f"frame-id seed regression passed: {got}")


if __name__ == "__main__":
    main()
