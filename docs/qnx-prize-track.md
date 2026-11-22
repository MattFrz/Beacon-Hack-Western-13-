# QNX prize track: what they want, and how we score

Date: 2026-11-21 (local, Saturday evening; about nine hours to the 8 am submission. `pi-bringup.md` rows are stamped UTC)
Status: judging source of truth for the Hack Western 13 **Best Use of QNX** track. It says what the sponsor asks for, the rubric that follows from their own words, and our audit against it with dated evidence.
Authority: `docs/nathans-revision.md` stays the product, geometry and mechanism source of truth. If this file disagrees with it on what we build, the revision wins. This file only decides what we say to judges, what we must measure, and what we may not claim.
Not committed with the repo: the workshop transcript and the prize research notes live outside this tree (see Sources). Everything needed to use this file is quoted or summarised below.

---

## 1. The prize, as published

> **Best Use of QNX.** 3 winners. Prizes: $1,000 for the winning team and $250 each for two runners-up.
>
> Build an embedded system that uses AI. Your project must run on QNX OS and use at least one open-source AI module from QNX. Judges will look for a use case where real-time performance or reliability matters, a creative use of AI, and a demo running on embedded hardware. QNX has loaner Raspberry Pi 5s preloaded with QNX.

Two sponsors publish the criteria behind that text in more detail, and both are consistent with it.

**Hack the North 2026 (same sponsor track, criteria published):** hard requirements are QNX OS plus one open-source AI module from `oss.qnx.com`; judging asks whether it is a "cannot-fail" embedded application, whether it needs real-time or reliability, whether AI is used in an interesting or creative way, and whether it runs on embedded hardware rather than in the cloud.

**CMU Hackberry Pi:** creativity/originality, functionality ("does it work?"), use of the QNX Developer Desktop, embedded market alignment, use of technical embedded-development concepts.

Read together, the prize is four hard gates and a mission-critical story. It is not an AI-app prize that happens to allow an RTOS.

## 2. What the sponsor said out loud

From the Hack Western 13 QNX workshop (machine transcript, 2026-11-21). Typos and mis-hearings of "QNX" are cleaned up; everything else is their framing, not ours.

1. **Mixed criticality is the thesis.** "Our system basically can handle things that can fail. We're not too concerned about them failing, but also those things are not going to bring down the critical things that cannot fail... like collision detection. The example I give is airbags deployed."
   *For us:* one capability that may die and one that must not, in the same product, with the boundary demonstrable.
2. **Determinism is measured, and speed is not determinism.** "The value of a real time operating system is both coming up with the correct calculation, but also being able to guarantee the time... we measure in microseconds." Also: "we can still execute threads in [priority]", and real time is "completely unrelated" to IPC overhead because a higher-priority thread can always cut in.
   *For us:* never argue from frames per second. Argue deadlines, priorities, and preemption.
3. **Reliability is chosen over speed on purpose.** Monolithic kernels "prioritize speed over reliability, whereas we prioritize reliability over speed", with the cost being message-passing overhead "which is less of an issue now with modern chips".
4. **Patch and restart without rebooting** is their flagship customer story: "with the atomic energy [Bruce Power, AECL], one of the things that power plants rely on is our ability to upgrade systems without having to shut the operating system down", and "we can update those things or reset them without resetting the whole operating system".
   *For us:* killing the perception process and continuing is this story at hackathon scale. Say it in those terms.
5. **A microkernel buys a smaller attack surface.** The slot-machine story: a USB port was exposed, and removing the USB stack from a monolithic kernel is "an exercise of removing something" whereas with QNX "you would manually have to add that". "The benefit of having a microkernel is you don't have to include things if you don't need them."
6. **Physical AI is where they are pushing.** "When AI models are interacting with the physical space." Named domains: automotive and collision detection, medical and surgical robotics (a Quebec company), rail signalling (UK railway), traffic systems for smart cities, power plants (Bruce Power, AECL), casinos and slot machines ("deterministic timing for sure for their outcomes"), and NVIDIA robotics. Also: "you're going to find us in any industry that's kind of in a cannot-fail situation."
7. **Their own APIs are the tell of real QNX work.** "The camera, for example, if anyone's using a camera, you'll have to interact with our sensor frame link, which is our custom camera kind of implementation... and any display... that's all custom from QNX. That's our screen software." Then: "one thing that Claude might be hiding from you is you probably have [hit this]."
   *For us:* the Sensor Framework grabber is the single most persuasive QNX artifact we own, because it is their API and it does not exist on Linux.

