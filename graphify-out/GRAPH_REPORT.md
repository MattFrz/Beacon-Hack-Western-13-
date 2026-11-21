# Graph Report - Beacon-Hack-Western-13-  (2026-11-21)

## Corpus Check
- 28 files · ~88,593 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1396 nodes · 2971 edges · 68 communities (56 shown, 12 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 268 edges (avg confidence: 0.87)
- Token cost: 75,033 input · 0 output

## Community Hubs (Navigation)
- Probe to World Sender
- Guided Law Engine
- Dashboard UI and Deps
- Voice Clip Enum
- Bridge and Caption Clips
- Probe Runtime
- CI Workflow
- Percept Head (C++)
- Frame Tools and JPEG Preview
- Guided Pi Test Plan
- Camera Calibration Tool
- Guided Audio Thread
- Probe Detection and Letterbox
- Audio and Navigation Research
- Reach Audio Design
- Voice Clip Tools and Tests
- camd Overview (README)
- Probe Test Suites
- Telemetry Format (README)
- Breadcrumbs and RETURN
- Spec Review Gates
- Depth Stabiliser
- Tape Check Tests
- Vocabulary and Depth Models
- Pi Bring-Up and Dev Workflow
- Shared-Memory Structs
- Speech Query and POI Store
- Depth Sampling
- Accessibility Research Papers
- Open-Vocab Model Choices
- Bluetooth Speaker Player
- Core-0 Deadline and Platform
- Inclusive Language and Framing
- Tape Check Tool
- Box IoU Slot Association
- camd Main Loop
- Hand-Steering Research
- World-Frame Dot Map
- Privacy and Modes
- telemd Sender
- Dashboard Overview (README)
- Calibration Loading
- Frame-ID Seed Test
- fakeworld Simulator
- Model Files and Labels
- Probe Test Fakes
- Model Export Scripts
- Audio Output Backends
- Typed Commands (beacon_cmd)
- Spec and Demo Lineage
- Intent Kinds
- Laptop World Input (world_in)
- Probe Resources
- Agent Notes and Graph Refresh
- Probe CLI Arguments
- JPEG Preview Encoding
- Clip Loader (clips.c)
- Heartbeat Pulses
- Guidance Laws
- Guidance Cue Fields
- Fake Hand Landmarker
- Fake Webcam
- Fake Video File
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
- **Beacon five-process QNX isolation** — docs_nathans_revision_five_process_architecture, docs_nathans_revision_supervisor, docs_nathans_revision_camd, docs_nathans_revision_guided, docs_nathans_revision_percept, docs_nathans_revision_voiced [EXTRACTED 1.00]
- **Sequential percept vision pipeline** — docs_nathans_revision_sequential_percept_pipeline, docs_nathans_revision_yoloe_26n, docs_nathans_revision_depth_anything_v2, docs_nathans_revision_mediapipe_hands, docs_nathans_revision_rgbd_visual_odometry [EXTRACTED 1.00]
- **QNX mixed-criticality mechanism without APS** — docs_nathans_revision_no_aps, docs_nathans_revision_runmask_core0_isolation, docs_nathans_revision_seqlock, docs_nathans_revision_supervisor, docs_nathans_revision_procmgr_ability, docs_nathans_revision_slay_percept_demo [EXTRACTED 1.00]
- **Bluetooth A2DP Audio Path on QNX** — docs_pi_bringup_bt_a2dp_bridge, docs_pi_bringup_pcm_fifo_contract, docs_pi_bringup_bt_speaker_py, docs_pi_bringup_bt_audio_service, docs_pi_bringup_boot_persistence [EXTRACTED 1.00]
- **Laptop Telemetry and Replay Chain** — docs_team_plan_telemd, docs_team_plan_replay_generator, docs_team_plan_bridge, docs_team_plan_dashboard [EXTRACTED 1.00]
- **Laptop World-dot Pipeline** — docs_pi_bringup_probe_frame_py, docs_superpowers_plans_2026_11_21_world_frame_dots_probe_to_world, laptop_samples_readme_world_sample_json, laptop_bridge_main, docs_superpowers_plans_2026_11_21_world_frame_dots_dashboard_world_view [EXTRACTED 1.00]
- **percept On-device Perception Stack** — percept_readme_percept, models_readme_yoloe26n, models_readme_depth_anything_v2, models_readme_mediapipe_hands, percept_readme_visual_odometry [EXTRACTED 1.00]
- **Telemetry Monitoring Pipeline (telemd -> bridge -> dashboard)** — telemd_readme_telemd, laptop_bridge_readme_bridge, laptop_dashboard_readme_dashboard, laptop_samples_readme_telemetry_format [EXTRACTED 1.00]
- **Newest-wins Buffering Pattern** — camd_readme_beacon_frames_ring, laptop_bridge_readme_newest_wins_backpressure, guided_readme_audio_thread [INFERRED 0.75]
- **Spoken-metre Gating (no metres until tape check passes)** — percept_readme_tape_check, percept_readme_depth_scale, percept_readme_fov_pinhole_guess, percept_readme_calibrate_camera, readme_lost_cue_principle [INFERRED 0.85]
- **Telemetry Flow from Pi or Probe to Dashboard** — readme_telemd, percept_readme_probe_to_world, laptop_samples_readme_udp_port_5005, readme_laptop_bridge, laptop_dashboard_readme_use_telemetry, laptop_dashboard_readme_dashboard [INFERRED 0.85]
- **Stand-ins feeding /beacon_world before real percept/voiced** — guided_readme_fakeworld, voiced_readme_world_in, voiced_readme_fake_probe, voiced_readme_beacon_cmd, guided_readme_beacon_world_shm [INFERRED 0.85]
- **Graph refresh gate for PRs into main** — agents_graph_refresh_workflow, agents_graphify_ci_check, agents_graph_report, agents_graph_json, agents_graph_html [EXTRACTED 1.00]
- **guided Pi validation sequence (build, silent run, JBL, timing under load)** — guided_pi_test_build_step, guided_pi_test_run_without_sound, guided_pi_test_jbl_bluetooth, guided_pi_test_timing_under_load [EXTRACTED 1.00]

## Communities (68 total, 12 thin omitted)

### Community 0 - "Probe to World Sender"
Cohesion: 0.06
Nodes (22): build_parser(), emit_lines(), format_readout(), load_target_names(), main(), _ns(), _number(), _output() (+14 more)

### Community 1 - "Guided Law Engine"
Cohesion: 0.08
Nodes (76): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH (+68 more)

### Community 2 - "Dashboard UI and Deps"
Cohesion: 0.06
Nodes (57): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+49 more)

