# Graph Report - Beacon-Hack-Western-13-  (2026-11-21)

## Corpus Check
- 38 files · ~76,754 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1262 nodes · 2677 edges · 61 communities (49 shown, 12 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 234 edges (avg confidence: 0.87)
- Token cost: 308,895 input · 0 output

## Community Hubs (Navigation)
- Probe to World Sender
- Probe CLI and Arguments
- Dashboard UI and Deps
- Guided Law Engine
- Bridge and Caption Clips
- Percept Head (C++)
- Accessibility Research Papers
- Camera Calibration Tool
- CI Workflow
- Guided Audio and Stats
- Voice Clip Enum
- camd Frame Tools
- Vocabulary and Vision Models
- Intent Kinds
- telemd and JPEG Preview
- Probe Detection and Letterbox
- Modes, Privacy and Commands
- Pi Bring-Up and Dev Workflow
- Open-Vocab Model Choices
- Depth Stabiliser
- Tape Check Tests
- Spec and Demo Lineage
- Guided Overview (README)
- Camera Daemon and Gates
- Bluetooth Speaker Player
- Depth Sampling
- Guided Entry and World Mapping
- Spec Review Gates
- Probe Resources and Fingertip
- Reach Audio Design
- Shared Memory and Synthesizer
- Tape Check Tool
- Model Files and Labels
- Voice Clip Tools and Tests
- Box IoU Slot Association
- camd Main Loop
- Probe Test Suites
- Calibration Loading
- Breadcrumbs and Navigation Research
- Dashboard Overview (README)
- Frame Ring and Bridge (README)
- Frame-ID Seed Test
- Model Export Scripts
- camd Overview (README)
- Spec Review Verdict
- Telemetry Transport
- Core-0 Deadline Test
- fakeworld Simulator
- World-Frame Dot Map
- JPEG Preview Encoding
- Depth Pipeline (README)
- Guidance Cue Fields
- Fake Hand Landmarker
- Fake Webcam
- Fake Video File
- Fake ONNX Session
- BT Audio Service
- Radio Auto Script
- No-Tag Homing

## God Nodes (most connected - your core abstractions)
1. `probe_to_world()` - 46 edges
2. `make_probe()` - 37 edges
3. `probe_once()` - 36 edges
4. `ProbeRuntimeTest` - 34 edges
5. `guided_step()` - 32 edges
6. `ProbeToWorldTest` - 32 edges
7. `beacon_clip` - 31 edges
8. `prepare()` - 26 edges
9. `main()` - 20 edges
10. `synthetic_probe_modules()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Heartbeat Fault Detection and Restart with Backoff` --semantically_similar_to--> `Processes Panel (heartbeat age, down at >=1 s)`  [INFERRED] [semantically similar]
  supervisor/README.md → telemd/README.md
- `Newest-wins Dashboard Backpressure (skip clients >1 MB behind)` --semantically_similar_to--> `/beacon_frames Newest-wins Three-slot Ring`  [INFERRED] [semantically similar]
  laptop/bridge/README.md → camd/README.md
- `Processes Panel (heartbeat age, down at >=1 s)` --semantically_similar_to--> `NO DATA Staleness Indicator (1 s)`  [INFERRED] [semantically similar]
  telemd/README.md → laptop/dashboard/README.md
- `probe_to_world.py World JSONL / UDP Emitter` --semantically_similar_to--> `telemd (read-only telemetry to the laptop)`  [INFERRED] [semantically similar]
  percept/README.md → README.md
- `--jpeg Raw UDP Preview Datagram` --semantically_similar_to--> `Optional Video JPEG (~5 fps, <60 KB per datagram)`  [INFERRED] [semantically similar]
  percept/README.md → laptop/samples/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Evidence-Backed Audio UX for a Chest-Worn Homing Device** — docs_beacon_accessibility_research_walk_speech_reach_ticks, docs_beacon_accessibility_research_tick_rate_distance_encoding, docs_beacon_accessibility_research_off_axis_search_cue, docs_beacon_accessibility_research_honest_lost_cue, docs_beacon_accessibility_research_open_ear_audio, docs_beacon_accessibility_research_parsimonious_instructions [EXTRACTED 1.00]
- **Telemetry Monitoring Pipeline (telemd -> bridge -> dashboard)** — telemd_readme_telemd, laptop_bridge_readme_bridge, laptop_dashboard_readme_dashboard, laptop_samples_readme_telemetry_format [EXTRACTED 1.00]
- **Newest-wins Buffering Pattern** — camd_readme_beacon_frames_ring, laptop_bridge_readme_newest_wins_backpressure, guided_readme_audio_thread [INFERRED 0.75]
- **Beacon five-process QNX isolation** — docs_nathans_revision_five_process_architecture, docs_nathans_revision_supervisor, docs_nathans_revision_camd, docs_nathans_revision_guided, docs_nathans_revision_percept, docs_nathans_revision_voiced [EXTRACTED 1.00]
- **Sequential percept vision pipeline** — docs_nathans_revision_sequential_percept_pipeline, docs_nathans_revision_yoloe_26n, docs_nathans_revision_depth_anything_v2, docs_nathans_revision_mediapipe_hands, docs_nathans_revision_rgbd_visual_odometry [EXTRACTED 1.00]
- **QNX mixed-criticality mechanism without APS** — docs_nathans_revision_no_aps, docs_nathans_revision_runmask_core0_isolation, docs_nathans_revision_seqlock, docs_nathans_revision_supervisor, docs_nathans_revision_procmgr_ability, docs_nathans_revision_slay_percept_demo [EXTRACTED 1.00]
- **Bluetooth A2DP Audio Path on QNX** — docs_pi_bringup_bt_a2dp_bridge, docs_pi_bringup_pcm_fifo_contract, docs_pi_bringup_bt_speaker_py, docs_pi_bringup_bt_audio_service, docs_pi_bringup_boot_persistence [EXTRACTED 1.00]
- **Laptop World-dot Pipeline** — docs_pi_bringup_probe_frame_py, docs_superpowers_plans_2026_11_21_world_frame_dots_probe_to_world, laptop_samples_readme_world_sample_json, laptop_bridge_main, docs_superpowers_plans_2026_11_21_world_frame_dots_dashboard_world_view [EXTRACTED 1.00]
- **Laptop Telemetry and Replay Chain** — docs_team_plan_telemd, docs_team_plan_replay_generator, docs_team_plan_bridge, docs_team_plan_dashboard [EXTRACTED 1.00]
- **percept On-device Perception Stack** — percept_readme_percept, models_readme_yoloe26n, models_readme_depth_anything_v2, models_readme_mediapipe_hands, percept_readme_visual_odometry [EXTRACTED 1.00]
- **Spoken-metre Gating (no metres until tape check passes)** — percept_readme_tape_check, percept_readme_depth_scale, percept_readme_fov_pinhole_guess, percept_readme_calibrate_camera, readme_lost_cue_principle [INFERRED 0.85]
- **Telemetry Flow from Pi or Probe to Dashboard** — readme_telemd, percept_readme_probe_to_world, laptop_samples_readme_udp_port_5005, readme_laptop_bridge, laptop_dashboard_readme_use_telemetry, laptop_dashboard_readme_dashboard [INFERRED 0.85]

## Communities (61 total, 12 thin omitted)

### Community 0 - "Probe to World Sender"
Cohesion: 0.06
Nodes (21): build_parser(), format_readout(), load_target_names(), main(), _ns(), _number(), _output(), parse_udp_target() (+13 more)

### Community 1 - "Probe CLI and Arguments"
Cohesion: 0.07
Nodes (15): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), prepare(), probe_once(), ProbeRuntimeTest (+7 more)

