#!/bin/sh
# Beacon supervisor child: keep the QNX Pi 5 -> JBL Go 3 A2DP bridge alive.
#
# This does not modify QNX boot config. Beacon's supervisor starts this script
# as root after io-snd; the script restarts the radio session if it dies and
# backs off briefly when the board guard refuses to start. Pairing lives in
# the qnx-bluetooth project's pairings.tlv and survives restarts.
set -u

PROJECT=${QNX_BT_PROJECT:-/data/home/qnxuser/projects/qnx-bluetooth}
LAUNCHER=${QNX_BT_LAUNCHER:-$PROJECT/run-radio-auto.sh}
LOG=${QNX_BT_LOG:-$PROJECT/bt_audio.log}

test "$(id -u)" = 0 || { echo 'Run as root (supervisor should do this)' >&2; exit 1; }
test -x "$LAUNCHER" || { echo "Missing launcher: $LAUNCHER" >&2; exit 1; }
mkdir -p "$(dirname "$LOG")"

child=
cleanup() {
    if test -n "$child"; then
        kill -TERM "$child" 2>/dev/null || true
        wait "$child" 2>/dev/null || true
    fi
    exit 143
}
trap cleanup TERM INT HUP

while :; do
    printf '%s starting Bluetooth audio\n' "$(date -u +%FT%TZ)" >>"$LOG"
    sh "$LAUNCHER" >>"$LOG" 2>&1 &
    child=$!
    status=0
    wait "$child" || status=$?
    child=
    printf '%s Bluetooth audio exited %s\n' "$(date -u +%FT%TZ)" "$status" >>"$LOG"
    if test "$status" = 0; then sleep 1; else sleep 5; fi
done
