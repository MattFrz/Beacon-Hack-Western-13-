# Graph Report - beacon  (2026-11-21)

## Corpus Check
- 122 files · ~125,529 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 11, .jsonl 3, .css 1)

## Summary
- 1799 nodes · 3926 edges · 94 communities (80 shown, 14 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 331 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c3a07454`
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
- os
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
- Model Files Directory (not committed)
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- probe_frame.py
- percept vision process (RR 22, cores 1-3)
- ProbeRuntimeTest
- camd/src/main.c
- Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)
- Model Files Directory (not committed)
- vo_core.py
- time
- probe_frame.py
- Any
- voiced speech process (RR 18, cores 1-3)
- Merge verdict: BLOCK
- Clip caption table (enum beacon_clip order)
- supervisor (spawn, runmasks, heartbeats, restarts)
- export_yoloe.py
- FakeLandmarker
- audio_out.c
- SlotTracker
- world_in.c
- Weekend build order (geometry order)
- ProbeResources
- Refresh the graph before a PR into main
- Weekend build order (geometry order)
- qnxpi Target (QNX 8.0 Raspberry Pi 5)
- FakeCapture
- FakeFileCapture
- Beacon: Nathan's revision (spec)
- Beacon Accessibility Research
- bt_audio_service.sh
- run-radio-auto.sh
- bridge/package.json
- make_clips.ps1
- irl_test.sh
- pi_live.sh
- test_frame_id_seed.py
- .test_capture_frames_prompts_between_views
- beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)
- /beacon_frames Newest-wins Three-slot Ring
- App.jsx
- Honest LOST Cue (no invented metres)
- test_frame_id_seed.py
- beacon_cmd.c
- Inclusive Language and Non-Cure Framing
- make-dev-reach.test.js
- beacon_pulse
- make_clip
- Beacon (chest-worn item-homing wearable)
- ingest
- device_live_demo.sh
- device_slay_beat.sh
- device_chain_demo.sh
- qnx_pkg_fetch.py
- Working notes (not shipped)
- ai-import-test.sh
- Depth Anything V2 Metric Indoor Small ONNX
- gen_ort_capi_table.py
- camd (camera daemon)
- telemd (read-only telemetry to the laptop)
- probe_to_world.py World JSONL / UDP Emitter
- export_depth.py

## God Nodes (most connected - your core abstractions)
1. `beacon_clip` - 60 edges
2. `probe_to_world()` - 47 edges
3. `guided_step()` - 43 edges
4. `probe_once()` - 38 edges
5. `make_probe()` - 37 edges
6. `ProbeRuntimeTest` - 34 edges
7. `ProbeToWorldTest` - 33 edges
8. `prepare()` - 27 edges
9. `Beacon: Nathan's revision (spec)` - 24 edges
10. `main()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Where it lives` --references--> `Vo`  [INFERRED]
  docs/superpowers/specs/2026-11-21-vo-integration-design.md → percept/tools/vo_core.py
- `Task 2: `vo_probe.py` — CLI over recorded or live walks` --references--> `predict_depth()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/probe_frame.py
- `Self-review` --references--> `VoConfig`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/vo_core.py
- `Self-review` --references--> `VoStep`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/vo_core.py
- `Task 6: Integration into the percept cycle and the measured gates` --references--> `crumb_due()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/vo_core.py

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

## Communities (94 total, 14 thin omitted)

### Community 0 - "tempfile"
Cohesion: 0.17
Nodes (6): probe_to_world(), make_detection(), make_last_bottle(), make_probe(), ProbeToWorldTest, fake_probe_once()

### Community 1 - "App.jsx"
Cohesion: 0.10
Nodes (69): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+61 more)

### Community 2 - "guided_step"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.06
Nodes (16): build_parser(), load_yolo_session(), main(), _positive_float_arg(), _positive_int_arg(), parse(), prepare(), probe_once() (+8 more)

### Community 4 - "make-dev-reach.test.js"
Cohesion: 0.10
Nodes (19): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, framesFlag, dependencies, ws@^8.23.0 (+11 more)

### Community 5 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.13
Nodes (14): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), CHI 2025: BLV Object-Recognition Technologies in India, CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021), Multi-Purpose Camera Apps (Seeing AI, Lookout, Be My Eyes, Envision), Find My Things (Morrison et al., ASSETS 2023), Floor-Level Dropped Items Scope Gap (+6 more)