### Community 2 - "Dashboard UI and Deps"
Cohesion: 0.06
Nodes (57): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+49 more)

### Community 3 - "Guided Law Engine"
Cohesion: 0.10
Nodes (62): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_kind, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE (+54 more)

### Community 4 - "Bridge and Caption Clips"
Cohesion: 0.07
Nodes (27): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+19 more)

### Community 5 - "Percept Head (C++)"
Cohesion: 0.07
Nodes (26): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+18 more)

### Community 6 - "Accessibility Research Papers"
Cohesion: 0.06
Nodes (26): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), CHI 2025: BLV Object-Recognition Technologies in India, Auditory Hand-Steering Guidance for BLV People (CHI 2026), CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021) (+18 more)

### Community 7 - "Camera Calibration Tool"
Cohesion: 0.11
Nodes (11): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, synthetic_view() (+3 more)

### Community 8 - "CI Workflow"
Cohesion: 0.07
Nodes (32): concurrency, cancel-in-progress, group, jobs, laptop, native, percept, name (+24 more)

### Community 9 - "Guided Audio and Stats"
Cohesion: 0.13
Nodes (25): audio_dropped_speech(), audio_main(), audio_publish_stats(), audio_start(), audio_stop(), audio_submit(), law_name(), mode_name() (+17 more)

