# Visual odometry integration design

Date: 2026-11-21
Status: approved approach, pre-review against the QNX track (findings in the
last section; amend after review)
Owner of the code this describes: Nathan (`percept/`)
Source of truth: [`nathans-revision.md`](../nathans-revision.md) §7–§8. Where
this document refines §8 (KLT front-end instead of per-frame ORB), the team
approved the change on 2026-11-21; that approval should be folded back into the
revision by its owner before feature freeze.

This document does not change `include/beacon.h`. Every field VO needs already
exists: `beacon_pose_t`, the crumb ring, `pose_epoch`, `health`. No ABI change,
so Matt and Munadir are not gatekeepers for this feature.

## Intent

One metric pose chain `T_world_from_cam` maintained at ~10 Hz on cores 1–3, so
that a `p_world` stored ten seconds ago can be aimed at after a turn (spec §7
Range 3: RETURN and off-camera "bottle I walked past"). The §13 build order
gates RETURN on a measured VO p95 over a 5–10 m aisle with one turn; until that
number exists, RETURN stays out of the 30 s script and off-camera memory is
refused, never faked.

## Goals

- Metric 6-DoF pose at ~10 Hz, budget ~10–15 ms per VO step on the Pi 5 under
  three hogs and a live `guided`.
- Breadcrumbs in the existing crumb ring per §8 (every ~0.4 s when moved
  ≳ 5 cm).
- Honest failure: `pose.valid = 0` whenever the step is not trusted; last pose
  ages out; RETURN refuses ("I cannot retrace without a path").
- Scale that survives the known Depth Anything V2 failure mode (the ~4×
  overestimate that `tape_check.py` exists to catch) via an independent
  ground-height watchdog.
- Zero new native dependencies beyond the OpenCV modules already in the QNX
  package plan — plus `video`, which this review adds (see QNX findings).

## Non-goals

- SLAM, loop closure, relocalization, map persistence across restarts.
- IMU fusion (no IMU in the kit is assumed; §8 keeps it optional sugar).
- Occupancy or floor modeling beyond the scale watchdog.
- Any `beacon.h` change.

## Anti-goals (what would make this a failure even if it works)

- Invented motion: extrapolating pose across `pose.valid = 0` gaps, or speaking
  RETURN from a pose that never passed its aisle gate.
- VO on core 0, or VO ever delaying the 60 Hz `guided` tick.
- A second scale authority: if `tape_check` fails, VO pose is as illegal as
  spoken metres, and says so by refusing Range 3.

## Constraints (measured facts, not targets)

- Pi 5, QNX 8.0, 4× Cortex-A76 @ 1.5 GHz, 8 GB RAM; `percept` is `SCHED_RR` 22
  on cores 1–3; core 0 is reserved (`beacon.h` runmasks).
- `CLOCK_MONOTONIC` resolution on this image is 1 ms
  (`pi-bringup.md`), so per-step timing counters are the right instrument, not
  single-shot clocks.
- Camera reality as of 2026-11-21: the C270 is **JPEG-only** through Sensor
  Framework (temporary `sensor` config), and `camd` has **no real camera
  adapter yet** — `/beacon_frames` currently carries stub or BMP frames. VO
  cannot be validated on-device until camd publishes real frames with real
  `t_ns`.
- The C270 is rolling shutter. Fast head turns corrupt both feature tracking
  and pose; we guard by rejection, not modeling.
- Depth: DAv2 Metric Indoor Small at ~210 px, tape-gated
  `depth_scale` (laptop-measured 0.25 correction outstanding), shared with
  detection. One scale authority.
- OpenCV **is not yet installed on the Pi** (`pi-bringup.md` §2 table is
  empty; pip source builds fail; qnx-ports are host-side build files). This is
  the hard prerequisite gate for all of `percept`, not just VO.

## Approaches considered (team decision 2026-11-21)

**A. Hybrid KLT front-end — chosen.** Detect corners once per keyframe,
`calcOpticalFlowPyrLK` them every VO frame, depth-backed PnP against the
keyframe's 3D points. Cheapest per-frame cost (no descriptor extraction or
matching, which dominates ORB); at 1 m/s walking and 10 Hz the inter-frame
motion (~10 cm) is inside KLT's small-displacement regime; the RGB-D ablation
literature has KLT+depth-PnP as the best backend combination (61.8% ATE
reduction vs 29.1% for per-frame ORB). Costs track-state bookkeeping and a
dependency on OpenCV `video`.

**B. Spec §8 literal (per-frame ORB).** Detect + descriptor-match every VO
frame. One code path, matches the frozen spec text, `features2d` only — but
~20–40 ms/frame more CPU and measurably weaker than A in the ablation. Kept as
the documented fallback if the QNX OpenCV package cannot provide the `video`
  module (see QNX findings F1).

**C. Ground-plane primary.** Track floor points, decompose the ground
homography, metric scale from known chest height. Cheapest of all and
scale-true, but dies whenever the floor leaves the frame — frequent for a
chest cam at table height. Rejected as primary; its scale logic survives inside
the watchdog.

