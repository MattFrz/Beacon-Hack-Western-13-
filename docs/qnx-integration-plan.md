# QNX integration plan: laptop → Pi

Date: 2026-11-21 (Saturday evening)
Status: findings from an adversarial review of the repo + bring-up log, then the deploy/integrate plan for the remaining hours. Submission is Sun Nov 22, 8 am; judging is after.
Source of truth for product/geometry remains `nathans-revision.md` ("the revision"). If this file disagrees with the revision on product, the revision wins; this file is ops.
Measured facts carry their date and where they were measured (laptop vs QNX). Anything unmeasured says so.

## 1. Findings

### 1.1 What laptop work has achieved (all true, all on the wrong machine)

- **Perception pipeline works end-to-end.** `percept/tools/probe_frame.py` (ORT YOLOE 320 + Depth Anything V2 210 + MediaPipe hands) runs a full cycle in **~124 ms (~8 Hz)** live: yolo ~14 ms, depth ~93 ms, hands ~15 ms, after the cadence fix (process-lifetime caching of capture/sessions). Measured 2026-11-21 on the laptop webcam.
- **Depth is usable after stabilisation.** `--depth-scale 0.25` + per-slot median stabiliser: real-video medians are a plausible desk scene (keyboard 0.83, cup 1.00, bottle 1.29, person 1.83 m). **Absolute scale is still tape-ungated** — the arbiter (prerecorded video + description) has not been run; do not speak metres from these numbers.
- **VO core is honest.** `vo_core` stride-1 on the handheld clip: valid_fraction 0.83, correction rate 0.083, 0.40 m loop drift after a full slow 360 return, wearer path p95 2.2 cm. Return/`slay`-style world-object anchoring (Anchor class, 1.5 m gate, median position) works on replay. **Tape-gated L-walk at chest height never happened.**
- **The guidance law works in C.** `guided/src/law.c` + tests implement LIVE/HOLD/LOST (max(1 s, 2×p95) LIVE window), REACH hysteresis 0.50/0.70 m, WALK speech, REPEAT/REJECT, off-axis amplitude floor — matching revision §6/§10.
- **The laptop demo (probe → UDP → bridge → dashboard) is good theatre** and can stay as the team monitor (`telemd` contract), but it is not the product path.

### 1.2 Gap table against the prize hard requirements

Prize text: *"runs on QNX OS and uses at least one open-source AI module from QNX"*; judges score real-time/reliability relevance, creative AI, **demo running on embedded hardware**.

| Requirement | State as of Sat evening | Verdict |
|---|---|---|
| Runs on QNX | `camd --stub/--bmp`, `percept-head`, deadline test ran on device; `guided` is QNX-ready in code | partial |
| QNX open-source AI module | Package table in `pi-bringup.md` §2 is **empty**. pip on PyPI failed (no QNX wheels). Nobody has attempted the QDD package UI / `oss.qnx.com` install for `python3-onnxruntime`, `opencv`, `mediapipe`, `whisper.cpp` | **fail — one install away** |
| AI on the device | Zero inference has ever run on the Pi. Models are staged with verified SHA-256 but there is no runtime | **fail** |
| Camera on the device | C270 is JPEG-only through Sensor Framework; `camd` consumes uncompressed only. The only "frames" ever in `/beacon_frames` were `screenshot` BMPs. Camera Module 3 was never acquired | **fail** |
| Whole loop on the device | `percept`→`guided` is not wired anywhere: the probe speaks UDP to the laptop; `guided` reads `/beacon_world`, which only `fakeworld` writes | **fail** |
| The QNX beat (`slay percept`) | No on-device process is in the guidance loop, so killing one demonstrates nothing yet | **not yet demonstrable** |

### 1.3 QNX-mechanism stubs (the pitch vs the code)

The pitch claims five mechanisms (revision §5.1: processes, FIFO priorities, runmasks, seqlock shm, supervisor). Reality:

