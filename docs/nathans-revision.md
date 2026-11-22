# Beacon: Nathan's revision

Date: 2026-11-21
Status: Nathan's revision. Product, accessibility framing, geometry, and QNX mechanism. Implementation source of truth for this repo.
Path: `docs/nathans-revision.md`
Repo: `/home/nate/Projects/Beacon-Hack-Western-13-`
Supersedes, for product and geometry: `Beacon Hack Western build plan.md` (Nov 20; removed from the repo, see git history) and the neighbour notes in `/home/nate/Projects/hackwestern13/docs/beacon-design.md`. Those remain research/ops background. Where they disagree with this file, this file wins. Operations (owners, folders, tonight's work) live in `docs/team-plan.md` and must not contradict this file.

Working name: Beacon.

A chest-worn Raspberry Pi 5 running QNX 8.0 that homes a wearer who is blind or has low vision to a named thing, without waiting for a sighted helper. Perception AI proposes a named 3D point. A high-priority QNX process is the only thing allowed to turn that point into sound. On Raspberry Pi OS a hung model can delay the beeps by hundreds of milliseconds with no error; this design is built so that cannot happen.

This is a hackathon prototype built by a sighted team. It has not been tested with people who are blind or have low vision. Say that in the pitch.

What this project is, in one place:

1. An accessibility product: named-object homing for people who are blind or have low vision (section 1).
2. A geometry loop: pixel to metre-scale 3D point to session memory to sound (sections 7–10).
3. A QNX isolation contract: five processes, FIFO on core 0, `slay percept` must not mute the piezo (section 5.1).
4. A weekend cut: Sunday is keys FIND+REACH, in-view bottle WALK, then kill → LOST. RETURN is gated on VO (sections 12–13).

## 1. Product

One-line job: a homing cue for a named item seen this session.

Beacon exists because a specific personal item that moved (keys, phone, a bottle on a table) still forces people to wait for whoever is nearby. A cane covers the floor. Memory and labels cover a consistent home. Camera apps describe a photo. AirTags work if you tagged the thing. Remote-help apps need another person on the line and occupy a hand. Digital tools are a last resort after touch and memory, and people drop them when they lie or go silent. Sources: `docs/beacon-accessibility-research.md`.

The wearer asks in ordinary English. The device answers with a short spoken instruction. Direction and distance in that sentence come from sensors, never from the language model. They walk on that speech.

Ticks start only when a hand is reaching for the targeted object. The chest camera estimates hand-to-object distance. Ticks speed up as the hand gets closer, stereo pans left/right, and a continuous tone when it is very close. Walking speech does not beep, so a cane hand is not fighting ticks. If the hand is close in range but far off-axis, ticks stay audible (hard pan, quieter, never silent). Silence while searching was the main failure in a 12-person BLV hand-steering study.

If vision dies, we kill `percept` live: speech or ticks hold from the last known place, then a distinct LOST. Never a guessed metre. Silence and a fake "two metres" are both unusable. Honest "I lost the target" is the wearer-facing claim and the QNX prize beat.

Independence here means control over when help arrives for this one job. Asking a person is not the failure.

### 1.1 Who it is for, and who built it

Wearer: a person who is blind or has low vision, indoors, with a cane or a free hand, looking for a named everyday item they have already been near this session.

Judges: Best Use of QNX. They should hear that a high-priority thread on core 0 still makes sound after the detector is dead.

Builders: a sighted hackathon team. Next step after the weekend is paid, BLV-led testing. Do not say the audio, the chest mount, or the LOST cue have been validated with wearers.

### 1.2 What the wearer can say

| Utterance | Job | Sunday |
|---|---|---|
| "Where are my keys?" | FIND a stored/live name | Required |
| "Where can I refill water?" | GO to a candidate in the session list | In-view bottle only until VO p95 exists |
| "Take me back." | RETURN along this-walk crumbs | Not in the 30 s script until VO p95 exists. Never faked |
| "Stop." / "Cancel." | STOP | Required |
| "Say that again." / "Repeat." | REPEAT last spoken cue | Required (cheap; no extra model) |
| "Not that one." | REJECT current bind; try the next candidate or NACK_UNSEEN | Required |

Hands stay free for a cane. All sensing, inference, guidance and audio run on the loaner Pi.

Three wearer journeys, same job at different ranges. Code may implement all three. Sunday's 30 s script does not.

| Journey | Wearer | Beacon | Sunday 30 s |
|---|---|---|---|
| Find and reach | "Where are my keys?" | Spoken bearing while beyond arm's reach; ticks only once a hand is reaching | Required |
| Ask the room | "Where can I refill water?" | Map the sentence onto a stored session label, then the same homing | In-view only until VO p95 exists. Demo object is a `bottle` |
| Return | "Take me back." | Replay this-walk breadcrumbs backwards as spoken walk waypoints | Not in the 30 s script until Saturday VO p95 exists. Never faked |

Floor-level dropped items (medication on white tile) are a documented pain and are out of the Sunday script. The chest camera is a tabletop and in-view claim until a floor drop is actually tested.

### 1.3 Pitch language

Say this:

> Beacon homes you to a named item you have already seen this session, fully on the Pi. It is a supplement to the cane and to your own labels. It does not detect stairs, traffic, or obstacles. The word list is baked (keys, bottle, cup, ...). If it loses the target it says so. Built this weekend by a sighted team; it has not been tested with BLV wearers yet.

| Avoid | Why | Use instead |
|---|---|---|
| "We give people sight" / "see with sound" / "a camera for the blind" | Cure framing is criticized by blind people | Homing cue for a named item: get there and reach it without waiting for a sighted person |
| "the blind," "suffering from," "brave," "inspirational" | Paternalistic or tragedy framing | "People who are blind or have low vision"; ask individuals how they self-identify |
| "Replaces the cane" / "keeps you safe" / obstacle, stair, or traffic claims | Safety the spec does not demonstrate | A supplement to the cane. It does not detect obstacles, stairs, or traffic |
| "Seeing AI / Be My Eyes, but better" | Those are description and remote-human tools | Different job: homing to a named thing seen this session, on-device, no one else watching the camera |
| "Works anywhere / finds anything / never wrong" | Confident wrong outputs cause overtrust | Short baked word list and objects in view; if it loses the target it says so and never invents a distance |
| "No more asking for help" | Asking can be an independent living skill; the problem is loss of control | Fewer moments where this one job depends on whoever happens to be nearby |
| "User-tested with the blind" | Untrue | Built by a sighted hackathon team; next step is paid, BLV-led testing |

Sunday 30 s must never imply: finding an object never seen this session; arbitrary nouns beyond the bake list; stairs/obstacles/traffic; ticks as a trusted guide after perception is dead; a room inventory; a floor drop; RETURN as indoor navigation. Show `slay percept` -> HOLD -> LOST. Do not only describe it.

### 1.4 Audio UX (wearer-facing)

- Query-driven and short. "Keys. About two metres ahead, a little left." Repeat about every 3 s while walking. Stop when REACH starts.
- Tick rate encodes hand-to-target distance. Stereo pan encodes left/right. Continuous tone inside about 15 cm. A faster tick must never mean error or lost (use a different timbre).
- Off-axis hand: keep a findable tick. Pan hard, drop amplitude to a floor (about 0.25), never to zero.
- LOST is a different sound, then one short sentence with no number: "I lost the target."
- Keep at least one ear open to the room. Prefer bone conduction or a single ear. Two-ear USB is the loaner default until something open-ear exists; do not claim the form factor is right.
- Repeat, reject, and stop are first-class. The wearer must be able to question a bind.
- Do not narrate the room. Do not stream corrections while walking.

## 2. What this is not

- A room narrator / Seeing AI clone. No “what’s in front of me” inventory as a v1 job.
- A cane, guide dog, or obstacle / stair / traffic detector. No safety claim we do not demonstrate.
- A floor-drop finder on Sunday. Chest camera is tabletop and in-view until a floor drop is tested.
- Building-scale SLAM, loop closure, indoor GPS, or place-recognition relocalization. RETURN is a short retrace of this walk, not “take me anywhere.”
- A physical tag / AprilTag fob. Identity is a baked detector label, not a printed marker. AirTag-style tagging is a different product.
- CLIP crop index, vector database, LingBot-Map, Cactus Mirage, Hailo NPU, CUDA companion.
- Distances, headings, or “stop” emitted by an LLM.
- Cloud APIs. The camera feed does not go to the internet or to a remote human. Optional `telemd` may send world-state JSON and a downscaled JPEG to a laptop on the local network so the team can monitor. Kill `telemd` and pixels stay on the Pi. The wearer path never waits on that laptop.
- Dual-camera headset as a v1 requirement.
- QNX 8.0 adaptive partitioning (APS). **QNX 8.0 does not support APS.** Isolation is processes, priorities, runmasks, and a supervisor. Do not pitch APS.

“Open-vocab” in v1 means **no retraining**: a baked noun list (6 today: `bottle`, `can`, `keys`, `phone`, `box`, `mouse`) is baked into YOLOE-26n before Saturday, up to 64 prompts. It does **not** mean arbitrary new nouns at runtime. Say that to judges. The noun list is a product limit, not an implementation detail.

## 3. Locked decisions

Talked through in alignment; do not silently reopen. Review patches below are contract fixes, not product forks.

| Call | Decision |
|---|---|
| Docs vs plan | This file (`docs/nathans-revision.md`) is the product/geometry/QNX source of truth. The Nov 20 plan was removed from the repo. `docs/team-plan.md` is ops only. |
| Physical tags | None. |
| Mapping | Session-scoped 3D POI store is in v1 (objects seen this walk). Not a building map. |
| Detector | YOLOE-26n **detect-only** static ONNX with baked prompts (6 today, 64 max) if Ultralytics export allows; otherwise note the extra seg-head cost. Runtime is QNX `onnxruntime` 1.24.4. Prompt-free 4,585-name checkpoint is stretch only, gated on loaner p95. |
| Product slice | Homing, not narration. |
| Walk vs reach | Walk = spoken instruction from sensors. Reach = ticks from hand-to-target distance. |
| Sunday script | FIND-and-reach + in-view bottle WALK + `slay percept` → LOST. Ask-the-room off-camera and RETURN drop unless VO p95 exists. Do not say “RETURN is implemented” from a log. |
| Failure demo | After a successful home, `slay percept`. HOLD then LOST. Cover-lens is the same path. |
| Weekend approach | Session homing on five processes. Optional sixth process `telemd` is read-only monitoring (JSON + downscaled JPEG to a local laptop). Kill it and the wearer hears no difference. No CLIP. No Laya unless Saturday is already green. |
| Speech | Wearer may speak ordinary English. `voiced` emits `{job, candidate names}`. `guided` binds a stored object and speaks a short instruction filled from sensors, then ticks on reach. Table first; llama.cpp only on table miss; keyword fallback if the LLM is late. REPEAT and REJECT are first-class. |
| Form factor | Chest, one Camera Module 3, GPIO piezo. Audio: keep at least one ear open if the kit allows (bone conduction or single-ear). Two-ear USB is the loaner fallback, not a claim that the form factor is right. Optional IMU does not replace VO. |
| Hands (review) | MediaPipe runs in `percept`, not on the 16 ms `guided` thread. After `slay percept`, REACH uses last `d` (HOLD) then LOST. No new unprojection without depth. |
| Off-axis ticks | REACH ticks stay findable when the hand is near in range but far in angle. Amplitude floor ~0.25, never silent. |
| Validation | Prototype. Not BLV-tested. Floor drops out of Sunday. |
| Remote monitor | Optional `telemd` may send JSON and a downscaled JPEG to a laptop on the local network. Kill it and pixels stay. Never cloud. |

## 4. Constraints

Hardware and OS:

- Raspberry Pi 5, 8 GB, QNX 8.0 loaner image, active cooler required. Thermal throttle on core 0 kills the guidance deadline.
- Camera Module 3 through QNX Sensor Framework (unit 3 on CAM/DISP 0, unit 4 on CAM/DISP 1). Frames are uncompressed. Confirm the loaner config (`sensor_rpi5.conf` or older `post_startup.sh`) before writing camera code.
- **Lock published `W×H` and focus before calibration.** After Phase 0 capture, write `CAM_W`, `CAM_H`, frametype into a header every consumer compiles against. If CamAPI can lock focus, lock it as a **step-2 gate**. If it cannot, Range 1 unprojection is unknown until a tape-check at two distances; do not speak metres.
- Audio out: USB headset is the loaner path (QNX Pi 5 has no usable 3.5 mm jack). Prefer single-ear or bone conduction so the other ear stays on the room. GPIO piezo is the cannot-fail actuator if USB audio vanishes. Do not put guidance vibration on the cane hand.
- Optional IMU: BNO055 or ICM-20948 on I2C. Visual odometry still publishes pose; IMU only helps WALK yaw.

Software (from `oss.qnx.com` unless noted):

- `whisper.cpp` (speech in)
- `onnxruntime` 1.24.4 (YOLOE-26n, Depth Anything V2)
- `tflite-runtime` 2.21.0 and/or `mediapipe` 0.10.26 (hands, in `percept`)
- `opencv` 4.12 (`features2d` + `calib3d` for VO; crop/scale). Do not depend on `opencv_rgbd` / ICP being in the QNX build.
- `llama.cpp` packaged. Invoked only on table miss. Must not emit numbers. Do not load it for the 30 s script if Friday rehearsal phrases all hit the table.

Scheduler (detail in section 5.1):

- Isolation is processes, thread priorities, CPU runmasks, and a supervisor. **QNX 8.0 has no APS.** Do not pitch partitions.
- Privileged priorities (64+) need `procmgr_ability(PROCMGR_AID_PRIORITY)` then drop root. Default unprivileged ceiling is 63. Stay at 63 max unless ability is proven.
- `guided` is `SCHED_FIFO` 58 on core 0. `percept` / `voiced` are `SCHED_RR` 22 / 18 on cores 1–3. Core 0 never runs a model thread.

Compute budget, CPU only, four Cortex-A76 cores. **Linux/QNX proxy numbers are not simultaneous cadences.** `percept` is one pipeline. Default is sequential YOLO then depth then hands then VO. Optional 2-thread YOLO∥depth only after a measured p95 on the loaner with `guided` running. Do not treat any ms in this table as a QNX fact until that gate.

| Job | Model | Where | Role | Proxy (not a QNX fact) |
|---|---|---|---|---|
| Boxes | YOLOE-26n ONNX 320 px, baked, detect-only if possible | `percept` | labels + boxes | Linux ~200–333 ms at 320; YOLO11n ONNX 320 was 168 ms on Pi 5 + QNX + ORT (Henomaly). **Loaner p50/p95 is a Saturday gate.** |
| Depth | Depth Anything V2 Metric Indoor Small INT8 ~210 px | `percept` | metres | ~120 ms on Pi 5 Linux; remeasure on QNX |
| Hands | MediaPipe palm + landmark lite | `percept` worker | fingertip pixel | **unsourced**; do not claim 5–10 ms |
| VO | ORB + `solvePnPRansac` | `percept` | pose | **unknown** |
| Combined vision | sequential default | `percept` | one `frame_id` bundle | expect ~2–3 Hz if proxies add; measure |
| Speech in | `whisper.cpp` tiny.en | `voiced` | on command | ~0.7 s per short command |
| Speech remap | `llama.cpp` ~0.5B GGUF, ≤16 tokens | `voiced` | table miss only | ~1–2 s Linux 0.5B proxy; skip if late |
| Guidance | templates + ticks | `guided` 60 Hz | synthesizer | 0 ms inference; USB writes off-thread |

A 60 Hz loop does **not** create 60 fresh 3D measurements per second. Depth and boxes update at the combined vision rate. `guided` interpolates the last valid `d`.

Depth Anything V2 collapses below ~210 px. Do not chase 30 fps depth. YOLOE export happens on a laptop; the 254 MB text encoder never ships to the Pi. Ultralytics YOLOE weights are AGPL-3.0; acceptable for a hackathon build, say so if asked.

## 5. Architecture

Five processes. That is the microkernel story. Do not collapse them into one binary.

```
core 0  (runmask pinned)
  supervisor   prio 63   spawn, heartbeat, restart, health LED / piezo fault
  camd         prio 50   Sensor Framework -> newest-frame shm ring
  guided       prio 58   synthesizer: WorldState -> speech templates + reach ticks
                         NO models, NO full-frame convert, NO blocking USB write

cores 1-3
  percept      prio 22   YOLOE + depth + hands + unproject + RGB-D odometry + objects[]
  voiced       prio 18   whisper.cpp + {job, candidates} + optional llama.cpp
```

`guided` never waits on ONNX, whisper, llama, or MediaPipe. Vision is whatever `percept` last published. If `percept` is late or we `slay` it, the last `WorldState` is still there.

Henomaly used nine processes, shared-memory frames, high-priority camera/alerts, low-priority inference, and a supervisor. Copy that shape. MOGGIE and EyeMelody dropped queued frames and kept the newest one; copy that too.

Pin ORT/TFLite/MediaPipe thread pools onto cores 1–3. They must not leak onto core 0.

### 5.1 QNX mechanism (the prize)

This is the part judges score. Geometry in later sections can drop (RETURN, off-camera memory) and the prize story still holds. If this section is not visible in the 30 s demo, Beacon is a Linux CV app that booted on QNX.

**Swap test.** Raspberry Pi OS is fully preemptive CFS. A 300 ms ONNX run on the same cores as `alsa` can delay a tick by hundreds of milliseconds with no error. QNX is a microkernel: drivers, filesystems, and these five programs are processes; a high-priority FIFO thread on core 0 preempts inference immediately. `slay percept` cannot mute the piezo. That is the product difference. Say it, then show it.

**Do not pitch APS.** QNX OS 8.0 Adaptive Partitioning is not on the loaner. Mixed criticality here is:

1. Separate address spaces (a `percept` SIGSEGV does not take `guided` with it).
2. `SCHED_FIFO` vs `SCHED_RR` priorities under the unprivileged ceiling (63).
3. CPU runmasks so model threads cannot migrate onto core 0.
4. A supervisor that restarts best-effort processes and faults if `guided` dies.
5. Seqlocked shared memory so `guided` never blocks on a mutex `percept` might hold when it dies.

**Who is C, who may be C++.** `supervisor`, `camd`, and `guided` are C (or C++ with no exceptions on the 16 ms path). `percept` and `voiced` may be C++ to wrap ORT / whisper.cpp / llama.cpp. Do not put the synthesizer in Python. Python is allowed for a laptop export script and for a one-shot CamAPI probe, not for the 60 Hz loop.

#### Process table

| Process | Runmask | Policy / prio | Language | May die during demo? |
|---|---|---|---|---|
| `supervisor` | `0x1` (core 0) | `SCHED_FIFO` 63 | C | No. If it dies, piezo fault from a last-gasp `atexit` / dying pulse is the only remaining cue |
| `camd` | `0x1` | `SCHED_FIFO` 50 | C | Restart. No invented frames while down |
| `guided` | `0x1` | `SCHED_FIFO` 58 | C | Restart + continuous piezo until the new instance heartbeats |
| `percept` | `0xe` (cores 1–3) | `SCHED_RR` 22 | C++ | Yes. `slay` this on Sunday |
| `voiced` | `0xe` | `SCHED_RR` 18 | C++ | Yes. Intent stays at last value; ticks continue |

Bit `0x1` = CPU 0, `0xe` = CPUs 1+2+3. Confirm with `pidin ar` on the loaner; Pi 5 is 4-way SMP.

`camd` stays on core 0 so Sensor Framework callbacks are not scheduled behind ORT. It does **not** convert colour and it does **not** run a net. If core 0 is too busy, drop `camd` to `0x2` (CPU 1) **only after** a Profiler trace shows the 16 ms thread missing because of camera ISR/callback time — never to make room for a model.

#### Abilities and uid

Boot the stack from a short script as root, then drop.

```
procmgr_ability(0,
    PROCMGR_ADN_ROOT    | PROCMGR_AOP_ALLOW | PROCMGR_AID_PRIORITY,
    PROCMGR_ADN_NONROOT | PROCMGR_AOP_ALLOW | PROCMGR_AID_PRIORITY,
    PROCMGR_ADN_NONROOT | PROCMGR_AOP_ALLOW | PROCMGR_AID_PATHSPACE,
    PROCMGR_AID_EOL);
```

Stay at priority ≤ 63 unless that call is proven. GPIO / CamAPI may need `PROCMGR_AID_IO` or to remain root; if they do, keep `camd` and `guided` as root and still drop `percept` / `voiced` to `qnxuser`. Do not run ORT as an unbounded root process on all four cores.

After spawn, each child also calls:

```
ThreadCtl(_NTO_TCTL_RUNMASK, (void *)(uintptr_t)runmask);
```

on **every** thread it creates (ORT intra-op threads included). Spawn runmask is not enough if a library creates threads later.

#### Spawn

`supervisor` is not OS pid 1. It is the parent of the other four.

1. Create `/beacon_frames`, `/beacon_depth`, `/beacon_world` with `shm_open` + `ftruncate` + `mmap` (`/dev/shmem/...` on QNX). Zero seqs to 0 (even = stable empty).
2. `ChannelCreate(0)` for heartbeats. Children `ConnectAttach` to that channel (pass chid via argv or a well-known name in shm).
3. `posix_spawn` each child with `POSIX_SPAWN_SETSCHEDULER` / `POSIX_SPAWN_EXPLICIT_SCHED`, `sched_priority`, and runmask (`posix_spawnattr_setrunmask` where the header provides it; otherwise the child sets `ThreadCtl` as its first line).
4. `waitpid` / `SIGCHLD` for death. `percept` and `voiced` are restarted with a backoff (100 ms, 500 ms, 2 s, then every 5 s). `guided` restart also drives the piezo fault until the new instance pulses.
5. Sunday kill is `slay percept` from SSH (or `kill -9 <pid>`). Supervisor must treat a clean kill the same as a crash: HOLD/LOST in `guided` is the wearer-facing path; supervisor only respawns.

Do **not** use a mutex in `/beacon_world` that `percept` could hold while dying. Seqlock only.

#### Heartbeats and the 16 ms loop

`guided` deadline is 16.67 ms (`CLOCK_MONOTONIC`). Loop shape:

```
next = now + 16'666'667 ns
loop:
  read seqlocks (never block)
  bind + select law
  write piezo (non-blocking GPIO)
  enqueue USB clip/tick (non-blocking; drop if the audio queue is full)
  MsgSendPulse to supervisor (or MsgSendPulse *from* a timer)
  clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, next)
  next += 16'666'667 ns
  if now > next: count a miss; jump next forward; do not catch up by skipping piezo
```

Use `clock_gettime(CLOCK_MONOTONIC)` for `now`, ages, and `last_seen_ns`. **Not** `CLOCK_REALTIME` (loaner NTP will jump). Store nanoseconds as `uint64_t`.

Supervisor: `timer_create(CLOCK_MONOTONIC, SIGEV_PULSE)` every 50 ms. If two pulses arrive with no `guided` heartbeat, `SIGKILL` the old `guided`, piezo continuous fault, respawn. `camd` heartbeat is looser (250 ms). `percept` / `voiced` heartbeats are health only (yellow LED), never a reason to stop ticks.

Pulse codes (suggestions; pick and freeze in a header):

| Pulse | From | Meaning |
|---|---|---|
| `_PULSE_CODE_MINAVAIL+0` | timer | supervisor 50 ms tick |
| `+1` | `guided` | heartbeat |
| `+2` | `camd` | heartbeat |
| `+3` | `percept` | heartbeat (optional) |
| `+4` | `voiced` | heartbeat (optional) |
| `+5` | `voiced` | new `intent` edge (wake bind; `guided` still polls seq) |
| `+6` | `guided` audio thread | USB audio underrun |

Large payloads stay in shm. Pulses are edges.

#### Shared memory on QNX

POSIX `shm_open` names appear as `/dev/shmem/<name>`. Use `O_CREAT|O_RDWR`, `ftruncate` to a fixed size computed from `CAM_W×CAM_H` **after** the Phase 0 probe (or mmap a generous max and store `W,H` in the header). `MAP_SHARED`. No file-backed `mmap` on `/tmp`.

Seqlock:

```
writer: seq |= 1u;  /* stay odd if previous writer died */  __sync_synchronize();
        memcpy fields;
        __sync_synchronize();
        seq++;  /* even */
reader: do { s1 = seq; if (s1 & 1) continue; read; s2 = seq; } while (s1 != s2 || (s1 & 1));
```

`guided` skips a torn read and keeps last good values. It never waits for `percept`.

QNX message passing (`MsgSend`/`MsgReceive`) is for heartbeats, clip ids, and “play this.” It is **not** the frame path. A `MsgSend` from `percept` to `guided` would invert the priority story (server `guided` blocked in `MsgReceive` is fine; `guided` must never `MsgSend` to `percept` and wait).

#### Sensor Framework camera (`camd`)

- Pi Camera Module 3: unit **3** on CAM/DISP 0, unit **4** on CAM/DISP 1. Probe both. Freeze the unit in a header.
- Config on newer QSTI: `/etc/config/sensor/sensor_rpi5.conf`. Older write-ups edit `/usr/etc/startup/post_startup.sh`. Read the loaner before writing CamAPI.
- API shape (from QNX AI Camera App / CamAPI): `camera_open(unit)`, set viewfinder size/format, `camera_start_viewfinder`, callback or `camera_get_frame`. Frames are **uncompressed**. There is no H.264 path; do not plan one.
- Three-slot ring, newest-wins. If the callback overruns, drop the frame; do not queue.
- Publish `frame_id` (monotonic uint64), `t_ns` from `CLOCK_MONOTONIC` at dequeue, `width`, `height`, `stride`, `frametype`.
- Colour convert in the **consumer ROI**, on cores 1–3, not in `camd`.
- If `camera_get_frame` fails or the unit vanishes: stop writing slots, leave last seq even, let health age. Do not repeat the last pixels with a new timestamp.

Reference: https://gitlab.com/qnx/projects/ai-camera-app and https://github.com/qnx/QNX-AI-workshop (MediaPipe hands on this Pi).

#### Audio and piezo

USB headset is the wearer-facing speaker/mic. QNX Pi 5 has **no usable 3.5 mm** path. `io-audio` + USB: confirm the device node on the loaner (`pidin` / `ls /dev/snd` or the QNX equivalent). Mic is 16 kHz mono into `voiced`. Playback is **not** on the 16 ms thread.

`guided` splits:

- **16 ms thread (prio 58, core 0):** law, piezo GPIO, enqueue `{clip_id, pan, tick_hz}` onto a 32-slot lock-free ring.
- **Audio thread (prio 40, core 0):** blocking USB writes. If this thread blocks forever, ticks still exist on the piezo. If the ring is full, drop speech clips first, never drop an in-REACH tick command.

Piezo: GPIO through a transistor (do not drive the pin at speaker current). Bit-bang a square wave from the 16 ms thread **or** PWM if the BSP exposes it. Continuous fault = 50% square at a fixed pitch, distinct from the REACH continuous tone. Samples: `github.com/qnx/Raspberry-Pi-Hardware-Component-Samples` (`rpi_gpio`).

`voiced` never opens the playback device. Prompt beeps are clip ids sent to `guided`.

#### Inference runtimes (cores 1–3 only)

Install from `oss.qnx.com` on the loaner (QDD package UI or the image's pkg tool). Record the exact package names in the bring-up log:

| Package | Version (research) | Used by |
|---|---|---|
| `onnxruntime` / `python3-onnxruntime` | 1.24.4 | YOLOE-26n, Depth Anything V2 |
| `tflite-runtime` / `mediapipe` | 2.21.0 / 0.10.26 | hands in `percept` |
| `opencv` | 4.12.0 | letterbox, ORB, `solvePnPRansac` |
| `whisper.cpp` | 2026-07 git | `voiced` |
| `llama.cpp` | 0.0.9006 | table-miss remap only |

ORT / TFLite / MediaPipe session options:

- Intra-op threads ≤ 3.
- Affinity mask `0xe`. If the API has no affinity, create a 3-thread pool you pin with `ThreadCtl` and point the runtime at it.
- After creating worker threads, dump `pidin` and confirm no tid of `percept` has runmask including CPU 0.

Default pipeline is **sequential** on one `frame_id`: YOLO → depth → hands → VO. Parallel YOLO∥depth is a measured option, not the spec.

#### Clocks, thermal, measurement

- Ages: `CLOCK_MONOTONIC` ns.
- Core 0 thermal throttle kills the deadline. Active cooler required. Read `/dev/thermal` (or the QNX thermal node on the image) during the busy-loop test.
- Must-capture before Sunday: System Profiler / `tracelogger` of the 60 s guidance log; `pidin ar`; worst `clock_nanosleep` lateness of the 16 ms thread with cores 1–3 hogged.
- `on -p 58 -C 1` is acceptable for a manual skeleton. The shipped path is `supervisor` spawn, not a pile of `on` jobs, so death/restart is in one place.

#### Startup (do not use `/boot/onboot`)

The loaner QSTI runs `/boot/onboot` from SLM **before** pipes and `/usr` exist. That script cannot launch Beacon. Constraints already learned on this image: **no pipes**, **only `/proc/boot`**. Do not add Beacon there.

Launch from a snippet after `io-audio`, Sensor Framework, and `/usr` (QSTI `post_startup` / an SLM component ordered after those). `supervisor` is the one binary the snippet starts.

Wi-Fi and SSH are bring-up, not the product. Staging files under `sd-stage/` in this working tree are **local** (they contain network secrets). They are not part of the design commit.

### Process contracts

**supervisor.** Spawns the other four, sets runmasks and priorities, then watches. Every 50 ms, `guided` must pulse. Two missed beats: kill `guided`, respawn, piezo to continuous fault until `guided` heartbeats again. Silence is not allowed. `percept` / `voiced` may die. Restart them. `guided` already handles stale targets. Optional GPIO LED: green = all fresh, yellow = percept stale, red = guided fault.

On `percept` start: if a writer seq is odd, skip that torn blob (do not copy it). Bump `pose_epoch`. Do not target using object `xyz` from another epoch.

**camd.** Open Camera Module 3 via CamAPI / Sensor Framework. Always overwrite the oldest of three ring slots. Readers take the newest completed seq, never a queue. If the camera vanishes, stop writing and let health age out; do not invent frames. Publish `frame_id`, `t_ns`, `CAM_W`, `CAM_H`. Do not convert colour in `camd`.

**guided (deadline 16 ms on core 0).** 60 Hz **synthesizer**:

1. Read latest completed `seq_percept` and `seq_voiced` (skip if odd / mismatch). `hand` is inside the percept blob.
2. Bind `intent` → `target` (section 9). Compute `mode` locally from `now` and `last_seen_ns` (section 6). **Do not write `mode` into shm.**
3. Select law: STOP, LOST, REACH, WALK, RETURN, REPEAT, REJECT (section 10).
4. Enqueue a clip id or tick command on a non-blocking queue. A lower-priority audio thread in this process (or `MsgSend` to an audio helper) performs USB writes. GPIO piezo is written from the 16 ms thread (it must not block).
5. Pulse supervisor.

Busy-loop test (build step 1): pin a `while(1)` on cores 1–3. Ticks on core 0 must stay inside 16 ms. If they do not, stop adding models.

Hard gate (build step 3): with cores 1–3 hogged, if synthesizer p95 misses 16 ms, drop REACH ticks (WALK speech still ships). Do not move models onto core 0 to “fix” it.

**percept.** Best effort, cores 1–3. One cycle consumes **one** `frame_id` and publishes one bundle:

1. Newest frame (`frame_id`, `t_ns`). Crop/scale for each net **without** converting the full published frame to RGB unless a net requires it. Work from mmap + ROI.
2. YOLOE-26n at 320 px → boxes, baked label strings, confidences. Inverse-letterbox to full-frame pixels (section 7). Reject boxes whose centre lands in pad.
3. Depth Anything V2 Metric Indoor Small INT8 at ~210 px. Metres, cap ~20 m. Publish `/beacon_depth` with its own letterbox affine and the same `frame_id`.
4. MediaPipe palm + landmark lite on a downscaled crop of the **same** `frame_id`. Inverse-crop landmark 8 to full-frame pixels. If two hands, keep the fingertip closer to the current target (or to the nearest object centroid if no target). Chest-down tabletop view is unknown; this is a step-3 gate, not a surprise Sunday.
5. Map every full-frame pixel through the depth affine before sampling Z. Sampling a 320-px box centre on a 210-px depth map is fiction.
6. Inside each box, centre 50% of depth pixels, median → Z, unproject with full-frame `(fx,fy,cx,cy)` → `p_cam`. Exclude the hand mask from object centroids. Skip padded / invalid depth pixels.
7. If `pose.valid` and `pose_epoch` matches, `p_world = T_world_from_cam · p_cam` (homogeneous; section 7).
8. Associate into `objects[32]`: same name and within ~0.4 m in world (or in cam if pose is down) **and** same `pose_epoch` for world matches. Else new id. **Do not delete a row when it leaves the camera.** That is the session map. LRU-evict the unused non-target row when full; never evict the current target.
9. Unproject the fingertip through the **same** depth map and `frame_id`. Publish `hand` in the percept-owned hand slot: `xyz_cam`, `xyz_world` if pose valid, `conf`, `t_ns`, `frame_id`.
10. RGB-D VO (section 8). Publish `pose`. If VO fails, `pose.valid = 0`. Do not invent motion.
11. If `pose.valid` and translation ≳ 5 cm, append a breadcrumb every ~0.4 s (`crumb_i`, `crumb_n`).
12. Update `last_yolo_ms`, `last_depth_ms`, `hb_percept_ns`.

`percept` restart **attaches** to `/beacon_world`; it does not zero `objects[]`, `crumbs[]`. It **does** bump `pose_epoch` and must not use `xyz_world` / `xyz_cam` from the previous epoch for “nearest” targeting. Targeting ignores rows older than the LOST gate (1.5 s) for setting a new target; older rows may remain in the session list for name binding.

**percept does not write `target`.** It proposes `objects[]`. `guided` selects.

**voiced.** USB mic, 16 kHz mono. Wake: push-to-talk GPIO if present, otherwise energy-gate a 2 s window after a short prompt beep (beep is a clip id sent to `guided`, not a USB write from `voiced`). `whisper.cpp` tiny.en → text. Then:

1. Deterministic synonym / keyword table → `{job, candidate_names[]}` (section 9).
2. If no row hits, `llama.cpp` ~0.5B GGUF remaps to one of `{FIND, GO, RETURN, STOP, REPEAT, REJECT}` plus candidate names from the **seen** `objects[].name` list (voiced may **read** names, not write objects). Cap ~16 tokens. Strip digits. If late or dead, write `intent.kind = NACK_UNHEARD` and return.
3. Write `intent` only (`seq_voiced`). Return.

`voiced` is forbidden from writing metres, headings, `target`, `objects[]`, `crumbs[]`, or playing USB audio. All wearer-facing clips go through `guided`.

## 6. Shared memory

Three POSIX shm regions. **Each writer has its own seq** (odd while writing, even when stable; readers skip if odd / mismatch). One global seq over a multi-writer blob is not a contract.

### Frame ring (`/beacon_frames`) — writer: `camd`

Three slots. Each: `seq`, `frame_id`, `t_ns`, `width`, `height`, `stride`, `frametype`, `pixels[]`. Prefer NV12 or BGR8888 depending on what Sensor Framework emits. Convert in the consumer’s ROI, not in `camd`, and not of the full frame on core 0.

### Depth slot (`/beacon_depth`) — writer: `percept`

Required. REACH cannot unproject a fingertip without it.

```
seq, frame_id, t_ns
W_d, H_d                  // depth net output, ~210
metres[W_d * H_d]         // metric Z, invalid sentinels allowed
depth_affine              // letterbox of CAM_W×CAM_H → W_d×H_d (section 7)
yolo_affine               // letterbox of CAM_W×CAM_H → 320×320
hand_crop                 // MediaPipe crop origin + scale in full-frame pixels
```

### World state (`/beacon_world`) — three seqs, three writers

```
seq_percept               // covers the percept-owned fields below
  pose        T_world_from_cam[4][4], t_ns, valid, age_ns, pose_epoch
  objects[32] id, name[32], xyz_cam[3], xyz_world[3], bbox_px[4],
              conf, last_seen_ns, frame_id, pose_epoch, in_latest_boxes
  crumbs[512] T_world_from_cam[4][4], t_ns
  crumb_i, crumb_n
  hand        xyz_cam[3], xyz_world[3], conf, t_ns, frame_id
              // written by percept; guided only reads
  health      hb_percept_ns, last_yolo_ms, last_depth_ms, p95_vision_ns
seq_voiced
  intent      kind, candidates[8][32], n_candidates, t_ns
seq_guided
  hb_guided_ns
  target      id, name[32], xyz_cam[3], xyz_world[3], conf,
              last_seen_ns, frame_id, pose_epoch
              // geometry copied from objects[] at bind time;
              // mode is NOT stored
```

`intent.kind`: `NONE | FIND | GO | RETURN | STOP | REPEAT | REJECT | NACK_UNHEARD | NACK_UNSEEN | NACK_CANT`.

`FIND` and `GO` are the same guidance law (set target). Keep both so the table/LLM can record phrasing; `guided` does not distinguish them.

`in_latest_boxes` is 1 iff this name had a box in the cycle that produced this `seq_percept`. That bit is the LIVE signal. `last_seen_ns` remains **capture time** of the last box (honest age). Do not use a 300 ms wall-clock gate. Capture-to-publish latency is on the order of the vision cycle (proxies 168–333 ms+). A 300 ms LIVE window makes spoken metres illegal at birth.

Mode is computed in `guided` only:

| Condition | mode | Sound |
|---|---|---|
| Bound target and `in_latest_boxes == 1` and `now - last_seen_ns < max(1.0 s, 2 × p95_vision_ns)` | LIVE | full REACH or WALK speech; metres allowed from this completed output, spoken as approximate |
| Bound target, not in latest boxes, `now - last_seen_ns < 1.5 s` | HOLD | last-known pose; darker/slower tick if already in REACH; **no new metres spoken** |
| else | LOST | unique cue; spoken “I lost the target”; never a number |

Until `p95_vision_ns` is measured, use `LIVE_MAX_NS = 1.0 s`. Replace with `max(1.0 s, 2 × p95)` after the Saturday gate.

Every observation carries source `frame_id`, capture time, and validity. Reused data keeps its original timestamp. An explicitly invalid observation is different from a missing one.

Message-passing (QNX pulses / `MsgSend`) is for heartbeats, intent edges, and “play this clip id.” Large frames, depth, and world stay in shm.

The route and the POI table **outlive** `percept`. Both live in `/beacon_world`, not in `percept`’s heap.

## 7. Relative position (the product)

Four frames, nothing else:

| Frame | What it is |
|---|---|
| **pixel** | Camera Module 3 image, size `CAM_W×CAM_H`. Origin top-left. |
| **cam** | Pinhole at this instant. OpenCV: +X right, +Y down, **+Z forward**. |
| **world** | Session frame. Identity at the first good keyframe. Not a building map. |
| **hand** | One point (index fingertip), not a frame. |

Intrinsics `(fx, fy, cx, cy)` come from a chessboard calibration of the chest camera **at `CAM_W×CAM_H`**. Every box and landmark is mapped to that full-frame pixel grid before depth is sampled.

### Letterbox / crop inverses (required)

YOLO 320 and depth ~210 are **independent** letterboxes of `CAM_W×CAM_H`. MediaPipe uses a third crop. Unproject only after mapping to full-frame pixels. Do not sample padded pixels.

Letterbox of full `W×H` onto net `w×h` (preserve aspect, pad):

```
scale = min(w / W, h / H)
pad_x = (w - W * scale) / 2
pad_y = (h - H * scale) / 2

# forward (full → net), for building the affine once
u_net = u_full * scale + pad_x
v_net = v_full * scale + pad_y

# inverse (net → full), used on every box / depth sample
u_full = (u_net - pad_x) / scale
v_full = (v_net - pad_y) / scale
valid  = u_full in [0, W) and v_full in [0, H)
         and u_net in [pad_x, w - pad_x) and v_net in [pad_y, h - pad_y)
```

Store `scale, pad_x, pad_y` per net in `/beacon_depth`. MediaPipe crop inverse is `u_full = u_crop / crop_scale + crop_origin_x` (same for v). Landmark 8 is then a full-frame pixel.

Unproject (full-frame `u,v` only):

```
Z = depth_at_full(u, v)         // sample via depth affine; metres, tape-checked
X = (u − cx) · Z / fx
Y = (v − cy) · Z / fy
p_cam = (X, Y, Z)
```

Homogeneous pose (column vectors):

```
p_world_h = T_world_from_cam * [X, Y, Z, 1]^T
p_cam_h   = inverse(T_world_from_cam) * [Xw, Yw, Zw, 1]^T
```

Three ranges. Only the third needs odometry.

### Range 1 — same camera frame (tabletop reach, no VO)

YOLOE gives a box. Depth gives metres at those pixels. Unproject object and fingertip through the **same** depth map, the **same** `frame_id`, and the **same** intrinsics.

```
if hand.frame_id != target.frame_id:
    # not the same camera frame — do not subtract
    if pose.valid and hand.pose_epoch == target.pose_epoch:
        p_target_cam = T_cam_from_world · target.xyz_world
        d = |hand.xyz_cam − p_target_cam|   # hand must also be this frame
    else:
        hold last d (EMA); do not invent a new metre
else:
    d = |hand.xyz_cam − target.xyz_cam|
```

No world frame required when `frame_id`s match. VO can be garbage. This is why REACH can ship even if RETURN does not.

Chest rotation between a 3 Hz object update and a later hand update makes camera-frame subtraction wrong. That is why the `frame_id` check exists.

### Range 2 — object still in view (walk while looking, still no VO)

Target centroid is already `p_cam` from the latest LIVE bundle. Spoken walk cue:

- range = `|p_cam|`
- left/right = `atan2(X, Z)`
- up/down = `atan2(−Y, hypot(X, Z))` (Y is down)

“Bottle. About four metres, a little left.” Repeat every ~3 s from a **LIVE** measurement. If the box is gone (HOLD/LOST), do not keep saying four metres.

### Range 3 — object left the view, or RETURN (needs world)

When we last saw the object we stored `p_world` and `pose_epoch`. Current pose is `T_world_from_cam`.

```
p_cam = T_cam_from_world · p_world
```

Then the same bearing math as range 2. If `pose.valid` is false or `pose_epoch` mismatches, we cannot point at a memory behind the wearer. Speak “I cannot retrace without a path.” We can still home to anything that re-enters the camera (back to ranges 1–2).

Contract for VO: a 5–10 m aisle with one turn, not a floor of the building. Textureless walls and fast head turns will break it; then fall back to ranges 1–2. Do not invent motion.

## 8. How odometry works

Not SLAM. Not loop closure. Not relocalization.

Need: one metric chain so a point stored ten seconds ago can be aimed at after a turn.

Method: **RGB-D visual odometry with OpenCV core only** (`features2d` + `calib3d`).

Keyframe `K` stores: small gray image, depth mapped onto that gray grid via the depth affine, `T_world_from_K`. First successful keyframe is the world origin (`T = I`, `pose_epoch` current).

New frame `F`:

1. ORB on a downscaled gray (~320×240) of `CAM_W×CAM_H`.
2. Match to `K` (Lowe ratio).
3. Each match: 3D in `K` by inverse-mapping the ORB pixel to full-frame then through the depth affine; 2D in `F` in the same ORB scale. Reject matches with invalid depth.
4. `solvePnPRansac` on 3D-in-K / 2D-in-F. OpenCV `rvec,tvec` here is `T_F_from_K` (points expressed in K, observed in camera F).
5. `T_world_from_F = T_world_from_K · inverse(T_F_from_K)`.
6. Too few inliers or huge reprojection error → `pose.valid = 0`. Keep last pose, age it. Do not invent motion.
7. New keyframe if we moved ≳ 10 cm or ≳ 15°.

Every ~0.4 s, if pose is valid and we moved ≳ 5 cm, append `T_world_from_cam` at `crumbs[(crumb_i++) % 512]`, `crumb_n = min(crumb_n+1, 512)`.

IMU is optional sugar for WALK yaw. It does not replace VO. If the kit has none, skip it.

## 9. How we label

Not a vector DB. Not CLIP. Not a live text encoder on the Pi.

Before Saturday, on a laptop:

1. Choose the nouns for the judging space (up to 64; 6 baked today). Locked demo list (edit only if the venue changes): `bottle`, `can`, `keys`, `phone`, `box`, `mouse`. Runtime names are `models/labels.txt`.

   Some names are **generic scene nouns**, not capabilities. `wall`, `floor`, `stairs`, `elevator`, `sign`, `window`, `door` exist so a wearer can ask for one by name and get a homing target. They are **not** safety features: a box labelled `stairs` is a named flat target, never a step, drop-off, or obstacle warning. That matches the pitch line above — Beacon does not detect stairs, traffic, or obstacles — and no demo script may imply otherwise. Wider vocabularies also trade confidence per class; demo objects (`keys`, `keychain`, `bottle`) are validated by their own run, not by these labels detecting at all.
2. Bake those prompts into YOLOE-26n. Save prompt embeddings. Export **static ONNX** at 320 px, **detect-only** if the exporter allows. The MobileCLIP encoder never ships.
3. Ship the ONNX file plus a `labels.txt` that is the only runtime vocabulary.

Each percept cycle writes `{id, name, xyz_cam, xyz_world, last_seen, frame_id, in_latest_boxes, conf}` as in section 5.

Query path, off the tick loop:

1. `whisper.cpp` → text.
2. Table returns a **job plus a candidate set**, not a single name.
3. `guided` reads `objects[].name` and binds the first stored hit in candidate order, skipping rows older than 1.5 s for a **new** bind (session list may still keep them). If two hits, pick nearest in cam (LIVE) else nearest in world if `pose.valid`.
4. If no candidate is in `objects[]`, `guided` plays “I have not seen that” (`NACK_UNSEEN`). Do not pick a class outside the candidate set.
5. llama.cpp runs only if the table misses. Prompt includes the seen names. Still may only pick from baked names. Abstain → “I cannot help with that” (`NACK_CANT`).

Worked binds:

- “Where are my keys” → `FIND`, candidates `keys`, `keychain` → bind stored `keys`
- “Where can I refill water” → `GO`, candidates `fountain`, `dispenser`, `sink`, `bottle` → bind whatever of those is stored
- “Take me back” → `RETURN`
- “Stop” → `STOP`

**Sunday 30 s lock:** the refill prop is a water bottle YOLOE will label `bottle`. Rehearse “where can I refill water” → bind `bottle`. Do not require a fountain in the hall.

Synonym table (fast path, before the LLM):

| Spoken fragments | Job | Candidate stored names |
|---|---|---|
| keys, keychain, key | FIND | `keys`, `keychain` |
| cup, mug | FIND | `cup`, `mug` |
| bottle | FIND | `bottle` |
| refill, water, drink, fountain, sink | GO | `fountain`, `dispenser`, `sink`, `bottle` |
| phone, mobile | FIND | `phone` |
| laptop, computer | FIND | `laptop` |
| keyboard | FIND | `keyboard` |
| mouse | FIND | `mouse` |
| headphones, headset, earbuds | FIND | `headphones` |
| charger | FIND | `charger` |
| badge, lanyard | FIND | `badge`, `lanyard` |
| wallet | FIND | `wallet` |
| glasses | FIND | `glasses` |
| pizza, food | FIND | `pizza` |
| can | FIND | `can` |
| jacket, coat | FIND | `jacket` |
| cable, cord | FIND | `cable` |
| shoes | FIND | `shoes` |
| whiteboard | FIND | `whiteboard` |
| back, retrace, return | RETURN | (none) |
| stop, cancel, quit | STOP | (none) |
| again, repeat, say that | REPEAT | (none) |
| not that, wrong one, other one | REJECT | (none) |

## 10. How we guide

Two laws. Mixing them is a product bug. Duck WALK audio the moment REACH enters.

### WALK (object beyond arm’s reach, or RETURN crumbs)

Spoken instruction only. `guided` fills a template from LIVE `WorldState`:

> “Keys. About two metres ahead, a little left.”

Pre-rendered clips concatenated (numbers 0–9, “metre(s)”, “ahead”, “left”, “right”, “up”, “down”, “I lost the target”, “stopping”, “I have not seen that”, “I cannot retrace without a path”, “I did not catch that”, “I cannot help with that”). Optional llama.cpp may paraphrase **after** the numbers are filled; if it is late, play the template. Repeat ~every 3 s, not every frame. Keep a copy of the last filled template for `REPEAT`. If no hand and `|p_cam|` ≲ 0.6 m, **faster repeats, still no ticks** (honor the reach lock). Treat a MediaPipe miss at tabletop as a blocking chest-mount test (section 16), not a Sunday surprise.

RETURN: play `crumbs` **backwards** as walk waypoints using `crumb_i` / `crumb_n`. Pop when the wearer is within ~0.6 m of the current crumb. When the named object is re-detected within ~3 m, drop crumbs and use the live track. If `pose.valid` is false, refuse: “I cannot retrace without a path.”

WALK ticks from the Nov 20 design are **removed**. Walking is speech so a cane hand is not fighting beeps.

### REACH (ticks only)

Enter REACH when all of:

- `mode == LIVE`
- `hand.conf` above threshold
- `|d| ≤ 0.50 m` for 3 consecutive synthesizer frames

Exit REACH when `|d| ≥ 0.70 m` or `mode != LIVE` or hand lost. Hysteresis is on the law, not only on the tick interval.

This is the **only** time ticks run.

- `d` from section 7 Range 1 (`frame_id` check).
- Tick interval interpolates from ~800 ms at 0.6 m to ~80 ms at 0.15 m.
- Continuous tone below ~0.15 m.
- Stereo pan from the lateral component of `(target − hand)` in camera frame.
- 200 ms EMA of `d` so depth noise does not chatter.
- If the hand is close in range but far off-axis, that is not hot. Pan hard toward the target. Tick amplitude scales with `max(0.25, cos(theta))` for `theta` the angle between camera +Z and the vector to target. Never go silent while REACH is live; losing the sound off-axis was the main failure in the 12-person BLV hand-steering study.

If a hand is visible but still outside the enter threshold, stay on WALK speech. Do not start ticks across the room.

HOLD while already in REACH: keep darker/slower ticks on last `d` up to 1.5 s, then LOST. Do not start REACH from HOLD (prevents phantom ticks after a turn).

### STOP / LOST / NACK / REPEAT / REJECT

Unique cue, not a faster tick. Spoken: “stopping”, “I lost the target”, “I did not catch that”, “I have not seen that”, or “I cannot help with that.” `guided` plays all of these.

`REPEAT`: replay the last filled WALK template or last NACK clip. Do not re-run whisper or llama. If nothing has been spoken yet, play “I have not seen that.”

`REJECT`: drop the current `target` id. Try the next unused name in `intent.candidates` that is still in `objects[]` and younger than 1.5 s. If none remain, play “I have not seen that” and clear the bind. Do not silently switch class outside the candidate set.

Sunday: after a successful home, `slay percept`. Ticks or last speech HOLD, then LOST. Cover-lens is the same path. Never keep a live distance while the camera is dark.

If `guided` itself dies, piezo goes continuous fault.

## 11. Error handling

| Failure | What the wearer hears | What must not happen |
|---|---|---|
| `percept` late, killed, or covered lens | HOLD then LOST; no metres | Guessed distance; silence |
| `voiced` late or dead | Keyword fallback or “I did not catch that”; ticks/speech already running continue | `guided` blocked; `voiced` writing USB audio |
| YOLOE miss / unknown name | “I have not seen that” | Homing to a class outside the candidate set |
| Depth scale bad (>30% vs tape on 1 m table) | Direction from box centre still allowed; **do not speak metres** until rechecked. Optional ground-plane fallback (camera height + floor homography) for WALK distances only | Speaking unchecked metres; using ground-plane for REACH `d` |
| `pose.valid = 0` | Ranges 1–2 still work. RETURN refused | Invented heading to a memory behind the wearer |
| USB audio gone | Piezo still ticks / faults | Silent `guided` |
| `guided` dead | Continuous piezo fault | Silence as the failure mode |
| CamAPI cannot lock focus | Tape-check two distances; if scale moves, mute metres | Calibrating then autofocusing mid-demo |

Ground-plane fallback is a compile-time switch after the tape-measure test, not a second product. Never use it for REACH `d`.

## 12. Demo script (30 seconds)

Table in front of judges. Untagged keys (or a high-contrast keychain that YOLOE labels `keys`) and a **bottle** (the refill prop) on the table.

**Required**

1. Wearer: “Where are my keys?” Device speaks a short LIVE bearing filled from sensors. Hand enters frame; ticks speed up; continuous tone at the keys.
2. Same table, bottle still in view: “Where can I refill water?” Binds `bottle`. Spoken WALK cue. Optional short REACH if they grab it.
3. On a laptop SSH: `slay percept`. Ticks or last speech HOLD, then LOST. Supervisor restarts `percept`. Cover the lens: same LOST, no guessed metres.

**Optional VO appendix** (only if Saturday p95 pose exists on a 5–10 m aisle with one turn): walk past the bottle so it leaves the view, ask again, then “take me back.” If that number does not exist, this appendix is absent. Do not show a breadcrumb log and call RETURN implemented.

Never skip step 3.

Line to say:

> Beacon homes you to a named item you have already seen this session. It is a supplement to a cane, not a replacement, and it does not detect stairs or obstacles. A late or wrong beep can put a hand on the wrong object. AI proposes the target. A high-priority QNX thread on core 0 disposes the sound. We kill the detector; the beeps keep going, then a lost cue, never a guessed distance. Sighted team, not yet tested with BLV wearers.

Named `oss.qnx.com` modules: `whisper.cpp`, `onnxruntime`, `tflite-runtime` / `mediapipe`. Camera via Sensor Framework. Isolation via processes, FIFO priorities, runmasks, seqlocked shm, and a supervisor, because QNX 8.0 has no APS. The kill in step 3 is the QNX beat; without it this is a CV demo.

Do not demo a floor drop. Do not inventory the room. Do not call RETURN indoor navigation.

## 13. Weekend build order

Geometry order. Do not skip ahead.

1. `supervisor` + `camd` + `guided` with a fake camera-frame target and piezo (section 5.1). Prove 60 Hz ticks while a busy-loop hogs cores 1–3. Capture Profiler + 16 ms miss count. If this is not obviously “QNX” vs Linux, stop adding models.
2. Probe loaner: lock `CAM_W×CAM_H`, frametype, unit number. Chessboard calibrate at that resolution. **Focus-lock gate.** Tape-measure depth on a 1 m table.
3. Depth + MediaPipe hands in `percept` → real REACH on a cup. **No VO. No YOLOE.** Hard gate: synthesizer 16 ms p95 under the cores 1–3 hog; chest-tabletop hand hit rate usable for the grab. If hands fail, ship WALK speech only.
4. YOLOE baked detect-only ONNX + whisper + table → FIND while the object stays in view. **No VO.** Speak metres only if tape-check passed. Combined vision p50/p95 on the loaner with `guided` live.
5. `slay percept` → HOLD → LOST.
6. ORB+PnP; only then store `p_world`, RETURN, and off-camera “bottle I walked past.”
7. Stretch only: prompt-free YOLOE-26n, llama.cpp paraphrase, IMU yaw, Align (bottle under a pitcher), second camera.

(1)–(5) plus spoken WALK while looking at the thing is the prize-shaped accessibility demo. (6) is what the fountain-behind-you story needs. If VO misses Saturday, drop RETURN and off-camera ask-the-room from the 30 s script. Keep the session store as “objects currently or recently in view.” Do not fake world pose.

## 14. What would make this not feasible

| If this is broken | What still works | What dies |
|---|---|---|
| VO / pose | Tabletop REACH, FIND while looking at it | Memory behind you, RETURN |
| YOLOE ONNX on QNX | Nothing labeled | All FIND/GO |
| Depth scale | Direction (box centre in image) | Spoken metres, tick distance |
| Hands | Walk speech | Reach ticks |
| llama.cpp | Keyword / synonym table | Odd phrasing not in the table |

Saturday detector gate: on QNX ORT with camera, depth, hands, and the 60 Hz audio thread running, record p50/p95 of the **combined** percept cycle (not YOLO and depth as if parallel) over 200 frames and labels on 10 held-up demo objects. Ship baked-prompt YOLOE if p95 still leaves `guided` inside 16 ms. Do not decide from Linux FPS claims.

## 15. Testing

Must exist before Sunday:

- 60 s guidance wakeup log with the full stack running (scheduled vs actual, observation age).
- Same reach with busy-loop load on cores 1–3: worst wakeup lateness, missed 16 ms deadlines, System Profiler trace.
- Freeze `percept` mid-reach: LOST plays, no metres, piezo still alive. After restart, first resumed cue matches a **new** placement (judge moved the object). Ghost `xyz` from the previous `pose_epoch` must not win “nearest.”
- Ten shuffled key/cup placements: miss rate, wrong-side pan, time-to-tone.
- Tape-measure vs spoken metres at 0.5 m, 1 m, 2 m. If error > 30% at 1 m, disable spoken metres.
- Chest-tabletop MediaPipe: hand entering from below actually produces landmark 8.
- Synonym table against the **actual** stored label (`water` → `bottle` on the judging table).
- REPEAT replays the last cue with no extra inference. REJECT skips a wrong bind and does not pick a class outside the candidate set.
- If VO is in the script: three L-shaped returns; report endpoint error. If VO is out of the script, do not claim it.

Only claim what was measured. If only software timestamps exist for LOST, label it “time to queue LOST.”

## 16. Hardware bill

Required: Pi 5 8 GB, QNX 8.0, official PSU, active cooler, Camera Module 3 on CAM/DISP 0, USB audio (mic + at least one ear of playback), GPIO piezo, chest strap or lanyard so the camera sees a tabletop and a hand entering from below.

Prefer single-ear or bone conduction so ambient sound stays available. Two-ear closed USB is acceptable for the loaner demo; do not pitch it as the right everyday form factor. Guidance never goes on the cane hand (no wrist haptic).

Optional: BNO055 or ICM-20948, push-to-talk GPIO, second Camera Module 3 (not v1), Hailo-8 (do not plan the demo on it).

## 17. Left to the builder (not product forks)

- Exact C structs and pulse codes. Shm names (`/beacon_frames`, `/beacon_depth`, `/beacon_world`) are suggestions; the writer/seq split is not.
- Tick waveform (square vs short sine bursts) and piezo vs USB mixing.
- Camera unit number and frametype after probing the loaner — then freeze `CAM_W×CAM_H`.
- Whether whisper tiny.en survives the hall; bump to base.en only if FIND misfires.
- Final noun list after walking the judging space (6 baked today; `models/labels.txt` is authoritative).
- Tape-measure calibration; enable ground-plane fallback if 1 m table error > 30% (WALK only).
- Startup snippets so the stack comes up on boot.

## 18. Changes from the Nov 20 notes

| Old | Now |
|---|---|
| AprilTag fob as “my keys” | No physical tags |
| YOLO11n COCO + paper-labeled fountain bottle | YOLOE-26n baked 6 prompts (bottle, can, keys, phone, box, mouse); session `objects[]` is the map |
| CLIP / vector DB as a later idea | Explicitly out of v1 |
| Slot parser only | Table first (candidate set), then tiny llama.cpp on miss |
| WALK used heading ticks | WALK is spoken instruction; ticks are REACH only |
| Fountain navigation was pitch, not table | Ask-the-room is in-view in the 30 s script; off-camera needs VO |
| Build plan lanes assumed a tag | Lanes stay A–D. Lane B owns YOLOE export + calibration, not AprilTags. Lane B also owns MediaPipe (in `percept`). Lane A `guided` is a synthesizer: no models |
| Hands + USB writes on the 16 ms thread | Hands in `percept`; USB audio off-thread |
| LIVE if age < 300 ms | LIVE if the latest percept bundle still contains the name, capped by `max(1.0 s, 2×p95)` |
| One seq over all of WorldState | Per-writer seq; `/beacon_depth` exists |
| “Say RETURN is implemented” from a log | Forbidden |
| USB two-ear headset as the product | Loaner fallback; prefer one ear open; do not claim the form factor is right |
| Off-axis ticks go silent | Amplitude floor ~0.25 while REACH is live |
| STOP only | REPEAT and REJECT are first-class |
| Implied BLV testing | Pitch: sighted hackathon prototype |
| Camera feed never leaves the Pi | Optional `telemd` JSON + JPEG to a local laptop for team monitoring; kill `telemd` and pixels stay; never cloud |
| Nov 20 plan as a second product doc | File removed from the repo. Ops live in `docs/team-plan.md` |

## 19. References

- Neighbour design (background): `/home/nate/Projects/hackwestern13/docs/beacon-design.md`
- QNX prize research: `/home/nate/Projects/hackwestern13/docs/QNX-research.md`
- Team ops plan: `docs/team-plan.md`
- Accessibility research (this revision): `docs/beacon-accessibility-research.md`
- Open-vocab model brief: `docs/beacon-open-vocab-pi-models.md`
- Spec review (BLOCK, 2026-11-21): `docs/beacon-spec-review.md`
- QNX 8.0 APS: not supported — https://www.qnx.com/developers/docs/8.0/com.qnx.doc.ide.userguide/topic/APS_view.html
- QNX AI Camera App (Sensor Framework + TFLite): https://gitlab.com/qnx/projects/ai-camera-app
- QNX hand-track workshop: https://github.com/qnx/QNX-AI-workshop
- Henomaly process split + ORT on this Pi: https://devpost.com/software/holy-crap
- Ultralytics YOLOE: https://docs.ultralytics.com/models/yoloe
- Depth Anything V2 metric indoor small: https://huggingface.co/depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf
- QNX Physical AI ports: https://qnx.software/en/blog/2026/how-qnx-gives-developers-the-building-blocks-for-physical-ai

## 20. Reviewer patches applied

Adversarial review (`/tmp/beacon-spec-review.md`) verdict was **BLOCK**. Product locks kept. Contract holes closed in this revision:

- P0 LIVE/HOLD vs capture-time aging
- P0 depth shm, letterbox inverses, `frame_id` before REACH subtract
- P1 per-writer seq, `crumb_i`/`crumb_n`, `pose_epoch`, single target author (`guided`)
- P1 `guided` is a synthesizer; MediaPipe in `percept`; 60 Hz ≠ 60 unique 3D samples
- P1 sequential percept budget; detect-only YOLOE; llama on table miss only
- P1 REACH hysteresis 0.50 / 0.70 m; no ticks without a LIVE hand
- P1 candidate-set bind so “refill water” hits stored `bottle`
- P1 30 s script = keys + in-view bottle + LOST; RETURN not faked
- P1 Nov 20 plan banner-superseded
- P2 LRU objects, NACK audio through `guided`, CamAPI focus-lock as step-2 gate, PnP convention
- Accessibility framing (2026-11-21): one-line job, pitch language, REPEAT/REJECT, off-axis tick floor, open-ear preference, prototype disclaimer, floor drops out of Sunday
- Reconcile with origin/main (2026-11-21): keep teammate skeleton and `docs/team-plan.md`; local spec wins; `telemd` JPEG is local-network monitoring only

## 21. Loaner bring-up (QNX image)

Do this before product code. None of it belongs in `/boot/onboot`.

1. First boot: do not interrupt QSTI updates. Hostname `qnxpi<n>.local`, SSH `qnxuser`. Change the default VNC password.
2. Confirm 8 GB, active cooler, `/dev/thermal` (or the node this image uses).
3. Install `onnxruntime`, `opencv`, `mediapipe` or `tflite-runtime`, `whisper.cpp` from `oss.qnx.com`. Write the exact package versions into the bring-up log.
4. Camera: read `sensor_rpi5.conf` vs `post_startup.sh`. Grab one uncompressed frame with the QNX AI Camera App or a 30-line CamAPI probe. Record unit, `W×H`, frametype, whether focus can be locked.
5. USB headset: playback a WAV, record 2 s. Confirm no 3.5 mm path.
6. GPIO: blink a pin from the QNX rpi_gpio sample; then the piezo.
7. Scheduler skeleton: `supervisor` spawns a FIFO 58 dummy `guided` on core 0 and three `while(1)` hogs on 1–3. Ticks stay inside 16 ms. Dump `pidin` so runmasks are visible.
8. Only then start section 13 step 2 (calibrate).

`sd-stage/` in this working tree is local image staging (Wi-Fi, `onboot`). It is **not** in git. It contains network secrets. Copy patterns from it (no pipes in `onboot`, install `wpa_supplicant.conf` onto `/data` before `start_net.sh`) but do not commit it.
