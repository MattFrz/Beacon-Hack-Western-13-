#!/usr/bin/env python3
"""Send the newest captured camera frame independently from object detection."""
import argparse
import socket
import time
from pathlib import Path

import cv2
import numpy as np

MAX_DATAGRAM = 60_000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grab-file", type=Path, default=Path("/tmp/live/latest.jpg"))
    parser.add_argument("--udp", required=True, help="dashboard host:port")
    parser.add_argument("--fps", type=float, default=24)
    args = parser.parse_args()
    host, port = args.udp.rsplit(":", 1)
    period = 1 / max(1, min(args.fps, 30))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    previous = None
    deadline = time.monotonic()
    while True:
        try:
            stat = args.grab_file.stat()
            stamp = (stat.st_mtime_ns, stat.st_size)
            if stamp != previous:
                source = args.grab_file.read_bytes()
                if source.startswith(b"\xff\xd8") and len(source) <= MAX_DATAGRAM:
                    sock.sendto(source, (host, int(port)))
                    previous = stamp
                else:
                    encoded = cv2.imdecode(np.frombuffer(source, dtype="uint8"), cv2.IMREAD_COLOR)
                    if encoded is not None:
                        # Keep full resolution (lower JPEG quality instead) so the dashboard's
                        # detection boxes, which are in full-frame pixels, line up with the video.
                        # Shrink only if even quality 25 does not fit one datagram.
                        height, width = encoded.shape[:2]
                        sent = False
                        for target_w in (width, 640, 320):
                            frame = encoded if target_w >= width else cv2.resize(
                                encoded, (target_w, max(1, round(height * target_w / width))))
                            for quality in (60, 45, 35, 25):
                                ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                                if ok and len(jpeg) <= MAX_DATAGRAM:
                                    sock.sendto(jpeg.tobytes(), (host, int(port)))
                                    sent = True
                                    break
                            if sent:
                                break
                        previous = stamp
                    # a half-written frame fails to decode: retry on the next tick, not in a busy loop
        except (FileNotFoundError, OSError):
            pass
        deadline += period
        time.sleep(max(0, deadline - time.monotonic()))


if __name__ == "__main__":
    main()