1. **Seqlock shm: real.** `include/beacon.h` per-writer seq, readers never block. Done, tested.
2. **`guided` scheduling: real in code, unproven on device.** `platform_set_thread_sched(FIFO 58, runmask 0x1)` exists; `deadline_test` on the Pi (2026-11-21) with 3 hogs: 1800 wakeups, `p95_late_ns=6.9 ms`, `over_period=2`. Note `clock_getres` is 1 ms on this image, so read `over_period`, not per-wakeup counts.
3. **Piezo: stub.** `platform_piezo_set()` is a printf/counter. "The beeps keep going" currently prints a line. Needs buzzer + transistor (workshop) and the GPIO write.
4. **Supervisor: not to spec.** `supervisor.c` uses `posix_spawnp(..., NULL, NULL, ...)` — no `POSIX_SPAWN_SETSCHEDULER`, no priority, no runmask; polls shm instead of pulses; does not create the shm regions. Only supervises one child.
5. **Runmask discipline: untested with real inference.** The `pidin ar` proof that no percept/ORT thread touches core 0 requires ORT on the device, which does not exist yet.

### 1.4 The real-time claim needs re-scoping

A 16.67 ms deadline for a *tick beep* is not a product requirement — no wearer can hear 100 ms of tick jitter — and a QNX engineer will ask why it is. The defensible claims, in order of strength:

- **Audio never stalls or blocks on inference** (USB/BT writes off-thread; if the audio path wedges, piezo survives).
- **The cue never lies**: LIVE/HOLD/LOST from capture-time ages; no guessed metre; cover-the-lens behaves identically to `slay percept`.
- **Guided control and audio never wait on a model**: priority + runmask keep the 16 ms loop intact under an inference-saturated cores 1–3 — with the measured `deadline_test` numbers as evidence, honestly labelled (`clock_getres` 1 ms caveat).
- **Restart without reboot**: supervisor respawns `percept` mid-session and the session store survives (revision's Bruce-Power-aligned story).

Lead with truthfulness-under-failure, not with "60 Hz".

### 1.5 Cuts already made or to be made now

- **Cut from Sunday:** VO/RETURN in the 30 s script (already gated by the revision §12–13), whisper/llama if the table covers the script phrases (they currently must, since `voiced/` is empty), off-camera ask-the-room, floor drops.
- **Keep at all costs:** on-device YOLOE+depth, REACH ticks, `slay percept` → HOLD → LOST, supervisor restart.
- **Dashboard stays a monitor**, never on the wearer's path.

### 1.6 Small risks that will burn an hour at the worst moment

- `models/labels.txt` is now 16 nouns; the 64-label ONNX was re-staged to the Pi **before** the 16-class re-export. Verify the on-device SHA matches the current export before any on-device run.
- `CAM_W`/`CAM_H` are still 0 in `beacon.h` (correct per policy — nothing is frozen until a real camera probe). Everything on-device must read per-slot dimensions until frozen.
- The QDD install is the **only unattempted** path to a runtime; `pkgadd`/`pkginfo` are absent on this image, and `apkgrel` is not an installer (checked 2026-11-21). Plan for the QDD UI being the way, with Discord/booth as the fallback authority.
- Audio out on the Pi is only the validated experimental BTstack→JBL bridge. It works (survives reboot, auto-reconnect) but is application-level, root, and one writer at a time on the FIFO. `guided` must keep its audio-thread shape and write S16 stereo 44.1 kHz frames via `bt_speaker.py`'s contract; piezo remains the cannot-fail channel.

## 2. Plan

Principle: **the first thing that runs on the Pi with AI in it beats every additional laptop feature.** Every step gates the next; if a step fails, take its fallback and keep moving. Time boxes assume the four of you in parallel where owners allow.

### Step 0 — Mentor ask (Nathan, 15 min, now, blocks everything)

Ask the QNX booth/Discord directly: *"On the QNX 8.0 QSTI Pi 5 image, what is the exact install command for `python3-onnxruntime`, `opencv`/`python3-opencv`, and `python3-mediapipe`? `pkgadd` is absent and PyPI has no QNX wheels."* Try the QDD package UI in parallel (`ssh -X`/VNC). This is the single highest-leverage action of the night. While asking, also confirm: is a Camera Module 3 + 22-pin cable available, and is a USB headset (mic+ear) available.

### Step 1 — Runtime on the Pi (Nathan, 45 min hard box)

Goal: one ORT inference on the device. Install `onnxruntime` (+`opencv`, `mediapipe`, `numpy` via QNX ports if offered). Verify with a 20-line on-device probe: load `models/yoloe26n_320.onnx` (16-class, verify SHA), run one stub frame, print one box. Record package names/versions in `pi-bringup.md` §2 — that table is currently the visible hole.

**Fallback if no install path exists tonight:** ship inference via a *stated* hybrid — but do not go silently: if `percept` cannot run on-device, the honest submission is laptop-percept + on-device `guided`/`supervisor`/`camd`/piezo, demoed as the QNX control half, and the Devpost text says exactly that. That is a much weaker QNX entry; spend everything before accepting it. Second fallback: `llama.cpp`/`whisper.cpp` are also `oss.qnx.com` binaries — if ORT refuses but whisper installs, on-device voice-in satisfies the letter of the "open-source AI module from QNX" requirement and salvages the criterion.

### Step 2 — A real frame into `/beacon_frames` (Nathan, 60 min)

Two options, in order:

- **A: C270 JPEG intake.** `mjpeg_example` proves the C270 enumerates and decodes at 640×480 JPEG (2026-11-21). Add a `--jpeg` source to `camd`: read the JPEG frame from the Sensor Framework path that `mjpeg_example` uses, decode (device has a JPEG decoder per that sample), publish NV12/BGR into the ring with real `frame_id`/`t_ns`. Delete the `--bmp` screenshot path from the demo story forever.
- **B: Camera Module 3** (only if the workshop hands one over + 22→15 pin cable): unit 3/4, `sensor_rpi5.conf` already configures `imx708` 2304×1296 nv12 — `camd` reads uncompressed directly. Prefer B if available; A is the default.

Freeze `CAM_W`/`CAM_H` + frametype in `beacon.h` after the first live capture (revision §4 gate). Then the 30-second chessboard/FOV calibration can use the committed `calibrate_camera.py`.

### Step 3 — `percept` on the Pi (Nathan, 60 min)

Run `probe_frame.py` **as the device process**, pointed at the ring (or its own Sensor Framework session if that is simpler tonight — flag the shortcut in the log): YOLOE+depth+hands on one frame → print boxes/metres/fingertip. This is the screenshot that satisfies "AI running on embedded hardware". Measure the combined cycle p50/p95 with `guided` live later (step 6); record in `pi-bringup.md`.

### Step 4 — `ingest`: the missing wire (Munadir or Nathan, 60 min, can start on laptop now)

A small C process (or on-device Python allowed *here* — it is off the 60 Hz path) that takes the probe's UDP JSON world records and writes `/beacon_world` through the seqlock helpers in `beacon.h`: objects[], hand, health, capture-time `t_ns`/`last_seen_ns`. This single relay fuses the two halves into one product. Contract notes:

- preserve `frame_id` and capture timestamps from the probe payload; never stamp publish time (spec violation caught once already);
- `in_latest_boxes` bit comes from the probe record — it is the LIVE signal;
- run on cores 1–3 at `SCHED_RR` 20; never core 0.

Alternative shape if UDP-on-loopback offends: have the on-device probe import `probe_frame` as a library and write `/beacon_world` directly in-process — one less hop, but more code motion; prefer `ingest` for time.

### Step 5 — Audio out + piezo (Munadir + Matt, parallel, 60 min)

- Wire `guided`'s audio thread to the validated BT path: FIFO contract 44.1 kHz S16 stereo, one writer, `QNX_PCM_VOLUME_SHIFT=0` for speech; `supervisor` already keeps `bt_audio_service.sh` alive across kills/reboots (validated 2026-11-21). Pre-rendered clips exist in `sounds/`.
- **Piezo**: buzzer + 2N2222 + 1 kΩ from the workshop; GPIO write in `platform_piezo_set()` via the `rpi_gpio` sample pattern; continuous fault on guided-death from the supervisor. This is the only channel that survives "audio vanishes", and it makes `slay percept` audible-proof.

### Step 6 — Supervisor to spec (Matt, 60 min)

Make `supervisor.c` do what §5.1 claims, minimum viable: create the three shm regions; spawn `camd` (FIFO 50, 0x1), `guided` (FIFO 58, 0x1), `percept`/`ingest` (RR 22, 0xe) with `POSIX_SPAWN_SETSCHEDULER` + child-side `ThreadCtl(_NTO_TCTL_RUNMASK)` on every thread; heartbeats over pulses (`ChannelCreate` + timer, 50 ms, two missed → SIGKILL + piezo fault + respawn with backoff); `percept`/`voiced` restart-only, never a reason to mute. Save `pidin ar` output proving runmasks. If pulses overrun the timebox, poll-shm heartbeats (current shape) are an acceptable demo-night downgrade — but spawn attrs and runmasks are not optional: they are the visible QNX engineering.

### Step 7 — The demo rehearsal on hardware (everyone, 60 min)

The 30 s script (revision §12, cut list applied):

1. "Where are my keys?" (button/table entry if `voiced` is not on-device) → spoken LIVE bearing → hand enters → ticks speed up → tone at the keys.
2. Bottle in view: "Where can I refill water?" → binds `bottle` → WALK speech.
3. SSH `slay percept` → HOLD → LOST → supervisor restarts it; cover-lens = same LOST.

Supporting numbers to have on screen (from `pi-bringup.md`, honestly labelled): deadline test p95/`over_period` with hogs, percept cycle p50/p95 on device, tape-check result. Rehearse twice, then record the video (it is the tie-breaker artifact).

### Step 8 — Tape check (Nathan, 20 min, before any spoken metre)

Tape on the floor/table at 0.5 m, 1 m, 2 m against the mounted camera with the device pipeline; record % error in `pi-bringup.md`. **> 30% at 1 m → metres leave the spoken sentence** ("Keys. Ahead, a little left.") per revision §11. Until this is run, `--depth-scale` 0.25 is an eyeball, not a calibration; say so in the Devpost text if it survives.

### Step 9 — Devpost + freeze (Matt, last 2 hours)

Devpost structure: 30 s recorded video first; failure demo (`slay`) second; then the mechanism list (processes/priorities/runmasks/seqlock/supervisor — no APS), named `oss.qnx.com` modules with installed versions, honesty block (sighted team, not BLV-tested, baked noun list, tape-check status). Freeze checklist: on-device model SHA matches `labels.txt`; no `--bmp` in the demo path; dashboard shown only as a monitor; `sd-stage/` never committed.

## 3. Ownership + order of attack (parallel tracks)

| Track | Owner | Steps |
|---|---|---|
| Runtime + camera + on-device percept + tape | Nathan | 0, 1, 2, 3, 8 |
| guided↔world wiring + audio + law polish | Munadir | 4, 5, 7 |
| supervisor + piezo + measurements + Devpost | Matt | 5, 6, 7, 9 |
| bridge/dashboard as monitor; replay capture for the video | Zain | (support in 7, 9) |

Critical path: **0 → 1 → 3**, with 2 overlapping, and 4 can be built on the laptop immediately against `fakeworld` + `dev-reach.jsonl` replays so it is drop-in when 3 lands.

## 4. What "done" means at 8 am Sunday

Minimum credible QNX entry (all four prize axes touched):

- one ORT inference on the Pi, package name recorded;
- one live camera frame into the ring;
- `slay percept` (the real percept) → HOLD → LOST → restart, audible through piezo/BT;
- measured deadline + cycle numbers, honestly labelled;
- a rehearsed, recorded 30 s script with no voice/VO claims beyond what ran.

Everything else — whisper on-device, llama, RETURN, VO numbers — is a bonus bullet, not a gate. If the mentor install path fails, the fallback ladder in Step 1 decides what the honest submission says, and it says it explicitly.
