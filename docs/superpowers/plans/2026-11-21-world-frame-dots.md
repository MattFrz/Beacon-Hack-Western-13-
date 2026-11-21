# World-frame 3D dots

Date: 2026-11-21
Owner: Nathan
Status: active plan

## Goal

Show the reconstructed session as a simple 3D dot map in the dashboard:

- named objects at `xyz_world`
- wearer at the camera pose
- optional crumb trail
- no meshes, no fake building map

Final target: the Pi computes perception, depth, pose, reconstruction, and guidance. The laptop only renders the dashboard.

Current reality: dashboard rendering runs on the laptop. YOLO/depth/hands currently run in the laptop probe because QNX runtime packages are missing. Odometry/3D reconstruction is not implemented yet. This plan is laptop-first so the geometry can be debugged before being ported to the Pi.

## Architecture

```text
laptop camera / C270 screenshot
  -> percept/tools/probe_frame.py
  -> percept/tools/probe_to_world.py
  -> JSONL in laptop/samples/world.sample.json shape
  -> laptop/bridge
  -> laptop/dashboard Scene world-frame dots
```

QNX `camd` and `percept-head` remain the later shm path. Do not freeze `CAM_W`, `CAM_H`, or frametype in `include/beacon.h`. Do not change `guided` or Bluetooth/audio work.

## Visual contract

- OpenCV world frame: `+X` right, `+Y` down, `+Z` forward.
- Three.js scene mapping: `toScene([x,y,z]) = [x, -y, -z]`.
- Object: sphere at `xyz_world`. Target gold, others blue. Fade if not in latest boxes.
- Wearer: distinct sphere at `pose.T_world_from_cam` translation. Row-major transform indices are `T[3]`, `T[7]`, `T[11]`.
- Crumbs: smaller faded dots at `crumbs[].xyz_world`.
- If `pose.valid` is false: freeze the last wearer dot. Do not slide or invent motion.
- Identity pose before VO is honest only as a static cloud: wearer stays at origin.

## Step 1 — sync remote

- `git fetch --all --prune`
- Confirm `origin/main` is an ancestor of `HEAD`
- Push `nathan/percept-core`
- Do not PR the Bluetooth audio commit into `main` as part of this work

## Step 2 — dashboard world-dot view

Use the existing fake replay only to verify rendering.

Files:

- `laptop/dashboard/src/Scene.jsx`
- `laptop/dashboard/src/App.jsx`
- `laptop/dashboard/README.md`

Work:

- Plot `objects[].xyz_world`, `hand.xyz_world`, and wearer pose translation.
- Draw hand-to-target using world coordinates when available.
- Draw crumb dots.
- Add a small pose readout: `pose.valid`, `pose.age_ns`, object count.
- Remove the fixed torso-as-camera-center assumption from the world view.
- Keep the patch small; Zain owns the dashboard design.

Verify:

```sh
cd laptop/bridge && npm install && npm run replay:dev
cd laptop/dashboard && npm install && npm run dev
```

Expect: keys and bottle appear as dots, wearer dot near origin, crumbs visible. This remains scripted data, not spatial truth.

## Step 3 — probe to world JSONL

Add `percept/tools/probe_to_world.py` as a thin wrapper around `probe_frame.py`. Do not fork a second detector.

Each frame emits one JSONL line in the sample shape:

- `objects[]`: `name`, `xyz_cam`, `xyz_world`, `bbox_px`, `conf`, `frame_id`, `in_latest_boxes`
- `hand`: landmark 8 in the same frame
- `target`: first in-view label of interest (`keys`, `keychain`, `bottle`)
- `d_m`: only when `hand.frame_id == target.frame_id`, otherwise omit or hold last
- Phase A pose: identity/static, `xyz_world = xyz_cam`, `crumbs = []`
- `health.last_yolo_ms`, `health.last_depth_ms`

Feed it with `node main.js /tmp/beacon-live.jsonl`.

Without `models/calib.json`, `probe_frame.py` omits `xyz_cam`; no real dots until step 4.

## Step 4 — calibration and tape check

- Capture chessboard at the exact laptop/C270 resolution used by the probe.
- Write `models/calib.json` with `{fx, fy, cx, cy, width, height}` for the laptop path only.
- Tape-check depth at 0.5 m, 1 m, 2 m.
- If error at 1 m is greater than 30%, do not speak metres and do not treat VO as metric.
- Never copy laptop/C270 calibration into `include/beacon.h`.

## Step 5 — Range 1 tabletop proof

No odometry yet.

- Put keys or bottle on a table with hand in view.
- Require same `frame_id` for object and fingertip.
- Dashboard success: object dot, hand dot, line length close to tape, `d_m` close to tape.
- A dropped detection must hold the last value, not jump.

If this is wrong, VO will scatter the map. Do not start step 6.

## Step 6 — RGB-D odometry

Laptop-only first, per spec §8:

- gray ~320x240, ORB matches to keyframe
- unproject matched pixels with the same depth map
- `solvePnPRansac`
- first good keyframe is world origin
- failure sets `pose.valid = 0` and freezes the wearer dot
- new keyframe after about 10 cm or 15 degrees
- crumbs about every 0.4 s if valid and moved at least 5 cm

Measure a 5–10 m aisle with one turn. Report p95/endpoint error. RETURN stays out if the number is missing.

## Verification

- Remote sync clean or intentionally one local commit ahead.
- Fake replay renders world dots.
- Live probe emits real `xyz_world` dots for a held-up object.
- Tape vs distance at 1 m recorded.
- Same-frame `d_m` vs fingertip tape recorded.
- With VO: wearer dot moves, objects stay, crumbs trail, and invalid pose freezes the dot.
