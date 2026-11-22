# Graph Report - beacon  (2026-11-21)

## Corpus Check
- 95 files · ~91,067 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .jsonl 2, .css 1)

## Summary
- 1416 nodes · 3048 edges · 78 communities (64 shown, 14 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 281 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `510f6203`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- tempfile
- App.jsx
- guided_step
- Beacon: Nathan's revision (spec)
- probe_frame_test.py
- probe_once
- probe_to_world
- with
- head.cpp
- probe_frame.py
- Any
- calibrate_images
- test_frame_id_seed.py
- guided/src/main.c
- telemd.c
- dashboard/package.json
- Model Files Directory (not committed)
- argparse
- beacon_intent_kind
- guided synthesizer (FIFO 58, core 0)
- percept vision process (RR 22, cores 1-3)
- telemd (read-only telemetry sender)
- 3D Dashboard (Vite + React + three.js)
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
- Logitech C270 Stand-In Camera and Mic
- DepthSamplingTest
- Beacon Accessibility Research
- voiced speech process (RR 18, cores 1-3)
- Merge verdict: BLOCK
- Clip caption table (enum beacon_clip order)
- .patch_chair_frames
- argparse
- FakeLandmarker
- Merge verdict: BLOCK
- build_parser
- world_in.c
- build_parser
- ProbeResources
- Refresh the graph before a PR into main
- Weekend build order (geometry order)
- qnxpi Target (QNX 8.0 Raspberry Pi 5)
- FakeCapture
- FakeFileCapture
- .test_capture_frames_prompts_between_views
- Five-process QNX isolation architecture
- bt_audio_service.sh
- run-radio-auto.sh
- beacon_pulse
- make_clips.ps1
- pi_live.sh
- test_frame_id_seed.py
- beacon_law
- /beacon_frames Newest-wins Three-slot Ring
- Deterministic Synonym Query Remap
- App.jsx
- Honest LOST Cue (no invented metres)
- bt_speaker.py
- Inclusive Language and Non-Cure Framing
- calib.json Camera Intrinsics (laptop-local, gitignored)
- FakeInferenceSession

## God Nodes (most connected - your core abstractions)
1. `beacon_clip` - 60 edges
2. `probe_to_world()` - 46 edges
3. `guided_step()` - 43 edges
4. `make_probe()` - 37 edges
5. `probe_once()` - 36 edges
6. `ProbeRuntimeTest` - 34 edges
7. `ProbeToWorldTest` - 32 edges
8. `prepare()` - 26 edges
9. `Beacon: Nathan's revision (spec)` - 25 edges
10. `main()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Heartbeat Fault Detection and Restart with Backoff` --semantically_similar_to--> `Processes Panel (heartbeat age, down at >=1 s)`  [INFERRED] [semantically similar]
  supervisor/README.md → telemd/README.md
- `main()` --calls--> `beacon_seq_read()`  [INFERRED]
  camd/tools/read_frames.c → include/beacon.h
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

## Communities (78 total, 14 thin omitted)

### Community 0 - "tempfile"
Cohesion: 0.15
Nodes (9): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips(), supervise() (+1 more)

### Community 1 - "App.jsx"
Cohesion: 0.10
Nodes (69): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+61 more)

### Community 2 - "guided_step"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.13
Nodes (16): Beacon: Nathan's revision (spec), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), QNX AI workshop (MediaPipe hands on Pi), QNX prize research (QNX-research.md), Team ops plan (docs/team-plan.md), Loaner Pi Bring-up Log, Pi Development Workflow (QNX 8.0 on Raspberry Pi 5) (+8 more)

### Community 5 - "probe_once"
Cohesion: 0.16
Nodes (6): main(), prepare(), probe_once(), fake_encode(), synthetic_probe_modules(), synthetic_video_modules()

### Community 6 - "probe_to_world"
Cohesion: 0.06
Nodes (22): build_parser(), emit_lines(), format_readout(), load_target_names(), main(), _ns(), _number(), _output() (+14 more)

### Community 7 - "with"
Cohesion: 0.07
Nodes (38): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+30 more)

### Community 8 - "head.cpp"
Cohesion: 0.12
Nodes (11): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, synthetic_view() (+3 more)

### Community 9 - "probe_frame.py"
Cohesion: 0.07
Nodes (28): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+20 more)

### Community 10 - "Any"
Cohesion: 0.15
Nodes (12): Affine, _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip() (+4 more)

### Community 11 - "calibrate_images"
Cohesion: 0.07
Nodes (26): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+18 more)

### Community 12 - "test_frame_id_seed.py"
Cohesion: 0.27
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 13 - "guided/src/main.c"
Cohesion: 0.10
Nodes (17): main(), put_u16(), put_u32(), write_bmp(), main(), open_world(), beacon_frame_slot_t, beacon_live_max_ns() (+9 more)

