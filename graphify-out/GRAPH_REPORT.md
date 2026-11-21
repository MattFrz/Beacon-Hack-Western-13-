# Graph Report - beacon  (2026-11-21)

## Corpus Check
- 97 files · ~90,115 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: (none) 11, .jsonl 2, .css 1)

## Summary
- 1411 nodes · 3038 edges · 68 communities (55 shown, 13 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 279 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- test_frame_id_seed.py
- guided_step
- beacon_clip
- Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)
- probe_frame_test.py
- probe_once
- probe_to_world Conversion
- with
- calibrate_images
- Bridge Relay and Replay
- probe_frame.py
- head.cpp
- Beacon Accessibility Research
- guided/src/main.c
- Guided Pi Test Plan
- Dashboard Dependencies
- DepthStabiliser
- Probe CLI and UDP Streaming
- beacon_intent_kind
- Guidance Runtime and Safety
- percept vision process (RR 22, cores 1-3)
- beacon.h
- Dashboard 3D Scene
- telemd.c
- guided (60 Hz guidance synthesizer)
- Saturday Build Order (spec section 13, steps 1-6)
- TapeCheckTest
- Beacon (chest-worn item-homing wearable)
- Mode Banner (LIVE / HOLD / LOST)
- Dashboard App and Panels
- deadline_test.c
- Guided Audio Thread
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- guided synthesizer (FIFO 58, core 0)
- percept (perception process)
- probe_to_world Output
- camd/src/main.c
- camd Frame Ring and Bring-up
- Model Files Directory (not committed)
- Clip Captions and Events Panel
- C270 Capture on QNX
- resolve_calibration
- DepthSamplingTest
- .patch_chair_frames
- Audio Out Backends (asound, FIFO)
- Guided Cues and Demo Replay
- fakeworld.c
- world_in.c
- beacon_cmd.c
- Pose and Depth Sampling
- build_parser
- ProbeResources
- string
- guided_cmd_kind
- encode_preview
- SlotTracker
- FakeLandmarker
- FakeCapture
- FakeFileCapture
- Refresh the graph before a PR into main
- Label Loading
- bt_audio_service.sh
- run-radio-auto.sh
- voiced Intent Commands
- AirTag Precision Finding
- irl_test.sh
- pi_live.sh

## God Nodes (most connected - your core abstractions)
1. `beacon_clip` - 60 edges
2. `probe_to_world()` - 46 edges
3. `guided_step()` - 41 edges
4. `make_probe()` - 37 edges
5. `probe_once()` - 36 edges
6. `ProbeRuntimeTest` - 34 edges
7. `ProbeToWorldTest` - 32 edges
8. `prepare()` - 26 edges
9. `Beacon: Nathan's revision (spec)` - 25 edges
10. `make_detection()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Heartbeat Fault Detection and Restart with Backoff` --semantically_similar_to--> `Processes Panel (heartbeat age, down at >=1 s)`  [INFERRED] [semantically similar]
  supervisor/README.md → telemd/README.md
- `main()` --calls--> `beacon_seq_read()`  [INFERRED]
  camd/tools/read_frames.c → include/beacon.h
- `world_in (laptop-camera fallback bridge to /beacon_world)` --semantically_similar_to--> `fakeworld (scripted percept/voiced stand-in)`  [INFERRED] [semantically similar]
  voiced/README.md → guided/README.md
- `probe_to_world.py World JSONL / UDP Emitter` --semantically_similar_to--> `telemd (read-only telemetry to the laptop)`  [INFERRED] [semantically similar]
  percept/README.md → README.md
- `--jpeg Raw UDP Preview Datagram` --semantically_similar_to--> `Optional Video JPEG (~5 fps, <60 KB per datagram)`  [INFERRED] [semantically similar]
  percept/README.md → laptop/samples/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Evidence-Backed Audio UX for a Chest-Worn Homing Device** — docs_beacon_accessibility_research_walk_speech_reach_ticks, docs_beacon_accessibility_research_tick_rate_distance_encoding, docs_beacon_accessibility_research_off_axis_search_cue, docs_beacon_accessibility_research_honest_lost_cue, docs_beacon_accessibility_research_open_ear_audio, docs_beacon_accessibility_research_parsimonious_instructions [EXTRACTED 1.00]
