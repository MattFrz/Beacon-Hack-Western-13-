#!/bin/sh
# device_chain_demo.sh: the whole Beacon loop on the QNX loaner, no camera.
#
#   percept (YOLOE + metric depth, ONNX Runtime C API)  --UDP 5006-->  ingest
#      --/beacon_world seq_percept-->  guided (60 Hz law)  -->  speech
#
# Capture is the one thing that is still a stand-in: this replays frames from a
# video file instead of a camera, because the loaner has no camera driver yet.
# Everything after "read a frame" runs on device.
#
# Order matters. guided must see objects before it sees an intent: a FIND that
# arrives when objects[] is empty gets one NACK ("I have not seen that") and is
# never retried, which is the documented behaviour (§9), not a bug.
#
# Usage: sh ingest/tools/device_chain_demo.sh [/path/to/clip.avi] [label]
#   CONF=0.05 (default) is the detection floor the Nov 22 clips can clear
#   (measured: box 0.14, bottle 0.06). The label must be in models/labels.txt;
#   the six-noun bake has no "cup".
set -e

REPO=${REPO:-/data/home/qnxuser/Beacon-Hack-Western-13-}
PERCEPT=${PERCEPT:-/data/home/qnxuser/beacon-test}
AIROOT=${AIROOT:-/data/home/qnxuser/airoot}
CLIP=${1:-/tmp/replay.avi}
TARGET=${2:-bottle}
DURATION=${DURATION:-40}
CONF=${CONF:-0.05}

export LD_LIBRARY_PATH=$AIROOT/usr/lib
export PYTHONPATH=$AIROOT/usr/lib/python3.14/site-packages
export ORT_LIB=$AIROOT/usr/lib/libonnxruntime.so.1

# QNX has no pkill; slay is the equivalent.
for p in $(pidin ar 2>/dev/null | grep -E "ingest/build/ingest|guided/build/guided|device_probe" | awk '{print $1}'); do
    slay -f "$p" >/dev/null 2>&1 || true
done
sleep 1
rm -f /dev/shmem/beacon_world

echo "== guided (owns the world) =="
cd "$REPO"
./guided/build/guided --create --metres --duration "$DURATION" > /tmp/guided.log 2>&1 &
sleep 1

echo "== ingest (relay; no intent yet) =="
./ingest/build/ingest --udp 5006 > /tmp/ingest-a.log 2>&1 &
sleep 1

echo "== percept ($CLIP) =="
cd "$PERCEPT"
timeout $((DURATION - 8)) python3 -s percept/tools/device_probe.py --tool probe_to_world.py -- \
    --udp 127.0.0.1:5006 --video "$CLIP" --labels models/labels.txt \
    --yolo models/yoloe26n_320.onnx \
    --depth models/depth_anything_v2_metric_indoor_small.onnx \
    --depth-scale 1.0 --fov 60 --conf "$CONF" --ort-intra 3 > /tmp/probe.log 2>&1 &

# Let perception warm up (the first depth frame also pays the session load).
sleep 11
echo "records so far: $(grep -c 'seq=' /tmp/probe.log || echo 0)"

echo "== intent: FIND:$TARGET (perception is warm now) =="
for p in $(pidin ar 2>/dev/null | grep "ingest/build/ingest" | awk '{print $1}'); do
    slay -f "$p" >/dev/null 2>&1 || true
done
sleep 1
cd "$REPO"
./ingest/build/ingest --udp 5006 --intent "FIND:$TARGET" > /tmp/ingest-b.log 2>&1 &
sleep 8

echo "== guided said =="
grep -vE "STAT" /tmp/guided.log | tail -15
echo "== deadlines =="
grep STAT /tmp/guided.log | tail -2

for p in $(pidin ar 2>/dev/null | grep -E "ingest/build/ingest|guided/build/guided|device_probe" | awk '{print $1}'); do
    slay -f "$p" >/dev/null 2>&1 || true
done
