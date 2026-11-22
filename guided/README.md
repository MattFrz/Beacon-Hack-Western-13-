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

Scenarios: `reach`, `lost` (`slay percept` mid-reach, keys moved, `pose_epoch` bumped), `walk` ("refill water" binds `bottle`, a mug beside it, the wearer turns to face it), `turn` (wearer turns away, the map says "turn left", turns back, reaches), `unseen`, `stop`, `return`, `reject` ("not that one" moves from `keys` to `keychain`, then "say that again").

Example (`lost`):

```
[  0.309] SAY   "keys: slightly to your right, about one step ahead."
[  3.351] TICK  x1  pan -0.93 amp 0.75
[  6.684] TICK  x3  pan -0.46 amp 0.75  (hold)
[  7.009] SAY!  "I lost the target"
[  9.719] SAY   "keys: slightly to your left, about one step ahead."
[ 14.039] TONE  on   pan -0.41
[ 14.639] SAY!  "found it."
guided: 930 loops, 0 missed deadlines, worst lateness 1078 us, p95 150 us
```

Flags: `--metres` speaks the distance in steps (spec §11: only after the tape-measure check passes; off by default; "within arm's reach" is always allowed), `--no-orient-pips` (turn off the turn-toward pips), `--duration S`, `--verbose` (every tick), `--create` (create `/beacon_world` when running alone), `--sup PID:CHID` (supervisor pulses, QNX), `--audio` (below), `--sounds DIR` (voice clips; default `sounds/` or `../sounds/`). `BEACON_WORLD=/beacon_x` overrides the shm name for tests and parallel instances (the product path never sets it; same pattern as supervisor's `BEACON_SUPERVISOR_WORLD`).

## Sound

The voice is Kokoro-82M (GGUF, voice `af_heart`) rendered by llama.cpp's `llama-tts` into WAV clips (`sounds/make_clips.py`); the same GGUF runs on the Pi's QNX llama.cpp port. `guided`'s audio thread loads the voice clips in `sounds/` at startup and mixes speech, pips, REACH ticks and the continuous tone into 10 ms stereo blocks.

What the wearer hears, Google Maps style (qualitative, body-relative, no degrees or exact numbers):

- **Walking, target in view:** one full sentence, "Your keys are slightly to your left, about two steps ahead." Then only short updates when something changes ("To your right."), and a reminder every ~8 s. A step is about 0.7 m; under 0.6 m it says "within arm's reach".
- **Landmark:** if another object sits within 0.3 m of the target, the full sentence is followed by "It's next to the mug."
- **Target out of view:** "Turn a little to your left." / "Turn left." / "Turn around." from the session map.
- **Turning toward it (ADDITION):** soft 600 Hz pips panned toward the target, faster as it comes in front, never over the voice, for ~6 s after each spoken cue. Once you face it (within 10°), one rising chime. `--no-orient-pips` turns them off.
- **Reaching:** 880 Hz ticks (523 Hz in HOLD) speeding up as the hand closes in, a steady tone under 0.15 m, then "Found it."

| `--audio` | Where it goes |
| --- | --- |
| `none` (default) | Nowhere; only the printed log |
| `out.wav` | A WAV file of exactly what the wearer hears (laptop testing) |
| `fifo:PATH` | The JBL over Bluetooth, through [Combadge-HTN/qnx-bluetooth](https://github.com/Combadge-HTN/qnx-bluetooth)'s PCM pipe (44.1 kHz stereo, resampled from 16 kHz). Waits quietly until the Bluetooth program is reading and reconnects if it restarts. |
| `qnx` | The QNX sound device (USB headset or speaker) via io-audio. Untested on the Pi. |

Listen on a laptop: `tools/run_scenario.sh walk --metres --audio /tmp/walk.wav` (write to a Linux folder; writing to `/mnt/c` every 10 ms is slow).

JBL on the Pi (from the qnx-bluetooth README):

1. Terminal 1: `cd ~/projects/qnx-bluetooth && test -p audio.pcm || mkfifo -m 600 audio.pcm`, then `sudo QNX_PCM_VOLUME_SHIFT=0 sh ./run-radio.sh`. Press `a`, wait for "Stream established", press `f`, wait for "PCM FIFO ready".
2. Terminal 2: `guided --audio fifo:$HOME/projects/qnx-bluetooth/audio.pcm ...`.

Bluetooth adds roughly 0.1–0.3 s of delay, which is fine for speech but makes ticks lag a fast hand; a USB headset (`--audio qnx`) has much less.

## On the Pi

`make` on the Pi (QNX Developer Desktop has a compiler), or cross-compile with `make CC="qcc -Vgcc_ntoaarch64le"`. Links `-lasound` on QNX. Not built on QNX yet.

## Still to do

- [ ] Build and run on the loaner Pi; capture the busy-loop test (spec §13 step 1) and a System Profiler trace.
- [ ] Hear it on the JBL through the Bluetooth pipe; try `--audio qnx` if a USB headset turns up.
- [ ] GPIO piezo through the transistor once the parts arrive (`platform_piezo_*`).
- [ ] Confirm the supervisor heartbeat pulse with Matt's `supervisor`.
- [ ] Swap `beacon_mode()`'s 1.0 s LIVE window for `max(1.0 s, 2 × p95)` once `percept` publishes `p95_vision_ns` (already wired; it reads `health.p95_vision_ns`).

## `beacon.h` additions to review (Matt, Nathan)

Not in spec §6, marked `ADDITION` in the header: `objects[].used`, `hand.valid`, `hand.pose_epoch` (§7 Range 1 compares it), `intent.utterance_id` (lets `guided` see the same request twice), `target.bound` / `target.in_latest_boxes`, and the `display` + `stats` blocks under `seq_guided` for `telemd`. Extra clips used by the WALK template: "about", "a little", "you are back", a prompt beep, the sentence clips (`INTRO_*`, `DIR_*`, `STEPS_*`, `WITHIN_REACH`, `TURN_*`, `NEXT_TO`). Two extra commands: `GUIDED_CMD_PIP` and `GUIDED_CMD_CHIME` (turn-toward pips, `--no-orient-pips` to disable).
