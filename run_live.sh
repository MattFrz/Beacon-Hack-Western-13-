#!/bin/sh
# run_live.sh: the whole live demo on the Pi, from this one checkout.
#
#   sh run_live.sh [target] [laptop-ip]
#
# target     what to find first (default bottle; must be in models/labels_hand.txt)
# laptop-ip  where the dashboard bridge runs (default: the machine you ssh'd in from)
# MODEL=hand  use the old 7-word bake (default: the "watch" bake, wristwatch = hand)
# RECORD=1   save every raw camera frame under ~/recordings/<time>/ (needs a live_probe with --record-video)
# AUDIO=jbl  speak on the JBL (start projects/qnx-bluetooth/run-radio.sh first,
#            press a then f); default: no audio, log only
#
# Models live in ./models (copied from ~/beacon-test/models, not in git).
# Phone mic: open http://<pi-ip>:8080 on the phone and type or dictate "find my keys".
# Stop everything: sh run_live.sh stop
HERE=$(cd "$(dirname "$0")" && pwd)
if [ "$1" = stop ]; then
    for p in $(pidin ar 2>/dev/null | grep -E "^ *[0-9]+ ([^ ]*/)?(ingest/build/ingest|voiced/build/beacon_cmd|[.]/guided/build/guided|timeout [0-9]+ python3|python3 -s [^ ]*live_(probe|preview)[.]py|[.]/beacon_grab|[^ ]*telemd/build/telemd)" | awk '{print $1}'); do
        slay -f "$p" >/dev/null 2>&1 || true
    done
    echo "stopped"
    exit 0
fi
LAPTOP=${2:-${SSH_CLIENT%% *}}
[ -n "$LAPTOP" ] || { echo "usage: sh run_live.sh [target] laptop-ip"; exit 2; }
export REPO="$HERE" PERCEPT="$HERE" BEACON_CMD="$HERE/voiced/build/beacon_cmd"
[ "$AUDIO" = jbl ] && export GUIDED_AUDIO=fifo:/data/home/qnxuser/projects/qnx-bluetooth/audio.pcm
# RECORD=1: save the raw camera frames of this run under ~/recordings/<time>/ (for the video)
[ "$RECORD" = 1 ] && export RECORD_DIR=/data/home/qnxuser/recordings
# Default bake: the 8 words with "watch" (a wristwatch also marks the hand). On the same
# 151 recorded reach frames it found the hand in 37 vs 1 for the 7-word bake, same speed.
# Built by percept/tools/export_yoloe.py --labels models/labels_watch.txt. MODEL=hand = old bake.
MODEL=${MODEL:-watch}
if [ "$MODEL" = watch ] && [ -f "$HERE/models/yoloe26n_320_watch.onnx" ]; then
    export YOLO="$HERE/models/yoloe26n_320_watch.onnx" LABELS="$HERE/models/labels_watch.txt"
fi
# The Bluetooth sender starts at priority 10, the same as the vision Python, which keeps
# all four cores busy: starved, the speaker runs dry and the voice stutters. 30 is above
# vision and below guided's audio thread (40) and control loop (58).
sudo -n slay -P 30r a2dp_source_demo >/dev/null 2>&1 || true
echo "live demo: target ${1:-bottle}, dashboard at $LAPTOP, audio ${GUIDED_AUDIO:-none}, model ${YOLO:-default}"
exec sh "$HERE/ingest/tools/device_live_demo.sh" "${1:-bottle}" "$LAPTOP" "${DURATION:-1800}"