Also from the talk, useful context rather than criteria: QNX is POSIX-compliant and Unix-like but "not a Linux distribution" (it predates Linux by about ten years); the kernel handles scheduling and is preemptible, only the scheduler cannot be interrupted; the scheduler runs the highest-priority longest-waiting thread; multi-core threads can be assigned to core clusters; free non-commercial licensing through QNX Everywhere, a Discord, code labs, and a free training portal. None of that is scored. All of it is available to us for a question.

## 3. The rubric

One reviewer's reading of the sources above. Weights are ours; the gates are theirs.

### 3.1 Gates: miss one and the track is over

| Gate | What counts as passing | How we prove it live |
|---|---|---|
| **G1 runs on QNX OS** | The loaner Pi 5 image, real processes, not a laptop or a VM standing in | `uname -a` on the device in the demo, and every process in the loop visible in `pidin` |
| **G2 one open-source AI module from QNX** | A package from `oss.qnx.com` / `repo.oss.qnx.com` in the product path | name and version on the slide, plus the library file on the device |
| **G3 AI runs on the device** | Inference executes on the Pi during the demo | a percept log line with per-frame timings, no network egress |
| **G4 demo on embedded hardware** | Sensing and actuation on the Pi | camera on the Pi, sound out of the Pi, hand in front of the Pi |

### 3.2 Scored: the mission-critical dimensions

| # | Dimension | Weight | The judge's question | Evidence they will accept |
|---|---|---|---|---|
| S1 | Cannot-fail boundary | 3 | "Which piece may fail, which must not, and what happens when the first one dies?" | a named killable process, a named critical process, and a show of the second surviving |
| S2 | Real-time necessity | 3 | "Why does this need determinism rather than a fast computer?" | a deadline tied to a human consequence, in milliseconds, not a frame rate |
| S3 | Measurement | 2 | "Prove the isolation under load." | miss count and p95 lateness with CPU hogs, `pidin ar` runmasks, a trace |
| S4 | Fault injection, live | 3 | "Do it now." | `slay <process>` on stage, the wearer-facing cue degrading honestly, then recovery |
| S5 | AI under constraint | 2 | "What stops the model from being wrong out loud?" | AI proposes, deterministic logic disposes, an explicit refuse case |
| S6 | QNX-native mechanism | 2 | "What did QNX buy you that Linux would not?" | process split, priorities, runmasks, pulses, seqlocked shm, Sensor Framework |
| S7 | Legible demo | 2 | "Can I see cause and effect in 30 seconds?" | one physical action, one audible reaction, one failure |
| S8 | Market alignment | 1 | "Does this map to a vertical QNX sells into?" | the words physical AI, industrial, medical, accessibility, autonomy |

### 3.3 Traps

Each of these loses the track on its own, no matter how good the AI is.

| Trap | How we could fall into it |
|---|---|
| Cloud inference, Pi as a prop | We are clean: audio and inference are local. Do not add a cloud LLM for polish. |
| Dashboard as the product | Show the laptop dashboard only as a read-only monitor, and say so before a judge asks |
| "We installed QNX" with no mechanism | Never describe the stack without naming processes, priorities, and the supervisor |
| Unvalidated safety claims | We do not detect obstacles, stairs, or traffic, and we say it first |
| Claiming APS | QNX 8.0 has no adaptive partitioning. The mechanism list is processes, priorities, runmasks, seqlock, supervisor |
| Implying BLV validation | Sighted hackathon team, no wearer testing yet, stated in the pitch |

## 4. Our audit

Scored 0 to 3 per dimension, 0 = not attempted, 1 = claimed, 2 = demonstrated once, 3 = demonstrated with numbers and a failure case. Scores are this reviewer's judgement, not a judge's.

