# Graph Report - Beacon-Hack-Western-13-  (2026-11-21)

## Corpus Check
- 2 files · ~90,771 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1414 nodes · 3041 edges · 74 communities (60 shown, 14 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 279 edges (avg confidence: 0.86)
- Token cost: 52,526 input · 0 output

## Community Hubs (Navigation)
- Beacon Accessibility Research
- App.jsx
- guided_step
- probe_once
- probe_frame.py
- deadline_test.c
- with
- calibrate_images
- guided/src/main.c
- head.cpp
- App.jsx (2)
- Logitech C270 Stand-In Camera and Mic
- App.jsx (3)
- probe_to_world
- telemd.c
- telemd (read-only telemetry sender)
- App.jsx (4)
- probe_frame_test.py
- YOLOE-26n baked detect-only ONNX detector
- beacon.h
- guided synthesizer (FIFO 58, core 0)
- bridge.test.js
- DepthStabiliser
- Model Files Directory (not committed)
- guided (60 Hz guidance synthesizer)
- bt_speaker.py
- guided synthesizer (FIFO 58, core 0) (2)
- probe_to_world (2)
- .patch_chair_frames
- beacon_intent_kind
- camd/src/main.c
- resolve_calibration
- DepthStabiliser (2)
- TapeCheckTest
- Logitech C270 Stand-In Camera and Mic (2)
- tape_check.py
- guided (60 Hz cue synthesizer)
- Beacon: Nathan's revision (spec)
- Beacon (chest-worn item-homing wearable)
- encode_preview
- telemd (read-only telemetry sender) (2)
- DepthSamplingTest
- world_in.c
- /boot/onboot Boot Hook
- guided (60 Hz cue synthesizer) (2)
- probe_to_world (3)
- Logitech C270 Stand-In Camera and Mic (3)
- probe_to_world (4)
- Merge verdict: BLOCK
- fakeworld.c
- guided (60 Hz cue synthesizer) (3)
- SlotTracker
- qnxpi Target (QNX 8.0 Raspberry Pi 5)
- Merge verdict: BLOCK (2)
- argparse
- build_parser
- ProbeResources
- Refresh the graph before a PR into main
- FakeLandmarker
- beacon_cmd.c
- bridge.test.js (2)
- .test_capture_frames_prompts_between_views
- Clip caption table (enum beacon_clip order)
- string
- FakeCapture
- FakeFileCapture
- bt_audio_service.sh
- run-radio-auto.sh
- telemd (read-only telemetry sender) (3)
- make_clips.ps1
- pi_live.sh
- test_frame_id_seed.py

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
10. `main()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Processes Panel (heartbeat age, down at >=1 s)` --semantically_similar_to--> `NO DATA after 1 s without world state`  [INFERRED] [semantically similar]
  telemd/README.md → laptop/dashboard/README.md
- `world_in (laptop-camera fallback bridge to /beacon_world)` --semantically_similar_to--> `fakeworld (scripted percept/voiced stand-in)`  [INFERRED] [semantically similar]
  voiced/README.md → guided/README.md
- `probe_to_world.py World JSONL / UDP Emitter` --semantically_similar_to--> `telemd (read-only telemetry to the laptop)`  [INFERRED] [semantically similar]
  percept/README.md → README.md
- `--jpeg Raw UDP Preview Datagram` --semantically_similar_to--> `Optional Video JPEG (~5 fps, <60 KB per datagram)`  [INFERRED] [semantically similar]
  percept/README.md → laptop/samples/README.md
- `Heartbeat Fault Detection and Restart with Backoff` --semantically_similar_to--> `Processes Panel (heartbeat age, down at >=1 s)`  [INFERRED] [semantically similar]
  supervisor/README.md → telemd/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Evidence-Backed Audio UX for a Chest-Worn Homing Device** — docs_beacon_accessibility_research_walk_speech_reach_ticks, docs_beacon_accessibility_research_tick_rate_distance_encoding, docs_beacon_accessibility_research_off_axis_search_cue, docs_beacon_accessibility_research_honest_lost_cue, docs_beacon_accessibility_research_open_ear_audio, docs_beacon_accessibility_research_parsimonious_instructions [EXTRACTED 1.00]
- **Beacon five-process QNX isolation** — docs_nathans_revision_five_process_architecture, docs_nathans_revision_supervisor, docs_nathans_revision_camd, docs_nathans_revision_guided, docs_nathans_revision_percept, docs_nathans_revision_voiced [EXTRACTED 1.00]
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

## Communities (74 total, 14 thin omitted)

### Community 0 - "Beacon Accessibility Research"
Cohesion: 0.06
Nodes (22): build_parser(), emit_lines(), format_readout(), load_target_names(), main(), _ns(), _number(), _output() (+14 more)

### Community 1 - "App.jsx"
Cohesion: 0.10
Nodes (67): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+59 more)

