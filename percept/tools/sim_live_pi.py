#!/usr/bin/env python3
"""sim_live_pi.py: pretend to be the Pi, from the vid360 mock recording. No Pi needed.

Sends what the live camera loop sends, on the same ports, so the bridge's Live source and the
dashboard's camera panel and 3D scene (camera pose moving, objects placed in world space) run
exactly as they would on a real walk:

    world JSON               -> UDP 5005   (the recording's own pose, objects, crumbs; ~12 Hz)
    raw camera JPEG, 24 fps  -> UDP 5005   (top half of the composite frame, boxes included)
    detector composite JPEG  -> UDP 5007   (boxes over depth, once per world record)

Run the bridge (`npm start` in laptop/bridge) and the dashboard, then:
    python percept/tools/sim_live_pi.py [--host 127.0.0.1] [--loops 0]
"""
from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

import cv2
import numpy as np

SAMPLES = Path(__file__).resolve().parents[2] / "laptop" / "samples"
RAW_FPS = 24


def load(samples: Path):
    records = [json.loads(line) for line in (samples / "vid360-look-around.jsonl").read_text().splitlines() if line.strip()]
    frames = [(samples / "vid360-frames" / f"{i:06d}.jpg").read_bytes() for i in range(len(records))]
    raws = []
    for jpeg in frames:
        img = cv2.imdecode(np.frombuffer(jpeg, "u1"), cv2.IMREAD_COLOR)
        raws.append(cv2.imencode(".jpg", img[: img.shape[0] // 2], [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes())
    return records, frames, raws


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1", help="the bridge's laptop (default this one)")
    ap.add_argument("--loops", type=int, default=0, help="play the recording this many times; 0 repeats until Ctrl+C")
    args = ap.parse_args()
    records, frames, raws = load(SAMPLES)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    world, preview = (args.host, 5005), (args.host, 5007)
    t0_ns = records[0]["t_ns"]
    loop = 0
    print(f"sim_live_pi: {len(records)} records to {args.host}; Ctrl+C stops")
    try:
        while args.loops == 0 or loop < args.loops:
            start = time.monotonic()
            i, next_raw = 0, 0.0
            while i < len(records):
                now = time.monotonic() - start
                while i < len(records) and (records[i]["t_ns"] - t0_ns) / 1e9 <= now:
                    sock.sendto(json.dumps(records[i], separators=(",", ":")).encode(), world)
                    sock.sendto(frames[i], preview)
                    i += 1
                if now >= next_raw:
                    sock.sendto(raws[min(i, len(raws) - 1)], world)
                    next_raw = now + 1 / RAW_FPS
                time.sleep(0.004)
            loop += 1
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
