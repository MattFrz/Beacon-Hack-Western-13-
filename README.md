# Beacon

Beacon helps a person who is blind or has low vision find an item they have already seen in this session, such as keys, a phone, or a bottle. The wearer asks for the item and gets a short spoken bearing. They walk toward it. As they get close, stereo ticks speed up and pan toward the object, and a steady tone marks it.

The device is a chest-worn Raspberry Pi 5 running QNX 8.0. Camera capture, object detection, depth, guidance, and audio all run on the Pi. Nothing in the wearer's path goes to a server. A laptop can show telemetry, read-only.

Beacon supplements a cane. It does not detect obstacles, stairs, or traffic.

## Status

Built at Hack Western 13 by a sighted team. It has not been tested with blind or low-vision wearers. That testing is the next step.

Running on the loaner Pi 5:

- Live C270 frames through QNX's Sensor Framework.
- Object detection (YOLOE-26n) and metric depth (Depth Anything V2) through ONNX Runtime.
- The guidance loop, with speech and ticks to a Bluetooth speaker.
- A supervisor that restarts a killed child.

Not running yet, or limited:

- Hand tracking. The MediaPipe binding on this image fails, so the device does not track the hand. The reach cue has run on recorded input, not on live hand position.
- Microphone. The C270 microphone does not capture on this image. A FIND request arrives as a record, not as speech.
- Distance. The depth scale has not been checked against a tape measure on this camera. Until it is, the wearer should get direction and ticks, not a number.
- Vocabulary. Six baked nouns, listed in `models/labels.txt`.
- Killing the perception process live. Rehearsal is still open. The measured kill is the `ingest` process (see below).

## Why QNX

Perception and guidance run as separate processes at different priorities. Perception can fail. Guidance keeps running. If perception dies, guidance holds the last cue for a moment, then says it lost the target. It does not invent a distance.

| Process | Role | Scheduling on the loaner |
| --- | --- | --- |
| `supervisor` | Starts children with scheduler settings, watches a 50 ms heartbeat, restarts a dead child | `SCHED_FIFO` 63, core 0 |
| `guided` | 60 Hz guidance and audio. The only process that makes sound | `SCHED_FIFO` 58, core 0 |
| `ingest` | Reads perception records from UDP and writes shared memory | `SCHED_RR`, runmask `0x2` |
| `beacon_grab` | Camera frames through QNX's Sensor Framework | Not pinned |
| `live_probe.py` | Detection and depth through ONNX Runtime | Not pinned yet |

Processes share state through seqlocked, newest-wins shared memory. The audio thread never waits for a model.

Measured on the loaner:

- Full loop with real detection and depth on the Pi, fed a recorded clip: 1500 guidance periods at 16.67 ms, 0 missed. Worst lateness 4.7 ms, p95 1.9 ms.
- `ingest` killed during guidance: guidance said "I lost the target" and kept its deadline across 1800 loops with 0 missed. A new `ingest` brought the cue back without restarting `guided` (2100 loops, 0 missed, p95 2.05 ms).
- `guided` killed under the supervisor: the fault is logged and the process respawns in about 100 ms. No reboot.

This image accepts only single-CPU runmasks. Perception runs on one core, not spread across three. We report the readback the kernel returns, not the mask we asked for.

## AI on the device

- `onnxruntime` 1.24.4 and `opencv` 4.12.0, from QNX's open-source repository (`repo.oss.qnx.com`).
- YOLOE-26n, detect-only, with a baked noun list: 62 to 65 ms per frame warm at 320 px.
- Depth Anything V2 metric indoor small: 456 to 483 ms per frame.
- The image's `python3-onnxruntime` ships the shared library without a Python binding. `percept/ort_capi.py` calls the ONNX Runtime C API through ctypes, with 415 generated members.

## Running the demo scripts

The live demo (camera → detection → guidance → JBL, phone page as the mic) is one command on the Pi, from this checkout; see `docs/demo-runbook.md` for setup:

```
AUDIO=jbl sh run_live.sh bottle
```

Replay scripts, also on the Pi. The first is the full chain on a replayed clip:

```
sh ingest/tools/device_chain_demo.sh /tmp/replay.avi cup
```

The second kills `ingest` during guidance and brings it back:

```
sh ingest/tools/device_slay_beat.sh /tmp/long.avi cup
```

Perception must be warm before a FIND arrives. A FIND received while `objects[]` is empty gets one NACK and is not retried. The chain script handles the order.

## Layout

| Path | What | Owner |
| --- | --- | --- |
| [`include/beacon.h`](include/beacon.h) | Shared contract: shared-memory layouts, sequence numbers, `intent.kind`, pulse codes | Matt, Munadir |
| [`supervisor/`](supervisor/) | Spawn, runmasks, heartbeats, restarts | Matt |
| [`camd/`](camd/) | Sensor Framework capture into the frame ring | Nathan |
| [`guided/`](guided/) | 60 Hz synthesizer: mode, binding, laws, audio | Munadir |
| [`percept/`](percept/) | YOLOE, depth, hands, unprojection, visual odometry | Nathan |
| [`ingest/`](ingest/) | Perception records from UDP to `/beacon_world` | Nathan |
| [`voiced/`](voiced/) | whisper.cpp, synonym table, optional llama.cpp | Munadir |
| [`telemd/`](telemd/) | Read-only telemetry to the laptop (optional) | Matt |
| [`laptop/bridge/`](laptop/bridge/) | UDP in, WebSocket out, JSONL recording | Zain |
| [`laptop/dashboard/`](laptop/dashboard/) | 3D dashboard (Vite, React, react-three-fiber) | Zain |
| [`laptop/samples/`](laptop/samples/) | Telemetry format and samples | Matt, Zain |
| [`models/`](models/) | Model files. Only `labels.txt` is committed | Nathan |
| [`sounds/`](sounds/) | Pre-rendered speech clips | Matt |

## Documents

- Design source of truth: [`docs/nathans-revision.md`](docs/nathans-revision.md). If another file disagrees, the revision wins.
- QNX track audit, including claims we avoid: [`docs/qnx-prize-track.md`](docs/qnx-prize-track.md)
- Demo runbook: [`docs/demo-runbook.md`](docs/demo-runbook.md)
- Devpost text: [`docs/devpost.md`](docs/devpost.md)
- Team plan: [`docs/team-plan.md`](docs/team-plan.md)
- Accessibility research: [`docs/beacon-accessibility-research.md`](docs/beacon-accessibility-research.md)
- Pi bring-up log, with dated measurements: [`docs/pi-bringup.md`](docs/pi-bringup.md)
- Pi workflow: [`docs/pi-dev-workflow.md`](docs/pi-dev-workflow.md)
- QNX integration plan: [`docs/qnx-integration-plan.md`](docs/qnx-integration-plan.md)

## Workflow

- `main` holds the shared base. Work on a branch per owner or feature and merge through a pull request.
- Changes to `include/beacon.h` or the telemetry format go through their owners, because every process builds against them.
- Never commit `sd-stage/` (it holds network secrets) or large model files.
