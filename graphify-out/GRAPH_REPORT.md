# Graph Report - beacon  (2026-11-21)

## Corpus Check
- 95 files · ~90,516 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .jsonl 2, .css 1)

## Summary
- 1416 nodes · 3035 edges · 70 communities (53 shown, 17 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 285 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b389e5e4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- probe_to_world
- App.jsx
- guided_step
- beacon_clip
- bridge.test.js
- probe_once
- Beacon Accessibility Research
- with
- head.cpp
- probe_frame.py
- guided (60 Hz cue synthesizer)
- calibrate_images
- audio.c
- guided/src/main.c
- telemd.c
- beacon_intent_kind
- Model Files Directory (not committed)
- percept (perception process)
- tempfile
- telemd.c
- Beacon (chest-worn item-homing wearable)
- telemd (read-only telemetry sender)
- Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)
- probe_frame_test.py
- DepthStabiliser
- TapeCheckTest
- guided (60 Hz guidance synthesizer)
- bt_speaker.py
- beacon.h
- Saturday Build Order (spec section 13, steps 1-6)
- guided synthesizer (FIFO 58, core 0)
- Logitech C270 Stand-In Camera and Mic
- deadline_test.c
- Laptop-first World-dot Pipeline (probe_frame -> probe_to_world -> bridge -> dashboard)
- math
- SlotTracker
- camd/src/main.c
- resolve_calibration
- encode_preview
- Mode Banner (LIVE / HOLD / LOST)
- Beacon 3D Dashboard (Vite + React + react-three-fiber)
- DepthSamplingTest
- beacon_cmd.c
- percept vision process (RR 22, cores 1-3)
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- Beacon: Nathan's revision (spec)
- .patch_chair_frames
- argparse
- FakeLandmarker
- Merge verdict: BLOCK
- fakeworld.c
- world_in.c
- build_parser
- ProbeResources
- Refresh the graph before a PR into main
- guided_cmd_kind
- string
- FakeCapture
- FakeFileCapture
- FakeInferenceSession
- bt_audio_service.sh
- run-radio-auto.sh
- AirTag Precision Finding
- irl_test.sh
- pi_live.sh
- test_frame_id_seed.py
- beacon_intent_kind
- synthetic_view

## God Nodes (most connected - your core abstractions)
1. `beacon_clip` - 60 edges
2. `probe_to_world()` - 46 edges
3. `guided_step()` - 42 edges
4. `make_probe()` - 37 edges
5. `probe_once()` - 36 edges
6. `ProbeRuntimeTest` - 34 edges
7. `ProbeToWorldTest` - 32 edges
8. `prepare()` - 26 edges
9. `Beacon: Nathan's revision (spec)` - 23 edges
10. `make_detection()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Heartbeat Fault Detection and Restart with Backoff` --semantically_similar_to--> `Processes Panel (heartbeat age, down at >=1 s)`  [INFERRED] [semantically similar]
  supervisor/README.md → telemd/README.md
