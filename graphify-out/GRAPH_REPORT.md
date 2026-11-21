# Graph Report - beacon-wearer  (2026-11-21)

## Corpus Check
- 18 files · ~89,458 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1410 nodes · 3008 edges · 76 communities (63 shown, 13 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 263 edges (avg confidence: 0.86)
- Token cost: 83,514 input · 0 output

## Community Hubs (Navigation)
- Probe to World Sender
- Guided Law Engine
- Voice Clip Tools and Tests
- Voice Clip Enum
- Bridge and Caption Clips
- Probe Runtime
- CI Workflow
- Percept Head (C++)
- Probe Detection and Letterbox
- camd Frame Tools
- Guided Audio Output
- Camera Calibration Tool
- Dashboard Dependencies
- Breadcrumbs and RETURN
- Dashboard Header and Replay (README)
- Guided Pi Test Plan
- Dashboard 3D Scene
- Telemetry Fields (README)
- Probe Test Suites
- Depth Stabiliser
- Tape Check Tests
- Reach Audio Design
- Shared-Memory Structs
- Core-0 Deadline and Platform
- Shared Memory and Synthesizer
- camd Overview (README)
- Spec Review Gates
- Dashboard App and Panels
- Spec and Demo Lineage
- Pi Bring-Up and Dev Workflow
- Tape Check Tool
- Box IoU Slot Association
- camd Main Loop
- Telemetry and Model Files (READMEs)
- Calibration Loading
- Vocabulary and Depth Models
- Spec Review Verdict
- Reach Law and BLV Study
- telemd and JPEG Preview
- Depth Sampling
- Probe Test Fakes
- Audio Out Backends (asound, FIFO)
- Accessibility and Model Research
- Camera Daemon and Gates
- Audio Stats and Typed Commands
- Blind-User Guidance Design
- Hand-Steering Research
- fakeworld Simulator
- Intent Kinds
- Pose and Depth Sampling
- Laptop World Input (world_in)
- Open-Vocab Models on Pi
- Supervisor and Heartbeat Faults
- Probe CLI Arguments
- Probe Resources
- Clip Loader (clips.c)
- Voice Intent and Binding
- Guided Command Kinds
- JPEG Preview Encoder
- Pulse Codes
- Guidance Laws
- Guided Cues and Demo Replay
- Model Runtimes and Packaging
- Session Memory and Query Remap
- Pi Boot and Network Recovery
- Fake Landmarker Test Double
- Fake Webcam
- Fake Video File
- Agent Notes and Graph Refresh
- Inclusive Language
- Fake ONNX Session
- BT Audio Service
- Radio Auto Script
- No-Tag Homing

## God Nodes (most connected - your core abstractions)
1. `beacon_clip` - 60 edges
2. `probe_to_world()` - 46 edges
3. `guided_step()` - 41 edges
4. `make_probe()` - 37 edges
5. `probe_once()` - 36 edges
6. `ProbeRuntimeTest` - 34 edges
7. `ProbeToWorldTest` - 32 edges
8. `prepare()` - 26 edges
9. `make_detection()` - 20 edges
10. `synthetic_probe_modules()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Heartbeat Fault Detection and Restart with Backoff` --semantically_similar_to--> `Processes Panel (heartbeat age, down at >=1 s)`  [INFERRED] [semantically similar]
  supervisor/README.md → telemd/README.md
- `world_in (laptop-camera fallback bridge to /beacon_world)` --semantically_similar_to--> `fakeworld (scripted percept/voiced stand-in)`  [INFERRED] [semantically similar]
  voiced/README.md → guided/README.md
- `probe_to_world.py World JSONL / UDP Emitter` --semantically_similar_to--> `telemd (read-only telemetry to the laptop)`  [INFERRED] [semantically similar]
  percept/README.md → README.md
- `--jpeg Raw UDP Preview Datagram` --semantically_similar_to--> `Optional Video JPEG (~5 fps, <60 KB per datagram)`  [INFERRED] [semantically similar]
  percept/README.md → laptop/samples/README.md
- `Processes Panel (heartbeat age, down at >=1 s)` --semantically_similar_to--> `NO DATA after 1 s without world state`  [INFERRED] [semantically similar]
  telemd/README.md → laptop/dashboard/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Evidence-Backed Audio UX for a Chest-Worn Homing Device** — docs_beacon_accessibility_research_walk_speech_reach_ticks, docs_beacon_accessibility_research_tick_rate_distance_encoding, docs_beacon_accessibility_research_off_axis_search_cue, docs_beacon_accessibility_research_honest_lost_cue, docs_beacon_accessibility_research_open_ear_audio, docs_beacon_accessibility_research_parsimonious_instructions [EXTRACTED 1.00]
- **Beacon five-process QNX isolation** — docs_nathans_revision_five_process_architecture, docs_nathans_revision_supervisor, docs_nathans_revision_camd, docs_nathans_revision_guided, docs_nathans_revision_percept, docs_nathans_revision_voiced [EXTRACTED 1.00]
- **Sequential percept vision pipeline** — docs_nathans_revision_sequential_percept_pipeline, docs_nathans_revision_yoloe_26n, docs_nathans_revision_depth_anything_v2, docs_nathans_revision_mediapipe_hands, docs_nathans_revision_rgbd_visual_odometry [EXTRACTED 1.00]
- **QNX mixed-criticality mechanism without APS** — docs_nathans_revision_no_aps, docs_nathans_revision_runmask_core0_isolation, docs_nathans_revision_seqlock, docs_nathans_revision_supervisor, docs_nathans_revision_procmgr_ability, docs_nathans_revision_slay_percept_demo [EXTRACTED 1.00]
- **Bluetooth A2DP Audio Path on QNX** — docs_pi_bringup_bt_a2dp_bridge, docs_pi_bringup_pcm_fifo_contract, docs_pi_bringup_bt_speaker_py, docs_pi_bringup_bt_audio_service, docs_pi_bringup_boot_persistence [EXTRACTED 1.00]
- **guided Pi validation sequence (build, silent run, JBL, timing under load)** — guided_pi_test_build_step, guided_pi_test_run_without_sound, guided_pi_test_jbl_bluetooth, guided_pi_test_timing_under_load [EXTRACTED 1.00]
- **Laptop Telemetry and Replay Chain** — docs_team_plan_telemd, docs_team_plan_replay_generator, docs_team_plan_bridge, docs_team_plan_dashboard [EXTRACTED 1.00]
- **Laptop World-dot Pipeline** — docs_pi_bringup_probe_frame_py, docs_superpowers_plans_2026_11_21_world_frame_dots_probe_to_world, laptop_samples_readme_world_sample_json, laptop_bridge_main, docs_superpowers_plans_2026_11_21_world_frame_dots_dashboard_world_view [EXTRACTED 1.00]
- **percept On-device Perception Stack** — percept_readme_percept, models_readme_yoloe26n, models_readme_depth_anything_v2, models_readme_mediapipe_hands, percept_readme_visual_odometry [EXTRACTED 1.00]
- **Stand-ins feeding /beacon_world before real percept/voiced** — guided_readme_fakeworld, voiced_readme_world_in, voiced_readme_fake_probe, voiced_readme_beacon_cmd, guided_readme_beacon_world_shm [INFERRED 0.85]
- **Spoken-metre Gating (no metres until tape check passes)** — percept_readme_tape_check, percept_readme_depth_scale, percept_readme_fov_pinhole_guess, percept_readme_calibrate_camera, readme_lost_cue_principle [INFERRED 0.85]
- **Telemetry Flow from Pi or Probe to Dashboard** — readme_telemd, percept_readme_probe_to_world, laptop_samples_readme_udp_port_5005, readme_laptop_bridge, laptop_dashboard_readme_dashboard [INFERRED 0.85]
- **Live telemetry pipeline: Pi telemd -> UDP 5005 -> bridge -> WebSocket 8765 -> dashboard** — laptop_bridge_readme_telemd, laptop_bridge_readme_udp_ingest_port_5005, laptop_bridge_readme_bridge, laptop_bridge_readme_websocket_out_8765, laptop_dashboard_src_usetelemetry, laptop_dashboard_readme_dashboard [EXTRACTED 1.00]
- **Recording, replay and dashboard history** — laptop_bridge_readme_session_recording_jsonl, laptop_bridge_readme_replay_mode, laptop_bridge_readme_dev_reach_sample, laptop_dashboard_readme_replay_scrubber, laptop_dashboard_readme_events_panel [INFERRED 0.85]
- **Graph refresh gate on PRs into main** — agents_graphify_graph_updated_check, agents_graph_refresh_workflow, agents_committed_graph_artifacts [EXTRACTED 1.00]

## Communities (76 total, 13 thin omitted)

### Community 0 - "Probe to World Sender"
Cohesion: 0.06
Nodes (22): build_parser(), emit_lines(), format_readout(), load_target_names(), main(), _ns(), _number(), _output() (+14 more)

### Community 1 - "Guided Law Engine"
Cohesion: 0.10
Nodes (67): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+59 more)

