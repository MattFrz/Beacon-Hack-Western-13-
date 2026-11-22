#!/usr/bin/env python3
"""udp_grab.py: receive the Pi's camera JPEGs over UDP and keep the newest in a file.

The laptop stand-in for beacon_grab, so live_probe.py can run on the laptop off the
Pi's camera (live_preview.py --udp LAPTOP:5009):

    python percept/tools/udp_grab.py --port 5009 --out live/latest.jpg
"""
import argparse
import os
import socket
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=5009)
    ap.add_argument("--out", type=Path, default=Path("live/latest.jpg"))
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(".tmp")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.port))
    print(f"udp_grab: UDP {args.port} -> {args.out}", flush=True)
    n = 0
    while True:
        data, _ = sock.recvfrom(65535)
        if not data.startswith(b"\xff\xd8"):
            continue
        tmp.write_bytes(data)
        try:
            os.replace(tmp, args.out)  # whole frames only: the reader never sees a half-written JPEG
        except PermissionError:
            continue  # Windows: the reader has the file open this instant; the next frame lands
        n += 1
        if n % 240 == 0:
            print(f"udp_grab: {n} frames", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