### Community 10 - "Voice Clip Enum"
Cohesion: 0.06
Nodes (31): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+23 more)

### Community 11 - "camd Frame Tools"
Cohesion: 0.10
Nodes (16): main(), put_u16(), put_u32(), write_bmp(), beacon_crumb_t, beacon_depth_t, beacon_frame_slot_t, beacon_guided_block_t (+8 more)

### Community 12 - "Vocabulary and Vision Models"
Cohesion: 0.11
Nodes (20): Depth Anything V2 Metric Indoor Small INT8, hand (percept-owned fingertip slot), models/labels.txt runtime vocabulary, MediaPipe hands (palm + landmark lite), onnxruntime 1.24.4 (QNX), percept vision process (RR 22, cores 1-3), QNX AI workshop (MediaPipe hands on Pi), Range 1: same camera frame (tabletop reach, no VO) (+12 more)

### Community 13 - "Intent Kinds"
Cohesion: 0.07
Nodes (26): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+18 more)

### Community 14 - "telemd and JPEG Preview"
Cohesion: 0.12
Nodes (13): beacon_frames_t, beacon_live_max_ns(), destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg() (+5 more)

### Community 15 - "Probe Detection and Letterbox"
Cohesion: 0.16
Nodes (10): Affine, detect(), detect_yolo_ort(), letterbox(), load_yolo(), make_affine(), parse_csv3(), predict_depth() (+2 more)

### Community 16 - "Modes, Privacy and Commands"
Cohesion: 0.15
Nodes (19): Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), REPEAT and REJECT commands, Dashboard World-dot View (Scene.jsx, App.jsx), include/beacon.h Shared Header, bridge (UDP-to-WebSocket laptop relay), Saturday Build Order (spec section 13, steps 1-6), 3D Dashboard (Vite + React + three.js), 30-Second Demo Script (spec section 12) (+11 more)

### Community 17 - "Pi Bring-Up and Dev Workflow"
Cohesion: 0.12
Nodes (14): qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB), Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Network Diagnostics Ladder, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay) (+6 more)

### Community 18 - "Open-Vocab Model Choices"
Cohesion: 0.13
Nodes (15): Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Embedding Pose Graph, Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764) (+7 more)

### Community 19 - "Depth Stabiliser"
Cohesion: 0.19
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 20 - "Tape Check Tests"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 21 - "Spec and Demo Lineage"
Cohesion: 0.11
Nodes (16): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), 30-second Sunday demo script, Henomaly (process split + ORT on Pi 5 QNX), Loaner bring-up checklist (QNX image), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md) (+8 more)

### Community 22 - "Guided Overview (README)"
Cohesion: 0.15
Nodes (18): guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon_mode() LIVE/HOLD/LOST Tracking Mode, /beacon_world Shared Memory, fakeworld (scripted percept/voiced stand-in), guided (60 Hz cue synthesizer), Law Module (pure bind/mode/REACH/WALK/RETURN/LOST/STOP/REPEAT/REJECT decisions), guided 60 Hz Loop (seqlock reads, guided_step, absolute-deadline sleep), QNX Platform Layer (runmask, SCHED_FIFO, heartbeat pulse, GPIO piezo) (+10 more)