- `Newest-wins Dashboard Backpressure (skip clients >1 MB behind)` --semantically_similar_to--> `/beacon_frames Newest-wins Three-slot Ring`  [INFERRED] [semantically similar]
  laptop/bridge/README.md → camd/README.md
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
- **Sequential percept vision pipeline** — docs_nathans_revision_sequential_percept_pipeline, docs_nathans_revision_yoloe_26n, docs_nathans_revision_depth_anything_v2, docs_nathans_revision_mediapipe_hands, docs_nathans_revision_rgbd_visual_odometry [EXTRACTED 1.00]
- **QNX mixed-criticality mechanism without APS** — docs_nathans_revision_no_aps, docs_nathans_revision_runmask_core0_isolation, docs_nathans_revision_seqlock, docs_nathans_revision_supervisor, docs_nathans_revision_procmgr_ability, docs_nathans_revision_slay_percept_demo [EXTRACTED 1.00]
- **Bluetooth A2DP Audio Path on QNX** — docs_pi_bringup_bt_a2dp_bridge, docs_pi_bringup_pcm_fifo_contract, docs_pi_bringup_bt_speaker_py, docs_pi_bringup_bt_audio_service, docs_pi_bringup_boot_persistence [EXTRACTED 1.00]
- **Graph refresh gate for PRs into main** — agents_graph_refresh_workflow, agents_graphify_ci_check, agents_graph_report, agents_graph_json, agents_graph_html [EXTRACTED 1.00]
- **guided Pi validation sequence (build, silent run, JBL, timing under load)** — guided_pi_test_build_step, guided_pi_test_run_without_sound, guided_pi_test_jbl_bluetooth, guided_pi_test_timing_under_load [EXTRACTED 1.00]
- **Components built on animate-ui primitives** — laptop_dashboard_readme_animate_ui, laptop_dashboard_readme_app_header, laptop_dashboard_readme_replay_scrubber [EXTRACTED 1.00]
- **Laptop Telemetry and Replay Chain** — docs_team_plan_telemd, docs_team_plan_replay_generator, docs_team_plan_bridge, docs_team_plan_dashboard [EXTRACTED 1.00]
- **Laptop World-dot Pipeline** — docs_pi_bringup_probe_frame_py, docs_superpowers_plans_2026_11_21_world_frame_dots_probe_to_world, laptop_samples_readme_world_sample_json, laptop_bridge_main, docs_superpowers_plans_2026_11_21_world_frame_dots_dashboard_world_view [EXTRACTED 1.00]
- **percept On-device Perception Stack** — percept_readme_percept, models_readme_yoloe26n, models_readme_depth_anything_v2, models_readme_mediapipe_hands, percept_readme_visual_odometry [EXTRACTED 1.00]
- **Telemetry Monitoring Pipeline (telemd -> bridge -> dashboard)** — telemd_readme_telemd, laptop_bridge_readme_bridge, laptop_dashboard_readme_dashboard, laptop_samples_readme_telemetry_format [EXTRACTED 1.00]
- **Newest-wins Buffering Pattern** — camd_readme_beacon_frames_ring, laptop_bridge_readme_newest_wins_backpressure, guided_readme_audio_thread [INFERRED 0.75]
- **Stand-ins feeding /beacon_world before real percept/voiced** — guided_readme_fakeworld, voiced_readme_world_in, voiced_readme_fake_probe, voiced_readme_beacon_cmd, guided_readme_beacon_world_shm [INFERRED 0.85]
- **World-state history views (scrub, events, paused camera)** — laptop_dashboard_readme_replay_scrubber, laptop_dashboard_readme_events_panel, laptop_dashboard_readme_camera_panel [INFERRED 0.85]
- **Bridge telemetry flow into dashboard views** — laptop_dashboard_readme_bridge_websocket, laptop_dashboard_readme_use_telemetry, laptop_dashboard_readme_camera_frame_rendering, laptop_dashboard_readme_camera_panel, laptop_dashboard_readme_no_data_staleness [INFERRED 0.85]
- **Spoken-metre Gating (no metres until tape check passes)** — percept_readme_tape_check, percept_readme_depth_scale, percept_readme_fov_pinhole_guess, percept_readme_calibrate_camera, readme_lost_cue_principle [INFERRED 0.85]
- **Telemetry Flow from Pi or Probe to Dashboard** — readme_telemd, percept_readme_probe_to_world, laptop_samples_readme_udp_port_5005, readme_laptop_bridge, laptop_dashboard_readme_use_telemetry, laptop_dashboard_readme_dashboard [INFERRED 0.85]

## Communities (70 total, 17 thin omitted)

### Community 0 - "probe_to_world"
Cohesion: 0.06
Nodes (21): build_parser(), format_readout(), load_target_names(), main(), _ns(), _number(), _output(), parse_udp_target() (+13 more)

### Community 1 - "App.jsx"
Cohesion: 0.06
Nodes (60): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+52 more)

### Community 2 - "guided_step"
Cohesion: 0.10
Nodes (68): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+60 more)

### Community 3 - "beacon_clip"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 4 - "bridge.test.js"
Cohesion: 0.07
Nodes (29): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+21 more)

### Community 5 - "probe_once"
Cohesion: 0.13
Nodes (7): prepare(), probe_once(), ProbeRuntimeTest, fake_encode(), synthetic_probe_modules(), synthetic_video_modules(), emit_lines()

### Community 6 - "Beacon Accessibility Research"
Cohesion: 0.06
Nodes (26): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), CHI 2025: BLV Object-Recognition Technologies in India, Auditory Hand-Steering Guidance for BLV People (CHI 2026), CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021) (+18 more)

### Community 7 - "with"
Cohesion: 0.07
Nodes (38): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+30 more)

### Community 8 - "head.cpp"
Cohesion: 0.07
Nodes (25): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+17 more)

### Community 9 - "probe_frame.py"
Cohesion: 0.14
Nodes (16): Affine, depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip(), letterbox(), load_calibration() (+8 more)

### Community 10 - "guided (60 Hz cue synthesizer)"
Cohesion: 0.11
Nodes (31): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+23 more)

### Community 11 - "calibrate_images"
Cohesion: 0.13
Nodes (10): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, write_synthetic_views() (+2 more)

### Community 12 - "audio.c"
Cohesion: 0.14
Nodes (21): audio_main(), law_name(), mode_name(), audio_out_close(), audio_out_open(), audio_out_paced(), audio_out_write(), fifo_try_open() (+13 more)

