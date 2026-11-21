# Beacon: team plan (who does what, when)

Date: 2026-11-21
Status: operations plan. **[`nathans-revision.md`](nathans-revision.md) is the product, geometry and QNX source of truth.** If this file disagrees with it, the revision wins. This file only says who does what tonight and tomorrow, what hardware we still need, and what we fall back to.

## Where we are

- Hacking runs Fri Nov 20, 9 pm → Sun Nov 22, 9 am. Submit by 8 am Sunday.
- We have: the loaner Pi 5 (8 GB, QNX 8.0, official active cooler fitted, HiPi case), a Logitech C270 USB webcam with built-in mic, speakers, four laptops.
- The hardware workshop was closed Friday night. Parts come Saturday morning (see the request below).
- So tonight is **software on laptops**. Tomorrow we bring the parts and the Pi together.

## Open decisions (settle these in the chat before coding)

| Question | Spec says | Team chat said | Proposal |
| --- | --- | --- | --- |
| Reach cue: ticks or voice? | WALK = speech, REACH = ticks (§10) | "actual voice guide, not beeps" | Keep the spec. Speech already covers walking; ticks only in the last ~50 cm are faster than words. Revisit only if judges can't follow the ticks in rehearsal. |
| Camera | Camera Module 3 via Sensor Framework (§4) | We have a C270 USB webcam | Ask the workshop for a Camera Module 3 + Pi 5 cable. Probe the C270 on QNX tonight anyway; if it works it is the fallback. |
| Telemetry for a laptop dashboard | Not in the spec | Munadir wants a 3D dashboard | Add an optional sixth process `telemd` (below). It only reads shm, runs at the lowest priority on cores 1–3, and can be killed without changing anything the wearer hears. |

## Tonight: laptop work, no new hardware needed

Everyone codes against the **same structs**. First 30 minutes: Matt and Nathan freeze `include/beacon.h` from spec §6 (frame ring, depth slot, world state, per-writer seqlocks, `intent.kind`). Everyone else waits for that header, then builds against it.

| Who | Tonight (laptop or Pi) | Done when |
| --- | --- | --- |
| **Matt (Lane A)** | `include/beacon.h` + seqlock helpers. `supervisor` and `guided` in C, QNX calls behind `#ifdef __QNX__` so the logic builds and runs on a laptop with stubs. `guided` reads a fake target from shm and prints the law it picks (WALK / REACH / HOLD / LOST) at 60 Hz. | On a laptop: fake target in, correct law and clip ids out; killing the fake writer gives HOLD then LOST. |
| **Nathan (Lane B)** | On a laptop: bake the noun list into YOLOE-26n, export static detect-only ONNX at 320 (spec §9). Export Depth Anything V2 Metric Indoor Small. Run both + MediaPipe hands on a laptop webcam through ONNX Runtime to check outputs and the letterbox inverses (§7). If he has the Pi: bring-up §21 steps 1–5 (packages, C270 probe, USB audio). | `yoloe26n_320.onnx`, `labels.txt` and the depth ONNX are in `models/` (not committed if large); a laptop script prints boxes, metres and fingertip for one frame. |
| **Zain (Lane D)** | `voiced` logic on a laptop: whisper.cpp tiny.en on recorded clips, then the synonym table (§9) → `{job, candidates}`. Pre-render every clip in §10 (numbers 0–9, "metre(s)", "ahead", "left", "right", "up", "down", "I lost the target", "stopping", "I have not seen that", "I cannot retrace without a path", "I did not catch that", "I cannot help with that") as 16 kHz mono WAVs in `sounds/`. | Ten spoken test phrases map to the right job and candidates; every clip in §10 exists as a WAV. |
| **Munadir** | `telemd` contract (below), a replay generator that writes fake `WorldState` JSON (a reach, a HOLD, a LOST), the `bridge` and the 3D dashboard against replay data. Devpost skeleton. Slack request for hardware. | The dashboard plays a replay: objects at their 3D positions, hand point, target, mode banner, health panel. |
| **Lane C (VO / RETURN)** | Not tonight. Spec build step 6 only starts after steps 1–5 work. | n/a |

## Saturday: put it on the Pi (spec §13 order, do not skip ahead)