### Community 2 - "Voice Clip Tools and Tests"
Cohesion: 0.05
Nodes (27): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout(), main() (+19 more)

### Community 3 - "Voice Clip Enum"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 4 - "Bridge and Caption Clips"
Cohesion: 0.06
Nodes (31): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+23 more)

### Community 5 - "Probe Runtime"
Cohesion: 0.14
Nodes (6): prepare(), probe_once(), ProbeRuntimeTest, fake_encode(), synthetic_probe_modules(), synthetic_video_modules()

### Community 6 - "CI Workflow"
Cohesion: 0.07
Nodes (38): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+30 more)

### Community 7 - "Percept Head (C++)"
Cohesion: 0.07
Nodes (26): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+18 more)

### Community 8 - "Probe Detection and Letterbox"
Cohesion: 0.13
Nodes (17): Affine, _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip() (+9 more)

### Community 9 - "camd Frame Tools"
Cohesion: 0.12
Nodes (7): main(), put_u16(), put_u32(), write_bmp(), destination_full(), destination_ready(), skip_jpeg()

### Community 10 - "Guided Audio Output"
Cohesion: 0.12
Nodes (27): audio_dropped_speech(), audio_main(), audio_publish_stats(), audio_start(), audio_stop(), audio_submit(), law_name(), mode_name() (+19 more)