All three share the §8 chaining, `pose.valid` gating, crumb cadence, and the
tape-check scale authority.

## The design

### Where it lives

- `percept/src/vo.hpp` / `vo.cpp`: a `Vo` class owned by the percept loop.
  Pure geometry, no ONNX, no shm writes of its own (the percept writer folds
  `vo.pose` into the block it already publishes under `seq_percept`).
  QNX-only calls behind `#ifdef __QNX__` per repo convention; builds with the
  on-device `cc` loop.
- `percept/tools/vo_probe.py` + `vo_probe_test.py`: laptop-first proof in the
  existing probe venv, same convention as `probe_frame.py` — no QNX code is
  written until the probe passes over a recorded walk.

### State (per-process, not shm)

```
keyframe K:
  gray_K          320x240 (or CAM aspect-scaled equivalent)
  pts2D_K         ~300 corners from goodFeaturesToTrack (grid-spread)
  pts3D_K         those corners backprojected through K's depth grid
  T_world_from_K  float[16]
  frame_id_K, t_ns_K
tracks:           last LK positions + forward-backward errors
watchdog:         deque of recent h_est values (window ~10)
pose:             last valid T_world_from_cam, its t_ns, valid flag, age
```

### Per VO step (~every 100 ms; every 3rd ring frame at 30 fps)

1. Read the newest `/beacon_frames` slot (existing seqlock reader). Convert
   to gray at the VO working scale. If `frame_id` is not newer than the last
   step's, skip silently.
2. **Rolling-shutter guard first:** `calcOpticalFlowPyrLK` K→F (pyramid level
   2), then F→K. Drop tracks with forward-backward error > 1 px. If the median
   surviving displacement exceeds ~8 px/frame (fast head turn) **or** fewer
   than ~60 tracks survive, the step is untrusted: set `pose.valid = 0`, keep
   the last pose, age it, publish nothing else. Do not model the shutter.
3. **Depth gate:** drop tracks whose keyframe corner has invalid depth
   (`<= 0` / NaN in the grid cell, after 3×3 median like the fingertip
   sampler).
4. `solvePnPRansac` (SOLVEPNP_EPNP, 2 px, confidence 0.99, ≥ 15 inliers,
   iteration cap) on `pts3D_K` / tracked-in-F. OpenCV returns `T_F_from_K`;
   chain per §8: `T_world_from_F = T_world_from_K · inv(T_F_from_K)`.
5. **Ground-height watchdog:** take PnP inlier 3D points, select the below-
   horizon band (camera-frame +Y large), least-squares plane fit if ≥ 20
   candidates with sane spread. `h_est` = camera height above that plane.
   - `|h_est − h_chest| / h_chest ≤ 0.25`: pass, no action.
   - Beyond 25%: rescale this step's **translation length** by
     `median(h_chest / h_est)` over the watchdog window. Log the correction
     rate — a persistently correcting VO is a failing VO and must say so.
   - Plane not fittable (floor out of frame, inlier band empty): no
     correction this step; the tape-gated `depth_scale` remains the only
     authority. If the tape gate has not passed, `pose.valid = 0` regardless.
   `h_chest` is a tape-measured constant (wearer chest height, from the §15
   measurement set), a config value in `percept`, never in shm.
6. **Keyframe swap** when moved ≳ 10 cm or ≳ 15° from K, or track count stays
   low: promote the most recent **depth-complete** frame (one whose
   `frame_id` has a finished depth grid from the detect cycle — VO never
   invokes the depth model itself) to the new keyframe, taking its gray and
   depth **from percept's in-memory copy of the frame it just processed**
   (the 3-slot newest-wins ring has already overwritten that frame — never
   re-read the ring for keyframe material); re-detect corners
   there; reset `T_world_from_K` from the chained pose. This bounds track
   drift and throttles cost naturally: at walking speed, swaps land at the
   ~2–3 Hz depth cadence, which is fine because keyframe lifetime is
   distance-gated anyway.
7. Publish: fold pose (valid, `t_ns`, `age_ns`, unchanged `pose_epoch`) into
   the next `seq_percept` write. Crumbs per §8: every ~0.4 s with ≳ 5 cm of
   valid movement, `crumbs[crumb_i++ % 512]`, `crumb_n = min(crumb_n+1, 512)`.

### Failure semantics (unchanged from §8, restated as contract)

- First successful keyframe after (re)start is the world origin, `T = I`,
  under the **current** `pose_epoch`. Everything stored under an older epoch is
  unreachable for Range 3 — that is the `slay percept` → LOST story.
- `pose.valid = 0` never extrapolates. `guided` refuses RETURN; ranges 1–2
  keep working. Covering the lens gives LOST, not a guessed metre.
- `pose` ages via `age_ns`; consumers already treat staleness.

### Scheduling