### 4.1 What actually runs on the loaner

Hardware in hand, as of 2026-11-21: the loaner Pi 5, one Logitech C270 (camera plus microphone), one JBL Go 3 over an application-level BT bridge, and laptops. No buzzer, no transistor, no LED, no IMU, no range sensor. That single fact removes the piezo from every claim we make; see S1 and A2.

The design is five processes. Tonight's demo is four, and one of them is Python. State it this way and the mechanism claim survives contact.

| Process | Language | Scheduler claim | Reality on the loaner |
|---|---|---|---|
| `guided` | C | `SCHED_FIFO` 58, runmask `0x1` | as specified, `--create --metres`, 60 Hz loop, audio thread |
| `ingest` | C | `SCHED_RR` 20, runmask `0xe` | as specified, UDP record to `/beacon_world` |
| `beacon_grab` | C | none | Sensor Framework session on unit 5 (C270), MJPEG, newest-frame file |
| `live_probe.py` | Python | none | YOLOE + metric depth through ORT's C API by ctypes, one frame per cycle |
| `supervisor` | C | `SCHED_FIFO` 63, runmask `0x1` | rewritten and **verified on the loaner 2026-11-21**: creates the regions, spawns guided/ingest with scheduler attributes, 50 ms QNX pulse timer, heartbeat fault, backoff respawn. `kill -9 guided` gives `guided fault (no output channel)` then a respawn; 300 loops, 0 missed, p95 750 us while that ran |
| `telemd` | C | read-only | monitor only, on the laptop path |

### 4.2 Gates

| Gate | Result | Evidence |
|---|---|---|
| G1 QNX OS | **pass** | `uname -a` = QNX 8.0.0, build 2026/06/05, RaspberryPi5 aarch64le, 8128 MB (`pi-bringup.md`, 2026-11-21 13:51) |
| G2 QNX AI module | **pass** | `onnxruntime` 1.24.4 and `opencv` 4.12.0 from `repo.oss.qnx.com`; `python3-onnxruntime` ships `libonnxruntime.so` without the Python binding, so we call the ORT C API directly through a generated ctypes table (415 members, `percept/ort_capi.py`) |
| G3 AI on device | **pass** | YOLOE-26n 320 at 62 to 65 ms/frame warm, Depth Anything V2 metric indoor small at 456 to 483 ms on the Pi (`pi-bringup.md`, 2026-11-22 01:15) |
| G4 embedded hardware | **pass with caveat** | C270 through the QNX sensor service at 1280x720 MJPEG, BT audio to a JBL Go 3, live loop at about 1.3 fps of perception. The piezo, which the design calls the cannot-fail actuator, is still a counter in `guided/src/platform.c` |

### 4.3 Scored dimensions