### Community 3 - "Voice Clip Enum"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 4 - "Bridge and Caption Clips"
Cohesion: 0.07
Nodes (27): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+19 more)

### Community 5 - "Probe Runtime"
Cohesion: 0.13
Nodes (7): main(), prepare(), probe_once(), ProbeRuntimeTest, fake_encode(), synthetic_probe_modules(), synthetic_video_modules()

### Community 6 - "CI Workflow"
Cohesion: 0.07
Nodes (38): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+30 more)

### Community 7 - "Percept Head (C++)"
Cohesion: 0.07
Nodes (26): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+18 more)

### Community 8 - "Frame Tools and JPEG Preview"
Cohesion: 0.12
Nodes (7): main(), put_u16(), put_u32(), write_bmp(), destination_full(), destination_ready(), skip_jpeg()

### Community 9 - "Guided Pi Test Plan"
Cohesion: 0.11
Nodes (31): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+23 more)

### Community 10 - "Camera Calibration Tool"
Cohesion: 0.11
Nodes (11): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, synthetic_view() (+3 more)

### Community 11 - "Guided Audio Thread"
Cohesion: 0.12
Nodes (27): audio_dropped_speech(), audio_main(), audio_publish_stats(), audio_start(), audio_stop(), audio_submit(), law_name(), mode_name() (+19 more)

### Community 12 - "Probe Detection and Letterbox"
Cohesion: 0.14
Nodes (16): Affine, depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip(), letterbox(), load_calibration() (+8 more)

### Community 13 - "Audio and Navigation Research"
Cohesion: 0.11
Nodes (18): Aural and Haptic Feedback for Visually Impaired People on a Track (ICHI), Less is More (VIA-Agent) PVI Study, /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535) (+10 more)

### Community 14 - "Reach Audio Design"
Cohesion: 0.12
Nodes (18): 12-person BLV hand-steering study, Error handling / failure-mode table, GPIO piezo (cannot-fail actuator), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, Range 1: same camera frame (tabletop reach, no VO), REACH guidance law (ticks only), supervisor process (FIFO 63, core 0) (+10 more)

### Community 15 - "Voice Clip Tools and Tests"
Cohesion: 0.16
Nodes (8): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips(), supervise()

### Community 16 - "camd Overview (README)"
Cohesion: 0.11
Nodes (17): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0), run_scenario.sh script (+9 more)

### Community 18 - "Telemetry Format (README)"
Cohesion: 0.16
Nodes (19): QNX CamAPI Adapter (not wired yet), Live JPEG Camera Panel, useTelemetry.js Bridge WebSocket Hook, intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram), World-state JSON Message (~10 Hz) (+11 more)

### Community 19 - "Breadcrumbs and RETURN"
Cohesion: 0.17
Nodes (19): NavCog / NavCog3 (CMU), /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, 30-second Sunday demo script, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite), objects[32] session POI store, OpenCV 4.12 (features2d + calib3d) (+11 more)

