#!/bin/sh
# One foreground Bluetooth A2DP session for the pinned JBL Go 3.
# Derived from the qnx-bluetooth bring-up launcher; no interactive keys needed.
set -eu
cd "$(dirname "$0")"

PROJECT=${QNX_BT_PROJECT:-/data/home/qnxuser/projects/qnx-bluetooth}
cd "$PROJECT"

test "$(id -u)" = 0 || { echo 'Run as root' >&2; exit 1; }
test "$(uname -m)" = RaspberryPi5 || exit 1
test -f BCM4345C0.hcd
test -x btstack-master/port/qnx-pi5/a2dp_source_demo
test -p audio.pcm || mkfifo -m 600 audio.pcm
if ! mkdir .radio-lock 2>/dev/null; then
    if test -f .radio-lock/pid && kill -0 "$(cat .radio-lock/pid)" 2>/dev/null; then
        echo 'Another radio session may be active' >&2; exit 1
    fi
    rm -rf .radio-lock
    mkdir .radio-lock || exit 1
fi
printf '%s\n' "$$" > .radio-lock/pid

child=
pins_changed=0
restore() {
    if test -n "$child"; then
        kill -TERM "$child" 2>/dev/null || true
        wait "$child" 2>/dev/null || true
        sleep 1   # let the UART driver release the pins before we mux them back
    fi
    if test "$pins_changed" = 1; then
        gpio-bcm set 29 op dl pd
        gpio-bcm set 24-27 ip pd
        gpio-bcm set 29 ip pd
        # A refused startup may leave the UART programmed even with no process.
        if test -x ./uart_probe; then
            ./uart_probe --idle-after-abort >/dev/null 2>&1 || true
        fi
    fi
    rm -rf .radio-lock
}
trap restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP

# Refuse to claim the UART if the board is not in the inspected idle state.
pins=$(gpio-bcm get 24-29)
for pin in 24 25 26 27 29; do
    printf '%s\n' "$pins" | grep "^GPIO${pin}/" | grep 'pull=pd.*func=INPUT' >/dev/null || {
        echo "GPIO$pin differs from inspected baseline; refusing" >&2; exit 1;
    }
done
gpio-bcm funcs 24 | grep 'SD_CARD_PRES_B.*UART_RTS_0' >/dev/null || exit 1

gpio-bcm set 29 op dl pd
gpio-bcm set 24-27 a4
gpio-bcm set 24,26 pn
gpio-bcm set 25,27 pu
pins_changed=1
sleep 1
gpio-bcm set 29 op dh
sleep 1

QNX_BT_AUTO=1 \
QNX_BT_ADDR=${QNX_BT_ADDR:-18:90:67:DE:BC:EF} \
QNX_PCM_VOLUME_SHIFT=${QNX_PCM_VOLUME_SHIFT:-0} \
    ./btstack-master/port/qnx-pi5/a2dp_source_demo \
    --onboard "$PWD/BCM4345C0.hcd" </dev/null &
child=$!
status=0
wait "$child" || status=$?
child=
exit "$status"