### Community 6 - "probe_to_world"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 7 - "with"
Cohesion: 0.07
Nodes (26): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+18 more)

### Community 8 - "head.cpp"
Cohesion: 0.15
Nodes (7): main(), put_u16(), put_u32(), write_bmp(), main(), sleep_until(), beacon_frame_slot_t

### Community 9 - "probe_frame.py"
Cohesion: 0.10
Nodes (11): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, synthetic_view() (+3 more)

### Community 10 - "Any"
Cohesion: 0.09
Nodes (27): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+19 more)

### Community 11 - "audio.c"
Cohesion: 0.15
Nodes (25): audio_dropped_speech(), audio_main(), audio_publish_stats(), audio_start(), audio_stop(), audio_submit(), law_name(), mode_name() (+17 more)

### Community 12 - "test_frame_id_seed.py"
Cohesion: 0.20
Nodes (16): Beacon dashboard index.html, dashboard README, animate-ui primitives (Highlight, RollingText, SlidingNumber, Slider, Button), App(), Caption(), isNum(), measured(), MODES (+8 more)

### Community 13 - "os"
Cohesion: 0.18
Nodes (7): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips()

### Community 14 - "telemd.c"
Cohesion: 0.11
Nodes (31): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode (+23 more)

### Community 15 - "beacon.h"
Cohesion: 0.14
Nodes (11): beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t, beacon_guided_stats_t, beacon_hand_t, beacon_letterbox_t, beacon_object_t (+3 more)

### Community 16 - "Model Files Directory (not committed)"
Cohesion: 0.25
Nodes (20): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+12 more)

### Community 17 - "argparse"
Cohesion: 0.13
Nodes (12): beacon_live_max_ns(), destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg(), escape_name() (+4 more)

### Community 18 - "beacon_intent_kind"
Cohesion: 0.19
Nodes (10): models/labels.txt runtime vocabulary, YOLOE-26n baked detect-only ONNX detector, Depth Anything V2 Static ONNX Export (210x210 metric), MediaPipe hand_landmarker.task Probe, percept/tools/probe_frame.py Laptop Probe, YOLOE-26n Detect-only ONNX Export (32 labels, (1,36,2100), no NMS), Depth Anything V2 Metric Indoor Small, MediaPipe Hands (+2 more)

### Community 19 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.11
Nodes (21): run_scenario.sh script, bridge README, bridge (Node UDP-to-WebSocket relay and recorder), dev-reach.jsonl sample (walk, reach, slay percept -> HOLD -> LOST), Optional live JPEG video frames, Live status line every 5 s (world, video, dropped, dashboards), Bridge replay mode (paced by t_ns), Session recording to recordings/<UTC>.jsonl (+13 more)

### Community 20 - "deadline_test.c"
Cohesion: 0.18
Nodes (9): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), platform_heartbeat(), platform_piezo_init(), platform_set_thread_sched() (+1 more)

### Community 21 - "telemd (read-only telemetry sender)"
Cohesion: 0.09
Nodes (3): SessionOptions, FakeInferenceSession, FakeSessionOptions

### Community 22 - "voiced speech process (RR 18, cores 1-3)"
Cohesion: 0.17
Nodes (7): Auditory Hand-Steering Guidance for BLV People (CHI 2026), HoldLight (BLV climbers), Evaluation of Short-Range Depth Sonifications (IEEE THMS), UI Preferences for a Camera-Based Wayfinding Aid (JVIB), NavGraph Parsimonious Instructions, Less is More (VIA-Agent) PVI Study, Guidance Laws (STOP, LOST, REACH, WALK, RETURN)

### Community 23 - "probe_frame_test.py"
Cohesion: 0.20
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 24 - "WALK Speech / REACH Ticks Audio Split"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 25 - "TapeCheckTest"
Cohesion: 0.08
Nodes (11): api(), _check(), _find_library(), _OrtApiBase, OrtError, _read_ptr(), Session, TensorInfo (+3 more)