### Community 14 - "telemd.c"
Cohesion: 0.10
Nodes (32): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+24 more)

### Community 15 - "dashboard/package.json"
Cohesion: 0.09
Nodes (28): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+20 more)

### Community 16 - "Model Files Directory (not committed)"
Cohesion: 0.10
Nodes (6): DepthStabiliser, _DepthState, _SlotState, SlotTracker, DepthStabiliserTest, SlotTrackerTest

### Community 17 - "argparse"
Cohesion: 0.21
Nodes (4): main(), __init__(), main(), read_labels()

### Community 18 - "beacon_intent_kind"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

### Community 19 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.12
Nodes (17): 12-person BLV hand-steering study, Error handling / failure-mode table, GPIO piezo (cannot-fail actuator), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, Range 1: same camera frame (tabletop reach, no VO), REACH guidance law (ticks only), supervisor process (FIFO 63, core 0) (+9 more)

### Community 20 - "percept vision process (RR 22, cores 1-3)"
Cohesion: 0.19
Nodes (18): /beacon_depth depth slot (shm), /beacon_frames newest-frame ring (shm), /beacon_world WorldState (shm), camd camera daemon (FIFO 50, core 0), crumbs[512] breadcrumb trail, Depth Anything V2 Metric Indoor Small INT8, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite) (+10 more)

### Community 21 - "telemd (read-only telemetry sender)"
Cohesion: 0.15
Nodes (19): audio_publish_stats(), audio_submit(), test_seq_writer_restart(), beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t, beacon_guided_stats_t (+11 more)

### Community 22 - "3D Dashboard (Vite + React + three.js)"
Cohesion: 0.16
Nodes (18): Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), Crumb Trail Dots (crumbs[].xyz_world), Dashboard World-dot View (Scene.jsx, App.jsx), Laptop RGB-D Odometry (ORB + solvePnPRansac, keyframes, crumbs), Wearer Dot at pose.T_world_from_cam Translation, bridge (UDP-to-WebSocket laptop relay), Saturday Build Order (spec section 13, steps 1-6), 3D Dashboard (Vite + React + three.js) (+10 more)

### Community 23 - "probe_frame_test.py"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 24 - "WALK Speech / REACH Ticks Audio Split"
Cohesion: 0.22
Nodes (5): Auditory Hand-Steering Guidance for BLV People (CHI 2026), Aural and Haptic Feedback for Visually Impaired People on a Track (ICHI), Evaluation of Short-Range Depth Sonifications (IEEE THMS), Less is More (VIA-Agent) PVI Study, Guidance Laws (STOP, LOST, REACH, WALK, RETURN)

### Community 25 - "TapeCheckTest"
Cohesion: 0.19
Nodes (12): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, 16.67 ms CLOCK_MONOTONIC guidance loop, Range 2: object still in view (walk while looking, no VO), Pre-Sunday testing requirements, WALK guidance law (spoken instruction) (+4 more)

### Community 26 - "guided (60 Hz guidance synthesizer)"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 27 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.24
Nodes (11): Even seq.* Values (telemd skips torn reads), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram), World-state JSON Message (~10 Hz), --jpeg Raw UDP Preview Datagram (+3 more)

### Community 28 - "beacon.h"
Cohesion: 0.11
Nodes (18): dev-reach.jsonl sample (walk, reach, slay percept -> HOLD -> LOST), Optional live JPEG video frames, Live status line every 5 s (world, video, dropped, dashboards), Bridge replay mode (paced by t_ns), Session recording to recordings/<UTC>.jsonl, telemd (Pi telemetry sender), UDP ingest on port 5005, WebSocket out ws://127.0.0.1:8765 (+10 more)

### Community 29 - "main"
Cohesion: 0.12
Nodes (14): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), audio_dropped_speech(), audio_stop(), main() (+6 more)

### Community 30 - "Scene.jsx"
Cohesion: 0.25
Nodes (20): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+12 more)

### Community 31 - "Logitech C270 Stand-In Camera and Mic"
Cohesion: 0.12
Nodes (22): audio_main(), audio_start(), law_name(), mode_name(), audio_out_close(), audio_out_open(), audio_out_paced(), audio_out_write() (+14 more)

### Community 32 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.20
Nodes (11): Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764), ONNX Runtime 1.24.4 on QNX, Ultralytics YOLOE Docs, YOLO-World INT8 TFLite (+3 more)

### Community 33 - "probe_frame.py"
Cohesion: 0.15
Nodes (10): _box_bounds(), _box_iou(), load_calibration(), load_depth_session(), load_labels(), load_yolo(), load_yolo_session(), _median_depth() (+2 more)

