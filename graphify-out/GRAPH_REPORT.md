# Graph Report - beacon  (2026-11-21)

## Corpus Check
- 95 files · ~91,127 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .jsonl 2, .css 1)

## Summary
- 1417 nodes · 3060 edges · 77 communities (64 shown, 13 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 281 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a88c085a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- tempfile
- App.jsx
- guided_step
- Beacon: Nathan's revision (spec)
- make-dev-reach.test.js
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- probe_to_world
- with
- head.cpp
- probe_frame.py
- Any
- audio.c
- test_frame_id_seed.py
- guided/src/main.c
- telemd.c
- beacon.h
- Model Files Directory (not committed)
- argparse
- beacon_intent_kind
- guided synthesizer (FIFO 58, core 0)
- deadline_test.c
- telemd (read-only telemetry sender)
- voiced speech process (RR 18, cores 1-3)
- probe_frame_test.py
- WALK Speech / REACH Ticks Audio Split
- TapeCheckTest
- guided (60 Hz guidance synthesizer)
- Beacon (chest-worn item-homing wearable)
- beacon.h
- main
- Scene.jsx
- Logitech C270 Stand-In Camera and Mic
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- probe_frame.py
- percept vision process (RR 22, cores 1-3)
- ProbeRuntimeTest
- camd/src/main.c
- Beacon (chest-worn item-homing wearable)
- Model Files Directory (not committed)
- tape_check.py
- bridge.test.js
- DepthSamplingTest
- main
- voiced speech process (RR 18, cores 1-3)
- Merge verdict: BLOCK
- Clip caption table (enum beacon_clip order)
- WALK Speech / REACH Ticks Audio Split
- argparse
- FakeLandmarker
- audio_out.c
- build_parser
- world_in.c
- Weekend build order (geometry order)
- ProbeResources
- Refresh the graph before a PR into main
- Weekend build order (geometry order)
- qnxpi Target (QNX 8.0 Raspberry Pi 5)
- FakeCapture
- FakeFileCapture
- .test_capture_frames_prompts_between_views
- Beacon Accessibility Research
- bt_audio_service.sh
- run-radio-auto.sh
- bridge/package.json
- make_clips.ps1
- irl_test.sh
- test_frame_id_seed.py
- .test_capture_frames_prompts_between_views
- beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)
- /beacon_frames Newest-wins Three-slot Ring
- App.jsx
- Honest LOST Cue (no invented metres)
- Honest LOST Cue (no invented metres)
- Deterministic Synonym Query Remap
- Inclusive Language and Non-Cure Framing

## God Nodes (most connected - your core abstractions)
1. `beacon_clip` - 60 edges
2. `probe_to_world()` - 46 edges
3. `guided_step()` - 43 edges
4. `make_probe()` - 37 edges
5. `probe_once()` - 36 edges
6. `ProbeRuntimeTest` - 34 edges
7. `ProbeToWorldTest` - 32 edges
8. `prepare()` - 26 edges
9. `Beacon: Nathan's revision (spec)` - 24 edges
10. `main()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Heartbeat Fault Detection and Restart with Backoff` --semantically_similar_to--> `Processes Panel (heartbeat age, down at >=1 s)`  [INFERRED] [semantically similar]
  supervisor/README.md → telemd/README.md
- `Processes Panel (heartbeat age, down at >=1 s)` --semantically_similar_to--> `NO DATA after 1 s without world state`  [INFERRED] [semantically similar]
  telemd/README.md → laptop/dashboard/README.md
- `probe_to_world.py World JSONL / UDP Emitter` --semantically_similar_to--> `telemd (read-only telemetry to the laptop)`  [INFERRED] [semantically similar]
  percept/README.md → README.md
- `--jpeg Raw UDP Preview Datagram` --semantically_similar_to--> `Optional Video JPEG (~5 fps, <60 KB per datagram)`  [INFERRED] [semantically similar]
  percept/README.md → laptop/samples/README.md
- `world_in (laptop-camera fallback bridge to /beacon_world)` --semantically_similar_to--> `fakeworld (scripted percept/voiced stand-in)`  [INFERRED] [semantically similar]
  voiced/README.md → guided/README.md

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

## Communities (77 total, 13 thin omitted)

### Community 0 - "tempfile"
Cohesion: 0.06
Nodes (21): build_parser(), format_readout(), load_target_names(), main(), _ns(), _number(), _output(), parse_udp_target() (+13 more)

### Community 1 - "App.jsx"
Cohesion: 0.11
Nodes (68): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_default_cfg(), guided_dir_cat(), guided_dist_clip() (+60 more)

### Community 2 - "guided_step"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.05
Nodes (17): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), prepare(), probe_once(), ProbeResources (+9 more)

