# voiced

Owner: Munadir. C++, cores 1-3 (`0xe`), `SCHED_RR` 18. whisper.cpp tiny.en, synonym table (including REPEAT / REJECT), optional llama.cpp on a table miss. Writes `intent` only. Never plays audio. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §9.

## What works now (stand-ins until the mic and Pi vision are ready)

```sh
cd voiced && make          # build/beacon_cmd, build/world_in (laptop or on the Pi)
```

| Tool | What it does |
| --- | --- |
| `build/beacon_cmd` | Typed commands → the intent block, exactly what voiced will write. `beacon_cmd find my water bottle`, or run it with no arguments and type: `find keys`, `go sink`, `stop`, `repeat`, `no` (REJECT), `back` (RETURN). "water" → fountain, dispenser, sink, bottle; "keys" → keys, keychain. |
| `build/world_in` | **Fallback bridge:** receives Nathan's laptop probe (`percept/tools/probe_to_world.py --udp <pi-ip>:5006`) and writes `/beacon_world`, so `guided` on the Pi guides from a laptop camera. Pi clock and frame ids, identity pose, rows kept when out of view. Don't run it once `percept` on the Pi writes `/beacon_world`. |
| `tools/fake_probe.py` | Sends probe-shaped JSON (a bottle drifting left to right, then a hand reaching in) to test `world_in` without a camera. Plain Python, no numpy. |

### Live loop with the laptop camera (Pi on the hotspot)

```sh
# Pi, terminal 1 (JBL Bluetooth running, see guided/README.md):
voiced/build/world_in
# Pi, terminal 2:
guided/build/guided --create --metres --audio fifo:$HOME/projects/qnx-bluetooth/audio.pcm
# laptop:
python3 percept/tools/probe_to_world.py --yolo ... --depth ... --hands ... --fov --udp 10.80.55.25:5006
# Pi, terminal 3:
voiced/build/beacon_cmd find my water bottle
```

Tested on a laptop with `fake_probe.py`: "The bottle is slightly to your left, about two steps ahead. It's next to the mug.", it follows the bottle across, then ticks, tone, "Found it.", 0 missed deadlines.