### Community 2 - "guided_step"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "probe_once"
Cohesion: 0.09
Nodes (7): prepare(), ProbeRuntimeTest, fake_detect(), fake_predict_depth(), fake_encode(), synthetic_probe_modules(), synthetic_video_modules()

### Community 4 - "probe_frame.py"
Cohesion: 0.07
Nodes (28): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+20 more)

### Community 5 - "deadline_test.c"
Cohesion: 0.05
Nodes (35): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), CHI 2025: BLV Object-Recognition Technologies in India, CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021), Multi-Purpose Camera Apps (Seeing AI, Lookout, Be My Eyes, Envision) (+27 more)

### Community 6 - "with"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 7 - "calibrate_images"
Cohesion: 0.07
Nodes (25): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+17 more)

### Community 8 - "guided/src/main.c"
Cohesion: 0.11
Nodes (11): main(), put_u16(), put_u32(), write_bmp(), open_world(), sleep_until(), beacon_frame_slot_t, beacon_world_t (+3 more)

### Community 9 - "head.cpp"
Cohesion: 0.13
Nodes (10): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, write_synthetic_views() (+2 more)

### Community 10 - "App.jsx (2)"
Cohesion: 0.09
Nodes (28): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+20 more)

### Community 11 - "Logitech C270 Stand-In Camera and Mic"
Cohesion: 0.15
Nodes (21): audio_main(), law_name(), mode_name(), audio_out_close(), audio_out_open(), audio_out_paced(), audio_out_write(), fifo_try_open() (+13 more)

### Community 12 - "App.jsx (3)"
Cohesion: 0.16
Nodes (18): Beacon dashboard index.html, dashboard README, animate-ui primitives (Highlight, RollingText, SlidingNumber, Slider, Button), App(), Caption(), isNum(), measured(), MODES (+10 more)

### Community 13 - "probe_to_world"
Cohesion: 0.16
Nodes (8): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips(), supervise()

### Community 14 - "telemd.c"
Cohesion: 0.17
Nodes (19): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+11 more)

### Community 15 - "telemd (read-only telemetry sender)"
Cohesion: 0.09
Nodes (18): beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t, beacon_guided_stats_t, beacon_hand_t, beacon_law, BEACON_LAW_LOST (+10 more)

### Community 16 - "App.jsx (4)"
Cohesion: 0.25
Nodes (20): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+12 more)

### Community 17 - "probe_frame_test.py"
Cohesion: 0.13
Nodes (12): beacon_live_max_ns(), destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg(), escape_name() (+4 more)

### Community 18 - "YOLOE-26n baked detect-only ONNX detector"
Cohesion: 0.11
Nodes (15): Depth Anything V2 Metric Indoor Small INT8, models/labels.txt runtime vocabulary, onnxruntime 1.24.4 (QNX), YOLOE-26n baked detect-only ONNX detector, Depth Anything V2 Static ONNX Export (210x210 metric), MediaPipe hand_landmarker.task Probe, percept/tools/probe_frame.py Laptop Probe, QNX Inference Runtime Packages (still missing) (+7 more)

### Community 19 - "beacon.h"
Cohesion: 0.15
Nodes (18): Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), bridge README, bridge (Node UDP-to-WebSocket relay and recorder), dev-reach.jsonl sample (walk, reach, slay percept -> HOLD -> LOST), Optional live JPEG video frames, Live status line every 5 s (world, video, dropped, dashboards), Bridge replay mode (paced by t_ns), Session recording to recordings/<UTC>.jsonl (+10 more)

### Community 20 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.15
Nodes (14): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), audio_dropped_speech(), audio_start(), audio_stop() (+6 more)

### Community 21 - "bridge.test.js"
Cohesion: 0.14
Nodes (3): synthetic_view(), FakeInferenceSession, FakeSessionOptions

### Community 22 - "DepthStabiliser"
Cohesion: 0.12
Nodes (16): Auditory Hand-Steering Guidance for BLV People (CHI 2026), Evaluation of Short-Range Depth Sonifications (IEEE THMS), intent (voiced-owned job + candidate names), llama.cpp ~0.5B remap (table miss only), Loaner bring-up checklist (QNX image), REPEAT and REJECT commands, Synonym / keyword table (fast path), voiced speech process (RR 18, cores 1-3) (+8 more)