### Community 13 - "guided/src/main.c"
Cohesion: 0.15
Nodes (5): main(), put_u16(), put_u32(), write_bmp(), beacon_frame_slot_t

### Community 14 - "telemd.c"
Cohesion: 0.17
Nodes (14): main(), open_world(), beacon_live_max_ns(), beacon_seq_read(), beacon_world_t, read_newest(), main(), open_world() (+6 more)

### Community 15 - "beacon_intent_kind"
Cohesion: 0.12
Nodes (15): beacon_law, BEACON_LAW_LOST, BEACON_LAW_NONE, BEACON_LAW_REACH, BEACON_LAW_RETURN, BEACON_LAW_STOP, BEACON_LAW_WALK, beacon_pulse (+7 more)

### Community 16 - "Model Files Directory (not committed)"
Cohesion: 0.10
Nodes (20): crumbs Breadcrumb Positions, intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Baked YOLOE Label Vocabulary (64 nouns), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, export_yoloe.py Detector Export (+12 more)

### Community 17 - "percept (perception process)"
Cohesion: 0.18
Nodes (10): Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), models/labels.txt runtime vocabulary, YOLOE-26n baked detect-only ONNX detector, Depth Anything V2 Static ONNX Export (210x210 metric), MediaPipe hand_landmarker.task Probe, percept/tools/probe_frame.py Laptop Probe, YOLOE-26n Detect-only ONNX Export (32 labels, (1,36,2100), no NMS), MediaPipe Hands (+2 more)

### Community 18 - "tempfile"
Cohesion: 0.16
Nodes (8): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips(), supervise()

### Community 19 - "telemd.c"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 20 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.13
Nodes (21): deadline-test (over_period vs over_1ms), xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, sim-reach-lost.jsonl Simulator Demo Replay, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram) (+13 more)

### Community 21 - "telemd (read-only telemetry sender)"
Cohesion: 0.11
Nodes (17): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), QNX CamAPI Adapter (not wired yet), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0) (+9 more)

### Community 22 - "Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)"
Cohesion: 0.13
Nodes (13): Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Network Diagnostics Ladder, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay), QNXE-1894 Wi-Fi Settings Copy Bug (+5 more)

### Community 24 - "DepthStabiliser"
Cohesion: 0.19
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 25 - "TapeCheckTest"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 26 - "guided (60 Hz guidance synthesizer)"
Cohesion: 0.14
Nodes (21): Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), REPEAT and REJECT commands, Crumb Trail Dots (crumbs[].xyz_world), Dashboard World-dot View (Scene.jsx, App.jsx), Laptop RGB-D Odometry (ORB + solvePnPRansac, keyframes, crumbs), Wearer Dot at pose.T_world_from_cam Translation, include/beacon.h Shared Header, bridge (UDP-to-WebSocket laptop relay) (+13 more)

### Community 27 - "bt_speaker.py"
Cohesion: 0.15
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 28 - "beacon.h"
Cohesion: 0.14
Nodes (11): beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t, beacon_guided_stats_t, beacon_hand_t, beacon_letterbox_t, beacon_object_t (+3 more)

### Community 29 - "Saturday Build Order (spec section 13, steps 1-6)"
Cohesion: 0.16
Nodes (16): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, Error handling / failure-mode table, 16.67 ms CLOCK_MONOTONIC guidance loop, Range 2: object still in view (walk while looking, no VO), slay percept -> HOLD -> LOST failure demo (+8 more)

### Community 30 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.17
Nodes (12): 12-person BLV hand-steering study, guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, intent (voiced-owned job + candidate names), llama.cpp ~0.5B remap (table miss only), REACH guidance law (ticks only), supervisor process (FIFO 63, core 0), Synonym / keyword table (fast path) (+4 more)

### Community 31 - "Logitech C270 Stand-In Camera and Mic"
Cohesion: 0.14
Nodes (17): GPIO piezo (cannot-fail actuator), No PCM Playback Device on QNX Image (io-snd control only, no 3.5 mm), post_startup.sh Boot Persistence (on -d -p 10, after io-snd), BTstack A2DP Bridge to JBL Go 3 (Combadge-HTN/qnx-bluetooth), supervisor/bt_audio_service.sh Supervisor-managed BT Child, guided/bt_speaker.py (stdlib 16 kHz mono -> 44.1 kHz stereo player), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), Camera Module 3 CSI (imx708, units 3-4, 2304x1296 nv12) (+9 more)

### Community 32 - "deadline_test.c"
Cohesion: 0.13
Nodes (14): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), audio_dropped_speech(), audio_start(), audio_stop() (+6 more)

