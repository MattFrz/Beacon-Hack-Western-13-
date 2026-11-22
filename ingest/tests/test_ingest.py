#!/usr/bin/env python3
"""End-to-end laptop test of the ingest relay (docs/qnx-integration-plan.md step 4).

Feeds the percept probe's world-record JSON (the exact schema probe_to_world.py
sends over --udp) into `ingest --udp`, then watches `guided` (60 Hz synthesizer)
react through a private /beacon_world (BEACON_WORLD env, never the live
/dev/shm/beacon_world):

  phase A  keys 2 m ahead, no hand            -> guided binds (FIND:keys) and says a WALK cue
  phase B  hand approaches 0.45 -> 0.05 m     -> guided enters REACH, ticks, then a tone
  phase C  records stop                      -> LIVE expires, HOLD, then LOST speech ("I lost the target")

This is the sequence the Sunday script needs on the Pi, minus real vision:
it proves the missing percept->guided wire is closed.

No model, no camera, no network beyond loopback. Runtime ~15 s.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
INGEST_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(INGEST_DIR)

WALK_SECONDS = 4.0
REACH_SECONDS = 4.0
RECORD_HZ = 4.0  # 250 ms cadence, faster than the probe's ~8 Hz cycle
KEYS_XYZ = [0.2, 0.1, 2.0]


def record(t_ns, frame_id, hand=None, in_latest_boxes=True):
    """One probe world record (probe_to_world.py schema, HOLD objects included)."""
    objs = [{
        "id": 3, "name": "keys",
        "xyz_cam": KEYS_XYZ, "xyz_world": KEYS_XYZ,
        "bbox_px": [700, 500, 800, 600], "conf": 0.81,
        "last_seen_ns": t_ns, "frame_id": frame_id,
        "pose_epoch": 1, "in_latest_boxes": in_latest_boxes,
    }]
    rec = {
        "v": 1, "t_ns": t_ns,
        "seq": {"percept": frame_id, "voiced": None, "guided": None},
        "mode": "LIVE", "law": "NONE", "cue": None, "intent": None,
        "target": None, "hand": hand, "objects": objs,
        "pose": {
            "valid": True, "pose_epoch": 1, "t_ns": t_ns, "age_ns": 0,
            "T_world_from_cam": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        },
        "pose_epoch": 1, "crumbs": [],
        "health": {"last_yolo_ms": 14, "last_depth_ms": 93,
                   "last_hands_ms": 15, "last_cycle_ms": 124},
    }
    return json.dumps(rec, separators=(",", ":")).encode()


def hand_at(t_ns, frame_id, d):
    """Hand at distance d (m) straight back from the keys, same frame."""
    xyz = [KEYS_XYZ[0], KEYS_XYZ[1], KEYS_XYZ[2] - d]
    return {"t_ns": t_ns, "frame_id": frame_id, "conf": 0.9,
            "xyz_cam": xyz, "xyz_world": xyz}


def free_udp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_for_exit(proc, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return proc.returncode
        time.sleep(0.05)
    proc.kill()
    raise AssertionError("process did not exit in time")


def main():
    for d in ("ingest", "guided"):
        r = subprocess.run(["make", "-C", os.path.join(REPO, d)], check=False,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout, file=sys.stderr)
            print(r.stderr, file=sys.stderr)
            raise SystemExit(f"{d} build failed")

    world = "/beacon-ingest-test-" + uuid.uuid4().hex[:8]
    port = free_udp_port()
    env = dict(os.environ, BEACON_WORLD=world)
    guided_duration = WALK_SECONDS + REACH_SECONDS + 5.0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)

    ingest_log = tempfile.NamedTemporaryFile(mode="w+", prefix="ingest-", suffix=".log")
    guided_out = tempfile.NamedTemporaryFile(mode="w+", prefix="guided-", suffix=".log")

    ingest = subprocess.Popen(
        [os.path.join(INGEST_DIR, "build", "ingest"),
         "--create", "--udp", str(port), "--intent", "FIND:keys", "--verbose"],
        env=env, stdout=ingest_log, stderr=subprocess.STDOUT)
    try:
        target = ("127.0.0.1", port)
        frame = 0

        guided = subprocess.Popen(
            [os.path.join(REPO, "guided", "build", "guided"),
             "--duration", f"{guided_duration:.1f}"],
            env=env, stdout=guided_out, stderr=subprocess.STDOUT)

        # phase A: keys ahead, no hand -> guided binds on the FIND intent and says a WALK cue
        t0 = time.monotonic()
        while time.monotonic() - t0 < WALK_SECONDS:
            sock.sendto(record(time.monotonic_ns(), frame), target)
            frame += 1
            time.sleep(1.0 / RECORD_HZ)

        # phase B: hand closes 0.45 -> 0.05 m -> REACH ticks, then a tone
        t0 = time.monotonic()
        while time.monotonic() - t0 < REACH_SECONDS:
            frac = (time.monotonic() - t0) / REACH_SECONDS
            d = 0.45 * (1.0 - frac) + 0.05 * frac
            now = time.monotonic_ns()
            sock.sendto(record(now, frame, hand=hand_at(now, frame, d)), target)
            frame += 1
            time.sleep(1.0 / RECORD_HZ)

        # phase C: silence -> LIVE expires (1 s), HOLD (to 1.5 s), LOST speech

        rc = wait_for_exit(guided, guided_duration + 20)
    finally:
        ingest.terminate()
        try:
            ingest.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ingest.kill()
        sock.close()

    guided_out.seek(0)
    lines = guided_out.readlines()
    text = "".join(lines)
    ingest_log.seek(0)
    ingest_text = ingest_log.read()

    shm_path = f"/dev/shm{world}"
    if os.path.exists(shm_path):
        os.unlink(shm_path)

    print("--- guided output ---")
    print(text)
    fails = []

    def find(pred, what):
        for i, line in enumerate(lines):
            if pred(line):
                return i
        fails.append(what)
        return -1

    i_say_keys = find(lambda l: "SAY" in l and "keys" in l, "no WALK SAY with 'keys'")
    i_tick = find(lambda l: ("TICK" in l or "TONE  on" in l), "no REACH tick/tone")
    i_lost = find(lambda l: "SAY" in l and "I lost the target" in l, "no LOST speech")
    if 0 <= i_say_keys < i_tick < i_lost:
        print(f"OK: WALK({i_say_keys}) < REACH({i_tick}) < LOST({i_lost})")
    else:
        fails.append(f"phase order wrong: say={i_say_keys} reach={i_tick} lost={i_lost}")

    if "intent FIND" not in ingest_text and "intent 1 with" not in ingest_text:
        fails.append("ingest never wrote the FIND intent")
    if "records," not in ingest_text:
        fails.append("ingest processed no records")
    if rc != 0:
        fails.append(f"guided exit code {rc}")

    if fails:
        print("--- ingest log ---")
        print(ingest_text)
        raise SystemExit("FAILED: " + "; ".join(fails))
    print("ingest end-to-end: PASS")


if __name__ == "__main__":
    main()
