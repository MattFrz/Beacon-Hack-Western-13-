# Beacon: team plan (who does what, when)

Date: 2026-11-21
Status: operations plan that builds on [`nathans-revision.md`](nathans-revision.md). The revision is the product, geometry and QNX source of truth; nothing here changes it. This file adds owners, tonight's laptop work, the hardware request, and the laptop dashboard.

## Where we are

- Hacking runs Fri Nov 20, 9 pm → Sun Nov 22, 9 am. Submit by 8 am Sunday.
- We have: the loaner Pi 5 (8 GB, QNX 8.0, official active cooler fitted, HiPi case), a Logitech C270 USB webcam with built-in mic, speakers, four laptops.
- The hardware workshop was closed Friday night. Parts come Saturday morning (request below).
- Tonight is software on laptops. Saturday we bring the parts and the Pi together and follow the spec's build order (§13).

## Owners

| Person | Owns (spec names) |
| --- | --- |
| **Nathan** | Hardware and perception: loaner bring-up (§21), `camd`, `percept` (YOLOE-26n, Depth Anything V2, MediaPipe hands, letterbox inverses, calibration), GPIO piezo wiring, camera choice. Helps with whisper.cpp on the Pi if needed. |
| **Munadir** | Guidance and voice: `guided` (the 60 Hz synthesizer, laws in §10, mode in §6, binding in §9) and `voiced` (whisper.cpp tiny.en, synonym table, optional llama.cpp on table miss). Co-owns `include/beacon.h` with Matt. |
| **Zain** | The laptop side: `bridge` and the 3D dashboard (below). |
| **Matt** | Everything around the core: `supervisor` (spawn, runmasks, heartbeats, restarts, piezo fault path), `include/beacon.h` with Munadir, `telemd` and its JSON format plus a replay generator for Zain, pre-rendered clips (§10 list), the measurements in §15, the Profiler trace, Devpost and demo video. Lane C (VO, RETURN) after build steps 1–5 are green. |

## Where your code goes and how to build it

`main` has the shared skeleton: one folder per process, each with a README naming its owner (see the [README](../README.md) layout table). Branch off `main`, work in your folders only, and merge back through a PR. Changes to `include/beacon.h` go through Matt and Munadir. Changes to `laptop/samples/` (the telemetry format) go through Matt and Zain.

**Shared conventions for the C/C++ processes**

- Each process folder gets its own `Makefile` that builds with `-I../include`. Plain `make` builds for the laptop with `cc`/`c++`. `make CC="qcc -Vgcc_ntoaarch64le" CXX="q++ -Vgcc_ntoaarch64le"` cross-compiles for the Pi from a laptop with QNX SDP 8.0 sourced (`source qnxsdp-env.sh`). Then `scp` the binary to the Pi.
- QNX-only calls (`ThreadCtl`, `procmgr_ability`, pulses, CamAPI, GPIO) go behind `#ifdef __QNX__`, so every process also builds and runs on a laptop.
- Output goes to `build/` (gitignored). Model files go in `models/` (gitignored, except `labels.txt`).

| Person | Branch | Folders | Builds with | Runs on a laptop as |
| --- | --- | --- | --- | --- |
| **Nathan** | `nathan/percept`, `nathan/camd` | `camd/` (C), `percept/` (C++), `models/` | Makefile per folder (above), linked against ONNX Runtime and OpenCV. Laptop export scripts (YOLOE prompt baking, ONNX export) live in `percept/tools/` and are Python. | `percept` on a webcam, printing boxes, metres and fingertip for one frame. `camd` is Pi-only (Sensor Framework). |
| **Munadir** | `munadir/guided`, `munadir/voiced` | `guided/` (C), `voiced/` (C++), `include/beacon.h` with Matt | Makefile per folder. `voiced` links whisper.cpp (and llama.cpp later). | `guided` reading a fake target from shm, printing law and clip ids at 60 Hz. `voiced` on recorded WAVs, printing `{job, candidates}`. |
| **Zain** | `zain/dashboard` | `laptop/bridge/`, `laptop/dashboard/`, `laptop/samples/` with Matt | Node 20+. `npm install` then `npm run dev` in `laptop/dashboard/`. `npm start` in `laptop/bridge/`. | Bridge replays a `.jsonl` file (or `world.sample.json`) over WebSocket, and the dashboard renders it. Never runs on the Pi. |
| **Matt** | `matt/supervisor`, `matt/telemd` | `supervisor/` (C), `telemd/` (C), `sounds/`, `include/beacon.h` with Munadir, `laptop/samples/` replay files | Makefile per folder. | `supervisor` spawning and restarting a dummy child. `telemd` reading shm and sending JSON over UDP to `bridge` on `localhost`. A replay generator writes `.jsonl` into `laptop/samples/`. |

Saturday integration: each person builds their own folder for QNX and copies the binaries to one directory on the Pi. `supervisor` is the only thing started by hand. It spawns the rest.

## Tonight: laptop work, no new hardware needed

First 30 minutes: Matt and Munadir freeze `include/beacon.h` from spec §6 (frame ring, depth slot, world state with per-writer seqs, `intent.kind`, pulse codes). Everyone builds against that header.

