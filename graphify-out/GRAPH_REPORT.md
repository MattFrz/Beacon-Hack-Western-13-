# Graph Report - beacon  (2026-11-21)

## Corpus Check
- 95 files · ~90,702 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .jsonl 2, .css 1)

## Summary
- 1412 nodes · 3038 edges · 82 communities (65 shown, 17 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 279 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `60ebc2bf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- probe_to_world
- App.jsx
- guided_step
- Beacon: Nathan's revision (spec)
- bridge.test.js
- probe_once
- Beacon Accessibility Research
- with
- head.cpp
- probe_frame.py
- guided (60 Hz cue synthesizer)
- calibrate_images
- Beacon Accessibility Research
- guided/src/main.c
- telemd.c
- App.jsx
- Model Files Directory (not committed)
- percept (perception process)
- beacon_intent_kind
- guided synthesizer (FIFO 58, core 0)
- Beacon (chest-worn item-homing wearable)
- telemd (read-only telemetry sender)
- Logitech C270 Stand-In Camera and Mic
- probe_frame_test.py
- DepthStabiliser
- TapeCheckTest
- guided (60 Hz guidance synthesizer)
- bt_speaker.py
- beacon.h
- main
- guided synthesizer (FIFO 58, core 0)
- Logitech C270 Stand-In Camera and Mic
- deadline_test.c
- Deterministic Synonym Query Remap
- YOLOE-26n baked detect-only ONNX detector
- SlotTracker
- camd/src/main.c
- resolve_calibration
- encode_preview
- tape_check.py
- Saturday Build Order (spec section 13, steps 1-6)
- DepthSamplingTest
- beacon_cmd.c
- percept vision process (RR 22, cores 1-3)
- Merge verdict: BLOCK
- Clip caption table (enum beacon_clip order)
- .patch_chair_frames
- argparse
- FakeLandmarker
- Merge verdict: BLOCK
- fakeworld.c
- world_in.c
- build_parser
- ProbeResources
- Refresh the graph before a PR into main
- SlotTracker
- string
- FakeCapture
- FakeFileCapture
- .test_capture_frames_prompts_between_views
- FakeInferenceSession
- bt_audio_service.sh
- run-radio-auto.sh
- telemd (read-only telemetry sender)
- make_clips.ps1
- pi_live.sh
- test_frame_id_seed.py
- qnxpi Target (QNX 8.0 Raspberry Pi 5)
- Hardware Request (USB audio, piezo, Camera Module 3)
- /boot/onboot Boot Hook
- Laptop-first World-dot Pipeline (probe_frame -> probe_to_world -> bridge -> dashboard)
- beacon_pulse
- Parsimonious, Query-Driven Instructions
- beacon_law
- percept (YOLOE, depth, hands, unproject, VO)
- Honest LOST Cue (no invented metres)
- beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)
- Inclusive Language and Non-Cure Framing
- Mode banner (LIVE / HOLD / LOST)
- FakeInferenceSession

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

## Communities (82 total, 17 thin omitted)

### Community 0 - "probe_to_world"
Cohesion: 0.05
Nodes (27): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout(), main() (+19 more)

### Community 1 - "App.jsx"
Cohesion: 0.10
Nodes (67): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+59 more)

### Community 2 - "guided_step"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.13
Nodes (16): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), procmgr_ability priority ability and root drop, QNX AI workshop (MediaPipe hands on Pi) (+8 more)

### Community 5 - "probe_once"
Cohesion: 0.13
Nodes (6): prepare(), probe_once(), ProbeRuntimeTest, fake_encode(), synthetic_probe_modules(), synthetic_video_modules()

### Community 6 - "Beacon Accessibility Research"
Cohesion: 0.15
Nodes (6): probe_to_world(), make_detection(), make_last_bottle(), make_probe(), ProbeToWorldTest, ReadoutTest

### Community 7 - "with"
Cohesion: 0.07
Nodes (38): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+30 more)

### Community 8 - "head.cpp"
Cohesion: 0.10
Nodes (11): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, synthetic_view() (+3 more)

### Community 9 - "probe_frame.py"
Cohesion: 0.07
Nodes (28): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+20 more)

### Community 10 - "guided (60 Hz cue synthesizer)"
Cohesion: 0.13
Nodes (17): Affine, _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip() (+9 more)

### Community 11 - "calibrate_images"
Cohesion: 0.07
Nodes (25): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+17 more)

### Community 12 - "Beacon Accessibility Research"
Cohesion: 0.20
Nodes (9): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), CHI 2025: BLV Object-Recognition Technologies in India, Multi-Purpose Camera Apps (Seeing AI, Lookout, Be My Eyes, Envision), Find My Things (Morrison et al., ASSETS 2023), Floor-Level Dropped Items Scope Gap, Kientz et al., Where's My Stuff? (ASSETS 2006), Tactile-First Problem-Solving Hierarchy (+1 more)

### Community 13 - "guided/src/main.c"
Cohesion: 0.13
Nodes (13): main(), put_u16(), put_u32(), write_bmp(), beacon_frame_slot_t, beacon_live_max_ns(), main(), open_world() (+5 more)

### Community 14 - "telemd.c"
Cohesion: 0.14
Nodes (22): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+14 more)

### Community 15 - "App.jsx"
Cohesion: 0.06
Nodes (67): Beacon dashboard index.html, dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9 (+59 more)

### Community 16 - "Model Files Directory (not committed)"
Cohesion: 0.19
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 17 - "percept (perception process)"
Cohesion: 0.11
Nodes (8): build_parser(), main(), _output(), parse_udp_target(), UdpEmitTest, fake_emit_lines(), fake_probe_once(), fake_probe_once()

### Community 18 - "beacon_intent_kind"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

### Community 19 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.17
Nodes (14): Error handling / failure-mode table, GPIO piezo (cannot-fail actuator), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, intent (voiced-owned job + candidate names), models/labels.txt runtime vocabulary, llama.cpp ~0.5B remap (table miss only), Range 1: same camera frame (tabletop reach, no VO) (+6 more)

### Community 20 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.19
Nodes (19): /beacon_depth depth slot (shm), /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, Depth Anything V2 Metric Indoor Small INT8, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite), objects[32] session POI store, OpenCV 4.12 (features2d + calib3d) (+11 more)

### Community 21 - "telemd (read-only telemetry sender)"
Cohesion: 0.13
Nodes (22): main(), audio_publish_stats(), audio_submit(), test_seq_writer_restart(), beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t (+14 more)

### Community 22 - "Logitech C270 Stand-In Camera and Mic"
Cohesion: 0.13
Nodes (16): Loaner bring-up checklist (QNX image), whisper.cpp tiny.en (speech in, spec), post_startup.sh Boot Persistence (on -d -p 10, after io-snd), BTstack A2DP Bridge to JBL Go 3 (Combadge-HTN/qnx-bluetooth), supervisor/bt_audio_service.sh Supervisor-managed BT Child, guided/bt_speaker.py (stdlib 16 kHz mono -> 44.1 kHz stereo player), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), Aborted Radio Session Recovery (gpio-bcm reset, uart_probe --idle-after-abort) (+8 more)

### Community 23 - "probe_frame_test.py"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 24 - "DepthStabiliser"
Cohesion: 0.13
Nodes (16): Auditory Hand-Steering Guidance for BLV People (CHI 2026), Evaluation of Short-Range Depth Sonifications (IEEE THMS), Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), Dashboard World-dot View (Scene.jsx, App.jsx), Wearer Dot at pose.T_world_from_cam Translation, bridge (UDP-to-WebSocket laptop relay), 3D Dashboard (Vite + React + three.js), Guidance Laws (STOP, LOST, REACH, WALK, RETURN) (+8 more)

### Community 25 - "TapeCheckTest"
Cohesion: 0.15
Nodes (14): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, 16.67 ms CLOCK_MONOTONIC guidance loop, onnxruntime 1.24.4 (QNX), Range 2: object still in view (walk while looking, no VO), Pre-Sunday testing requirements (+6 more)

### Community 26 - "guided (60 Hz guidance synthesizer)"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 27 - "bt_speaker.py"
Cohesion: 0.24
Nodes (11): Even seq.* Values (telemd skips torn reads), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram), World-state JSON Message (~10 Hz), --jpeg Raw UDP Preview Datagram (+3 more)

### Community 28 - "beacon.h"
Cohesion: 0.15
Nodes (14): dev-reach.jsonl sample (walk, reach, slay percept -> HOLD -> LOST), Optional live JPEG video frames, Live status line every 5 s (world, video, dropped, dashboards), Bridge replay mode (paced by t_ns), Session recording to recordings/<UTC>.jsonl, telemd (Pi telemetry sender), UDP ingest on port 5005, WebSocket out ws://127.0.0.1:8765 (+6 more)

### Community 29 - "main"
Cohesion: 0.16
Nodes (12): audio_dropped_speech(), audio_stop(), main(), open_world(), sleep_until(), platform_heartbeat(), platform_piezo_init(), platform_piezo_set() (+4 more)

### Community 30 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.31
Nodes (5): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns()

### Community 31 - "Logitech C270 Stand-In Camera and Mic"
Cohesion: 0.13
Nodes (22): audio_main(), audio_start(), law_name(), mode_name(), audio_out_close(), audio_out_open(), audio_out_paced(), audio_out_write() (+14 more)

### Community 32 - "deadline_test.c"
Cohesion: 0.20
Nodes (11): Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764), ONNX Runtime 1.24.4 on QNX, Ultralytics YOLOE Docs, YOLO-World INT8 TFLite (+3 more)

### Community 33 - "Deterministic Synonym Query Remap"
Cohesion: 0.33
Nodes (4): Embedding Pose Graph, llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, NLMap

### Community 34 - "YOLOE-26n baked detect-only ONNX detector"
Cohesion: 0.40
Nodes (3): YOLOE-26n baked detect-only ONNX detector, YOLOE-26n Detect-only ONNX Export (32 labels, (1,36,2100), no NMS), YOLOE-26n (baked noun list, static detect-only ONNX at 320)

### Community 35 - "SlotTracker"
Cohesion: 0.27
Nodes (6): emit_lines(), format_readout(), _ns(), _number(), _timing(), _vec3()

### Community 36 - "camd/src/main.c"
Cohesion: 0.25
Nodes (12): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+4 more)

### Community 37 - "resolve_calibration"
Cohesion: 0.22
Nodes (10): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0), /beacon_depth Shared Memory (+2 more)

### Community 38 - "encode_preview"
Cohesion: 0.20
Nodes (10): QNX CamAPI Adapter (not wired yet), intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), Baked YOLOE Label Vocabulary (64 nouns), Optional llama.cpp GGUF, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin, Beacon (chest-worn item-homing wearable), nathans-revision.md Design (source of truth) (+2 more)

### Community 39 - "tape_check.py"
Cohesion: 0.26
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 40 - "Saturday Build Order (spec section 13, steps 1-6)"
Cohesion: 0.13
Nodes (20): /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), 30-second Sunday demo script, QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), slay percept -> HOLD -> LOST failure demo, Weekend build order (geometry order), camd --bmp Bring-up Frame Source (frametype 65535) (+12 more)

### Community 41 - "DepthSamplingTest"
Cohesion: 0.22
Nodes (6): Calibration, guess_calibration(), load_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 42 - "beacon_cmd.c"
Cohesion: 0.15
Nodes (3): make_affine(), parse_csv3(), DepthSamplingTest

### Community 45 - "Clip caption table (enum beacon_clip order)"
Cohesion: 0.33
Nodes (6): deadline-test (over_period vs over_1ms), Clip caption table (enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids)

### Community 46 - ".patch_chair_frames"
Cohesion: 0.35
Nodes (9): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+1 more)

### Community 47 - "argparse"
Cohesion: 0.42
Nodes (8): apply(), find_key(), get_num(), get_str(), get_vec3(), main(), row_for(), skip_value()

### Community 48 - "FakeLandmarker"
Cohesion: 0.43
Nodes (6): add(), handle(), is_skip(), kind_name(), main(), send_intent()

### Community 49 - "Merge verdict: BLOCK"
Cohesion: 0.22
Nodes (8): pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, Per-instance Depth Slot Median Stabiliser, Box IoU Slot Association (--slot-iou 0.30), tape_check.py Absolute-depth Gate, Visual Odometry (VO)

### Community 50 - "fakeworld.c"
Cohesion: 0.24
Nodes (6): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), _unit_float_arg()

### Community 52 - "build_parser"
Cohesion: 0.36
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 53 - "ProbeResources"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 55 - "SlotTracker"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 59 - ".test_capture_frames_prompts_between_views"
Cohesion: 0.70
Nodes (3): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), CLAUDE.md (imports AGENTS.md)

### Community 63 - "telemd (read-only telemetry sender)"
Cohesion: 0.18
Nodes (11): /beacon_world Shared Memory, Seqlock Shared-memory Reads (seq_percept / seq_voiced / seq_guided), run_scenario.sh script, Dummy Worker Heartbeat Test, Heartbeat Fault Detection and Restart with Backoff, Piezo Fault Path, supervisor (spawn, runmasks, heartbeats, restarts), telemd (read-only telemetry sender) (+3 more)

### Community 68 - "qnxpi Target (QNX 8.0 Raspberry Pi 5)"
Cohesion: 0.20
Nodes (8): qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB), Before-Demo Checklist, Default qnxuser Password Risk, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay), QNXE-195 ssh-rsa Host Key Negotiation, qnxpi Target (QNX 8.0 Raspberry Pi 5), slog2info / slogger2 Logging

### Community 69 - "Hardware Request (USB audio, piezo, Camera Module 3)"
Cohesion: 0.22
Nodes (7): Aural and Haptic Feedback for Visually Impaired People on a Track (ICHI), Less is More (VIA-Agent) PVI Study, 12-person BLV hand-steering study, USB headset audio (off-thread playback), No PCM Playback Device on QNX Image (io-snd control only, no 3.5 mm), Camera Module 3 CSI (imx708, units 3-4, 2304x1296 nv12), Hardware Request (USB audio, piezo, Camera Module 3)

### Community 70 - "/boot/onboot Boot Hook"
Cohesion: 0.29
Nodes (5): CRLF Line Endings Break onboot, Network Diagnostics Ladder, QNXE-1894 Wi-Fi Settings Copy Bug, QNXE-2016 Shared Default Wi-Fi MAC, Serial Console (UART on 40-pin header)

### Community 71 - "Laptop-first World-dot Pipeline (probe_frame -> probe_to_world -> bridge -> dashboard)"
Cohesion: 0.29
Nodes (4): World-frame 3D Dots Plan, percept/tools/probe_to_world.py World JSONL Wrapper, Range 1 Tabletop Proof (no odometry), world.sample.json

### Community 72 - "beacon_pulse"
Cohesion: 0.25
Nodes (8): beacon_pulse, BEACON_PULSE_AUDIO_UNDERRUN, BEACON_PULSE_HB_CAMD, BEACON_PULSE_HB_GUIDED, BEACON_PULSE_HB_PERCEPT, BEACON_PULSE_HB_VOICED, BEACON_PULSE_INTENT_EDGE, BEACON_PULSE_SUP_TICK

### Community 73 - "Parsimonious, Query-Driven Instructions"
Cohesion: 0.29
Nodes (4): HoldLight (BLV climbers), UI Preferences for a Camera-Based Wayfinding Aid (JVIB), NavCog / NavCog3 (CMU), NavGraph Parsimonious Instructions

### Community 74 - "beacon_law"
Cohesion: 0.29
Nodes (7): beacon_law, BEACON_LAW_LOST, BEACON_LAW_NONE, BEACON_LAW_REACH, BEACON_LAW_RETURN, BEACON_LAW_STOP, BEACON_LAW_WALK

### Community 75 - "percept (YOLOE, depth, hands, unproject, VO)"
Cohesion: 0.33
Nodes (6): crumbs Breadcrumb Positions, export_yoloe.py Detector Export, MediaPipe Hand Models, yoloe26n_320.onnx (baked prompts, detect-only), percept (YOLOE, depth, hands, unproject, VO), probe_frame.py Laptop Stand-in

### Community 77 - "Honest LOST Cue (no invented metres)"
Cohesion: 0.47
Nodes (4): AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), Sighted by Default: Calibrated Honesty (CHI 2026), This is My Fault, Really? BLV Perception of LVLM Hallucination (UIST 2025)

### Community 78 - "beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)"
Cohesion: 0.33
Nodes (5): xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), calib.json Camera Intrinsics (laptop-local, gitignored), calibrate_camera.py Chessboard Calibration, --fov Pinhole Guess (66 deg), beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)

### Community 79 - "Inclusive Language and Non-Cure Framing"
Cohesion: 0.40
Nodes (5): CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021), Hoffman-Andrews et al., Cure Rhetoric Criticized by Blind Participants, Inclusive Language and Non-Cure Framing, Independence as Control, Not Avoiding Help

### Community 80 - "Mode banner (LIVE / HOLD / LOST)"
Cohesion: 0.40
Nodes (3): Events panel (process kills, restarts, mode changes), Mode banner (LIVE / HOLD / LOST), dev-reach.jsonl (made by make-dev-reach.js)

## Knowledge Gaps
- **162 isolated node(s):** `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE`, `BEACON_MODE_LOST`, `BEACON_MODE_NONE`, `full_h` (+157 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 416 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clip caption table (enum beacon_clip order)` connect `Clip caption table (enum beacon_clip order)` to `telemd (read-only telemetry sender)`, `App.jsx`?**
  _High betweenness centrality (0.413) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE`, `BEACON_MODE_LOST` to the rest of the system?**
  _162 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `probe_to_world` be split into smaller, more focused modules?**
  _Cohesion score 0.0505175983436853 - nodes in this community are weakly interconnected._
- **Why does `Beacon: Nathan's revision (spec)` connect `Beacon: Nathan's revision (spec)` to `deadline_test.c`, `/boot/onboot Boot Hook`, `Saturday Build Order (spec section 13, steps 1-6)`, `Beacon Accessibility Research`, `Honest LOST Cue (no invented metres)`, `Merge verdict: BLOCK`, `App.jsx`, `telemd.c`, `Beacon (chest-worn item-homing wearable)`, `TapeCheckTest`, `telemd (read-only telemetry sender)`?**
  _High betweenness centrality (0.194) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.10434782608695652 - nodes in this community are weakly interconnected._