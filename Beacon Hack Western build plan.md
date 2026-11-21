# Beacon | Hack Western build plan

> **SUPERSEDED for product and geometry** by [`docs/nathans-revision.md`](docs/nathans-revision.md).
>
> Do **not** build: B4 AprilTag fob, C6 WALK ticks, YOLO11n as the detector, MediaPipe on the 16 ms `guided` thread, or a Sunday L-return that is not gated on VO p95.
>
> This file is weekend ops history (lane names A–D, phase order). If it disagrees with the spec, the spec wins.

Nov 20, 2026

A chest-worn Raspberry Pi 5 running QNX 8.0 helps the wearer find an object, reach for it in 3D, and retrace a short route by sound. The wearer says “where are my keys,” turns toward the bearing, and listens for faster ticks as their hand approaches. After walking a few metres, “take me back” guides them through the breadcrumbs in reverse. **All sensing, inference, guidance and audio run on the Pi.**

## The four lanes

*Owners not assigned yet.*

| Lane | Owns |
| --- | --- |
| **A** | QNX guidance, timing, supervision and recovery: `guided`, `supervisor`, piezo watchdog, timing and fault tests |
| **B** | Camera, calibration and detection: `camd`, AprilTag fob, YOLO11n, metric depth, hand |
| **C** | 3D reach fusion, visual odometry, breadcrumbs and RETURN |
| **D** | `voiced`, speech and audio output, mount, trials, demo recording and submission |

The order below is a dependency chain. The four lanes in Phase 2 only run in parallel because Phase 1 freezes the observation format first.

## Phase 0 · Bring-up

*All four together · first two hours of hacking*

- **0.1** Check out available peripherals.
- **0.2** Capture a live Camera Module 3 frame on the loaner Pi.
- **0.3** Live microphone into QNX Whisper.
- **0.4** Stereo output through the speaker or headset.

> **Gate:** camera, mic and stereo output all proven on the real Pi before anyone writes product code.

## Phase 1 · Freeze the observation contract

*All four together · about 1 hour · blocking*

Everything passed between processes carries where it came from and when. Agree on these shapes in one sitting, then nobody waits on anybody.

- **1.1 Frame.** Frame ID plus monotonic capture time, stamped by `camd`.
- **1.2 Observation.** Hand, object, tag, depth and pose results, each with its source frame ID, capture time and validity. An observation that is *explicitly invalid* is different from one that is *missing*.
- **1.3 Pose and route.** Pose with a coordinate-frame ID; breadcrumb with position, time and frame ID.
- **1.4 Intent.** FIND (object), GO, RETURN, STOP.
- **1.5 Cue.** What `guided` hands to audio: pan, cadence, LOST, and spoken templates.
- **1.6 Replay fixture.** A short recorded set of observations (one reach, one occlusion, one short walk) that every lane can replay without the camera. Lanes A, C and D build against it until Lane B is live.

> **Gate:** `guided` produces stereo ticks from the replayed fixture. Then split up.

## Phase 2 · Four lanes in parallel

*The long stretch · Friday night through Saturday*

Within a lane the order matters; across lanes it does not. Cross-lane handoffs are marked.

### Lane A — QNX guidance, timing and recovery

- **A1 · `guided` timing thread.** High-priority thread on core 0, 60 Hz target (16.7 ms period). Read the latest complete observations without waiting on a worker. No model calls, blocking device writes or logging on this thread.
- **A2 · Stereo ticks.** Compute pan and cadence and hand off short cues to audio output.
- **A3 · Observation handoff.** Consume the Phase 1 records. Reusing an old result must preserve its original timestamp.
- **A4 · Occlusion and staleness rules — CRITICAL.** Suppress directional ticks as soon as a required observation is explicitly invalid. For missing updates, start with a 350 ms capture-age cutoff: clear queued directional audio and play LOST. Resume after two distinct fresh, valid observations agree on the target. At 1.5 s, trigger the spoken prompt “scan for your keys.” Tune with real reaches and the headset delay from D5.
- **A5 · `supervisor`.** Watch exits and progress on new frame IDs. A healthy worker can report “no object” on each new frame; a stuck worker stops completing frames. Restart the stuck process.
- **A6 · Piezo watchdog.** A separate watchdog owns the GPIO piezo and sounds a continuous fault tone if `guided` stops responding while the Pi is powered.
- **A7 · Baseline.** Log scheduled and actual guidance wakeups for 60 seconds with the full stack running, plus the age of observations when guidance uses them.
- **A8 · Load.** Same reach with additional lower-priority CPU work. Show worst wakeup lateness and missed guidance deadlines. Capture a QNX System Profiler trace of the guidance and perception threads.
- **A9 · Freeze.** With load running, freeze perception mid-reach: LOST plays and ticks cease. Judge moves the keys to the opposite side. After automatic recovery, the first resumed cue points to the new position.
- **A10 · Measure what is heard.** Elapsed time from last valid frame capture to audible LOST, using D7’s recording. If only software timestamps exist, label it “time to queue LOST.” Separately, fail `guided` to demonstrate the piezo.

### Lane B — camera, calibration and detection