### Community 23 - "Camera Daemon and Gates"
Cohesion: 0.15
Nodes (16): /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535), Camera Module 3 CSI (imx708, units 3-4, 2304x1296 nv12), Sensor Framework Camera Probe (sensor_rpi5.conf units) (+8 more)

### Community 24 - "Bluetooth Speaker Player"
Cohesion: 0.15
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 25 - "Depth Sampling"
Cohesion: 0.15
Nodes (6): _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), _median_depth(), DepthSamplingTest

### Community 26 - "Guided Entry and World Mapping"
Cohesion: 0.16
Nodes (4): open_world(), sleep_until(), beacon_world_t, open_world()

### Community 27 - "Spec Review Gates"
Cohesion: 0.16
Nodes (13): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, Error handling / failure-mode table, 16.67 ms CLOCK_MONOTONIC guidance loop, slay percept -> HOLD -> LOST failure demo, Pre-Sunday testing requirements (+5 more)

### Community 28 - "Probe Resources and Fingertip"
Cohesion: 0.18
Nodes (5): find_fingertip(), load_depth_session(), load_labels(), load_yolo_session(), ProbeResources

### Community 29 - "Reach Audio Design"
Cohesion: 0.15
Nodes (12): 12-person BLV hand-steering study, GPIO piezo (cannot-fail actuator), REACH guidance law (ticks only), USB headset audio (off-thread playback), No PCM Playback Device on QNX Image (io-snd control only, no 3.5 mm), post_startup.sh Boot Persistence (on -d -p 10, after io-snd), BTstack A2DP Bridge to JBL Go 3 (Combadge-HTN/qnx-bluetooth), supervisor/bt_audio_service.sh Supervisor-managed BT Child (+4 more)

### Community 30 - "Shared Memory and Synthesizer"
Cohesion: 0.23
Nodes (12): /beacon_depth depth slot (shm), /beacon_world WorldState (shm), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, intent (voiced-owned job + candidate names), llama.cpp ~0.5B remap (table miss only), objects[32] session POI store, Spec review (BLOCK, docs/beacon-spec-review.md) (+4 more)

### Community 31 - "Tape Check Tool"
Cohesion: 0.25
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 32 - "Model Files and Labels"
Cohesion: 0.17
Nodes (12): intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), Baked YOLOE Label Vocabulary (64 nouns), export_yoloe.py Detector Export, Optional llama.cpp GGUF, MediaPipe Hand Models, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin, yoloe26n_320.onnx (baked prompts, detect-only) (+4 more)

### Community 33 - "Voice Clip Tools and Tests"
Cohesion: 0.20
Nodes (4): main(), make_inflect(), to_clip(), supervise()

### Community 34 - "Box IoU Slot Association"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 35 - "camd Main Loop"
Cohesion: 0.25
Nodes (11): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+3 more)

### Community 37 - "Calibration Loading"
Cohesion: 0.22
Nodes (6): Calibration, guess_calibration(), load_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 38 - "Breadcrumbs and Navigation Research"
Cohesion: 0.20
Nodes (13): NavCog / NavCog3 (CMU), crumbs[512] breadcrumb trail, OpenCV 4.12 (features2d + calib3d), pose_epoch, Range 2: object still in view (walk while looking, no VO), Range 3: object out of view / RETURN (needs world pose), RETURN ('take me back') breadcrumb retrace, RGB-D visual odometry (ORB + solvePnPRansac) (+5 more)