### Community 4 - "make-dev-reach.test.js"
Cohesion: 0.16
Nodes (11): clock(), Events(), eventsFromLog(), texts(), buildDevReach(), dist(), lerp(), lastLive (+3 more)

### Community 5 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.20
Nodes (11): Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764), ONNX Runtime 1.24.4 on QNX, Ultralytics YOLOE Docs, YOLO-World INT8 TFLite (+3 more)

### Community 6 - "probe_to_world"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 7 - "with"
Cohesion: 0.07
Nodes (25): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+17 more)

### Community 8 - "head.cpp"
Cohesion: 0.13
Nodes (11): main(), put_u16(), put_u32(), write_bmp(), beacon_frame_slot_t, beacon_live_max_ns(), escape_name(), heartbeat_alive() (+3 more)

### Community 9 - "probe_frame.py"
Cohesion: 0.13
Nodes (10): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, write_synthetic_views() (+2 more)

### Community 10 - "Any"
Cohesion: 0.09
Nodes (28): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+20 more)

### Community 11 - "audio.c"
Cohesion: 0.18
Nodes (15): audio_dropped_speech(), audio_main(), audio_start(), audio_stop(), law_name(), mode_name(), audio_out_paced(), pan_gains() (+7 more)

### Community 12 - "test_frame_id_seed.py"
Cohesion: 0.17
Nodes (18): Beacon dashboard index.html, dashboard README, animate-ui primitives (Highlight, RollingText, SlidingNumber, Slider, Button), App(), Caption(), isNum(), measured(), MODES (+10 more)

### Community 13 - "guided/src/main.c"
Cohesion: 0.16
Nodes (8): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips(), supervise()

### Community 14 - "telemd.c"
Cohesion: 0.11
Nodes (31): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+23 more)

### Community 15 - "beacon.h"
Cohesion: 0.12
Nodes (25): main(), audio_publish_stats(), audio_submit(), test_seq_writer_restart(), beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t (+17 more)

### Community 16 - "Model Files Directory (not committed)"
Cohesion: 0.25
Nodes (20): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+12 more)

### Community 17 - "argparse"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 18 - "beacon_intent_kind"
Cohesion: 0.16
Nodes (10): Depth Anything V2 Metric Indoor Small INT8, onnxruntime 1.24.4 (QNX), YOLOE-26n baked detect-only ONNX detector, Depth Anything V2 Static ONNX Export (210x210 metric), MediaPipe hand_landmarker.task Probe, percept/tools/probe_frame.py Laptop Probe, YOLOE-26n Detect-only ONNX Export (32 labels, (1,36,2100), no NMS), Depth Anything V2 Metric Indoor Small (+2 more)

### Community 19 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.15
Nodes (18): bridge README, bridge (Node UDP-to-WebSocket relay and recorder), dev-reach.jsonl sample (walk, reach, slay percept -> HOLD -> LOST), Optional live JPEG video frames, Live status line every 5 s (world, video, dropped, dashboards), Bridge replay mode (paced by t_ns), Session recording to recordings/<UTC>.jsonl, telemd (Pi telemetry sender) (+10 more)

### Community 20 - "deadline_test.c"
Cohesion: 0.23
Nodes (5): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns()

### Community 21 - "telemd (read-only telemetry sender)"
Cohesion: 0.09
Nodes (4): synthetic_view(), FakeInferenceSession, FakeSessionOptions, wait_for()

### Community 22 - "voiced speech process (RR 18, cores 1-3)"
Cohesion: 0.20
Nodes (13): intent (voiced-owned job + candidate names), models/labels.txt runtime vocabulary, llama.cpp ~0.5B remap (table miss only), REPEAT and REJECT commands, Spec review (BLOCK, docs/beacon-spec-review.md), Synonym / keyword table (fast path), voiced speech process (RR 18, cores 1-3), whisper.cpp tiny.en (speech in, spec) (+5 more)

### Community 24 - "WALK Speech / REACH Ticks Audio Split"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 25 - "TapeCheckTest"
Cohesion: 0.15
Nodes (15): xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), dev-reach.jsonl (made by make-dev-reach.js), Even seq.* Values (telemd skips torn reads), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram) (+7 more)

### Community 26 - "guided (60 Hz guidance synthesizer)"
Cohesion: 0.13
Nodes (17): 12-person BLV hand-steering study, Error handling / failure-mode table, GPIO piezo (cannot-fail actuator), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, REACH guidance law (ticks only), supervisor process (FIFO 63, core 0), USB headset audio (off-thread playback) (+9 more)

### Community 27 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.15
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 28 - "beacon.h"
Cohesion: 0.35
Nodes (9): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+1 more)

### Community 29 - "main"
Cohesion: 0.07
Nodes (26): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+18 more)

