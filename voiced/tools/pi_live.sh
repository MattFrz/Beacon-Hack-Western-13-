#!/bin/sh
# Live guidance on the Pi from the laptop camera (fallback until percept runs on the Pi).
#   sh voiced/tools/pi_live.sh [--metres]        (--metres only after the tape check)
# Needs: the JBL Bluetooth program running (guided/README.md), voiced and guided built.
# Then, on the laptop:  python3 percept/tools/probe_to_world.py ... --udp 10.80.55.25:5006
# And in a second ssh:  voiced/build/beacon_cmd find bottle
cd "$(dirname "$0")/../.." || exit 1
FIFO="${FIFO:-$HOME/projects/qnx-bluetooth/audio.pcm}"
voiced/build/world_in &
WI=$!
trap 'kill $WI 2>/dev/null' EXIT INT TERM
echo "pi_live: bridge on UDP 5006; speaking to $FIFO"
cd guided && ./build/guided --create "$@" --audio "fifo:$FIFO"
