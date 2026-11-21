# guided

Owner: Munadir. C, core 0 (`0x1`), `SCHED_FIFO` 58. The 60 Hz synthesizer: mode, bind, laws (including REPEAT / REJECT), piezo, audio thread. No models, no blocking writes on the 16 ms thread. QNX calls behind `#ifdef __QNX__` so it runs on a laptop. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §6, §9, §10.

## Layout

| File | What |
| --- | --- |
| `src/law.c`, `src/law.h` | All decisions, pure (no I/O, no clock): bind (§9), mode (§6, via `beacon_mode()` in `beacon.h`), REACH / WALK / RETURN / LOST / STOP / REPEAT / REJECT (§10), Range 1 `d` with the `frame_id` check (§7). Unit-tested. |
| `src/main.c` | The 60 Hz loop: seqlock reads of `seq_percept` / `seq_voiced`, `guided_step()`, audio hand-off, piezo, publish `seq_guided`, absolute-deadline sleep, miss and lateness stats. |
| `src/audio.c` | Audio thread at prio 40: speech ring (drops speech when full), newest-wins tick/tone slot. Prints what the wearer hears. |
| `src/platform.c` | QNX-only calls: `ThreadCtl` runmask, `SCHED_FIFO`, heartbeat pulse to the supervisor, GPIO piezo (TODO). |
| `tools/fakeworld.c` | Stands in for `percept` and `voiced`: writes scripted bundles at 5 Hz into `/beacon_world`. |
| `tools/run_scenario.sh` | Runs `fakeworld` + `guided` together. |
| `tests/test_law.c` | Unit tests for the law. |

## Build and run on a laptop (Linux or WSL Ubuntu)

```bash
cd guided
make            # build/guided, build/fakeworld, build/test_law
make test       # unit tests
tools/run_scenario.sh reach --metres
```

Scenarios: `reach`, `lost` (`slay percept` mid-reach, keys moved, `pose_epoch` bumped), `walk` ("refill water" binds `bottle`), `unseen`, `stop`, `return`, `reject` ("not that one" moves from `keys` to `keychain`, then "say that again").

Example (`lost`):

```
[  3.302] SAY   "keys about one metre ahead down"
[  3.351] TICK  x1  pan -0.93 amp 0.75
[  5.935] TICK  x2  pan -0.47 amp 0.75
[  6.684] TICK  x3  pan -0.46 amp 0.75  (hold)
[  7.001] SAY!  "I lost the target"
[  9.701] SAY   "keys about one metre a little left down"
[ 14.035] TONE  on   pan -0.41
guided: 930 loops, 0 missed deadlines, worst lateness 208 us, p95 150 us
```

Flags: `--metres` speaks metres (spec §11: only after the tape-measure check passes; off by default), `--duration S`, `--verbose` (every tick), `--create` (create `/beacon_world` when running alone), `--sup PID:CHID` (supervisor pulses, QNX). `BEACON_WORLD=/beacon_x` overrides the shm name for tests and parallel instances (the product path never sets it; same pattern as supervisor's `BEACON_SUPERVISOR_WORLD`).

## On the Pi

`make` on the Pi (QNX Developer Desktop has a compiler), or cross-compile with `make CC="qcc -Vgcc_ntoaarch64le"`. Not built on QNX yet.

## Still to do

- [ ] Build and run on the loaner Pi; capture the busy-loop test (spec §13 step 1) and a System Profiler trace.
- [ ] USB audio out through `io-audio`: play `sounds/<clip>.wav` and `sounds/name_<label>.wav` (needs a USB headset or speaker; the JBL Go 3 is Bluetooth-only).
- [ ] GPIO piezo through the transistor once the parts arrive (`platform_piezo_*`).
- [ ] Confirm the supervisor heartbeat pulse with Matt's `supervisor`.
- [ ] Swap `beacon_mode()`'s 1.0 s LIVE window for `max(1.0 s, 2 × p95)` once `percept` publishes `p95_vision_ns` (already wired; it reads `health.p95_vision_ns`).

## `beacon.h` additions to review (Matt, Nathan)

Not in spec §6, marked `ADDITION` in the header: `objects[].used`, `hand.valid`, `hand.pose_epoch` (§7 Range 1 compares it), `intent.utterance_id` (lets `guided` see the same request twice), `target.bound` / `target.in_latest_boxes`, and the `display` + `stats` blocks under `seq_guided` for `telemd`. Extra clips used by the WALK template: "about", "a little", "you are back", a prompt beep.