### Community 30 - "Scene.jsx"
Cohesion: 0.25
Nodes (12): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+4 more)

### Community 31 - "Logitech C270 Stand-In Camera and Mic"
Cohesion: 0.15
Nodes (13): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0), run_scenario.sh script (+5 more)

### Community 32 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.16
Nodes (18): Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), telemd optional monitoring process, Dashboard World-dot View (Scene.jsx, App.jsx), Wearer Dot at pose.T_world_from_cam Translation, bridge (UDP-to-WebSocket laptop relay), Saturday Build Order (spec section 13, steps 1-6), camd (camera process), 3D Dashboard (Vite + React + three.js) (+10 more)

### Community 33 - "probe_frame.py"
Cohesion: 0.19
Nodes (12): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, 16.67 ms CLOCK_MONOTONIC guidance loop, Range 2: object still in view (walk while looking, no VO), Pre-Sunday testing requirements, WALK guidance law (spoken instruction) (+4 more)

### Community 34 - "percept vision process (RR 22, cores 1-3)"
Cohesion: 0.19
Nodes (8): C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535), QNX /beacon_frames shm Round-trip (camd --bmp -> read-frames -> dump-frame), World-frame 3D Dots Plan, percept/tools/probe_to_world.py World JSONL Wrapper, Logitech C270 Stand-In Camera and Mic, Hardware Inventory (Pi 5, C270, JBL Go 3, ultrasonic, IMU), Experimental BTstack A2DP Bridge to JBL Go 3

### Community 35 - "ProbeRuntimeTest"
Cohesion: 0.25
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 36 - "camd/src/main.c"
Cohesion: 0.31
Nodes (7): Affine, detect(), detect_yolo_ort(), find_fingertip(), letterbox(), predict_depth(), tensor_scalar()

### Community 37 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.15
Nodes (12): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), procmgr_ability priority ability and root drop, QNX prize research (QNX-research.md) (+4 more)

### Community 38 - "Model Files Directory (not committed)"
Cohesion: 0.16
Nodes (22): /beacon_depth depth slot (shm), /beacon_frames newest-frame ring (shm), /beacon_world WorldState (shm), camd camera daemon (FIFO 50, core 0), crumbs[512] breadcrumb trail, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite), objects[32] session POI store (+14 more)

### Community 39 - "tape_check.py"
Cohesion: 0.18
Nodes (14): crumbs Breadcrumb Positions, Baked YOLOE Label Vocabulary (64 nouns), export_yoloe.py Detector Export, Optional llama.cpp GGUF, MediaPipe Hand Models, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin, yoloe26n_320.onnx (baked prompts, detect-only) (+6 more)

### Community 40 - "bridge.test.js"
Cohesion: 0.23
Nodes (6): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, ws

### Community 41 - "DepthSamplingTest"
Cohesion: 0.22
Nodes (6): Calibration, guess_calibration(), load_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 42 - "main"
Cohesion: 0.18
Nodes (10): main(), open_world(), sleep_until(), platform_heartbeat(), platform_piezo_init(), platform_piezo_set(), platform_set_thread_sched(), platform_supervisor_connect() (+2 more)

### Community 43 - "voiced speech process (RR 18, cores 1-3)"
Cohesion: 0.12
Nodes (14): qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB), Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Network Diagnostics Ladder, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay) (+6 more)

### Community 44 - "Merge verdict: BLOCK"
Cohesion: 0.16
Nodes (6): _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), _median_depth(), DepthSamplingTest

### Community 45 - "Clip caption table (enum beacon_clip order)"
Cohesion: 0.27
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 46 - "WALK Speech / REACH Ticks Audio Split"
Cohesion: 0.12
Nodes (9): Auditory Hand-Steering Guidance for BLV People (CHI 2026), HoldLight (BLV climbers), Aural and Haptic Feedback for Visually Impaired People on a Track (ICHI), Evaluation of Short-Range Depth Sonifications (IEEE THMS), UI Preferences for a Camera-Based Wayfinding Aid (JVIB), NavCog / NavCog3 (CMU), NavGraph Parsimonious Instructions, Less is More (VIA-Agent) PVI Study (+1 more)

### Community 47 - "argparse"
Cohesion: 0.21
Nodes (4): main(), __init__(), main(), read_labels()

### Community 49 - "audio_out.c"
Cohesion: 0.29
Nodes (9): audio_out_close(), audio_out_open(), audio_out_write(), fifo_try_open(), fifo_write(), put16(), put32(), qnx_open() (+1 more)

### Community 50 - "build_parser"
Cohesion: 0.17
Nodes (9): _box_bounds(), _box_iou(), _DepthState, load_depth_session(), load_labels(), load_yolo(), load_yolo_session(), _slot_match_score() (+1 more)