### Community 11 - "Camera Calibration Tool"
Cohesion: 0.13
Nodes (10): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, write_synthetic_views() (+2 more)

### Community 12 - "Dashboard Dependencies"
Cohesion: 0.09
Nodes (28): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+20 more)

### Community 13 - "Breadcrumbs and RETURN"
Cohesion: 0.11
Nodes (23): NavCog / NavCog3 (CMU), Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), slay percept -> HOLD -> LOST failure demo, telemd optional monitoring process, Crumb Trail Dots (crumbs[].xyz_world), Dashboard World-dot View (Scene.jsx, App.jsx), Laptop RGB-D Odometry (ORB + solvePnPRansac, keyframes, crumbs), Wearer Dot at pose.T_world_from_cam Translation (+15 more)

### Community 14 - "Dashboard Header and Replay (README)"
Cohesion: 0.12
Nodes (19): bridge README, bridge (Node UDP-to-WebSocket relay and recorder), dev-reach.jsonl sample (walk, reach, slay percept -> HOLD -> LOST), Optional live JPEG video frames, Live status line every 5 s (world, video, dropped, dashboards), Bridge replay mode (paced by t_ns), Session recording to recordings/<UTC>.jsonl, telemd (Pi telemetry sender) (+11 more)

### Community 15 - "Guided Pi Test Plan"
Cohesion: 0.15
Nodes (22): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+14 more)

### Community 16 - "Dashboard 3D Scene"
Cohesion: 0.25
Nodes (20): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+12 more)

### Community 17 - "Telemetry Fields (README)"
Cohesion: 0.14
Nodes (19): QNX CamAPI Adapter (not wired yet), xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram) (+11 more)