### Community 39 - "Dashboard Overview (README)"
Cohesion: 0.22
Nodes (11): Bridge Replay (paced by t_ns), Beacon dashboard HTML Entry (#root, /src/main.jsx), animate-ui Primitives, Beacon 3D Dashboard (Vite + React + react-three-fiber), Mode Banner (LIVE / HOLD / LOST), Replay Scrubber (last 10 min of world states), dev-reach.jsonl (made by make-dev-reach.js), CLOCK_MONOTONIC t_ns Timestamps (+3 more)

### Community 40 - "Frame Ring and Bridge (README)"
Cohesion: 0.18
Nodes (10): /beacon_frames Newest-wins Three-slot Ring, dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Seqlock Shared-memory Reads (seq_percept / seq_voiced / seq_guided), bridge (UDP in, WebSocket out, JSONL recording), Session JSONL Recording, Bridge Wire Format (UDP 5005 in, ws://127.0.0.1:8765 out) (+2 more)

### Community 41 - "Frame-ID Seed Test"
Cohesion: 0.27
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 42 - "Model Export Scripts"
Cohesion: 0.21
Nodes (4): main(), __init__(), main(), read_labels()

### Community 43 - "camd Overview (README)"
Cohesion: 0.20
Nodes (9): BMP Bring-up Frame Source (frametype 65535), QNX CamAPI Adapter (not wired yet), camd (camera daemon), Synthetic Stub Frame Source (frametype 0), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), Even seq.* Values (telemd skips torn reads), beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes), nathans-revision.md Design (source of truth) (+1 more)

### Community 45 - "Telemetry Transport"
Cohesion: 0.32
Nodes (12): Live JPEG Camera Panel, useTelemetry.js Bridge WebSocket Hook, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram), World-state JSON Message (~10 Hz), --jpeg Raw UDP Preview Datagram, probe_to_world.py World JSONL / UDP Emitter (+4 more)

### Community 46 - "Core-0 Deadline Test"
Cohesion: 0.27
Nodes (6): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), wait_for()

### Community 47 - "fakeworld Simulator"
Cohesion: 0.38
Nodes (8): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), set_pose_yaw(), world_from_cam()

### Community 48 - "World-Frame Dot Map"
Cohesion: 0.25
Nodes (9): World-frame Dot Map Scene (Scene.jsx), worldScene.js Coordinate Helpers (OpenCV world to three.js), xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), crumbs Breadcrumb Positions, pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), calib.json Camera Intrinsics (laptop-local, gitignored), calibrate_camera.py Chessboard Calibration (+1 more)

### Community 50 - "Depth Pipeline (README)"
Cohesion: 0.29
Nodes (6): Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, Per-instance Depth Slot Median Stabiliser, Box IoU Slot Association (--slot-iou 0.30), tape_check.py Absolute-depth Gate, Visual Odometry (VO)

### Community 51 - "Guidance Cue Fields"
Cohesion: 0.33
Nodes (6): deadline-test (over_period vs over_1ms), Clip Captions (clips.js in enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids)

## Knowledge Gaps
- **129 isolated node(s):** `GUIDED_CMD_FLUSH_SPEECH`, `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK`, `GUIDED_CMD_TONE_OFF` (+124 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 370 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Dashboard World-dot View (Scene.jsx, App.jsx)` connect `Modes, Privacy and Commands` to `Dashboard UI and Deps`, `Breadcrumbs and Navigation Research`, `Dashboard Overview (README)`, `Vocabulary and Vision Models`, `World-Frame Dot Map`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GUIDED_CMD_FLUSH_SPEECH`, `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY` to the rest of the system?**
  _129 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Probe to World Sender` be split into smaller, more focused modules?**
  _Cohesion score 0.05852842809364549 - nodes in this community are weakly interconnected._
- **Why does `Beacon 3D Dashboard (Vite + React + react-three-fiber)` connect `Dashboard Overview (README)` to `Frame Ring and Bridge (README)`, `camd Overview (README)`, `Telemetry Transport`, `Modes, Privacy and Commands`, `World-Frame Dot Map`, `Guidance Cue Fields`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `Probe CLI and Arguments` be split into smaller, more focused modules?**
  _Cohesion score 0.07122153209109731 - nodes in this community are weakly interconnected._