### Community 51 - "world_in.c"
Cohesion: 0.23
Nodes (3): _SlotState, SlotTracker, SlotTrackerTest

### Community 52 - "Weekend build order (geometry order)"
Cohesion: 0.24
Nodes (8): 30-second Sunday demo script, Loaner bring-up checklist (QNX image), QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), slay percept -> HOLD -> LOST failure demo, Weekend build order (geometry order), post_startup.sh Boot Persistence (on -d -p 10, after io-snd), Sensor Framework Camera Probe (sensor_rpi5.conf units)

### Community 53 - "ProbeResources"
Cohesion: 0.22
Nodes (8): pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, Per-instance Depth Slot Median Stabiliser, Box IoU Slot Association (--slot-iou 0.30), tape_check.py Absolute-depth Gate, Visual Odometry (VO)

### Community 54 - "Refresh the graph before a PR into main"
Cohesion: 0.33
Nodes (11): apply(), find_key(), get_id(), get_num(), get_str(), get_vecn(), main(), publish() (+3 more)

### Community 55 - "Weekend build order (geometry order)"
Cohesion: 0.36
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 56 - "qnxpi Target (QNX 8.0 Raspberry Pi 5)"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 58 - "FakeFileCapture"
Cohesion: 0.48
Nodes (5): add(), handle(), is_skip(), kind_name(), main()

### Community 60 - "Beacon Accessibility Research"
Cohesion: 0.20
Nodes (9): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), CHI 2025: BLV Object-Recognition Technologies in India, Multi-Purpose Camera Apps (Seeing AI, Lookout, Be My Eyes, Envision), Find My Things (Morrison et al., ASSETS 2023), Floor-Level Dropped Items Scope Gap, Kientz et al., Where's My Stuff? (ASSETS 2006), Tactile-First Problem-Solving Hierarchy (+1 more)

### Community 61 - "bt_audio_service.sh"
Cohesion: 0.60
Nodes (4): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), graph-not-needed PR label, CLAUDE.md (imports AGENTS.md)

### Community 62 - "run-radio-auto.sh"
Cohesion: 0.33
Nodes (6): deadline-test (over_period vs over_1ms), Clip caption table (enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids)

### Community 63 - "bridge/package.json"
Cohesion: 0.17
Nodes (11): dependencies, ws@^8.23.0, name, private, scripts, replay, replay:dev, replay:sim (+3 more)

### Community 69 - "beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)"
Cohesion: 0.29
Nodes (5): QNX CamAPI Adapter (not wired yet), intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), calib.json Camera Intrinsics (laptop-local, gitignored), calibrate_camera.py Chessboard Calibration, beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)

### Community 74 - "Honest LOST Cue (no invented metres)"
Cohesion: 0.47
Nodes (4): AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), Sighted by Default: Calibrated Honesty (CHI 2026), This is My Fault, Really? BLV Perception of LVLM Hallucination (UIST 2025)

### Community 75 - "Deterministic Synonym Query Remap"
Cohesion: 0.33
Nodes (4): Embedding Pose Graph, llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, NLMap

### Community 76 - "Inclusive Language and Non-Cure Framing"
Cohesion: 0.40
Nodes (5): CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021), Hoffman-Andrews et al., Cure Rhetoric Criticized by Blind Participants, Inclusive Language and Non-Cure Framing, Independence as Control, Not Avoiding Help

## Knowledge Gaps
- **162 isolated node(s):** `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK`, `GUIDED_CMD_TONE_ON`, `GUIDED_CMD_TONE_OFF` (+157 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 415 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clip caption table (enum beacon_clip order)` connect `run-radio-auto.sh` to `test_frame_id_seed.py`, `beacon.h`?**
  _High betweenness centrality (0.417) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK` to the rest of the system?**
  _162 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `tempfile` be split into smaller, more focused modules?**
  _Cohesion score 0.059917920656634746 - nodes in this community are weakly interconnected._
- **Why does `Beacon: Nathan's revision (spec)` connect `Beacon (chest-worn item-homing wearable)` to `probe_frame.py`, `YOLOE-26n-seg (text-prompted, baked static ONNX)`, `Model Files Directory (not committed)`, `Honest LOST Cue (no invented metres)`, `voiced speech process (RR 18, cores 1-3)`, `test_frame_id_seed.py`, `telemd.c`, `FakeLandmarker`, `guided synthesizer (FIFO 58, core 0)`, `Weekend build order (geometry order)`, `voiced speech process (RR 18, cores 1-3)`, `Beacon Accessibility Research`, `Logitech C270 Stand-In Camera and Mic`?**
  _High betweenness centrality (0.217) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.10543259557344065 - nodes in this community are weakly interconnected._