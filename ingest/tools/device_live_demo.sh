#!/bin/sh
# device_live_demo.sh: the whole Beacon loop on the QNX loaner, from the C270.
#
#   C270 -> beacon_grab (JPEG) -> latest.jpg
#            -> live_probe.py (YOLOE + metric depth, one frame at a time)
#               --UDP 5006--> ingest --/beacon_world--> guided (60 Hz) -> speech
#               --UDP 5005--> bridge on the laptop -> dashboard (live JPEG)
#
# Everything here runs on the Pi except the bridge and the dashboard, which are
# the team monitor (never on the wearer's path).
#
# Capture is real: the sensor service is started with the USB unit configured
# "jpeg" + create_window=false + memory_allocator_type=from_sensor. Without
# those three keys the service renders into a Screen window that does not exist
# and every frame is a blank 10 80 YCbCr stub.
#
# Order matters. guided must see objects before it sees an intent: a FIND that
# arrives with objects[] empty gets one NACK ("I have not seen that") and is
# never retried, which is documented behaviour (§9), not a bug.
#
# Usage: sh ingest/tools/device_live_demo.sh [target] [laptop-ip] [duration]
set -e

REPO=${REPO:-/data/home/qnxuser/Beacon-Hack-Western-13-}
PERCEPT=${PERCEPT:-/data/home/qnxuser/beacon-test}
AIROOT=${AIROOT:-/data/home/qnxuser/airoot}
SENSOR_CONF=${SENSOR_CONF:-/data/home/qnxuser/sensor-usbjpeg.conf}
TARGET=${1:-cup}
DASHBOARD_HOST=${2:-10.80.55.92}
DURATION=${3:-120}
FRAME=${FRAME:-/tmp/live/latest.jpg}
GRAB_FPS=${GRAB_FPS:-30}

export LD_LIBRARY_PATH=$AIROOT/usr/lib
export PYTHONPATH=$AIROOT/usr/lib/python3.14/site-packages
export ORT_LIB=$AIROOT/usr/lib/libonnxruntime.so.1

slay_matching() {
    for p in $(pidin ar 2>/dev/null | grep -E "$1" | awk '{print $1}'); do
        slay -f "$p" >/dev/null 2>&1 || true
    done
}

echo "== stop leftovers =="
slay_matching "ingest/build/ingest|guided/build/guided|live_probe|beacon_grab|telemd/build/telemd"
sleep 1
rm -f /dev/shmem/beacon_world
mkdir -p /tmp/live
rm -f "$FRAME"

echo "== sensor service (usb camera, jpeg) =="
sudo -n slay -f sensor >/dev/null 2>&1 || true
sleep 2
sudo -n sh -c "/usr/bin/sensor -U 521:521 -b external -r /data/share/sensor -c $SENSOR_CONF \
    > /tmp/sensor.log 2>&1 &"
sleep 5

echo "== guided (owns the world) =="
cd "$REPO"
./guided/build/guided --create --metres --duration "$DURATION" > /tmp/guided.log 2>&1 &
sleep 1

echo "== ingest (relay, no intent yet) =="
./ingest/build/ingest --udp 5006 > /tmp/ingest-a.log 2>&1 &
sleep 1

echo "== grabber: newest frame at camera rate =="
cd "$PERCEPT"
./beacon_grab -u 5 -w -r "$GRAB_FPS" -s 6 -o "$FRAME" > /tmp/grab.log 2>&1 &
python3 -s percept/tools/live_preview.py --grab-file "$FRAME" --udp "$DASHBOARD_HOST:5005" --fps 24 > /tmp/live_preview.log 2>&1 &
# Wait for a real frame before starting inference: the first ones are black
# while the camera's auto-exposure settles.
i=0
while [ $i -lt 100 ]; do
    [ -s "$FRAME" ] && break
    sleep 1
    i=$((i + 1))
done
echo "   frame: $(ls -l "$FRAME" 2>/dev/null | awk '{print $5}') bytes"

echo "== percept: YOLOE + depth on one frame per cycle =="
timeout $((DURATION - 4)) python3 -s percept/tools/live_probe.py \
    --grab-file "$FRAME" \
    --udp 127.0.0.1:5006 \
    --video-udp "$DASHBOARD_HOST:5007" \
    --labels models/labels.txt \
    --yolo models/yoloe26n_320.onnx \
    --depth models/depth_anything_v2_metric_indoor_small.onnx \
    --depth-scale 0.25 --max-depth 3.0 --fov 60 --conf 0.10 --ort-intra 3 \
    > /tmp/live_probe.log 2>&1 &
PROBE_PID=$!

# The monitor: world state to the bridge on the laptop, read-only.
if [ -x "$REPO/telemd/build/telemd" ]; then
    echo "== telemd (monitor, read-only) -> $DASHBOARD_HOST:5005 =="
    "$REPO/telemd/build/telemd" "$DASHBOARD_HOST" 5005 > /tmp/telemd.log 2>&1 &
else
    echo "!! telemd not built: dashboard gets video only (make -C telemd)"
fi

# Perception must be warm *and* see the target before an intent: a FIND that
# arrives with objects[] empty is NACKed once and never retried (§9). Waiting
# for a LIVE record that names the target is the honest way to sequence it.
echo "== waiting for percept to see $TARGET =="
waited=0
while [ $waited -lt 40 ]; do
    if grep -q "mode=LIVE name=$TARGET" /tmp/live_probe.log 2>/dev/null; then
        echo "   $TARGET visible after ${waited}s"
        break
    fi
    sleep 2
    waited=$((waited + 2))
done
if [ $waited -ge 40 ]; then
    echo "   !! $TARGET never seen: the intent below will be NACKed (aim the camera first)"
fi

slay_matching "ingest/build/ingest"
sleep 1
./ingest/build/ingest --udp 5006 --intent "FIND:$TARGET" > /tmp/ingest-b.log 2>&1 &
sleep 12

echo "== what guided heard =="
grep -vE "STAT" /tmp/guided.log | tail -12
echo "== deadlines =="
grep STAT /tmp/guided.log | tail -2
echo "== percept timing =="
grep -E "rec |timing|depth" /tmp/live_probe.log | tail -5
echo "== telemd =="
tail -3 /tmp/telemd.log 2>/dev/null
echo "== grabber =="
tail -3 /tmp/grab.log

echo "(processes left running: guided, ingest, grabber, percept — dashboard on $DASHBOARD_HOST:5005)"
wait "$PROBE_PID" || true