- **Beacon five-process QNX isolation** — docs_nathans_revision_five_process_architecture, docs_nathans_revision_supervisor, docs_nathans_revision_camd, docs_nathans_revision_guided, docs_nathans_revision_percept, docs_nathans_revision_voiced [EXTRACTED 1.00]
- **Graph refresh gate on PRs into main** — agents_graphify_graph_updated_check, agents_graph_refresh_workflow, agents_committed_graph_artifacts [EXTRACTED 1.00]
- **Live telemetry pipeline: Pi telemd -> UDP 5005 -> bridge -> WebSocket 8765 -> dashboard** — laptop_bridge_readme_telemd, laptop_bridge_readme_udp_ingest_port_5005, laptop_bridge_readme_bridge, laptop_bridge_readme_websocket_out_8765, laptop_dashboard_src_usetelemetry, laptop_dashboard_readme_dashboard [EXTRACTED 1.00]
- **Sequential percept vision pipeline** — docs_nathans_revision_sequential_percept_pipeline, docs_nathans_revision_yoloe_26n, docs_nathans_revision_depth_anything_v2, docs_nathans_revision_mediapipe_hands, docs_nathans_revision_rgbd_visual_odometry [EXTRACTED 1.00]
- **QNX mixed-criticality mechanism without APS** — docs_nathans_revision_no_aps, docs_nathans_revision_runmask_core0_isolation, docs_nathans_revision_seqlock, docs_nathans_revision_supervisor, docs_nathans_revision_procmgr_ability, docs_nathans_revision_slay_percept_demo [EXTRACTED 1.00]
- **Bluetooth A2DP Audio Path on QNX** — docs_pi_bringup_bt_a2dp_bridge, docs_pi_bringup_pcm_fifo_contract, docs_pi_bringup_bt_speaker_py, docs_pi_bringup_bt_audio_service, docs_pi_bringup_boot_persistence [EXTRACTED 1.00]
- **guided Pi validation sequence (build, silent run, JBL, timing under load)** — guided_pi_test_build_step, guided_pi_test_run_without_sound, guided_pi_test_jbl_bluetooth, guided_pi_test_timing_under_load [EXTRACTED 1.00]
- **Laptop Telemetry and Replay Chain** — docs_team_plan_telemd, docs_team_plan_replay_generator, docs_team_plan_bridge, docs_team_plan_dashboard [EXTRACTED 1.00]
- **Laptop World-dot Pipeline** — docs_pi_bringup_probe_frame_py, docs_superpowers_plans_2026_11_21_world_frame_dots_probe_to_world, laptop_samples_readme_world_sample_json, laptop_bridge_main, docs_superpowers_plans_2026_11_21_world_frame_dots_dashboard_world_view [EXTRACTED 1.00]
- **percept On-device Perception Stack** — percept_readme_percept, models_readme_yoloe26n, models_readme_depth_anything_v2, models_readme_mediapipe_hands, percept_readme_visual_odometry [EXTRACTED 1.00]
- **Recording, replay and dashboard history** — laptop_bridge_readme_session_recording_jsonl, laptop_bridge_readme_replay_mode, laptop_bridge_readme_dev_reach_sample, laptop_dashboard_readme_replay_scrubber, laptop_dashboard_readme_events_panel [INFERRED 0.85]
- **Stand-ins feeding /beacon_world before real percept/voiced** — guided_readme_fakeworld, voiced_readme_world_in, voiced_readme_fake_probe, voiced_readme_beacon_cmd, guided_readme_beacon_world_shm [INFERRED 0.85]
- **Spoken-metre Gating (no metres until tape check passes)** — percept_readme_tape_check, percept_readme_depth_scale, percept_readme_fov_pinhole_guess, percept_readme_calibrate_camera, readme_lost_cue_principle [INFERRED 0.85]
- **Telemetry Flow from Pi or Probe to Dashboard** — readme_telemd, percept_readme_probe_to_world, laptop_samples_readme_udp_port_5005, readme_laptop_bridge, laptop_dashboard_readme_dashboard [INFERRED 0.85]