### Community 34 - "percept vision process (RR 22, cores 1-3)"
Cohesion: 0.11
Nodes (16): models/labels.txt runtime vocabulary, onnxruntime 1.24.4 (QNX), YOLOE-26n baked detect-only ONNX detector, Depth Anything V2 Static ONNX Export (210x210 metric), MediaPipe hand_landmarker.task Probe, percept/tools/probe_frame.py Laptop Probe, QNX Inference Runtime Packages (still missing), QNX /beacon_frames shm Round-trip (camd --bmp -> read-frames -> dump-frame) (+8 more)

### Community 35 - "ProbeRuntimeTest"
Cohesion: 0.12
Nodes (3): ProbeRuntimeTest, fake_detect(), fake_predict_depth()

### Community 36 - "camd/src/main.c"
Cohesion: 0.25
Nodes (12): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+4 more)

### Community 37 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.25
Nodes (9): BMP Bring-up Frame Source (frametype 65535), QNX CamAPI Adapter (not wired yet), camd (camera daemon), Synthetic Stub Frame Source (frametype 0), intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), Beacon (chest-worn item-homing wearable), beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes), nathans-revision.md Design (source of truth) (+1 more)

### Community 38 - "Model Files Directory (not committed)"
Cohesion: 0.19
Nodes (11): crumbs Breadcrumb Positions, Baked YOLOE Label Vocabulary (64 nouns), export_yoloe.py Detector Export, Optional llama.cpp GGUF, MediaPipe Hand Models, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin, yoloe26n_320.onnx (baked prompts, detect-only) (+3 more)

### Community 39 - "tape_check.py"
Cohesion: 0.26
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 40 - "Logitech C270 Stand-In Camera and Mic"
Cohesion: 0.33
Nodes (8): C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535), World-frame 3D Dots Plan, Logitech C270 Stand-In Camera and Mic, camd (camera process), Hardware Inventory (Pi 5, C270, JBL Go 3, ultrasonic, IMU), Experimental BTstack A2DP Bridge to JBL Go 3, Nathan (hardware and perception owner)

### Community 41 - "DepthSamplingTest"
Cohesion: 0.26
Nodes (5): Calibration, guess_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 42 - "Beacon Accessibility Research"
Cohesion: 0.20
Nodes (9): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), CHI 2025: BLV Object-Recognition Technologies in India, Multi-Purpose Camera Apps (Seeing AI, Lookout, Be My Eyes, Envision), Find My Things (Morrison et al., ASSETS 2023), Floor-Level Dropped Items Scope Gap, Kientz et al., Where's My Stuff? (ASSETS 2006), Tactile-First Problem-Solving Hierarchy (+1 more)

### Community 43 - "voiced speech process (RR 18, cores 1-3)"
Cohesion: 0.24
Nodes (11): intent (voiced-owned job + candidate names), llama.cpp ~0.5B remap (table miss only), REPEAT and REJECT commands, Synonym / keyword table (fast path), voiced speech process (RR 18, cores 1-3), whisper.cpp tiny.en (speech in, spec), include/beacon.h Shared Header, REPEAT / REJECT Intents (+3 more)

### Community 45 - "Clip caption table (enum beacon_clip order)"
Cohesion: 0.18
Nodes (9): deadline-test (over_period vs over_1ms), run_scenario.sh script, Clip caption table (enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids), telemd-preview JPEG Sender (libjpeg) (+1 more)

### Community 46 - ".patch_chair_frames"
Cohesion: 0.35
Nodes (9): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+1 more)

### Community 47 - "argparse"
Cohesion: 0.38
Nodes (9): apply(), find_key(), get_num(), get_str(), get_vec3(), main(), publish(), row_for() (+1 more)

### Community 48 - "FakeLandmarker"
Cohesion: 0.43
Nodes (6): add(), handle(), is_skip(), kind_name(), main(), send_intent()

### Community 49 - "Merge verdict: BLOCK"
Cohesion: 0.20
Nodes (8): pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, Per-instance Depth Slot Median Stabiliser, Box IoU Slot Association (--slot-iou 0.30), tape_check.py Absolute-depth Gate, Visual Odometry (VO)

### Community 50 - "build_parser"
Cohesion: 0.13
Nodes (7): build_parser(), make_affine(), parse_csv3(), _positive_float_arg(), _positive_int_arg(), parse(), _unit_float_arg()

### Community 52 - "build_parser"
Cohesion: 0.36
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 53 - "ProbeResources"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 55 - "Weekend build order (geometry order)"
Cohesion: 0.22
Nodes (9): 30-second Sunday demo script, Loaner bring-up checklist (QNX image), QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), slay percept -> HOLD -> LOST failure demo, Weekend build order (geometry order), post_startup.sh Boot Persistence (on -d -p 10, after io-snd), qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB) (+1 more)