### Community 19 - "Depth Stabiliser"
Cohesion: 0.19
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 20 - "Tape Check Tests"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 21 - "Reach Audio Design"
Cohesion: 0.14
Nodes (15): Error handling / failure-mode table, GPIO piezo (cannot-fail actuator), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, Range 2: object still in view (walk while looking, no VO), supervisor process (FIFO 63, core 0), USB headset audio (off-thread playback), WALK guidance law (spoken instruction) (+7 more)

### Community 22 - "Shared-Memory Structs"
Cohesion: 0.12
Nodes (12): beacon_crumb_t, beacon_depth_t, beacon_frame_slot_t, beacon_guided_block_t, beacon_guided_display_t, beacon_guided_stats_t, beacon_hand_t, beacon_letterbox_t (+4 more)

### Community 23 - "Core-0 Deadline and Platform"
Cohesion: 0.16
Nodes (5): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns()

### Community 24 - "Shared Memory and Synthesizer"
Cohesion: 0.21
Nodes (16): /beacon_depth depth slot (shm), /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, Depth Anything V2 Metric Indoor Small INT8, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite), objects[32] session POI store, onnxruntime 1.24.4 (QNX) (+8 more)

### Community 25 - "camd Overview (README)"
Cohesion: 0.14
Nodes (14): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0), run_scenario.sh script (+6 more)

### Community 26 - "Spec Review Gates"
Cohesion: 0.18
Nodes (14): First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Busy-loop core 0 deadline test, 16.67 ms CLOCK_MONOTONIC guidance loop, Loaner bring-up checklist (QNX image), QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), Pre-Sunday testing requirements, Weekend build order (geometry order) (+6 more)

### Community 27 - "Dashboard App and Panels"
Cohesion: 0.27
Nodes (14): dashboard README, animate-ui primitives (Highlight, RollingText, SlidingNumber, Slider, Button), App(), Caption(), isNum(), measured(), MODES, msAgo() (+6 more)

### Community 28 - "Spec and Demo Lineage"
Cohesion: 0.14
Nodes (13): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), 30-second Sunday demo script, Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), procmgr_ability priority ability and root drop (+5 more)

### Community 29 - "Pi Bring-Up and Dev Workflow"
Cohesion: 0.16
Nodes (10): qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB), Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay), QNXE-195 ssh-rsa Host Key Negotiation (+2 more)

### Community 30 - "Tape Check Tool"
Cohesion: 0.25
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 31 - "Box IoU Slot Association"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 32 - "camd Main Loop"
Cohesion: 0.25
Nodes (11): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+3 more)

### Community 33 - "Telemetry and Model Files (READMEs)"
Cohesion: 0.19
Nodes (11): crumbs Breadcrumb Positions, Baked YOLOE Label Vocabulary (64 nouns), export_yoloe.py Detector Export, Optional llama.cpp GGUF, MediaPipe Hand Models, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin, yoloe26n_320.onnx (baked prompts, detect-only) (+3 more)

### Community 34 - "Calibration Loading"
Cohesion: 0.22
Nodes (6): Calibration, guess_calibration(), load_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 35 - "Vocabulary and Depth Models"
Cohesion: 0.18
Nodes (11): Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), models/labels.txt runtime vocabulary, YOLOE-26n baked detect-only ONNX detector, Depth Anything V2 Static ONNX Export (210x210 metric), MediaPipe hand_landmarker.task Probe, percept/tools/probe_frame.py Laptop Probe, YOLOE-26n Detect-only ONNX Export (32 labels, (1,36,2100), no NMS), Depth Anything V2 Metric Indoor Small (+3 more)

### Community 36 - "Spec Review Verdict"
Cohesion: 0.15
Nodes (4): Beacon spec adversarial review, Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), AprilTag fob (rejected physical tag identity), Nov 20 Beacon build plan (superseded, removed)

### Community 37 - "Reach Law and BLV Study"
Cohesion: 0.16
Nodes (9): 12-person BLV hand-steering study, Range 1: same camera frame (tabletop reach, no VO), REACH guidance law (ticks only), Laptop Calibration and Tape Check (models/calib.json, 0.5/1/2 m), percept/tools/probe_to_world.py World JSONL Wrapper, Range 1 Tabletop Proof (no odometry), dev-reach.jsonl (made by make-dev-reach.js), world.sample.json (+1 more)