| # | Score | Evidence we have | What is missing |
|---|---|---|---|
| S1 cannot-fail boundary | 3 | On the loaner: killing the relay mid-guidance gave "I lost the target" while `guided` held its deadline record (1800 loops, 0 missed) and never restarted; separately, killing `guided` under the supervisor produced a logged fault and a respawn in about 100 ms. Both directions of the boundary are now demonstrated | one audio path, so a dead speaker is silence; the script still kills the relay rather than the AI process |
| S2 real-time necessity | 1 | 16.67 ms deadline, `over_period` and p95 lateness measured with hogs on cores 1 to 3 | the pitch still leads with the tick rate. A QNX engineer will ask why a beep needs 16 ms and there is no answer in the script yet |
| S3 measurement | 3 | 1500 loops, 0 missed, worst 4.7 ms, p95 1.9 ms in the full-loop run; 2100 loops, p95 2.05 ms in the slay run; `pidin` shows `58f` / `40f` for guided and `22r` for ingest with `last_cpu=0` and `last_cpu=1`; `clock_getres` is 1 ms, so `over_period` is the number to quote | no System Profiler trace; no combined percept p50/p95 with `guided` unloaded vs loaded side by side; the Python producer is not pinned yet |
| S4 fault injection | 3 | `slay ingest` rehearsed (`device_slay_beat.sh`), and `kill -9 guided` rehearsed under the supervisor with a respawn; both on hardware | the demo must name the process that died, and the 30 s script should kill the perception producer rather than the relay |
| S5 AI under constraint | 2 | depth gate drops objects past `--max-depth 3.0` and says LOST rather than naming a target it cannot locate; HOLD/LOST from capture-time ages; no guessed metre when the target is lost | `guided` runs with `--metres` and the tape check has not been run (`pi-bringup.md`, 2026-11-22 02:00: depth-scale 0.25 is "an eyeball, not a calibration"). Speaking metres now is the one place we can be caught being wrong |
| S6 QNX-native mechanism | 3 | Sensor Framework grabber in C (`sensor_open`, `premap_buffers`, JPEG reassembly from a mapped pool); `SCHED_FIFO` 58 on core 0 and `last_cpu=0` measured; `ingest` logs `runmask 0x2 applied (kernel said it was 0xf)`; per-writer seqlock shm; `guided` never blocks on the model; supervisor verified on device | the Python producer is unpinned; `pidin -F %i` renders empty on this image, so the readback line is the only runmask evidence |
| S7 legible demo | 2 | 30 s script in revision §12, rehearsed pieces, dashboard, recorded replay samples | no single end-to-end rehearsal on hardware in the log, from button to tone to kill |
| S8 market alignment | 3 | accessibility homing framed as a cannot-fail assistive device | none, this one is strong |

Gates 4 of 4. Scored 19 of 24 after the loaner run. The remaining points are framing (S2) and rehearsal (S7), not features.

### 4.4 Sentences we can defend, and sentences we cannot

Defensible, each with evidence:

- "A perception process dies and the guidance process keeps its 16.67 ms deadline, then says it lost the target instead of inventing a distance." (Measured.)
- "A dead guidance process is restarted by a supervisor with a 50 ms heartbeat; measured on the loaner, fault to respawn about 100 ms." (Measured.)
- "The 60 Hz thread is pinned to core 0 and everything else is pinned off it, with the kernel's own readback in the log." (Measured; note the image only accepts single-CPU masks, so perception sits on one core, not three.)
- "Inference runs on the Pi through ONNX Runtime 1.24.4 from QNX's open-source repo, on a frame captured through QNX Sensor Framework." (Measured.)
- "The camera process is a C program against QNX's sensor API, which is why this did not run on the laptop." (Measured.)

Not defensible yet, do not say:

- "Perception is spread across cores 1 to 3" (this image rejects multi-bit runmasks; it is pinned to one core off core 0).
- "`pidin` shows the runmask" (that field renders empty here; use the process readback).
- "The piezo keeps beeping" (no buzzer exists; there is one audio path).
- "Two independent audio paths" (one BT path, one speaker).
- "We measure distance in metres accurately" (no tape check).
- "The wearer asks out loud" (no `voiced` in the shipped path; FIND arrives as a table entry or through `ingest --intent`).
- "Five processes" (four run tonight, plus the monitor).

## 5. Ranked work for what is left

Ordered by score per hour, with about nine hours to the 8 am submission. A1 and A2 close the two gaps a judge will probe first, in S1 and S6.

| # | Work | Owner | Done when |
|---|---|---|---|
| A1 | ~~Supervisor to spec~~ **done and verified on the loaner 2026-11-21**: builds with the device `cc`, spawns with scheduler attributes, 50 ms pulse timer, heartbeat fault, respawn; `pidin` shows 58f/40f/22r and `last_cpu` 0 and 1; `make test-beacon` green off-device | Matt | done. Keep the 30 s script pointing at the process that actually dies |
| A2 | ~~Piezo~~ **cancelled, no hardware**: drop the second-channel claim and use the BT audio service restart as the restart-without-reboot beat (`slay` the radio process, the script brings it back) | Matt, Munadir | the 30 s script no longer mentions a piezo, and the audio-service restart is rehearsed once |
| A3 | `pidin ar` with ORT live, saved to `pi-bringup.md`, showing no `percept` thread on CPU 0 | Nathan | the file is in the log and on the slide |
| A4 | Re-scope the real-time sentence: audio never blocks on inference, the cue never lies, a dead component restarts without a reboot. Tick rate becomes supporting evidence | Matt | the 30 s line no longer opens with 60 Hz |
| A5 | Rehearse killing the perception producer, not the relay, and say the process name out loud | Nathan | `device_slay_beat.sh` variant runs on hardware twice |
| A6 | Either run the tape check at 0.5/1/2 m or drop `--metres` for the demo | Nathan | number in the log, or metres gone from the spoken cue |
| A7 | Devpost structure: video first, failure second, mechanism list, installed package versions, honesty block | Matt | matches the section below |