| Who | Tonight | Done when |
| --- | --- | --- |
| **Nathan** | If he has the Pi: bring-up §21 steps 1–5 (packages, C270 probe on Sensor Framework, USB audio playback and record). On a laptop: bake the noun list into YOLOE-26n and export static detect-only ONNX at 320 (§9); export Depth Anything V2 Metric Indoor Small; run both plus MediaPipe hands on a webcam through ONNX Runtime to check outputs and the §7 letterbox inverses. | Models and `labels.txt` in `models/` (large files not committed); a laptop script prints boxes, metres and fingertip for one frame; bring-up log notes package versions, camera unit, `W×H`, frametype. |
| **Munadir** | `guided` in C, QNX calls behind `#ifdef __QNX__` so it builds and runs on a laptop: read a fake target from shm with the seqlock reader, compute mode (LIVE / HOLD / LOST), pick the law (STOP, LOST, REACH, WALK, RETURN), enqueue clip ids and tick commands. `voiced` logic: whisper.cpp tiny.en on recorded clips, then the §9 synonym table to `{job, candidates}`, written to `intent` with its own seq. | Fake target in, correct law and clip ids out at 60 Hz; stopping the fake writer gives HOLD then LOST; ten test phrases map to the right job and candidates. |
| **Zain** | `bridge` and the 3D dashboard against a hand-written sample first, then Matt's replay files. | The dashboard plays a replay: objects at their 3D positions, hand point, target, mode banner, health panel. |
| **Matt** | `supervisor` skeleton (spawn, heartbeats over a channel, restart with backoff, piezo fault path as a stub). `telemd` JSON format and a replay generator (a reach, a HOLD, a LOST) so Zain is never blocked. Pre-render every §10 clip as 16 kHz mono WAV in `sounds/`. | Supervisor restarts a killed dummy child on a laptop; replay files exist; every §10 clip exists. |

## Saturday: on the Pi, in the spec's build order (§13)

| Step | What (spec) | Lead |
| --- | --- | --- |
| Morning | Collect parts. Bring-up §21 on the Pi: packages, camera probe (unit, `W×H`, frametype, focus lock), USB headset, GPIO piezo. | Nathan |
| 1 | `supervisor` + `camd` + `guided` with a fake target and the piezo. Busy-loop hogs on cores 1–3; 60 Hz ticks hold. Profiler trace and 16 ms miss count. | Munadir + Matt (Nathan for `camd`) |
| 2 | Lock `CAM_W×CAM_H` and focus, chessboard calibration, tape-measure depth on a 1 m table. | Nathan |
| 3 | Depth + MediaPipe in `percept` → real REACH on a cup. No VO, no YOLOE yet. | Nathan + Munadir |
| 4 | YOLOE + whisper + table → FIND while the object stays in view. | Nathan + Munadir |
| 5 | `slay percept` → HOLD → LOST. | Everyone |
| Evening | Dashboard live from `telemd`; rehearse the 30 s script (§12). | Zain + Matt |
| 6, only if 1–5 are green | ORB+PnP, then RETURN and off-camera memory. | Matt |

Feature freeze Saturday midnight. Sunday 1–6 am: the §15 measurements, demo video, Devpost.

## Hardware request (send on Slack, collect Saturday morning)

Matches the spec's hardware bill (§16).

| Item | Why | Spec ref |
| --- | --- | --- |
| Pi Camera Module 3 + **Pi 5 camera cable (22-pin to 15-pin)** | The camera the spec and Sensor Framework use | §4, §16 |
| USB headset with mic | Speech out and voice in; no 3.5 mm audio on the Pi 5 under QNX | §4, §16 |
| Piezo buzzer + NPN transistor (e.g. 2N2222) + 1 kΩ resistor | The cannot-fail actuator, driven through a transistor | §5.1 |
| Push button | Push-to-talk for `voiced` | §16 optional |
| Female-female jumper wires, small breadboard | Piezo and button to GPIO | |
| Optional: BNO055 or ICM-20948 | WALK yaw help | §4 |

The Pi already has the official active cooler. Check the power supply is the official 27 W (5 V / 5 A) so USB devices do not drop out.

## If parts are late: camera and mic only

We already hold a C270 with a mic. If Nathan's probe shows it on Sensor Framework, it can stand in until the Camera Module 3 arrives, and the USB speaker or C270 mic can stand in for the headset. Everything up to build step 5 can be developed that way; the piezo path waits for the buzzer and transistor.

## Laptop dashboard (additive, never on the wearer's path)

- **`telemd`** (Matt): an optional sixth process at the lowest priority we use, runmask `0xe`. Read-only on `/beacon_world` and `/beacon_frames` with the same seqlock readers; skips torn reads; never writes shm, never sends to `guided`. It recomputes `mode` for display with the same function `guided` uses (shared header), since `mode` is not stored in shm. Sends UDP to the laptop: world-state JSON at ~10 Hz (objects with `xyz_cam` / `xyz_world`, hand, target, intent, pose, crumbs, health) and a downscaled JPEG at ~5 fps.
- **Timing panel:** if Munadir and Nathan agree, `guided` also publishes a small stats block (miss count, worst lateness) under `seq_guided`; otherwise the panel shows the Profiler trace.
- **`bridge`** (Zain): Node, UDP in, WebSocket out, records every session to JSONL for replay.
- **Dashboard** (Zain): Vite + React + three.js via react-three-fiber. Torso with a chest camera cone and live video, objects at their real 3D positions from depth, fingertip-to-target line, the spoken cue as a caption, mode banner (LIVE / HOLD / LOST), process health, timing panel, replay scrubber.
- **Rule:** kill `telemd` or unplug the laptop mid-demo and the wearer hears no difference.

## Demo (spec §12)

1. "Where are my keys?" → spoken LIVE bearing → hand enters → ticks speed up → tone at the keys.
2. "Where can I refill water?" → binds `bottle` → spoken WALK cue.
3. `slay percept` → HOLD → LOST → supervisor restarts it. Cover the lens: same LOST, no guessed metres.

The dashboard runs on a laptop beside the table the whole time so judges see what the wearer hears.
