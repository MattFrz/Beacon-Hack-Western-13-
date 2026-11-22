# Telemetry format (DRAFT, needs Matt's sign-off)

`telemd` sends both of these to **UDP port 5005** on the laptop running `bridge`, one message per datagram, local network only (never cloud):

- **World state:** one JSON object at ~10 Hz, shaped like [`world.sample.json`](world.sample.json).
- **Video (optional, team monitoring):** one downscaled JPEG at ~5 fps, under 60 KB so it fits in one datagram (~320 px wide is plenty). Kill `telemd` and the JPEG stops. Dashboard 3D markers come from JSON even if JPEG is off.

`bridge` tells them apart by the first bytes (a JPEG starts `FF D8`) and drops anything else. It forwards both to the dashboard over WebSocket and writes the world state, one JSON object per line, to a `.jsonl` file per session. The bridge never writes video to disk. Replay files (for example from Matt's generator) use the same line format, with `t_ns` setting the pace. Details: [`../bridge/`](../bridge/).

## Files

- [Simulator demo replay](sim-reach-lost.jsonl) - 15 seconds recorded through `fakeworld lost`, `guided`, `telemd`, and the live bridge. Watch the hand approach the keys, tracking switch from LIVE to HOLD to LOST, and the keys reappear on the left. The caption shows the reach ticks and then the continuous tone after recovery. To loop the recording, run `npm run replay:sim` from `laptop/bridge` with the dashboard open.
- [`world.sample.json`](world.sample.json): one world-state message, mid-reach on the keys with a bottle in view.
- [`dev-reach.jsonl`](dev-reach.jsonl): a 9 s replay made by [`make-dev-reach.js`](make-dev-reach.js) from the sample: WALK cue, reach (ticks, then continuous tone), `slay percept` at 6 s, HOLD, LOST. A stopgap so the dashboard can be built without the Pi; Matt's generator and real recordings replace it. HOLD keeps the last objects faded (`in_latest_boxes: false`) with no frozen hand, while LOST clears them to an empty cloud (`objects: []`, no `d_m`).

## Field notes

Field names follow `include/beacon.h`, frozen from [`docs/nathans-revision.md`](../../docs/nathans-revision.md) §6. If the header renames a field, rename it here too.

| Field | Source | Notes |
| --- | --- | --- |
| `t_ns` and every `*_ns` | `CLOCK_MONOTONIC` on the Pi | Not wall time. JSON numbers are exact up to about 104 days of uptime. |
| `seq.*` | per-writer seqs | Always even (`telemd` skips torn reads). |
| `mode` | recomputed by `telemd` | `LIVE` / `HOLD` / `LOST`, using the same function as `guided`. Not stored in shm. |
| `law`, `cue`, `d_m` | recomputed by `telemd`, or published by `guided` | `law`: `STOP` / `LOST` / `REACH` / `WALK` / `RETURN` / `NONE`. `cue.caption` is display text for what the wearer hears. Instead of `caption`, `telemd` may send `cue.clip_ids` (guided's last spoken `enum beacon_clip` ids), which the dashboard turns into text. All three may be missing or `null`. |
| `intent.kind` | `voiced` | `NONE`, `FIND`, `GO`, `RETURN`, `STOP`, `REPEAT`, `REJECT`, `NACK_UNHEARD`, `NACK_UNSEEN`, `NACK_CANT`. REPEAT/REJECT are intents, not extra walk laws. |
| `target`, `hand` | `guided`, `percept` | `null` when unbound or not seen. |
| `xyz_cam` | camera frame | OpenCV: +X right, +Y down, +Z forward, metres. |
| `xyz_world` | session frame | Only meaningful when `pose.valid` and `pose_epoch` match. |
| `pose.T_world_from_cam` | `percept` VO | 4x4, row-major, 16 numbers. |
| `crumbs` | `percept` | Positions only (the translation of each crumb pose), oldest first. |
| `health.timing` | `guided` stats block | Optional. Only present if `guided` publishes it (team plan, timing panel). |