## Communities (68 total, 13 thin omitted)

### Community 0 - "test_frame_id_seed.py"
Cohesion: 0.05
Nodes (27): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout(), main() (+19 more)

### Community 1 - "guided_step"
Cohesion: 0.10
Nodes (67): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+59 more)

### Community 2 - "beacon_clip"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)"
Cohesion: 0.05
Nodes (31): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), AprilTag fob (rejected physical tag identity), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Nov 20 Beacon build plan (superseded, removed), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md) (+23 more)

### Community 4 - "probe_frame_test.py"
Cohesion: 0.09
Nodes (9): FakeInferenceSession, FakeSessionOptions, build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction() (+1 more)

### Community 5 - "probe_once"
Cohesion: 0.14
Nodes (6): prepare(), probe_once(), ProbeRuntimeTest, fake_encode(), synthetic_probe_modules(), synthetic_video_modules()

### Community 6 - "probe_to_world Conversion"
Cohesion: 0.15
Nodes (6): probe_to_world(), make_detection(), make_last_bottle(), make_probe(), ProbeToWorldTest, ReadoutTest

### Community 7 - "with"
Cohesion: 0.07
Nodes (38): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+30 more)

### Community 8 - "calibrate_images"
Cohesion: 0.10
Nodes (11): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, synthetic_view() (+3 more)

### Community 9 - "Bridge Relay and Replay"
Cohesion: 0.08
Nodes (24): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+16 more)

### Community 10 - "probe_frame.py"
Cohesion: 0.12
Nodes (18): Affine, _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip() (+10 more)

### Community 11 - "head.cpp"
Cohesion: 0.07
Nodes (25): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+17 more)

### Community 12 - "Beacon Accessibility Research"
Cohesion: 0.07
Nodes (25): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), CHI 2025: BLV Object-Recognition Technologies in India, Auditory Hand-Steering Guidance for BLV People (CHI 2026), CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021) (+17 more)

### Community 13 - "guided/src/main.c"
Cohesion: 0.12
Nodes (9): main(), put_u16(), put_u32(), write_bmp(), main(), sleep_until(), beacon_frame_slot_t, main() (+1 more)

### Community 14 - "Guided Pi Test Plan"
Cohesion: 0.12
Nodes (28): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+20 more)

### Community 15 - "Dashboard Dependencies"
Cohesion: 0.09
Nodes (28): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+20 more)

### Community 16 - "DepthStabiliser"
Cohesion: 0.11
Nodes (5): DepthStabiliser, _DepthState, SlotTracker, DepthStabiliserTest, SlotTrackerTest

### Community 17 - "Probe CLI and UDP Streaming"
Cohesion: 0.13
Nodes (7): build_parser(), main(), parse_udp_target(), UdpEmitTest, fake_emit_lines(), fake_probe_once(), fake_probe_once()

### Community 18 - "beacon_intent_kind"
Cohesion: 0.07
Nodes (26): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+18 more)

### Community 19 - "Guidance Runtime and Safety"
Cohesion: 0.11
Nodes (18): 12-person BLV hand-steering study, GPIO piezo (cannot-fail actuator), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, REACH guidance law (ticks only), slay percept -> HOLD -> LOST failure demo, supervisor process (FIFO 63, core 0), USB headset audio (off-thread playback) (+10 more)

### Community 20 - "percept vision process (RR 22, cores 1-3)"
Cohesion: 0.16
Nodes (21): /beacon_depth depth slot (shm), /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, 30-second Sunday demo script, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite), objects[32] session POI store, OpenCV 4.12 (features2d + calib3d) (+13 more)

### Community 21 - "beacon.h"
Cohesion: 0.15
Nodes (22): audio_publish_stats(), audio_submit(), main(), test_seq_writer_restart(), beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t (+14 more)

### Community 22 - "Dashboard 3D Scene"
Cohesion: 0.25
Nodes (20): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+12 more)

### Community 23 - "telemd.c"
Cohesion: 0.13
Nodes (12): beacon_live_max_ns(), destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg(), escape_name() (+4 more)