### Community 20 - "Spec Review Gates"
Cohesion: 0.14
Nodes (15): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, 16.67 ms CLOCK_MONOTONIC guidance loop, Range 2: object still in view (walk while looking, no VO), Pre-Sunday testing requirements, WALK guidance law (spoken instruction) (+7 more)

### Community 21 - "Depth Stabiliser"
Cohesion: 0.19
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 22 - "Tape Check Tests"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 23 - "Vocabulary and Depth Models"
Cohesion: 0.12
Nodes (15): /beacon_depth depth slot (shm), Depth Anything V2 Metric Indoor Small INT8, models/labels.txt runtime vocabulary, Loaner bring-up checklist (QNX image), onnxruntime 1.24.4 (QNX), Pinhole unprojection to p_cam / p_world, YOLOE-26n baked detect-only ONNX detector, Loaner Pi Bring-up Log (+7 more)

### Community 24 - "Pi Bring-Up and Dev Workflow"
Cohesion: 0.14
Nodes (14): qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB), Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Network Diagnostics Ladder, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay) (+6 more)

### Community 25 - "Shared-Memory Structs"
Cohesion: 0.12
Nodes (12): beacon_crumb_t, beacon_depth_t, beacon_frame_slot_t, beacon_guided_block_t, beacon_guided_display_t, beacon_guided_stats_t, beacon_hand_t, beacon_letterbox_t (+4 more)

### Community 26 - "Speech Query and POI Store"
Cohesion: 0.13
Nodes (16): Embedding Pose Graph, llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, NLMap, intent (voiced-owned job + candidate names), llama.cpp ~0.5B remap (table miss only), REPEAT and REJECT commands, Spec review (BLOCK, docs/beacon-spec-review.md) (+8 more)

### Community 27 - "Depth Sampling"
Cohesion: 0.13
Nodes (5): _central_bounds(), depth_at_box(), make_affine(), parse_csv3(), DepthSamplingTest

### Community 28 - "Accessibility Research Papers"
Cohesion: 0.14
Nodes (13): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), CHI 2025: BLV Object-Recognition Technologies in India, Multi-Purpose Camera Apps (Seeing AI, Lookout, Be My Eyes, Envision), Find My Things (Morrison et al., ASSETS 2023), Floor-Level Dropped Items Scope Gap (+5 more)

### Community 29 - "Open-Vocab Model Choices"
Cohesion: 0.16
Nodes (14): Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764), ONNX Runtime 1.24.4 on QNX, Ultralytics YOLOE Docs, YOLO-World INT8 TFLite (+6 more)

### Community 30 - "Bluetooth Speaker Player"
Cohesion: 0.16
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 31 - "Core-0 Deadline and Platform"
Cohesion: 0.17
Nodes (5): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns()

### Community 32 - "Inclusive Language and Framing"
Cohesion: 0.12
Nodes (7): CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021), Hoffman-Andrews et al., Cure Rhetoric Criticized by Blind Participants, Inclusive Language and Non-Cure Framing, Independence as Control, Not Avoiding Help, AprilTag fob (rejected physical tag identity), Nov 20 Beacon build plan (superseded, removed)

### Community 33 - "Tape Check Tool"
Cohesion: 0.25
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 34 - "Box IoU Slot Association"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 35 - "camd Main Loop"
Cohesion: 0.25
Nodes (11): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+3 more)

### Community 36 - "Hand-Steering Research"
Cohesion: 0.14
Nodes (8): Auditory Hand-Steering Guidance for BLV People (CHI 2026), HoldLight (BLV climbers), Evaluation of Short-Range Depth Sonifications (IEEE THMS), UI Preferences for a Camera-Based Wayfinding Aid (JVIB), NavGraph Parsimonious Instructions, Guidance Laws (STOP, LOST, REACH, WALK, RETURN), guided (60 Hz guidance synthesizer), Timing Panel (guided stats block under seq_guided)

### Community 37 - "World-Frame Dot Map"
Cohesion: 0.17
Nodes (13): World-frame Dot Map Scene (Scene.jsx), worldScene.js Coordinate Helpers (OpenCV world to three.js), xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), crumbs Breadcrumb Positions, pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export (+5 more)

### Community 38 - "Privacy and Modes"
Cohesion: 0.23
Nodes (12): Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), telemd optional monitoring process, Dashboard World-dot View (Scene.jsx, App.jsx), Wearer Dot at pose.T_world_from_cam Translation, bridge (UDP-to-WebSocket laptop relay), 3D Dashboard (Vite + React + three.js), 30-Second Demo Script (spec section 12), Guidance Modes LIVE / HOLD / LOST (+4 more)

### Community 39 - "telemd Sender"
Cohesion: 0.19
Nodes (10): beacon_frames_t, beacon_live_max_ns(), preview_tick(), sample_frame(), send_jpeg(), escape_name(), heartbeat_alive(), main() (+2 more)