1. **Morning:** collect parts. Bring-up §21 on the Pi: packages, camera probe (unit, `W×H`, frametype, focus lock), USB headset playback and record, GPIO piezo.
2. **Build step 1:** `supervisor` + `camd` + `guided` with a fake target + piezo. Busy-loop hogs on cores 1–3; 60 Hz ticks hold. Capture the Profiler trace and the 16 ms miss count.
3. **Build step 2:** lock `CAM_W×CAM_H` and focus, chessboard calibration, tape-measure depth on a 1 m table.
4. **Build step 3:** depth + MediaPipe in `percept` → real REACH on a cup. No VO, no YOLOE yet.
5. **Build step 4:** YOLOE + whisper + table → FIND while the object stays in view.
6. **Build step 5:** `slay percept` → HOLD → LOST. This is the QNX beat; never skip it.
7. **Evening:** dashboard live from `telemd`; rehearse the 30 s script (spec §12).
8. **Only if 1–6 are green:** VO and RETURN (build step 6).

Feature freeze Saturday midnight. Sunday 1–6 am: the measurements in spec §15, demo video, Devpost.

## Hardware request (send on Slack, collect Saturday morning)

| Item | Why | Spec ref |
| --- | --- | --- |
| Pi Camera Module 3 + **Pi 5 camera cable (22-pin to 15-pin)** | The camera the spec and QNX Sensor Framework support; the C270 is unproven on QNX | §4, §16 |
| USB headset with mic | Speech out and voice in; QNX on Pi 5 has no 3.5 mm audio | §4, §16 |
| Piezo buzzer + NPN transistor (e.g. 2N2222) + 1 kΩ resistor | The cannot-fail actuator; the spec says drive it through a transistor, not straight from the pin | §5.1 Audio and piezo |
| Push button | Push-to-talk for `voiced` | §16 optional |
| Female-female jumper wires, small breadboard | Connect the piezo and button to GPIO | |
| Optional: BNO055 or ICM-20948 | WALK yaw help only; does not replace VO | §4 |

The Pi already has the official active cooler, so no fan is needed. Check the power supply is the official 27 W (5 V / 5 A); a weaker one cuts USB power and the camera and headset drop out.

## Fallback: camera and mic only

If the workshop has nothing, the spec still mostly works with the Pi, a camera and USB audio:

| Still works | Lost |
| --- | --- |
| FIND with spoken WALK cues, REACH with ticks through the USB speaker/headset, `slay percept` → HOLD → LOST, supervisor restarts | The piezo, so "guided died" has no independent cue. Say so honestly; the supervisor can still restart `guided` and the USB clip says "stopping". |
| Voice in through the C270 mic (if it enumerates on QNX) or button-free energy gate (§5 `voiced`) | Push-to-talk |
| Everything in `percept` if the C270 works on Sensor Framework | Everything in `percept` if it does not: then we need the Camera Module 3, full stop |

## `telemd` and the dashboard (optional, never on the wearer's path)

- **Process:** `telemd`, `SCHED_RR` at the lowest priority we use, runmask `0xe` (cores 1–3). Read-only on `/beacon_world` and `/beacon_frames` using the same seqlock readers; skips torn reads; never writes shm, never sends to `guided`.
- **Mode:** the spec forbids writing `mode` into shm. `telemd` recomputes it for display with the same pure function `guided` uses (share it in a header). Display only.
- **Sends** UDP to the laptop: world-state JSON at ~10 Hz (objects with `xyz_cam` / `xyz_world`, hand, target, intent, pose, crumbs, health) and a downscaled JPEG at ~5 fps.
- **Timing panel:** needs `guided`'s miss count and worst lateness. Proposal for Matt: add a small `guided_stats` block under `seq_guided`. If he says no, the panel shows the Profiler trace instead.
- **Laptop:** `bridge` (Node: UDP in, WebSocket out, records sessions to JSONL for replay) and the dashboard (Vite + React + three.js via react-three-fiber: torso with a camera cone and live video, objects at their real 3D positions from depth, fingertip-to-target line, mode banner, health and timing panels, replay scrubber).
- **Rule:** kill `telemd` or unplug the laptop mid-demo and the wearer hears no difference.

## Demo (spec §12, unchanged)

1. "Where are my keys?" → spoken LIVE bearing → hand enters → ticks speed up → tone at the keys.
2. "Where can I refill water?" → binds `bottle` → spoken WALK cue.
3. `slay percept` → HOLD → LOST → supervisor restarts it. Cover the lens: same LOST, no guessed metres.

Never skip step 3. Do not claim RETURN unless it was measured.
