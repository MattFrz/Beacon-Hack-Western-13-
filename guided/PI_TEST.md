# Testing guided on the Pi

For Nathan (on the Pi) with Munadir. About 30 minutes. Each step says what you should see. If a step fails, copy the output into the team chat and stop there.

`guided` is the program that decides what Beacon says and when it beeps. Here it runs with **fakeworld**, a stand-in for the camera and voice programs that feeds it made-up positions ("keys at 60 cm, hand closing in"), so we can test sound and timing before the real camera is wired in.

## 1. Build (5 min)

```sh
cd ~/Beacon-Hack-Western-13-        # wherever the repo is on the Pi
git fetch
git checkout munadir/audio
cd guided
make
```

**You should see:** no errors, and `build/guided`, `build/fakeworld`, `build/test_law` exist. Then:

```sh
./build/test_law | tail -1
```

**You should see:** `56 passed, 0 failed`.

This is the first time this code is compiled on QNX. If `make` fails, send the error.

## 2. Run without sound (2 min)

Run from the `guided/` folder (it finds the voice clips in `../sounds`).

```sh
./build/fakeworld lost & ./build/guided --metres --duration 15
```

**You should see**, ending with `0 missed deadlines`:

```
guided: 127 voice clips loaded from ../sounds
[  0.3] SAY   "keys: slightly to your right, about one step ahead."
[  3.3] TICK  ...                       (ticks while the hand closes in)
[  7.0] SAY!  "I lost the target"       (the camera program "dies")
[  9.7] SAY   "keys: slightly to your left, about one step ahead."
[ 14.0] TONE  on
[ 14.6] SAY!  "found it."
guided: 930 loops, 0 missed deadlines, ...
```

Ignore `running without SCHED_FIFO` if it appears; that just means it isn't running as root.

## 3. Hear it on the JBL (10 min)

Uses [Combadge-HTN/qnx-bluetooth](https://github.com/Combadge-HTN/qnx-bluetooth).

**Terminal 1** (Bluetooth):

```sh
cd ~/projects/qnx-bluetooth
test -p audio.pcm || mkfifo -m 600 audio.pcm
sudo QNX_PCM_VOLUME_SHIFT=0 sh ./run-radio.sh
```

Press `a`, wait for `Stream established`, press `f`, wait for `PCM FIFO ready`.

**Terminal 2** (Beacon), from `guided/`:

```sh
./build/fakeworld lost & ./build/guided --metres --duration 15 \
    --audio fifo:$HOME/projects/qnx-bluetooth/audio.pcm
```

**You should hear:** "Your keys are slightly to your right, about one step ahead." then beeps speeding up, a lower beep, "I lost the target", the cue again, a steady tone, then "Found it."

Also try `turn` ("turn a little to your left", "turn left", soft pips on the left as you turn back, a chime when facing it) and `walk` ("It's next to the mug."):

```sh
./build/fakeworld turn & ./build/guided --metres --duration 14.5 \
    --audio fifo:$HOME/projects/qnx-bluetooth/audio.pcm
```

| Problem | Fix |
| --- | --- |
| `waiting for the Bluetooth PCM reader` and silence | Press `f` in terminal 1 |
| Very quiet | Restart terminal 1 with `QNX_PCM_VOLUME_SHIFT=0` |
| Sound arrives a little late | Normal for Bluetooth (about 0.1–0.3 s) |

## 4. Timing under load: the QNX proof (5 min)

Keep three CPU cores busy, then run step 2 again:

```sh
for i in 1 2 3; do sh -c 'while :; do :; done' & done
./build/fakeworld lost & ./build/guided --metres --duration 15
kill $(jobs -p)          # stop the busy loops afterwards
```

**You should see:** still `0 missed deadlines`. Copy the final `guided:` line (loops, misses, worst lateness) into the chat; it goes in the Devpost.

For the real proof, run `guided` as root so it gets `SCHED_FIFO 58` on core 0 (the message about running without SCHED_FIFO disappears), then repeat.

## What this does not test yet

- The real camera: once `percept` writes real objects and a real hand into `/beacon_world`, run `guided` without `fakeworld`.
- Every cue says "down" because the chest camera looks down at the table. Expected; we tune it on the real mount.
