# Beacon

Chest-worn Raspberry Pi 5 on QNX 8.0 that homes a wearer who is blind or has low vision to a named item by sound. Say "where are my keys," walk on a short spoken bearing, then stereo ticks speed up as your hand reaches. Kill the detector and the ticks hold, then a lost cue, never a guessed metre. On-device, no tags, supplement to a cane. Built at Hack Western 13.

- Design (source of truth): [`docs/nathans-revision.md`](docs/nathans-revision.md). If another file in this repo disagrees with it, the revision wins.
- Team plan (owners, schedule, hardware): [`docs/team-plan.md`](docs/team-plan.md)
- Accessibility research: [`docs/beacon-accessibility-research.md`](docs/beacon-accessibility-research.md)
- Pi bring-up notes: [`docs/pi-dev-workflow.md`](docs/pi-dev-workflow.md)
- Pi bring-up log: [`docs/pi-bringup.md`](docs/pi-bringup.md)

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
| [`models/`](models/) | Model files; only `labels.txt` is committed | Nathan |
| [`sounds/`](sounds/) | Pre-rendered speech clips | Matt |

## Workflow

- `main` holds the shared base. Work on a branch per owner or feature (`zain/dashboard`, `munadir/guided`, ...) and merge back through a PR.
- Changes to `include/beacon.h` or the telemetry format go through their owners, since every process builds against them.
- Freeze `include/beacon.h` from **this** copy of `docs/nathans-revision.md` §6 (`intent.kind` includes `REPEAT` and `REJECT`). Do not freeze `CAM_W` / `CAM_H` from the C270.
- Never commit `sd-stage/` (it holds network secrets) or large model files.
