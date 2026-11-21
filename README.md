# Beacon

Chest-worn Raspberry Pi 5 on QNX 8.0 that homes you to a thing by sound. Say "where are my keys", walk on a short spoken bearing, then stereo ticks speed up as your hand reaches. Kill the detector and the ticks hold, then a lost cue, never a guessed metre. Vision, speech and guidance run on-device. Built at Hack Western 13.

- Design (source of truth): [`docs/nathans-revision.md`](docs/nathans-revision.md)
- Team plan (owners, schedule, hardware): [`docs/team-plan.md`](docs/team-plan.md)

## Layout

| Path | What | Owner |
| --- | --- | --- |
| [`include/beacon.h`](include/beacon.h) | Shared contract: shm layouts, seqs, `intent.kind`, pulse codes | Matt + Munadir |
| [`supervisor/`](supervisor/) | Spawn, runmasks, heartbeats, restarts, piezo fault | Matt |
| [`camd/`](camd/) | Sensor Framework into the frame ring | Nathan |
| [`guided/`](guided/) | 60 Hz synthesizer: mode, bind, laws, audio, piezo | Munadir |
| [`percept/`](percept/) | YOLOE, depth, hands, unproject, VO | Nathan |
| [`voiced/`](voiced/) | whisper.cpp, synonym table, optional llama.cpp | Munadir |
| [`telemd/`](telemd/) | Read-only telemetry to the laptop (optional) | Matt |
| [`laptop/bridge/`](laptop/bridge/) | UDP in, WebSocket out, JSONL recording | Zain |
| [`laptop/dashboard/`](laptop/dashboard/) | 3D dashboard (Vite + React + r3f) | Zain |
| [`laptop/samples/`](laptop/samples/) | Telemetry JSON format and samples | Matt + Zain |
| [`models/`](models/) | Model files (not committed) | Nathan |
| [`sounds/`](sounds/) | Pre-rendered speech clips | Matt |

## Workflow

- `main` holds the shared base. Work on a branch per owner or feature (`zain/dashboard`, `munadir/guided`, ...) and merge back through a PR.
- Changes to `include/beacon.h` or the telemetry format go through their owners, since every process builds against them.
- Never commit `sd-stage/` (it holds network secrets) or large model files.
