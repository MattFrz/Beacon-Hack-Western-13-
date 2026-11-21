# Telemetry format (DRAFT, needs Matt's sign-off)

`telemd` sends to the laptop over UDP:

- **World state:** one JSON object per datagram at ~10 Hz, shaped like [`world.sample.json`](world.sample.json).
- **Video (optional, team monitoring):** a downscaled JPEG at ~5 fps on a separate UDP port, local network only. Kill `telemd` and the JPEG stops. Port numbers are not set yet. Dashboard 3D markers come from JSON even if JPEG is off.

`bridge` forwards both over WebSocket and writes one JSON object per line to a `.jsonl` file per session. Replay files use the same line format, so the dashboard can't tell live from replay.

## Field notes

Field names follow `include/beacon.h`, frozen from [`docs/nathans-revision.md`](../../docs/nathans-revision.md) §6. If the header renames a field, rename it here too.

| Field | Source | Notes |
| --- | --- | --- |
| `t_ns` and every `*_ns` | `CLOCK_MONOTONIC` on the Pi | Not wall time. JSON numbers are exact up to about 104 days of uptime. |
| `seq.*` | per-writer seqs | Always even (`telemd` skips torn reads). |
| `mode` | recomputed by `telemd` | `LIVE` / `HOLD` / `LOST`, using the same function as `guided`. Not stored in shm. |
| `law`, `cue`, `d_m` | recomputed by `telemd`, or published by `guided` | `law`: `STOP` / `LOST` / `REACH` / `WALK` / `RETURN` / `NONE`. `cue.caption` is display text for what the wearer hears. All three may be `null` if not available. |
| `intent.kind` | `voiced` | `NONE`, `FIND`, `GO`, `RETURN`, `STOP`, `REPEAT`, `REJECT`, `NACK_UNHEARD`, `NACK_UNSEEN`, `NACK_CANT`. REPEAT/REJECT are intents, not extra walk laws. |
| `target`, `hand` | `guided`, `percept` | `null` when unbound or not seen. |
| `xyz_cam` | camera frame | OpenCV: +X right, +Y down, +Z forward, metres. |
| `xyz_world` | session frame | Only meaningful when `pose.valid` and `pose_epoch` match. |
| `pose.T_world_from_cam` | `percept` VO | 4x4, row-major, 16 numbers. |
| `crumbs` | `percept` | Positions only (the translation of each crumb pose), oldest first. |
| `health.timing` | `guided` stats block | Optional. Only present if `guided` publishes it (team plan, timing panel). |