### Community 33 - "Laptop-first World-dot Pipeline (probe_frame -> probe_to_world -> bridge -> dashboard)"
Cohesion: 0.12
Nodes (13): /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), Loaner bring-up checklist (QNX image), onnxruntime 1.24.4 (QNX), QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), camd --bmp Bring-up Frame Source (frametype 65535), qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB) (+5 more)

### Community 34 - "math"
Cohesion: 0.25
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 35 - "SlotTracker"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 36 - "camd/src/main.c"
Cohesion: 0.23
Nodes (13): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+5 more)

### Community 37 - "resolve_calibration"
Cohesion: 0.23
Nodes (5): Calibration, guess_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 39 - "Mode Banner (LIVE / HOLD / LOST)"
Cohesion: 0.18
Nodes (12): Bridge Replay (paced by t_ns), animate-ui Primitives, App.jsx Header and Side Panels, enum beacon_clip (include/beacon.h), Clip Captions (clips.js in enum beacon_clip order), Events Panel (events.js / Events.jsx), Mode Banner (LIVE / HOLD / LOST), Replay Scrubber (last 10 min of world states) (+4 more)

### Community 40 - "Beacon 3D Dashboard (Vite + React + react-three-fiber)"
Cohesion: 0.21
Nodes (13): Beacon dashboard HTML Entry (#root, /src/main.jsx), Breadcrumb Trail (crumbs[]), Bridge Replay Mode (replay:dev, dev-reach.jsonl), Bridge WebSocket (ws://127.0.0.1:8765), World-frame Dot Map Scene (Scene.jsx), Live JPEG Camera Panel, Beacon 3D Dashboard (Vite + React + react-three-fiber), Nathan's Revision Design Doc (docs/nathans-revision.md) (+5 more)

### Community 41 - "DepthSamplingTest"
Cohesion: 0.13
Nodes (5): _central_bounds(), depth_at_box(), make_affine(), parse_csv3(), DepthSamplingTest

### Community 42 - "beacon_cmd.c"
Cohesion: 0.43
Nodes (6): add(), handle(), is_skip(), kind_name(), main(), send_intent()

### Community 43 - "percept vision process (RR 22, cores 1-3)"
Cohesion: 0.18
Nodes (19): /beacon_depth depth slot (shm), /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, Depth Anything V2 Metric Indoor Small INT8, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite), objects[32] session POI store, OpenCV 4.12 (features2d + calib3d) (+11 more)

### Community 44 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.12
Nodes (15): Find My Things (Morrison et al., ASSETS 2023), Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Embedding Pose Graph, llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764) (+7 more)

### Community 45 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.14
Nodes (14): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), 30-second Sunday demo script, Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), procmgr_ability priority ability and root drop (+6 more)

### Community 47 - "argparse"
Cohesion: 0.21
Nodes (4): main(), __init__(), main(), read_labels()

### Community 50 - "fakeworld.c"
Cohesion: 0.22
Nodes (16): audio_publish_stats(), audio_submit(), test_seq_writer_restart(), drop_crumb(), lerp(), main(), publish_percept(), put_hand() (+8 more)

### Community 51 - "world_in.c"
Cohesion: 0.27
Nodes (12): wait_for(), apply(), find_key(), get_id(), get_num(), get_str(), get_vecn(), main() (+4 more)

### Community 52 - "build_parser"
Cohesion: 0.24
Nodes (6): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), _unit_float_arg()

### Community 54 - "Refresh the graph before a PR into main"
Cohesion: 0.28
Nodes (8): Beacon: notes for coding agents, graphify-out/graph.html, graphify-out/graph.json, graphify-out/GRAPH_REPORT.md (code/spec/docs map), 'graphify graph updated' CI check, graphify update . (code-only, no LLM), /graphify . --update (Claude Code skill run), CLAUDE.md (imports AGENTS.md)

### Community 55 - "guided_cmd_kind"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 56 - "string"
Cohesion: 0.43
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 67 - "test_frame_id_seed.py"
Cohesion: 0.27
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 68 - "beacon_intent_kind"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

## Knowledge Gaps
- **170 isolated node(s):** `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK`, `GUIDED_CMD_TONE_ON`, `GUIDED_CMD_TONE_OFF` (+165 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 420 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `beacon_clip` connect `beacon_clip` to `beacon.h`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK` to the rest of the system?**
  _170 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `probe_to_world` be split into smaller, more focused modules?**
  _Cohesion score 0.05750350631136045 - nodes in this community are weakly interconnected._
- **Why does `probe_once()` connect `probe_once` to `resolve_calibration`, `encode_preview`, `probe_frame.py`, `DepthSamplingTest`, `.patch_chair_frames`, `world_in.c`, `build_parser`, `ProbeResources`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06277665995975855 - nodes in this community are weakly interconnected._