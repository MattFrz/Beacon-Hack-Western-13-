"""Stand-in for percept/tools/probe_to_world.py --udp: sends world JSON like the probe.

    python3 voiced/tools/fake_probe.py [HOST:PORT]     (default 127.0.0.1:5006)

A bottle 1.5 m away drifts from the left to the right, a mug sits beside it,
then the camera walks up and a hand reaches in. 4 Hz, like the laptop probe.
No numpy needed. Use it to test world_in + guided without a camera.
"""
import json
import socket
import sys
import time

host, port = (sys.argv[1].split(":") if len(sys.argv) > 1 else ("127.0.0.1", "5006"))
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
t0 = time.time()
while True:
    t = time.time() - t0
    if t > 20:
        break
    x = -0.6 + min(1.0, t / 8.0) * 1.0           # 0-8 s: left -> right
    if t > 10:
        x = 0.05
    z = 1.5 - max(0.0, min(1.0, (t - 10) / 4.0)) * 0.95  # 10-14 s: walk up to 0.55 m
    objs = [{"id": 5, "name": "bottle", "xyz_cam": [x, 0.2, z], "conf": 0.85, "in_latest_boxes": True},
            {"id": 7, "name": "mug", "xyz_cam": [x + 0.18, 0.2, z + 0.05], "conf": 0.7, "in_latest_boxes": True}]
    hand = None
    if t > 14.5:
        f = min(1.0, (t - 14.5) / 3.0)
        hand = {"xyz_cam": [0.35 + (0.06 - 0.35) * f, 0.5 + (0.21 - 0.5) * f, 0.2 + (0.53 - 0.2) * f],
                "conf": 0.9}
    msg = {"v": 1, "t_ns": int(t * 1e9), "mode": "LIVE", "objects": objs, "hand": hand}
    sock.sendto(json.dumps(msg).encode(), (host, int(port)))
    time.sleep(0.25)