- **B1 · `camd`.** Capture Camera Module 3 frames through QNX Sensor Framework. Stamp each with monotonic capture time and frame ID. Publish the newest frame in the three-slot ring, dropping late frames.
- **B2 · Chest-height test.** Live frames from the mounted position; test the key fob and the generic object path.
- **B3 · Calibrate — before B4.** Calibrate the chest camera at its operating resolution.
- **B4 · AprilTag fob.** Two-sided printed tag; measure the printed size and register its ID as “my keys.” A visible tag gives identity and 3D position relative to the camera. *Ref: AprilTag pose estimation*
- **B5 · YOLO11n.** Cups and other supported objects. The cup is the quick check that the general object pipeline works. *Ref: YOLO11 models · COCO class list*
- **B6 · Metric depth.** Depth Anything V2 Metric Indoor Small for object depth and the hand.
- **B7 · Hand.** MediaPipe hand inference in a worker on cores 1–3. **Unblocks C1.**
- **B8 · `percept` publishing.** All workers on cores 1–3; publish hand, object, tag and depth results with source frame IDs and validity, per Phase 1.
- **B9 · Measure with all workers on.** Achieved detection and depth rates (6 Hz and 8 Hz are targets). If observations arrive too old, lower input resolution or drop old work, then repeat the reach test.
- **B10 · Verify range.** Report measured bearing; announce range only over distances checked against a ruler.
- **B11 · Optional: untagged keys.** Fine-tune a keys detector as a second path. Test on unseen placements, clutter, glare and no-keys scenes before using it on stage.

### Lane C — reach fusion, odometry and RETURN

- **C1 · Reach fusion.** Align fingertip, depth, target and pose by capture time before subtracting 3D positions. Start with same-frame fusion. *Build against the fixture until B7 lands.*
- **C2 · Fused reach output.** Publish the hand-to-target vector with validity and capture age so A4 can act on it. A 60 Hz loop does not create 60 fresh hand measurements per second.
- **C3 · Visual odometry.** Runs in `percept` on cores 1–3; pose carries its coordinate-frame ID.
- **C4 · Breadcrumbs.** Save one about every 0.4 s while pose is valid.
- **C5 · Route store — CRITICAL.** Keep the route and its frame ID outside the restartable perception process, so A5 restarts never lose it.
- **C6 · RETURN guidance.** Walk breadcrumbs in reverse using a fresh pose, with faster pulses as the wearer faces the next waypoint. Hand visibility is irrelevant in this mode.
- **C7 · Lost odometry.** Pause the beacon; resume only after re-establishing pose in the original route frame.
- **C8 · Occlusion and recovery tests.** With B: hand over the keys, and route-frame recovery.
- **C9 · L-shaped walk.** So judges hear a real turn. Record route endpoint error.

### Lane D — speech, audio, hardware, demo

- **D1 · `voiced`.** Run the QNX build of `whisper.cpp` locally. [QNX ARM64 package index](https://repo.oss.qnx.com/8.0.5/extra/aarch64/)
- **D2 · Intents.** Parse FIND, GO, RETURN and STOP into the Phase 1 intent.
- **D3 · Speech templates.** Fixed templates for measured bearings and ranges, plus LOST and “scan for your keys.”
- **D4 · Audio output path.** Speaker/headset output for ticks and speech.
- **D5 · Headset delay.** Measure it and feed it into the A4 tuning.
- **D6 · Mount.** Assemble the chest mount.
- **D7 · Synchronized audio capture.** Record output with a synchronized reference if available, for A10.
- **D8 · Trial log.** Run trials and record misses, wrong-side cues, recovery time and route endpoint error.
- **D9 · Demo recording.** Record the demo with audible cues; keep a trace and recording of the same run for judges.
- **D10 · Submission.** Best Use of QNX selected on both Devpost and the event live site, with matching team members. *Ref: Event rules · Sponsor criteria*

> **Gate:** each lane runs standalone. A ticks and recovers on replayed data; B publishes valid tag, cup and hand observations live; C produces a fused reach vector and a recorded route; D turns speech into intents and plays cues.

## Phase 3 · Integration

*All four · Saturday*

- **3.1 · Saturday morning:** one spoken FIND and a complete reach, end to end.
- **3.2 · Saturday late afternoon:** the loaded fault test (A8–A9) and a short RETURN.

> **Gate:** a judge can place the keys, ask for them, and the wearer reaches them under load. **This is the MVP.** Tag the commit.

## Phase 4 · Hardening

*All four · before feature freeze Saturday night*

- **4.1** Ten shuffled key placements.
- **4.2** Five detector stalls with the keys moved.
- **4.3** Three L-shaped returns.
- **4.4** Record misses, wrong-side cues, recovery time and route endpoint error. Achieved measurements go in the submission.

## Phase 5 · Judging

*Sunday*

- **B + C:** verify calibration, recovery and the L-turn in the judging space.
- **A:** show the timing trace and run the judge-controlled fault.
- **D:** confirm submission, reset the unit between demos and handle hardware.

**Judge sequence**

1. Judge places the keys, requests them, and the wearer starts reaching under load.
2. Freeze perception and move the keys.
3. Wearer finishes after recovery.
4. Walk the L and say “take me back.”

Keep a trace and a recording of the same run available for the other judges at the table.

## Standing rules

- **Nothing slow on the timing thread.** No model calls, blocking writes or logging in `guided`.
- **Every observation knows its age.** Frame ID, capture time and validity travel with every result; reused data keeps its original timestamp.
- **The route outlives perception.** A restart of `percept` never loses the route or its frame.
- **Only claim what you measured.** Range only where ruler-checked; “time to queue LOST” when that’s all you have; report achieved rates, not targets.
- **Be upfront with judges.** If using the fob, tell them the keys are registered.

## Timeline

- Hacking runs **Friday, November 20, 9 pm** to **Sunday, November 22, 9 am** local time.
- Aim to submit by **8 am Sunday**.