### Community 23 - "Model Files Directory (not committed)"
Cohesion: 0.19
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 24 - "guided (60 Hz guidance synthesizer)"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 25 - "bt_speaker.py"
Cohesion: 0.15
Nodes (17): xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), dev-reach.jsonl (made by make-dev-reach.js), Even seq.* Values (telemd skips torn reads), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram) (+9 more)

### Community 26 - "guided synthesizer (FIFO 58, core 0) (2)"
Cohesion: 0.15
Nodes (13): /beacon_depth depth slot (shm), 12-person BLV hand-steering study, Error handling / failure-mode table, GPIO piezo (cannot-fail actuator), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, Range 1: same camera frame (tabletop reach, no VO), REACH guidance law (ticks only) (+5 more)

### Community 27 - "probe_to_world (2)"
Cohesion: 0.15
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 28 - ".patch_chair_frames"
Cohesion: 0.20
Nodes (17): audio_publish_stats(), audio_submit(), test_seq_writer_restart(), drop_crumb(), lerp(), main(), publish_percept(), put_hand() (+9 more)

### Community 29 - "beacon_intent_kind"
Cohesion: 0.10
Nodes (19): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+11 more)

### Community 30 - "camd/src/main.c"
Cohesion: 0.20
Nodes (15): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+7 more)

### Community 31 - "resolve_calibration"
Cohesion: 0.14
Nodes (15): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), QNX CamAPI Adapter (not wired yet), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0) (+7 more)

### Community 32 - "DepthStabiliser (2)"
Cohesion: 0.19
Nodes (14): NavCog / NavCog3 (CMU), Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), Dashboard World-dot View (Scene.jsx, App.jsx), Wearer Dot at pose.T_world_from_cam Translation, bridge (UDP-to-WebSocket laptop relay), Saturday Build Order (spec section 13, steps 1-6), 3D Dashboard (Vite + React + three.js), 30-Second Demo Script (spec section 12) (+6 more)

### Community 33 - "TapeCheckTest"
Cohesion: 0.18
Nodes (13): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, 16.67 ms CLOCK_MONOTONIC guidance loop, Range 2: object still in view (walk while looking, no VO), Pre-Sunday testing requirements, WALK guidance law (spoken instruction) (+5 more)

### Community 34 - "Logitech C270 Stand-In Camera and Mic (2)"
Cohesion: 0.18
Nodes (13): /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535), QNX /beacon_frames shm Round-trip (camd --bmp -> read-frames -> dump-frame), World-frame 3D Dots Plan, include/beacon.h Shared Header, Logitech C270 Stand-In Camera and Mic (+5 more)

### Community 35 - "tape_check.py"
Cohesion: 0.23
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 36 - "guided (60 Hz cue synthesizer)"
Cohesion: 0.26
Nodes (9): Affine, depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip(), letterbox(), _median_depth(), predict_depth() (+1 more)

### Community 37 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.15
Nodes (13): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), procmgr_ability priority ability and root drop, QNX AI workshop (MediaPipe hands on Pi) (+5 more)

### Community 38 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.24
Nodes (16): /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, 30-second Sunday demo script, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite), objects[32] session POI store, OpenCV 4.12 (features2d + calib3d), percept vision process (RR 22, cores 1-3) (+8 more)

### Community 39 - "encode_preview"
Cohesion: 0.17
Nodes (12): crumbs Breadcrumb Positions, intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), Baked YOLOE Label Vocabulary (64 nouns), export_yoloe.py Detector Export, Optional llama.cpp GGUF, MediaPipe Hand Models, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin (+4 more)

### Community 40 - "telemd (read-only telemetry sender) (2)"
Cohesion: 0.15
Nodes (13): /beacon_world Shared Memory, fakeworld (scripted percept/voiced stand-in), Simulator Scenarios (reach, lost, walk, turn, unseen, stop, return, reject), run_scenario.sh script, Dummy Worker Heartbeat Test, Heartbeat Fault Detection and Restart with Backoff, Piezo Fault Path, supervisor (spawn, runmasks, heartbeats, restarts) (+5 more)

### Community 41 - "DepthSamplingTest"
Cohesion: 0.22
Nodes (6): Calibration, guess_calibration(), load_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 42 - "world_in.c"
Cohesion: 0.16
Nodes (5): load_depth_session(), load_labels(), load_yolo(), load_yolo_session(), ProbeResources

### Community 43 - "/boot/onboot Boot Hook"
Cohesion: 0.16
Nodes (9): Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Network Diagnostics Ladder, QNX Process Idioms (pidin, slay), QNXE-1894 Wi-Fi Settings Copy Bug, QNXE-2016 Shared Default Wi-Fi MAC, Serial Console (UART on 40-pin header) (+1 more)