VO is a step inside `percept`'s loop on its own cadence, fed from the frame
ring, never from the detect bundle's critical path: the YOLO→depth→hands cycle
is untouched and never waits on VO. VO's worst-case step (~15 ms) lands on
cores 1–3 at RR 22, below `guided`'s FIFO 58 on core 0. Instrumentation follows
the `camd/deadline-test` pattern: per-step ms counters plus a `p95` over the
run, reported the same way, with hogs on cores 1–3 and `guided` live. 1 ms
clock resolution is coarse for a 10 ms step but fine for the p95 question.

### What "done and trusted" means (acceptance gates)

All numbers measured on the loaner, hogs on cores 1–3, `guided` live, after
the QNX OpenCV/ORT packages exist and `camd` publishes real frames.

1. `vo_probe.py` over a **recorded** L-shaped walk (captured via
   `webcam-record/`): recovered trajectory endpoint error ≤ 0.5 m over 5–10 m
   with one turn (stretch: ≤ 0.25 m); watchdog correction rate reported.
2. `vo_probe_test.py`: synthetic translate/rotate frame pairs recover `T`
   within tolerance (translation ±5%, rotation ±2°) — the same "every answer
   known" style as the other probe tests.
3. On-device: VO step p50/p95 ms under the hog load; valid-pose fraction
   ≥ 90% while walking the aisle (a VO that is half garbage is worse than one
   that refuses).
4. Three live L-shaped returns: endpoint error reported on the dashboard;
   `slay percept` mid-walk → `pose.valid = 0`, RETURN refuses with the
   `CANNOT_RETRACE` clip. No breadcrumb log is ever presented as "RETURN
   implemented" without the live number (spec §12 rule).
5. VO pose is legal for Range 3 **only after** `tape_check.py` passes for the
   shared `depth_scale`. Same gate as spoken metres, one authority.

## Open items (builder calls, marked at implementation)

- Exact VO working scale (320×240 vs aspect-preserving) and frame stride N —
  tune on the recorded walk, record the choice here.
- Watchdog thresholds (25% band, ≥20 plane candidates, window 10) are initial
  values from the research, to be tuned by the probe's correction-rate readout.
- LK pyramid depth and track count floor (60) — same.
- `h_chest` measurement procedure and value (§15 set, owner Matt).

## QNX track review (2026-11-21, against `pi-dev-workflow.md` and `pi-bringup.md`)

- **F1 — OpenCV module availability is the top risk.** §8 budgeted only
  `features2d` + `calib3d`. Approach A additionally needs `video`
  (`calcOpticalFlowPyrLK`) and `imgproc` (`goodFeaturesToTrack`, `cvtColor`,
  `resize`). As of the last bring-up entry, **no OpenCV is installed on the
  Pi**; pip source builds fail, and the qnx-ports catalog is host-side build
  files that assume a Linux host with QNX SDP — which this NixOS laptop does
  not have configured. Gate: install/verify the oss.qnx.com OpenCV package and
  confirm `video` + `calib3d` link before writing `vo.cpp`. If `video` cannot
  be had, the documented fallback is **approach B** (ORB per frame,
  `features2d` only), at the measured CPU cost, decided Saturday morning at
  the latest.
- **F2 — No real frames yet.** `camd` has no CamAPI adapter; the C270 is
  JPEG-only via a temporary sensor config; `/beacon_frames` carries stub/BMP
  data. VO's on-device validation is blocked behind the same camd work as
  everything else — it shares camd's gate, it does not add a new one.
- **F3 — Runtime packages missing.** onnxruntime is also uninstalled, which
  gates the depth half of RGB-D VO (and all of detection). VO probe work on
  the laptop is deliberately unblocked by design; on-device VO inherits the
  percept package gate.
- **F4 — Build/deploy loop.** VO builds with the on-device `cc`/`make` loop
  (rsync → ssh make → slay/restart), no cross-toolchain, no new workflow.
- **F5 — Timing instrumentation.** 1 ms clock resolution; use deadline-test
  style counters, not per-step single-shot clocks. Over-period counting stays
  the miss metric for anything 60 Hz; VO's own metric is step p95.
- **F6 — Restart semantics already in the contract.** `pose_epoch` bump on
  percept restart makes stale objects unreachable for Range 3. No persistence
  across restarts is correct for QNX too: nothing about VO belongs on the
  `/data` partition.
- **F7 — Process/thread placement.** VO thread inherits `percept`'s runmask
  (cores 1–3, RR 22); verify with the `pidin ar` dump in bring-up §2, same as
  the ORT thread-pool note there.
- **F8 — JPEG decode on camd's path.** If the C270 stays JPEG-only, camd will
  decode JPEG into the ring; that cost is camd's, not VO's, but it caps the
  honest ring rate and the VO stride N derives from the real frame rate, not
  from 30 fps assumed.
- **F9 — the 3-slot ring cannot hold keyframe material.** Newest-wins at ~30
  fps overwrites a frame in ~100 ms, while a depth-complete frame is up to
  ~0.4 s old. Keyframe gray and depth must come from percept's in-process copy
  of the last processed frame; the ring serves only VO's fresh per-step
  frames. `camd/README.md` documents the newest-wins contract this relies on.