### Community 38 - "telemd and JPEG Preview"
Cohesion: 0.19
Nodes (10): beacon_frames_t, beacon_live_max_ns(), preview_tick(), sample_frame(), send_jpeg(), escape_name(), heartbeat_alive(), main() (+2 more)

### Community 39 - "Depth Sampling"
Cohesion: 0.15
Nodes (3): make_affine(), parse_csv3(), DepthSamplingTest

### Community 41 - "Audio Out Backends (asound, FIFO)"
Cohesion: 0.29
Nodes (9): audio_out_close(), audio_out_open(), audio_out_write(), fifo_try_open(), fifo_write(), put16(), put32(), qnx_open() (+1 more)

### Community 42 - "Accessibility and Model Research"
Cohesion: 0.20
Nodes (9): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), CHI 2025: BLV Object-Recognition Technologies in India, Multi-Purpose Camera Apps (Seeing AI, Lookout, Be My Eyes, Envision), Find My Things (Morrison et al., ASSETS 2023), Floor-Level Dropped Items Scope Gap, Kientz et al., Where's My Stuff? (ASSETS 2006), Tactile-First Problem-Solving Hierarchy (+1 more)

### Community 43 - "Camera Daemon and Gates"
Cohesion: 0.24
Nodes (11): /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535), QNX /beacon_frames shm Round-trip (camd --bmp -> read-frames -> dump-frame), World-frame 3D Dots Plan, Logitech C270 Stand-In Camera and Mic, camd (camera process) (+3 more)

### Community 44 - "Audio Stats and Typed Commands"
Cohesion: 0.25
Nodes (9): open_world(), beacon_world_t, open_world(), add(), handle(), is_skip(), kind_name(), main() (+1 more)

### Community 45 - "Blind-User Guidance Design"
Cohesion: 0.22
Nodes (7): AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), HoldLight (BLV climbers), UI Preferences for a Camera-Based Wayfinding Aid (JVIB), NavGraph Parsimonious Instructions, Sighted by Default: Calibrated Honesty (CHI 2026), This is My Fault, Really? BLV Perception of LVLM Hallucination (UIST 2025)

### Community 46 - "Hand-Steering Research"
Cohesion: 0.18
Nodes (7): Auditory Hand-Steering Guidance for BLV People (CHI 2026), Aural and Haptic Feedback for Visually Impaired People on a Track (ICHI), Evaluation of Short-Range Depth Sonifications (IEEE THMS), Less is More (VIA-Agent) PVI Study, Camera Module 3 CSI (imx708, units 3-4, 2304x1296 nv12), Guidance Laws (STOP, LOST, REACH, WALK, RETURN), Hardware Request (USB audio, piezo, Camera Module 3)

### Community 47 - "fakeworld Simulator"
Cohesion: 0.35
Nodes (9): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+1 more)

### Community 48 - "Intent Kinds"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

### Community 49 - "Pose and Depth Sampling"
Cohesion: 0.20
Nodes (8): pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, Per-instance Depth Slot Median Stabiliser, Box IoU Slot Association (--slot-iou 0.30), tape_check.py Absolute-depth Gate, Visual Odometry (VO)

### Community 50 - "Laptop World Input (world_in)"
Cohesion: 0.38
Nodes (9): apply(), find_key(), get_num(), get_str(), get_vec3(), main(), publish(), row_for() (+1 more)

### Community 51 - "Open-Vocab Models on Pi"
Cohesion: 0.31
Nodes (7): Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, Ultralytics YOLOE Docs, YOLO-World INT8 TFLite, YOLO-Worldv2-s ONNX, YOLOE-26n-seg (text-prompted, baked static ONNX), YOLOE-26n-seg-pf (prompt-free, 4,585 names)

### Community 52 - "Supervisor and Heartbeat Faults"
Cohesion: 0.22
Nodes (9): /beacon_world Shared Memory, Seqlock Shared-memory Reads (seq_percept / seq_voiced / seq_guided), Dummy Worker Heartbeat Test, Heartbeat Fault Detection and Restart with Backoff, Piezo Fault Path, supervisor (spawn, runmasks, heartbeats, restarts), beacon_cmd (typed commands to intent block), Synonym Table (with REPEAT / REJECT, llama.cpp on miss) (+1 more)