### Community 24 - "guided (60 Hz guidance synthesizer)"
Cohesion: 0.16
Nodes (18): Evaluation of Short-Range Depth Sonifications (IEEE THMS), Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), Dashboard World-dot View (Scene.jsx, App.jsx), Wearer Dot at pose.T_world_from_cam Translation, include/beacon.h Shared Header, bridge (UDP-to-WebSocket laptop relay), Saturday Build Order (spec section 13, steps 1-6), 3D Dashboard (Vite + React + three.js) (+10 more)

### Community 25 - "Saturday Build Order (spec section 13, steps 1-6)"
Cohesion: 0.13
Nodes (18): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, Error handling / failure-mode table, 16.67 ms CLOCK_MONOTONIC guidance loop, Loaner bring-up checklist (QNX image), QNX AI Camera App (+10 more)

### Community 26 - "TapeCheckTest"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 27 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.15
Nodes (17): xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), dev-reach.jsonl (made by make-dev-reach.js), Even seq.* Values (telemd skips torn reads), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram) (+9 more)

### Community 28 - "Mode Banner (LIVE / HOLD / LOST)"
Cohesion: 0.14
Nodes (16): dev-reach.jsonl sample (walk, reach, slay percept -> HOLD -> LOST), Optional live JPEG video frames, Live status line every 5 s (world, video, dropped, dashboards), Bridge replay mode (paced by t_ns), Session recording to recordings/<UTC>.jsonl, telemd (Pi telemetry sender), UDP ingest on port 5005, WebSocket out ws://127.0.0.1:8765 (+8 more)

### Community 29 - "Dashboard App and Panels"
Cohesion: 0.22
Nodes (15): Beacon dashboard index.html, dashboard README, animate-ui primitives (Highlight, RollingText, SlidingNumber, Slider, Button), App(), Caption(), isNum(), measured(), MODES (+7 more)

### Community 30 - "deadline_test.c"
Cohesion: 0.16
Nodes (9): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), platform_heartbeat(), platform_piezo_init(), platform_piezo_set() (+1 more)

### Community 31 - "Guided Audio Thread"
Cohesion: 0.18
Nodes (15): audio_dropped_speech(), audio_main(), audio_start(), audio_stop(), law_name(), mode_name(), audio_out_paced(), pan_gains() (+7 more)

### Community 32 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.17
Nodes (12): Find My Things (Morrison et al., ASSETS 2023), Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764), ONNX Runtime 1.24.4 on QNX, Ultralytics YOLOE Docs (+4 more)

### Community 33 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.15
Nodes (14): Embedding Pose Graph, llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, NLMap, intent (voiced-owned job + candidate names), models/labels.txt runtime vocabulary, llama.cpp ~0.5B remap (table miss only), REPEAT and REJECT commands (+6 more)

### Community 34 - "percept (perception process)"
Cohesion: 0.13
Nodes (12): Depth Anything V2 Metric Indoor Small INT8, onnxruntime 1.24.4 (QNX), YOLOE-26n baked detect-only ONNX detector, Depth Anything V2 Static ONNX Export (210x210 metric), MediaPipe hand_landmarker.task Probe, percept/tools/probe_frame.py Laptop Probe, QNX Inference Runtime Packages (still missing), YOLOE-26n Detect-only ONNX Export (32 labels, (1,36,2100), no NMS) (+4 more)

### Community 35 - "probe_to_world Output"
Cohesion: 0.19
Nodes (8): emit_lines(), format_readout(), _ns(), _number(), _output(), _stable_id(), _timing(), _vec3()

### Community 36 - "camd/src/main.c"
Cohesion: 0.23
Nodes (13): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+5 more)

### Community 37 - "camd Frame Ring and Bring-up"
Cohesion: 0.15
Nodes (14): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), QNX CamAPI Adapter (not wired yet), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0) (+6 more)

### Community 38 - "Model Files Directory (not committed)"
Cohesion: 0.17
Nodes (12): crumbs Breadcrumb Positions, intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), Baked YOLOE Label Vocabulary (64 nouns), export_yoloe.py Detector Export, Optional llama.cpp GGUF, MediaPipe Hand Models, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin (+4 more)