### Community 56 - "qnxpi Target (QNX 8.0 Raspberry Pi 5)"
Cohesion: 0.22
Nodes (7): Before-Demo Checklist, Default qnxuser Password Risk, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay), QNXE-195 ssh-rsa Host Key Negotiation, qnxpi Target (QNX 8.0 Raspberry Pi 5), slog2info / slogger2 Logging

### Community 59 - ".test_capture_frames_prompts_between_views"
Cohesion: 0.70
Nodes (3): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), CLAUDE.md (imports AGENTS.md)

### Community 60 - "Five-process QNX isolation architecture"
Cohesion: 0.25
Nodes (5): Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), procmgr_ability priority ability and root drop, telemd optional monitoring process

### Community 63 - "beacon_pulse"
Cohesion: 0.25
Nodes (8): beacon_pulse, BEACON_PULSE_AUDIO_UNDERRUN, BEACON_PULSE_HB_CAMD, BEACON_PULSE_HB_GUIDED, BEACON_PULSE_HB_PERCEPT, BEACON_PULSE_HB_VOICED, BEACON_PULSE_INTENT_EDGE, BEACON_PULSE_SUP_TICK

### Community 69 - "beacon_law"
Cohesion: 0.29
Nodes (7): beacon_law, BEACON_LAW_LOST, BEACON_LAW_NONE, BEACON_LAW_REACH, BEACON_LAW_RETURN, BEACON_LAW_STOP, BEACON_LAW_WALK

### Community 70 - "/beacon_frames Newest-wins Three-slot Ring"
Cohesion: 0.33
Nodes (6): /beacon_frames Newest-wins Three-slot Ring, dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, /beacon_depth Shared Memory, percept-head Shm Reader (src/head.cpp)

### Community 71 - "Deterministic Synonym Query Remap"
Cohesion: 0.33
Nodes (4): Embedding Pose Graph, llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, NLMap

### Community 72 - "App.jsx"
Cohesion: 0.19
Nodes (17): dashboard README, animate-ui primitives (Highlight, RollingText, SlidingNumber, Slider, Button), App(), Caption(), isNum(), measured(), MODES, msAgo() (+9 more)

### Community 73 - "Honest LOST Cue (no invented metres)"
Cohesion: 0.18
Nodes (8): AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), HoldLight (BLV climbers), UI Preferences for a Camera-Based Wayfinding Aid (JVIB), NavCog / NavCog3 (CMU), NavGraph Parsimonious Instructions, Sighted by Default: Calibrated Honesty (CHI 2026), This is My Fault, Really? BLV Perception of LVLM Hallucination (UIST 2025)

### Community 74 - "bt_speaker.py"
Cohesion: 0.16
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 75 - "Inclusive Language and Non-Cure Framing"
Cohesion: 0.40
Nodes (5): CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021), Hoffman-Andrews et al., Cure Rhetoric Criticized by Blind Participants, Inclusive Language and Non-Cure Framing, Independence as Control, Not Avoiding Help

### Community 76 - "calib.json Camera Intrinsics (laptop-local, gitignored)"
Cohesion: 0.50
Nodes (4): xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), calib.json Camera Intrinsics (laptop-local, gitignored), calibrate_camera.py Chessboard Calibration, --fov Pinhole Guess (66 deg)

## Knowledge Gaps
- **162 isolated node(s):** `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE`, `BEACON_MODE_LOST`, `BEACON_MODE_NONE`, `full_h` (+157 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 418 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clip caption table (enum beacon_clip order)` connect `Clip caption table (enum beacon_clip order)` to `App.jsx`, `telemd (read-only telemetry sender)`?**
  _High betweenness centrality (0.416) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE`, `BEACON_MODE_LOST` to the rest of the system?**
  _162 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `tempfile` be split into smaller, more focused modules?**
  _Cohesion score 0.1476923076923077 - nodes in this community are weakly interconnected._
- **Why does `Beacon: Nathan's revision (spec)` connect `Beacon: Nathan's revision (spec)` to `YOLOE-26n-seg (text-prompted, baked static ONNX)`, `App.jsx`, `Honest LOST Cue (no invented metres)`, `Beacon Accessibility Research`, `Merge verdict: BLOCK`, `Clip caption table (enum beacon_clip order)`, `telemd.c`, `percept vision process (RR 22, cores 1-3)`, `Weekend build order (geometry order)`, `TapeCheckTest`, `Five-process QNX isolation architecture`?**
  _High betweenness centrality (0.213) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.10328638497652583 - nodes in this community are weakly interconnected._