### Community 26 - "guided (60 Hz guidance synthesizer)"
Cohesion: 0.09
Nodes (35): NavCog / NavCog3 (CMU), /beacon_depth depth slot (shm), /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, Depth Anything V2 Metric Indoor Small INT8, guided synthesizer (FIFO 58, core 0), hand (percept-owned fingertip slot), Heartbeat pulses and supervisor 50 ms timer (+27 more)

### Community 27 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.16
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 28 - "beacon.h"
Cohesion: 0.35
Nodes (9): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+1 more)

### Community 29 - "main"
Cohesion: 0.10
Nodes (18): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+10 more)

### Community 30 - "Scene.jsx"
Cohesion: 0.25
Nodes (12): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+4 more)

### Community 31 - "Model Files Directory (not committed)"
Cohesion: 0.19
Nodes (11): crumbs Breadcrumb Positions, Baked YOLOE Label Vocabulary (64 nouns), export_yoloe.py Detector Export, Optional llama.cpp GGUF, MediaPipe Hand Models, Model Files Directory (not committed), whisper.cpp ggml-tiny.en.bin, yoloe26n_320.onnx (baked prompts, detect-only) (+3 more)

### Community 32 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.15
Nodes (16): AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), Sighted by Default: Calibrated Honesty (CHI 2026), Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), This is My Fault, Really? BLV Perception of LVLM Hallucination (UIST 2025), 30-second Sunday demo script, slay percept -> HOLD -> LOST failure demo, Dashboard World-dot View (Scene.jsx, App.jsx) (+8 more)

### Community 33 - "probe_frame.py"
Cohesion: 0.11
Nodes (18): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, Error handling / failure-mode table, 16.67 ms CLOCK_MONOTONIC guidance loop, Loaner bring-up checklist (QNX image), onnxruntime 1.24.4 (QNX) (+10 more)

### Community 34 - "percept vision process (RR 22, cores 1-3)"
Cohesion: 0.11
Nodes (23): /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535), Camera Module 3 CSI (imx708, units 3-4, 2304x1296 nv12), qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB) (+15 more)

### Community 35 - "ProbeRuntimeTest"
Cohesion: 0.26
Nodes (7): build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 36 - "camd/src/main.c"
Cohesion: 0.12
Nodes (5): _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), DepthSamplingTest

### Community 37 - "Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)"
Cohesion: 0.13
Nodes (13): Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Network Diagnostics Ladder, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay), QNXE-1894 Wi-Fi Settings Copy Bug (+5 more)

### Community 38 - "Model Files Directory (not committed)"
Cohesion: 0.18
Nodes (8): MergeTests, rec(), person_at(), record_with(), T(), vo_record(), world_record(), write_jsonl()

### Community 39 - "vo_core.py"
Cohesion: 0.08
Nodes (22): Task 6: Integration into the percept cycle and the measured gates, backproject(), _camera_matrix(), chain(), fit_ground_height(), keyframe_due(), lk_track(), PoseResult (+14 more)

### Community 40 - "time"
Cohesion: 0.23
Nodes (7): free_udp_port(), hand_at(), main(), record(), wait_for_exit(), supervise(), wait_for()

### Community 41 - "probe_frame.py"
Cohesion: 0.08
Nodes (22): Task 2: `vo_probe.py` — CLI over recorded or live walks, _box_bounds(), _box_iou(), Calibration, guess_calibration(), load_calibration(), load_depth_session(), load_labels() (+14 more)

### Community 42 - "Any"
Cohesion: 0.28
Nodes (8): Affine, detect(), detect_yolo_ort(), find_fingertip(), letterbox(), predict_depth(), tensor_scalar(), process()

### Community 43 - "voiced speech process (RR 18, cores 1-3)"
Cohesion: 0.19
Nodes (28): jalloc(), jarr_at(), jarray(), jis(), jnew(), jnum(), jnumber(), jobj_get() (+20 more)

### Community 44 - "Merge verdict: BLOCK"
Cohesion: 0.18
Nodes (4): crop_depth_padding(), _draw_boxes(), render_preview(), RenderPreviewTest

### Community 45 - "Clip caption table (enum beacon_clip order)"
Cohesion: 0.12
Nodes (12): Anchor, blend_pose(), build_crumbs(), component_median(), first_frame_id(), main(), median(), merge() (+4 more)

