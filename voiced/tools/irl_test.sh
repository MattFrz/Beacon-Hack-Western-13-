#!/usr/bin/env bash
# Hear what Beacon would say for a REAL recording (laptop, Linux/WSL).
#   voiced/tools/irl_test.sh clip.jsonl ["find bottle"] [out.wav]
# clip.jsonl: Nathan's probe on a recorded video, e.g.
#   python3 percept/tools/probe_to_world.py --video clip.mp4 --yolo ... --depth ... \
#       --hands --hand-model ... --fov --out clip.jsonl
# Same pipeline as the Pi: recording -> world_in -> /beacon_world -> guided.
set -euo pipefail
cd "$(dirname "$0")/../.."
clip="$(realpath "$1")"
cmd="${2:-find bottle}"
out="${3:-/tmp/beacon_irl.wav}"
make -s -C voiced all
make -s -C guided all
dur=$(python3 voiced/tools/replay_world.py "$clip" --duration)
rm -f /dev/shm/beacon_world   # no stale request from an earlier run
voiced/build/world_in & wi=$!
trap 'kill $wi 2>/dev/null || true' EXIT
sleep 0.3
(cd guided && ./build/guided --create --metres --duration "$(python3 -c "print($dur + 3)")" --audio "$out") & g=$!
sleep 0.5
python3 voiced/tools/replay_world.py "$clip" & r=$!
sleep 0.5
voiced/build/beacon_cmd $cmd
wait $g
kill $r 2>/dev/null || true
echo "audio: $out"
