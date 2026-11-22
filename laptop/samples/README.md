# Telemetry format (DRAFT, needs Matt's sign-off)

`telemd` sends both of these to **UDP port 5005** on the laptop running `bridge`, one message per datagram, local network only (never cloud):

- **World state:** one JSON object at ~10 Hz, shaped like [`world.sample.json`](world.sample.json).
- **Video (optional, team monitoring):** one downscaled JPEG at ~5 fps, under 60 KB so it fits in one datagram (~320 px wide is plenty). Kill `telemd` and the JPEG stops. Dashboard 3D markers come from JSON even if JPEG is off.

`bridge` tells them apart by the first bytes (a JPEG starts `FF D8`) and drops anything else. It forwards both to the dashboard over WebSocket and writes the world state, one JSON object per line, to a `.jsonl` file per session. The bridge never writes video to disk. Replay files (for example from Matt's generator) use the same line format, with `t_ns` setting the pace. Details: [`../bridge/`](../bridge/).

## Files

- [Video replay: 360 look-around](vid360-look-around.jsonl) — 21 s (`249` lines at ~12 Hz) built from the recorded clip `20261121_173217.mp4`: the six-noun YOLOE bake plus metric depth and the VO pass, replayed over UDP through `ingest` → `guided` → `telemd` on a private `BEACON_WORLD`, so `mode` / `law` / `cue` / `target` are what `guided` really decided. `telemd`'s v1 packet has no `objects` / `pose` / `crumbs` fields, so those are joined back from the same run's world stream by timestamp. What it exercises: `NONE` → `LIVE` → `HOLD` → `LOST`, a target that binds to `bottle` at ~2 s and then turns out of view, real VO pose (`pose.valid` true on 215 of 249 lines, two `T_world_from_cam` rotations included), crumbs, and objects named from the current vocabulary (`bottle`, `box`, `can`, `mouse`). `npm run replay:vid360`.

  The companion [`vid360-frames/`](vid360-frames/) directory holds 249 composite JPEGs (`000000.jpg`, one per replay line) written by `probe_to_world.py --frames-dir`. Each is the camera frame with the YOLO boxes on top and the depth map with the same box projected below, so the dashboard's video panel shows RGB + detections + depth together, in sync with the telemetry. They are committed because a replay is only useful to whoever is building the frontend; 3.5 MB in total.

  To rebuild: `probe_to_world.py --video <clip> --yolo models/yoloe26n_320.onnx --labels models/labels.txt --depth models/depth_anything_v2_metric_indoor_small.onnx --fov 55 --out world.jsonl`, `vo_probe.py --video <clip> --depth ... --depth-scale 0.25 --fov 55 --h-chest 1.4 --stride 1 --out vo.jsonl`, `merge_vo_world.py --world world.jsonl --vo vo.jsonl --out merged.jsonl --fps 29.5`, then replay `merged.jsonl` at its `t_ns` pace into `ingest --create --udp PORT` on a private world, with `guided`, `telemd` and the bridge attached.

  Two traps worth knowing: the stream's `t_ns` is relative, so rebase every timestamp onto a real `CLOCK_MONOTONIC` **at the moment you start pacing** (`guided` refuses a new bind when the row is ≥1.5 s old), and issue the FIND while a row for that object is still in `in_latest_boxes`, because a `NACK` is never retried.

- [Simulator demo replay](sim-reach-lost.jsonl) — 15 seconds recorded through `fakeworld lost`, `guided`, `telemd`, and the live bridge. Watch the hand approach the keys, tracking switch from LIVE to HOLD to LOST, and the keys reappear on the left. The caption shows the reach ticks and then the continuous tone after recovery. To loop the recording, run `npm run replay:sim` from `laptop/bridge` with the dashboard open.
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