### Community 53 - "Probe CLI Arguments"
Cohesion: 0.24
Nodes (6): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), _unit_float_arg()

### Community 55 - "Clip Loader (clips.c)"
Cohesion: 0.36
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 56 - "Voice Intent and Binding"
Cohesion: 0.28
Nodes (8): intent (voiced-owned job + candidate names), llama.cpp ~0.5B remap (table miss only), REPEAT and REJECT commands, Spec review (BLOCK, docs/beacon-spec-review.md), Synonym / keyword table (fast path), voiced speech process (RR 18, cores 1-3), whisper.cpp tiny.en (speech in, spec), whisper.cpp tiny.en

### Community 57 - "Guided Command Kinds"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 59 - "Pulse Codes"
Cohesion: 0.25
Nodes (8): beacon_pulse, BEACON_PULSE_AUDIO_UNDERRUN, BEACON_PULSE_HB_CAMD, BEACON_PULSE_HB_GUIDED, BEACON_PULSE_HB_PERCEPT, BEACON_PULSE_HB_VOICED, BEACON_PULSE_INTENT_EDGE, BEACON_PULSE_SUP_TICK

### Community 60 - "Guidance Laws"
Cohesion: 0.29
Nodes (7): beacon_law, BEACON_LAW_LOST, BEACON_LAW_NONE, BEACON_LAW_REACH, BEACON_LAW_RETURN, BEACON_LAW_STOP, BEACON_LAW_WALK

### Community 61 - "Guided Cues and Demo Replay"
Cohesion: 0.33
Nodes (6): deadline-test (over_period vs over_1ms), Clip caption table (enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids)

### Community 62 - "Model Runtimes and Packaging"
Cohesion: 0.33
Nodes (4): CLIP / MobileCLIP2 Region Retrieval, CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764), ONNX Runtime 1.24.4 on QNX, QNX Inference Runtime Packages (still missing)

### Community 63 - "Session Memory and Query Remap"
Cohesion: 0.33
Nodes (4): Embedding Pose Graph, llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, NLMap

### Community 64 - "Pi Boot and Network Recovery"
Cohesion: 0.40
Nodes (4): Network Diagnostics Ladder, QNXE-1894 Wi-Fi Settings Copy Bug, QNXE-2016 Shared Default Wi-Fi MAC, Serial Console (UART on 40-pin header)

### Community 68 - "Agent Notes and Graph Refresh"
Cohesion: 0.70
Nodes (3): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), CLAUDE.md (imports AGENTS.md)

### Community 69 - "Inclusive Language"
Cohesion: 0.40
Nodes (5): CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021), Hoffman-Andrews et al., Cure Rhetoric Criticized by Blind Participants, Inclusive Language and Non-Cure Framing, Independence as Control, Not Avoiding Help

## Knowledge Gaps
- **163 isolated node(s):** `BEACON_INTENT_FIND`, `BEACON_INTENT_GO`, `BEACON_INTENT_NACK_CANT`, `BEACON_INTENT_NACK_UNHEARD`, `BEACON_INTENT_NACK_UNSEEN` (+158 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 421 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clip caption table (enum beacon_clip order)` connect `Guided Cues and Demo Replay` to `Bridge and Caption Clips`, `Shared-Memory Structs`?**
  _High betweenness centrality (0.412) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BEACON_INTENT_FIND`, `BEACON_INTENT_GO`, `BEACON_INTENT_NACK_CANT` to the rest of the system?**
  _163 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Probe to World Sender` be split into smaller, more focused modules?**
  _Cohesion score 0.05711086226203808 - nodes in this community are weakly interconnected._
- **Why does `dashboard README` connect `Dashboard App and Panels` to `Dashboard 3D Scene`, `Spec and Demo Lineage`, `Bridge and Caption Clips`, `Dashboard Header and Replay (README)`?**
  _High betweenness centrality (0.206) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Guided Law Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.10434782608695652 - nodes in this community are weakly interconnected._