Deliberately not on this list: whisper on device, llama remap, RETURN, off-camera ask-the-room, dashboard features. They are bonus bullets, not gates, and every one of them costs the two hours A1 and A2 need.

## 6. Thirty seconds, mapped

| Seconds | What happens | Earns | Line to say |
|---|---|---|---|
| 0 to 8 | "Where are my keys" entry, target binds, short spoken bearing from sensors | S7, S8 | "It homes to a named item seen this session, on the Pi." |
| 8 to 18 | Hand enters, ticks speed up, tone at the object | S7, S2 | "The cue comes from a 60 Hz thread on core 0. No model runs there." |
| 18 to 24 | `slay <perception>`: HOLD, then "I lost the target", no metre | S1, S3, S4 | "The AI is dead. The guidance process is not, and it refuses to guess." |
| 24 to 30 | Supervisor restarts the dead perception process; kill the BT audio service and it comes back on its own; the cue returns | S1, S6 | "QNX is why these are separate processes: the thing that can fail cannot take the thing that must not with it, and nothing here needs a reboot." |

Say once, early: sighted hackathon team, not BLV-tested, baked noun list, one camera, supplement to a cane, no obstacle or stair detection.

## 7. Devpost shape

1. 30 s video, the failure beat inside it, not described in text.
2. One paragraph of problem: a named item that moved forces a wait for whoever is nearby.
3. Mechanism list with numbers: processes, priorities, runmasks (`pidin ar`), seqlock shm, Sensor Framework, supervisor restart, and the measured 16.67 ms lateness under hogs.
4. Installed package names and versions from `oss.qnx.com`, including the ctypes detail, because it is a true and unusual thing.
5. Honesty block: sighted team, no BLV testing, 6 to 16 noun bake, tape-check status, capture path, what is replayed.
6. What we would test next with a wearer and an occupational therapist.

## 8. Questions only QNX can answer

Ask the mentors, since they are on site and the answers reorder the plan.

1. Is archive-extraction installation from `repo.oss.qnx.com` acceptable for the "module from QNX" criterion, or does the judge want the QDD package UI path specifically?
2. We call the ORT C API from Python through ctypes because the shipped `python3-onnxruntime` has no binding. Does that count as using their module, in their view?
3. Is there a supported way to get `SCHED_FIFO` above 63 on the loaner without root, or is staying at 58 the intended shape?
4. Do they want the trace (`tracelogger` / System Profiler) as an artifact, or is `pidin ar` plus the miss count enough?

## 9. Sources

- Prize description, Hack Western 13 (user-provided, quoted in full in section 1).
- QNX workshop, Hack Western 13, 2026-11-21: machine transcript (about 29 minutes). Quotes in section 2 are cleaned for ASR errors only.
- Prize research notes compiled 2026-11-21: Hack the North 2026 criteria and winner gallery, CMU Hackberry Pi judging criteria, `oss.qnx.com` catalog, five prior QNX-winning projects (Surgy, Combadge, MOGGIE, Praxis, EyeMelody) and what separated the winners from the honourable mentions.
- Measured evidence in this repo: `docs/pi-bringup.md` (bring-up log, dated rows), `docs/qnx-integration-plan.md` (gap table and plan of record), `docs/nathans-revision.md` §5.1 and §12 (mechanism and script), `supervisor/supervisor.c`, `guided/src/platform.c`, `include/beacon.h`.

Excluded from the graphify graph (`.graphifyignore`) because it is judging reference rather than code or product documentation.
