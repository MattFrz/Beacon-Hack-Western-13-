#!/usr/bin/env bash
# Run guided against a fakeworld scenario and print what the wearer would hear.
#   tools/run_scenario.sh <bottle|reach|lost|walk|turn|unseen|stop|return|reject> [guided flags...]
# Example: tools/run_scenario.sh lost --metres
set -euo pipefail
cd "$(dirname "$0")/.."
sc="${1:-reach}"
shift || true
case "$sc" in
  lost) dur=15.5 ;;
  return) dur=21.5 ;;
  turn) dur=14.5 ;;
  bottle) dur=22.5 ;;
  *) dur=11 ;;
esac
make -s all
./build/fakeworld "$sc" &
fw=$!
sleep 0.3
./build/guided --duration "$dur" "$@"
wait "$fw"