### Community 44 - "guided (60 Hz cue synthesizer) (2)"
Cohesion: 0.19
Nodes (4): _central_bounds(), depth_at_box(), depth_at_full(), DepthSamplingTest

### Community 45 - "probe_to_world (3)"
Cohesion: 0.27
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 46 - "Logitech C270 Stand-In Camera and Mic (3)"
Cohesion: 0.15
Nodes (10): Aural and Haptic Feedback for Visually Impaired People on a Track (ICHI), Less is More (VIA-Agent) PVI Study, No PCM Playback Device on QNX Image (io-snd control only, no 3.5 mm), post_startup.sh Boot Persistence (on -d -p 10, after io-snd), BTstack A2DP Bridge to JBL Go 3 (Combadge-HTN/qnx-bluetooth), supervisor/bt_audio_service.sh Supervisor-managed BT Child, guided/bt_speaker.py (stdlib 16 kHz mono -> 44.1 kHz stereo player), Camera Module 3 CSI (imx708, units 3-4, 2304x1296 nv12) (+2 more)

### Community 47 - "probe_to_world (4)"
Cohesion: 0.21
Nodes (4): main(), __init__(), main(), read_labels()

### Community 49 - "fakeworld.c"
Cohesion: 0.21
Nodes (7): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), probe_once(), _unit_float_arg()

### Community 50 - "guided (60 Hz cue synthesizer) (3)"
Cohesion: 0.25
Nodes (4): _box_bounds(), _box_iou(), _slot_match_score(), _stable_detection_id()

### Community 51 - "SlotTracker"
Cohesion: 0.25
Nodes (3): _SlotState, SlotTracker, SlotTrackerTest

### Community 52 - "qnxpi Target (QNX 8.0 Raspberry Pi 5)"
Cohesion: 0.20
Nodes (8): ONNX Runtime 1.24.4 on QNX, QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB), Sensor Framework Camera Probe (sensor_rpi5.conf units), Read-Only IFS Image (qnx_sdp.ifs), QNXE-195 ssh-rsa Host Key Negotiation, qnxpi Target (QNX 8.0 Raspberry Pi 5)

### Community 53 - "Merge verdict: BLOCK (2)"
Cohesion: 0.22
Nodes (8): pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, Per-instance Depth Slot Median Stabiliser, Box IoU Slot Association (--slot-iou 0.30), tape_check.py Absolute-depth Gate, Visual Odometry (VO)

### Community 54 - "argparse"
Cohesion: 0.42
Nodes (8): apply(), find_key(), get_num(), get_str(), get_vec3(), main(), row_for(), skip_value()

### Community 55 - "build_parser"
Cohesion: 0.36
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 56 - "ProbeResources"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 58 - "FakeLandmarker"
Cohesion: 0.43
Nodes (6): add(), handle(), is_skip(), kind_name(), main(), send_intent()

### Community 61 - ".test_capture_frames_prompts_between_views"
Cohesion: 0.60
Nodes (4): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), graph-not-needed PR label, CLAUDE.md (imports AGENTS.md)

### Community 62 - "Clip caption table (enum beacon_clip order)"
Cohesion: 0.33
Nodes (6): deadline-test (over_period vs over_1ms), Clip caption table (enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids)

### Community 69 - "telemd (read-only telemetry sender) (3)"
Cohesion: 1.00
Nodes (3): beacon_cmd (typed commands to intent block), Synonym Table (with REPEAT / REJECT, llama.cpp on miss), voiced (speech to intent)

## Knowledge Gaps
- **162 isolated node(s):** `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE`, `BEACON_MODE_LOST`, `BEACON_MODE_NONE`, `full_h` (+157 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 416 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clip caption table (enum beacon_clip order)` connect `Clip caption table (enum beacon_clip order)` to `App.jsx (3)`, `telemd (read-only telemetry sender)`?**
  _High betweenness centrality (0.397) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE`, `BEACON_MODE_LOST` to the rest of the system?**
  _162 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Beacon Accessibility Research` be split into smaller, more focused modules?**
  _Cohesion score 0.05635964912280702 - nodes in this community are weakly interconnected._
- **Why does `Beacon: Nathan's revision (spec)` connect `Beacon: Nathan's revision (spec)` to `TapeCheckTest`, `deadline_test.c`, `telemd (read-only telemetry sender) (2)`, `/boot/onboot Boot Hook`, `App.jsx (3)`, `telemd.c`, `Merge verdict: BLOCK`, `beacon.h`, `qnxpi Target (QNX 8.0 Raspberry Pi 5)`, `guided synthesizer (FIFO 58, core 0) (2)`?**
  _High betweenness centrality (0.225) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.10434782608695652 - nodes in this community are weakly interconnected._