### Community 39 - "Clip Captions and Events Panel"
Cohesion: 0.21
Nodes (7): captionFromClips(), CLIP_NAMES, CLIPS, clock(), Events(), eventsFromLog(), texts()

### Community 40 - "C270 Capture on QNX"
Cohesion: 0.21
Nodes (11): /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535), QNX /beacon_frames shm Round-trip (camd --bmp -> read-frames -> dump-frame), World-frame 3D Dots Plan, Logitech C270 Stand-In Camera and Mic, camd (camera process) (+3 more)

### Community 41 - "resolve_calibration"
Cohesion: 0.23
Nodes (5): Calibration, guess_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 42 - "DepthSamplingTest"
Cohesion: 0.15
Nodes (3): make_affine(), parse_csv3(), DepthSamplingTest

### Community 44 - "Audio Out Backends (asound, FIFO)"
Cohesion: 0.29
Nodes (9): audio_out_close(), audio_out_open(), audio_out_write(), fifo_try_open(), fifo_write(), put16(), put32(), qnx_open() (+1 more)

### Community 45 - "Guided Cues and Demo Replay"
Cohesion: 0.17
Nodes (10): deadline-test (over_period vs over_1ms), run_scenario.sh script, Clip caption table (enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids), telemd-preview JPEG Sender (libjpeg) (+2 more)

### Community 46 - "fakeworld.c"
Cohesion: 0.35
Nodes (9): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+1 more)

### Community 47 - "world_in.c"
Cohesion: 0.38
Nodes (9): apply(), find_key(), get_num(), get_str(), get_vec3(), main(), publish(), row_for() (+1 more)

### Community 48 - "beacon_cmd.c"
Cohesion: 0.29
Nodes (8): open_world(), beacon_world_t, add(), handle(), is_skip(), kind_name(), main(), world_open()

### Community 49 - "Pose and Depth Sampling"
Cohesion: 0.22
Nodes (8): pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, Per-instance Depth Slot Median Stabiliser, Box IoU Slot Association (--slot-iou 0.30), tape_check.py Absolute-depth Gate, Visual Odometry (VO)

### Community 50 - "build_parser"
Cohesion: 0.24
Nodes (6): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), _unit_float_arg()

### Community 52 - "string"
Cohesion: 0.36
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 53 - "guided_cmd_kind"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 55 - "SlotTracker"
Cohesion: 0.38
Nodes (4): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState

### Community 59 - "Refresh the graph before a PR into main"
Cohesion: 0.70
Nodes (3): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), CLAUDE.md (imports AGENTS.md)

### Community 63 - "voiced Intent Commands"
Cohesion: 1.00
Nodes (3): beacon_cmd (typed commands to intent block), Synonym Table (with REPEAT / REJECT, llama.cpp on miss), voiced (speech to intent)

## Knowledge Gaps
- **162 isolated node(s):** `BEACON_INTENT_FIND`, `BEACON_INTENT_GO`, `BEACON_INTENT_NACK_CANT`, `BEACON_INTENT_NACK_UNHEARD`, `BEACON_INTENT_NACK_UNSEEN` (+157 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 415 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clip caption table (enum beacon_clip order)` connect `Guided Cues and Demo Replay` to `beacon.h`, `Clip Captions and Events Panel`?**
  _High betweenness centrality (0.400) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BEACON_INTENT_FIND`, `BEACON_INTENT_GO`, `BEACON_INTENT_NACK_CANT` to the rest of the system?**
  _162 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_frame_id_seed.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05217391304347826 - nodes in this community are weakly interconnected._
- **Why does `Beacon: Nathan's revision (spec)` connect `Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)` to `YOLOE-26n-seg (text-prompted, baked static ONNX)`, `Beacon Accessibility Research`, `Guided Cues and Demo Replay`, `Guided Pi Test Plan`, `percept vision process (RR 22, cores 1-3)`, `Saturday Build Order (spec section 13, steps 1-6)`, `Dashboard App and Panels`?**
  _High betweenness centrality (0.191) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `guided_step` be split into smaller, more focused modules?**
  _Cohesion score 0.10434782608695652 - nodes in this community are weakly interconnected._