### Community 46 - "supervisor (spawn, runmasks, heartbeats, restarts)"
Cohesion: 0.14
Nodes (13): Aural and Haptic Feedback for Visually Impaired People on a Track (ICHI), 12-person BLV hand-steering study, GPIO piezo (cannot-fail actuator), USB headset audio (off-thread playback), No PCM Playback Device on QNX Image (io-snd control only, no 3.5 mm), post_startup.sh Boot Persistence (on -d -p 10, after io-snd), BTstack A2DP Bridge to JBL Go 3 (Combadge-HTN/qnx-bluetooth), supervisor/bt_audio_service.sh Supervisor-managed BT Child (+5 more)

### Community 49 - "audio_out.c"
Cohesion: 0.09
Nodes (22): 1.1 What laptop work has achieved (all true, all on the wrong machine), 1.2 Gap table against the prize hard requirements, 1.3 QNX-mechanism stubs (the pitch vs the code), 1.4 The real-time claim needs re-scoping, 1.5 Cuts already made or to be made now, 1.6 Small risks that will burn an hour at the worst moment, 1. Findings, 2. Plan (+14 more)

### Community 50 - "SlotTracker"
Cohesion: 0.23
Nodes (3): _SlotState, SlotTracker, SlotTrackerTest

### Community 51 - "world_in.c"
Cohesion: 0.21
Nodes (3): main(), UdpEmitTest, fake_emit_lines()

### Community 52 - "Weekend build order (geometry order)"
Cohesion: 0.13
Nodes (15): Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Embedding Pose Graph, Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764) (+7 more)

### Community 53 - "ProbeResources"
Cohesion: 0.11
Nodes (17): Accuracy ruling (Nathan, 2026-11-21, after the 360-degree clip demo), Anti-goals (what would make this a failure even if it works), Approaches considered (team decision 2026-11-21), Constraints (measured facts, not targets), Failure semantics (unchanged from §8, restated as contract), Goals, Intent, Non-goals (+9 more)

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
Cohesion: 0.23
Nodes (6): format_readout(), _ns(), _number(), ReadoutTest, _timing(), _vec3()

### Community 59 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.16
Nodes (12): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), procmgr_ability priority ability and root drop, QNX prize research (QNX-research.md) (+4 more)

### Community 60 - "Beacon Accessibility Research"
Cohesion: 0.09
Nodes (9): build_parser(), gate_by_depth(), lift_hand(), main(), _open_sock(), load_target_names(), _output(), parse_udp_target() (+1 more)

### Community 61 - "bt_audio_service.sh"
Cohesion: 0.60
Nodes (4): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), graph-not-needed PR label, CLAUDE.md (imports AGENTS.md)

### Community 62 - "run-radio-auto.sh"
Cohesion: 0.15
Nodes (4): build_parser(), emit_lines(), fake_probe_once(), fake_probe_once()

### Community 66 - "pi_live.sh"
Cohesion: 0.26
Nodes (10): audio_out_close(), audio_out_open(), audio_out_paced(), audio_out_write(), fifo_try_open(), fifo_write(), put16(), put32() (+2 more)

### Community 69 - "beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)"
Cohesion: 0.17
Nodes (9): Global Constraints, Review Focus, Self-review, Task 1: `vo_core.py` — the geometry core with synthetic tests, Task 3: Record a real L-walk and tune, Task 4: On-device OpenCV gate — the A/B decision (spec F1), Task 5: `vo.hpp` / `vo.cpp` — the C++ port, VO Integration Implementation Plan (+1 more)

### Community 74 - "test_frame_id_seed.py"
Cohesion: 0.23
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 75 - "beacon_cmd.c"
Cohesion: 0.27
Nodes (9): open_world(), beacon_world_t, add(), handle(), is_skip(), kind_name(), main(), send_intent() (+1 more)

### Community 76 - "Inclusive Language and Non-Cure Framing"
Cohesion: 0.31
Nodes (4): find_eoi(), now_ns(), on_data(), write_atomic()

### Community 77 - "make-dev-reach.test.js"
Cohesion: 0.11
Nodes (17): Clip caption table (enum beacon_clip order), captionFromClips(), CLIP_NAMES, CLIPS, clock(), Events(), eventsFromLog(), texts() (+9 more)