### Community 40 - "Dashboard Overview (README)"
Cohesion: 0.22
Nodes (11): Bridge Replay (paced by t_ns), Beacon dashboard HTML Entry (#root, /src/main.jsx), animate-ui Primitives, Beacon 3D Dashboard (Vite + React + react-three-fiber), Mode Banner (LIVE / HOLD / LOST), Replay Scrubber (last 10 min of world states), dev-reach.jsonl (made by make-dev-reach.js), CLOCK_MONOTONIC t_ns Timestamps (+3 more)

### Community 41 - "Calibration Loading"
Cohesion: 0.23
Nodes (5): Calibration, guess_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 42 - "Frame-ID Seed Test"
Cohesion: 0.27
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 43 - "fakeworld Simulator"
Cohesion: 0.27
Nodes (10): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+2 more)

### Community 44 - "Model Files and Labels"
Cohesion: 0.21
Nodes (9): Baked YOLOE Label Vocabulary (64 nouns), export_yoloe.py Detector Export, Optional llama.cpp GGUF, MediaPipe Hand Models, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin, yoloe26n_320.onnx (baked prompts, detect-only), probe_frame.py Laptop Stand-in (+1 more)

### Community 46 - "Model Export Scripts"
Cohesion: 0.21
Nodes (4): main(), __init__(), main(), read_labels()

### Community 47 - "Audio Output Backends"
Cohesion: 0.29
Nodes (9): audio_out_close(), audio_out_open(), audio_out_write(), fifo_try_open(), fifo_write(), put16(), put32(), qnx_open() (+1 more)

### Community 48 - "Typed Commands (beacon_cmd)"
Cohesion: 0.25
Nodes (9): open_world(), beacon_world_t, open_world(), add(), handle(), is_skip(), kind_name(), main() (+1 more)

### Community 49 - "Spec and Demo Lineage"
Cohesion: 0.22
Nodes (9): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), procmgr_ability priority ability and root drop, QNX prize research (QNX-research.md) (+1 more)

### Community 50 - "Intent Kinds"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

### Community 51 - "Laptop World Input (world_in)"
Cohesion: 0.38
Nodes (9): apply(), find_key(), get_num(), get_str(), get_vec3(), main(), publish(), row_for() (+1 more)

### Community 53 - "Agent Notes and Graph Refresh"
Cohesion: 0.28
Nodes (8): Beacon: notes for coding agents, graphify-out/graph.html, graphify-out/graph.json, graphify-out/GRAPH_REPORT.md (code/spec/docs map), 'graphify graph updated' CI check, graphify update . (code-only, no LLM), /graphify . --update (Claude Code skill run), CLAUDE.md (imports AGENTS.md)

### Community 54 - "Probe CLI Arguments"
Cohesion: 0.28
Nodes (5): build_parser(), _positive_float_arg(), _positive_int_arg(), parse(), _unit_float_arg()

### Community 56 - "Clip Loader (clips.c)"
Cohesion: 0.43
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 57 - "Heartbeat Pulses"
Cohesion: 0.25
Nodes (8): beacon_pulse, BEACON_PULSE_AUDIO_UNDERRUN, BEACON_PULSE_HB_CAMD, BEACON_PULSE_HB_GUIDED, BEACON_PULSE_HB_PERCEPT, BEACON_PULSE_HB_VOICED, BEACON_PULSE_INTENT_EDGE, BEACON_PULSE_SUP_TICK

### Community 58 - "Guidance Laws"
Cohesion: 0.29
Nodes (7): beacon_law, BEACON_LAW_LOST, BEACON_LAW_NONE, BEACON_LAW_REACH, BEACON_LAW_RETURN, BEACON_LAW_STOP, BEACON_LAW_WALK

### Community 59 - "Guidance Cue Fields"
Cohesion: 0.33
Nodes (6): deadline-test (over_period vs over_1ms), Clip Captions (clips.js in enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids)

## Knowledge Gaps
- **165 isolated node(s):** `full_h`, `full_w`, `net_h`, `net_w`, `pad_x` (+160 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 420 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `beacon_clip` connect `Voice Clip Enum` to `Shared-Memory Structs`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `full_h`, `full_w`, `net_h` to the rest of the system?**
  _165 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Probe to World Sender` be split into smaller, more focused modules?**
  _Cohesion score 0.05711086226203808 - nodes in this community are weakly interconnected._
- **Why does `Dashboard World-dot View (Scene.jsx, App.jsx)` connect `Privacy and Modes` to `Dashboard UI and Deps`, `World-Frame Dot Map`, `Dashboard Overview (README)`, `Audio and Navigation Research`, `Breadcrumbs and RETURN`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Guided Law Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.08471275559883155 - nodes in this community are weakly interconnected._