#!/bin/sh
# device_slay_beat.sh: the QNX beat, on hardware.
#
# Demonstrates the claim that actually matters for this prize: the guidance law
# degrades honestly when a producer dies, and recovers when it comes back.
#
#   A. perception is live  -> guided speaks "cup about one metre ahead"
#   B. slay ingest         -> the producer of seq_percept disappears
#   C. guided              -> "I lost the target", law LOST, still 60 Hz, 0 misses
#   D. restart ingest      -> guidance resumes without touching guided
#
# guided is never restarted: that is the point. Its deadline record continues
# through the fault.
#
# Ordering note: the intent is introduced only after perception is warm. A FIND
# that arrives while objects[] is empty gets one NACK and is never retried,
# which is the specified behaviour (§9), not a fault.
#
# Usage: sh ingest/tools/device_slay_beat.sh [/path/to/clip.avi] [label]
#   CONF default 0.05 (measured floor for the Nov 22 clips; box 0.14, bottle 0.06).
#   The label must be in models/labels.txt; the six-noun bake has no "cup".
set -e

REPO=${REPO:-/data/home/qnxuser/Beacon-Hack-Western-13-}
PERCEPT=${PERCEPT:-/data/home/qnxuser/beacon-test}
AIROOT=${AIROOT:-/data/home/qnxuser/airoot}
CLIP=${1:-/tmp/long.avi}
TARGET=${2:-bottle}
CONF=${CONF:-0.05}

export LD_LIBRARY_PATH=$AIROOT/usr/lib
export PYTHONPATH=$AIROOT/usr/lib/python3.14/site-packages
export ORT_LIB=$AIROOT/usr/lib/libonnxruntime.so.1

kill_matching() {
    for p in $(pidin ar 2>/dev/null | grep -E "$1" | awk '{print $1}'); do
        slay -f "$p" >/dev/null 2>&1 || true
    done
}

kill_matching "ingest/build/ingest|guided/build/guided|device_probe|probe_to_world"
sleep 1
rm -f /dev/shmem/beacon_world

cd "$REPO"
./guided/build/guided --create --metres --duration 55 --verbose > /tmp/beat-guided.log 2>&1 &
sleep 1
./ingest/build/ingest --udp 5006 > /tmp/beat-ingest-a.log 2>&1 &
sleep 1

cd "$PERCEPT"
timeout 45 python3 -s percept/tools/device_probe.py --tool probe_to_world.py -- \
    --udp 127.0.0.1:5006 --video "$CLIP" --labels models/labels.txt \
    --yolo models/yoloe26n_320.onnx \
    --depth models/depth_anything_v2_metric_indoor_small.onnx \
    --depth-scale 1.0 --fov 60 --conf "$CONF" --ort-intra 3 > /tmp/beat-probe.log 2>&1 &

sleep 12
echo "== A. hand the wire to an intent-bearing ingest (perception is warm) =="
kill_matching "ingest/build/ingest"
sleep 1
cd "$REPO"
./ingest/build/ingest --udp 5006 --intent "FIND:$TARGET" > /tmp/beat-ingest-b.log 2>&1 &
sleep 8
grep -vE "STAT" /tmp/beat-guided.log | tail -3

echo "== B. slay ingest (no camera, no model touched) =="
kill_matching "ingest/build/ingest"
sleep 7
echo "== C. guided after the producer died =="
grep -vE "STAT" /tmp/beat-guided.log | tail -4
grep STAT /tmp/beat-guided.log | tail -1

echo "== D. restart ingest: recovery, guided never restarted =="
cd "$REPO"
./ingest/build/ingest --udp 5006 > /tmp/beat-ingest-c.log 2>&1 &
sleep 8
grep -vE "STAT" /tmp/beat-guided.log | tail -4
grep STAT /tmp/beat-guided.log | tail -1
echo "== totals =="
grep "guided:" /tmp/beat-guided.log | tail -1

kill_matching "ingest/build/ingest|guided/build/guided|device_probe|probe_to_world"
