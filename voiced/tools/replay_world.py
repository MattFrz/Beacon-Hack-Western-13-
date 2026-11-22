"""Replay a recorded world JSONL into world_in, at the speed it was recorded.

    python3 voiced/tools/replay_world.py clip.jsonl [HOST:PORT] [--speed 1.0] [--duration]

clip.jsonl comes from Nathan's probe on a recorded video or the webcam, e.g.
    python3 percept/tools/probe_to_world.py --video clip.mp4 --yolo ... --depth ... \
        --hands --hand-model ... --fov --out clip.jsonl
Each line is one world JSON (same as the probe's --udp datagrams), paced by t_ns.
--duration only prints the recording length in seconds and exits.
Plain Python, no numpy.
"""
import json
import socket
import sys
import time

args = [a for a in sys.argv[1:] if not a.startswith("--")]
speed = float(sys.argv[sys.argv.index("--speed") + 1]) if "--speed" in sys.argv else 1.0
if "--speed" in sys.argv:
    args.remove(sys.argv[sys.argv.index("--speed") + 1])
if not args:
    sys.exit(__doc__)
lines = [l for l in open(args[0], encoding="utf-8") if l.strip()]
ts = [json.loads(l).get("t_ns", 0) for l in lines]
if "--duration" in sys.argv:
    print(f"{(ts[-1] - ts[0]) / 1e9 / speed:.1f}" if len(ts) > 1 else "0")
    sys.exit(0)

host, port = (args[1].split(":") if len(args) > 1 else ("127.0.0.1", "5006"))
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
start = time.monotonic()
for line, t in zip(lines, ts):
    due = start + (t - ts[0]) / 1e9 / speed
    wait = due - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    sock.sendto(line.strip().encode(), (host, int(port)))
print(f"replay_world: sent {len(lines)} frames over {(ts[-1] - ts[0]) / 1e9:.1f} s", file=sys.stderr)