### Community 78 - "beacon_pulse"
Cohesion: 0.25
Nodes (8): beacon_pulse, BEACON_PULSE_AUDIO_UNDERRUN, BEACON_PULSE_HB_CAMD, BEACON_PULSE_HB_GUIDED, BEACON_PULSE_HB_PERCEPT, BEACON_PULSE_HB_VOICED, BEACON_PULSE_INTENT_EDGE, BEACON_PULSE_SUP_TICK

### Community 80 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.21
Nodes (11): QNX CamAPI Adapter (not wired yet), intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Beacon (chest-worn item-homing wearable), beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes) (+3 more)

### Community 81 - "ingest"
Cohesion: 0.33
Nodes (5): Build / test, ingest, Known limits (deliberate), Usage, What it writes (and never writes)

### Community 82 - "device_live_demo.sh"
Cohesion: 0.40
Nodes (5): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_live_demo.sh script, slay_matching()

### Community 83 - "device_slay_beat.sh"
Cohesion: 0.40
Nodes (5): kill_matching(), LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_slay_beat.sh script

### Community 84 - "device_chain_demo.sh"
Cohesion: 0.40
Nodes (4): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_chain_demo.sh script

### Community 85 - "qnx_pkg_fetch.py"
Cohesion: 0.25
Nodes (4): dep_names(), main(), parse_index(), version_gt()

### Community 86 - "Working notes (not shipped)"
Cohesion: 0.40
Nodes (4): Regenerating a review diff, Review verdicts, Where things are, Working notes (not shipped)

### Community 87 - "ai-import-test.sh"
Cohesion: 0.50
Nodes (3): LD_LIBRARY_PATH, PYTHONPATH, ai-import-test.sh script

### Community 88 - "Depth Anything V2 Metric Indoor Small ONNX"
Cohesion: 0.20
Nodes (8): pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, Per-instance Depth Slot Median Stabiliser, Box IoU Slot Association (--slot-iou 0.30), tape_check.py Absolute-depth Gate, Visual Odometry (VO)

### Community 89 - "gen_ort_capi_table.py"
Cohesion: 0.33
Nodes (5): clean(), ctype_of(), expand(), main(), split_args()

### Community 90 - "camd (camera daemon)"
Cohesion: 0.22
Nodes (10): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0), /beacon_depth Shared Memory (+2 more)

### Community 91 - "telemd (read-only telemetry to the laptop)"
Cohesion: 0.25
Nodes (7): deadline-test (over_period vs over_1ms), Even seq.* Values (telemd skips torn reads), sim-reach-lost.jsonl Simulator Demo Replay, Optional Video JPEG (~5 fps, <60 KB per datagram), --jpeg Raw UDP Preview Datagram, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), telemd (read-only telemetry to the laptop)

### Community 92 - "probe_to_world.py World JSONL / UDP Emitter"
Cohesion: 0.25
Nodes (8): xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), dev-reach.jsonl (made by make-dev-reach.js), world.sample.json, World-state JSON Message (~10 Hz), calib.json Camera Intrinsics (laptop-local, gitignored), calibrate_camera.py Chessboard Calibration, --fov Pinhole Guess (66 deg), probe_to_world.py World JSONL / UDP Emitter

## Knowledge Gaps
- **173 isolated node(s):** `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK`, `GUIDED_CMD_TONE_ON`, `GUIDED_CMD_TONE_OFF` (+168 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 573 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clip caption table (enum beacon_clip order)` connect `make-dev-reach.test.js` to `beacon.h`?**
  _High betweenness centrality (0.388) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK` to the rest of the system?**
  _173 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.10367762128325508 - nodes in this community are weakly interconnected._
- **Why does `Beacon: Nathan's revision (spec)` connect `Beacon: Nathan's revision (spec)` to `YOLOE-26n-seg (text-prompted, baked static ONNX)`, `probe_frame.py`, `percept vision process (RR 22, cores 1-3)`, `YOLOE-26n-seg (text-prompted, baked static ONNX)`, `Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)`, `test_frame_id_seed.py`, `telemd.c`, `FakeLandmarker`, `guided synthesizer (FIFO 58, core 0)`, `Weekend build order (geometry order)`, `guided (60 Hz guidance synthesizer)`?**
  _High betweenness centrality (0.190) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `guided_step` be split into smaller, more focused modules?**
  _Cohesion score 0.03333333333333333 - nodes in this community are weakly interconnected._