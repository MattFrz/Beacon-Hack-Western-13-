# Graph Report - Beacon-Hack-Western-13-  (2026-11-22)

## Corpus Check
- 127 files · ~132,110 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 11, .jsonl 3, .css 1)

## Summary
- 1873 nodes · 4109 edges · 93 communities (79 shown, 14 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 332 edges (avg confidence: 0.87)
- Token cost: 831,404 input · 0 output

## Graph Freshness
- Built from commit: `2429b7c9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- probe_to_world
- guided_step
- beacon_clip
- probe_once
- bridge.test.js
- Beacon Accessibility Research
- with
- head.cpp
- stdio
- calibrate_camera.py
- dashboard/package.json
- audio.c
- App.jsx
- tempfile
- guided (60 Hz cue synthesizer)
- ingest/src/main.c
- Scene.jsx
- preview.c
- time
- dashboard (Vite + React + three.js remote monitor)
- argparse
- probe_frame_test.py
- percept (perception process)
- DepthStabiliser
- TapeCheckTest
- ort_capi.py
- percept vision process (RR 22, cores 1-3)
- bt_speaker.py
- string
- beacon_intent_kind
- camd/src/main.c
- audio_out.c
- Saturday Build Order (spec section 13, steps 1-6)
- Tape-measure depth gate (>30% error mutes metres)
- Laptop-first World-dot Pipeline (probe_frame -> probe_to_world -> bridge -> dashboard)
- test_frame_id_seed.py
- probe_frame.py
- Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)
- math
- vo_core.py
- beacon.h
- vo_probe.py
- telemd.c
- ingest/src/main.c
- render_preview
- qnx_pkg_fetch.py
- supervisor (spawn, runmasks, heartbeats, restarts)
- icons.jsx
- Merge verdict: BLOCK
- 2. Plan
- SlotTracker
- probe_frame.py
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- Visual odometry integration design
- world_in.c
- gen_ort_capi_table.py
- guided_cmd_kind
- encode_preview
- telemd (read-only telemetry sender)
- Beacon: Nathan's revision (spec)
- time
- AGENTS.md: Beacon notes for coding agents
- beacon_pulse
- FakeLandmarker
- FakeCapture
- FakeFileCapture
- deadline_test.c
- bt_audio_service.sh
- run-radio-auto.sh
- Dashboard redesign and live Pi connection
- AirTag Precision Finding
- irl_test.sh
- pi_live.sh
- ProbeResources
- beacon_cmd.c
- beacon_grab.c
- Mode banner (LIVE / HOLD / LOST)
- FakeInferenceSession
- Tip
- Beacon (chest-worn item-homing wearable)
- ingest
- device_live_demo.sh
- device_slay_beat.sh
- device_chain_demo.sh
- beacon_law
- Working notes (not shipped)
- ai-import-test.sh
- Depth Anything V2 Metric Indoor Small ONNX
- Clip caption table (enum beacon_clip order)
- camd (camera daemon)
- scripts
- calib.json Camera Intrinsics (laptop-local, gitignored)

## God Nodes (most connected - your core abstractions)
1. `beacon_clip` - 60 edges
2. `probe_to_world()` - 47 edges
3. `guided_step()` - 43 edges
4. `probe_once()` - 38 edges
5. `make_probe()` - 37 edges
6. `ProbeRuntimeTest` - 34 edges
7. `ProbeToWorldTest` - 33 edges
8. `App()` - 29 edges
9. `prepare()` - 27 edges
10. `Beacon: Nathan's revision (spec)` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Where it lives` --references--> `Vo`  [INFERRED]
  docs/superpowers/specs/2026-11-21-vo-integration-design.md → percept/tools/vo_core.py
- `What changed` --references--> `targetObjectId()`  [INFERRED]
  docs/dashboard-redesign.md → laptop/dashboard/src/worldScene.js
- `Processes Panel (heartbeat age, down at >=1 s)` --semantically_similar_to--> `NO DATA after 1 s without world state`  [INFERRED] [semantically similar]
  telemd/README.md → laptop/dashboard/README.md
- `Task 6: Integration into the percept cycle and the measured gates` --references--> `Vo`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/vo_core.py
- `Self-review` --references--> `VoConfig`  [INFERRED]
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

## Communities (93 total, 14 thin omitted)

### Community 0 - "probe_to_world"
Cohesion: 0.05
Nodes (23): build_parser(), emit_lines(), format_readout(), load_target_names(), main(), _ns(), _number(), _output() (+15 more)

### Community 1 - "guided_step"
Cohesion: 0.10
Nodes (70): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+62 more)

### Community 2 - "beacon_clip"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "probe_once"
Cohesion: 0.09
Nodes (7): prepare(), ProbeRuntimeTest, fake_detect(), fake_predict_depth(), fake_encode(), synthetic_probe_modules(), synthetic_video_modules()

### Community 4 - "bridge.test.js"
Cohesion: 0.06
Nodes (40): adapterFor(), gapMs(), isV4(), laptopAddresses(), loadReplay(), parseWorld(), startBridge(), collect() (+32 more)

### Community 5 - "Beacon Accessibility Research"
Cohesion: 0.06
Nodes (27): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), CHI 2025: BLV Object-Recognition Technologies in India, Auditory Hand-Steering Guidance for BLV People (CHI 2026), CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021) (+19 more)

### Community 6 - "with"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 7 - "head.cpp"
Cohesion: 0.07
Nodes (26): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+18 more)

### Community 8 - "stdio"
Cohesion: 0.12
Nodes (8): main(), put_u16(), put_u32(), write_bmp(), main(), open_world(), sleep_until(), beacon_frame_slot_t

### Community 9 - "calibrate_camera.py"
Cohesion: 0.10
Nodes (11): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, synthetic_view() (+3 more)

### Community 10 - "dashboard/package.json"
Cohesion: 0.08
Nodes (31): Beacon dashboard index.html, dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, @fontsource/ibm-plex-mono@^5.3.0, @fontsource/ibm-plex-sans@^5.3.0, motion@^14.14.0, react@^19.3.1 (+23 more)

### Community 11 - "audio.c"
Cohesion: 0.16
Nodes (19): audio_dropped_speech(), audio_main(), audio_start(), audio_stop(), law_name(), mode_name(), pan_gains(), print_say() (+11 more)

### Community 12 - "App.jsx"
Cohesion: 0.11
Nodes (38): dashboard README, Ago(), agoText(), App(), BOTH, Camera(), Caption(), DataSource() (+30 more)

### Community 13 - "tempfile"
Cohesion: 0.19
Nodes (7): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips()

### Community 14 - "guided (60 Hz cue synthesizer)"
Cohesion: 0.16
Nodes (19): Build on QNX (make; test_law 56 passed), Hear it on the JBL (Bluetooth PCM FIFO), Testing guided on the Pi (fakeworld test plan), Run without sound (fakeworld lost, 0 missed deadlines), --audio outputs (none, out.wav, fifo:PATH, qnx), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon_mode() LIVE/HOLD/LOST Tracking Mode, guided (60 Hz cue synthesizer) (+11 more)

### Community 15 - "ingest/src/main.c"
Cohesion: 0.29
Nodes (10): beacon_world_t, apply_sched(), attach_block(), main(), open_world(), parse_intent(), usage(), write_intent() (+2 more)

### Community 16 - "Scene.jsx"
Cohesion: 0.23
Nodes (22): World-frame dot map, COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene() (+14 more)

### Community 17 - "preview.c"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 18 - "time"
Cohesion: 0.15
Nodes (8): free_udp_port(), hand_at(), main(), record(), wait_for_exit(), main(), supervise(), wait_for()

### Community 19 - "dashboard (Vite + React + three.js remote monitor)"
Cohesion: 0.16
Nodes (15): bridge README, bridge (Node UDP-to-WebSocket relay and recorder), dev-reach.jsonl sample (walk, reach, slay percept -> HOLD -> LOST), Optional live JPEG video frames, Live status line every 5 s (world, video, dropped, dashboards), Bridge replay mode (paced by t_ns), Session recording to recordings/<UTC>.jsonl, telemd (Pi telemetry sender) (+7 more)

### Community 20 - "argparse"
Cohesion: 0.21
Nodes (4): main(), __init__(), main(), read_labels()

### Community 22 - "percept (perception process)"
Cohesion: 0.16
Nodes (13): Depth Anything V2 Metric Indoor Small INT8, models/labels.txt runtime vocabulary, onnxruntime 1.24.4 (QNX), YOLOE-26n baked detect-only ONNX detector, Depth Anything V2 Static ONNX Export (210x210 metric), MediaPipe hand_landmarker.task Probe, percept/tools/probe_frame.py Laptop Probe, QNX Inference Runtime Packages (still missing) (+5 more)

### Community 23 - "DepthStabiliser"
Cohesion: 0.22
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 24 - "TapeCheckTest"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 25 - "ort_capi.py"
Cohesion: 0.08
Nodes (11): api(), _check(), _find_library(), _OrtApiBase, OrtError, _read_ptr(), Session, TensorInfo (+3 more)

### Community 26 - "percept vision process (RR 22, cores 1-3)"
Cohesion: 0.19
Nodes (18): /beacon_depth depth slot (shm), /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, hand (percept-owned fingertip slot), MediaPipe hands (palm + landmark lite), objects[32] session POI store, OpenCV 4.12 (features2d + calib3d), percept vision process (RR 22, cores 1-3) (+10 more)

### Community 27 - "bt_speaker.py"
Cohesion: 0.16
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 28 - "string"
Cohesion: 0.36
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 29 - "beacon_intent_kind"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

### Community 30 - "camd/src/main.c"
Cohesion: 0.25
Nodes (12): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+4 more)

### Community 31 - "audio_out.c"
Cohesion: 0.26
Nodes (10): audio_out_close(), audio_out_open(), audio_out_paced(), audio_out_write(), fifo_try_open(), fifo_write(), put16(), put32() (+2 more)

### Community 32 - "Saturday Build Order (spec section 13, steps 1-6)"
Cohesion: 0.17
Nodes (15): Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), 30-second Sunday demo script, slay percept -> HOLD -> LOST failure demo, telemd optional monitoring process, Crumb Trail Dots (crumbs[].xyz_world), Dashboard World-dot View (Scene.jsx, App.jsx), Wearer Dot at pose.T_world_from_cam Translation, bridge (UDP-to-WebSocket laptop relay) (+7 more)

### Community 33 - "Tape-measure depth gate (>30% error mutes metres)"
Cohesion: 0.11
Nodes (20): Beacon spec adversarial review, First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Busy-loop core 0 deadline test, Error handling / failure-mode table, 16.67 ms CLOCK_MONOTONIC guidance loop, Loaner bring-up checklist (QNX image), QNX AI Camera App (+12 more)

### Community 34 - "Laptop-first World-dot Pipeline (probe_frame -> probe_to_world -> bridge -> dashboard)"
Cohesion: 0.11
Nodes (19): /beacon_frames newest-frame ring (shm), camd camera daemon (FIFO 50, core 0), C270 JPEG-only Capture via mjpeg_example (err 25 on uncompressed), camd --bmp Bring-up Frame Source (frametype 65535), QNX /beacon_frames shm Round-trip (camd --bmp -> read-frames -> dump-frame), World-frame 3D Dots Plan, percept/tools/probe_to_world.py World JSONL Wrapper, include/beacon.h Shared Header (+11 more)

### Community 35 - "test_frame_id_seed.py"
Cohesion: 0.29
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 36 - "probe_frame.py"
Cohesion: 0.12
Nodes (11): Affine, _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), letterbox() (+3 more)

### Community 37 - "Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)"
Cohesion: 0.14
Nodes (14): qnxpi Device (QNX 8.0, Raspberry Pi 5, 4x Cortex-A76, 8 GB), Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Network Diagnostics Ladder, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay) (+6 more)

### Community 38 - "math"
Cohesion: 0.07
Nodes (27): Anchor, blend_pose(), build_crumbs(), component_median(), first_frame_id(), main(), median(), merge() (+19 more)

### Community 39 - "vo_core.py"
Cohesion: 0.05
Nodes (33): Global Constraints, Review Focus, Self-review, Task 1: `vo_core.py` — the geometry core with synthetic tests, Task 3: Record a real L-walk and tune, Task 4: On-device OpenCV gate — the A/B decision (spec F1), Task 5: `vo.hpp` / `vo.cpp` — the C++ port, Task 6: Integration into the percept cycle and the measured gates (+25 more)

### Community 40 - "beacon.h"
Cohesion: 0.11
Nodes (28): audio_publish_stats(), audio_submit(), test_seq_writer_restart(), drop_crumb(), lerp(), main(), publish_percept(), put_hand() (+20 more)

### Community 41 - "vo_probe.py"
Cohesion: 0.11
Nodes (14): Task 2: `vo_probe.py` — CLI over recorded or live walks, guess_calibration(), load_depth_session(), make_affine(), parse_csv3(), predict_depth(), resolve_calibration(), GuessCalibrationTest (+6 more)

### Community 42 - "telemd.c"
Cohesion: 0.38
Nodes (7): append(), append_scene(), escape_name(), heartbeat_alive(), main(), snapshot(), vector_json()

### Community 43 - "ingest/src/main.c"
Cohesion: 0.30
Nodes (21): jalloc(), jarr_at(), jarray(), jis(), jnew(), jnum(), jnumber(), jobj_get() (+13 more)

### Community 44 - "render_preview"
Cohesion: 0.18
Nodes (4): crop_depth_padding(), _draw_boxes(), render_preview(), RenderPreviewTest

### Community 45 - "qnx_pkg_fetch.py"
Cohesion: 0.25
Nodes (4): dep_names(), main(), parse_index(), version_gt()

### Community 46 - "supervisor (spawn, runmasks, heartbeats, restarts)"
Cohesion: 0.10
Nodes (23): 12-person BLV hand-steering study, GPIO piezo (cannot-fail actuator), guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, intent (voiced-owned job + candidate names), llama.cpp ~0.5B remap (table miss only), REACH guidance law (ticks only), REPEAT and REJECT commands (+15 more)

### Community 47 - "icons.jsx"
Cohesion: 0.29
Nodes (12): animate-ui primitives (Highlight, RollingText, SlidingNumber, Slider, Button), ChevronLeft(), ChevronRight(), Collapse(), Expand(), Icon(), Panel(), PanelLeftClose() (+4 more)

### Community 49 - "2. Plan"
Cohesion: 0.09
Nodes (22): 1.1 What laptop work has achieved (all true, all on the wrong machine), 1.2 Gap table against the prize hard requirements, 1.3 QNX-mechanism stubs (the pitch vs the code), 1.4 The real-time claim needs re-scoping, 1.5 Cuts already made or to be made now, 1.6 Small risks that will burn an hour at the worst moment, 1. Findings, 2. Plan (+14 more)

### Community 50 - "SlotTracker"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 51 - "probe_frame.py"
Cohesion: 0.13
Nodes (14): build_parser(), Calibration, find_fingertip(), load_calibration(), load_labels(), load_yolo(), load_yolo_session(), main() (+6 more)

### Community 52 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.13
Nodes (15): Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, Embedding Pose Graph, Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764) (+7 more)

### Community 53 - "Visual odometry integration design"
Cohesion: 0.11
Nodes (17): Accuracy ruling (Nathan, 2026-11-21, after the 360-degree clip demo), Anti-goals (what would make this a failure even if it works), Approaches considered (team decision 2026-11-21), Constraints (measured facts, not targets), Failure semantics (unchanged from §8, restated as contract), Goals, Intent, Non-goals (+9 more)

### Community 54 - "world_in.c"
Cohesion: 0.33
Nodes (11): apply(), find_key(), get_id(), get_num(), get_str(), get_vecn(), main(), publish() (+3 more)

### Community 55 - "gen_ort_capi_table.py"
Cohesion: 0.33
Nodes (5): clean(), ctype_of(), expand(), main(), split_args()

### Community 56 - "guided_cmd_kind"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 58 - "telemd (read-only telemetry sender)"
Cohesion: 0.14
Nodes (16): beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), /beacon_world Shared Memory, fakeworld (scripted percept/voiced stand-in), Kokoro-82M voice clips (llama-tts WAV, sounds/make_clips.py), Simulator Scenarios (reach, lost, walk, turn, unseen, stop, return, reject), Seqlock Shared-memory Reads (seq_percept / seq_voiced / seq_guided), run_scenario.sh script, Heartbeat Fault Detection and Restart with Backoff (+8 more)

### Community 59 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.16
Nodes (12): Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), Neighbour design notes (hackwestern13 beacon-design.md), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), procmgr_ability priority ability and root drop, QNX AI workshop (MediaPipe hands on Pi) (+4 more)

### Community 60 - "time"
Cohesion: 0.17
Nodes (5): build_parser(), gate_by_depth(), lift_hand(), main(), _open_sock()

### Community 61 - "AGENTS.md: Beacon notes for coding agents"
Cohesion: 0.60
Nodes (4): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), graph-not-needed PR label, CLAUDE.md (imports AGENTS.md)

### Community 62 - "beacon_pulse"
Cohesion: 0.25
Nodes (8): beacon_pulse, BEACON_PULSE_AUDIO_UNDERRUN, BEACON_PULSE_HB_CAMD, BEACON_PULSE_HB_GUIDED, BEACON_PULSE_HB_PERCEPT, BEACON_PULSE_HB_VOICED, BEACON_PULSE_INTENT_EDGE, BEACON_PULSE_SUP_TICK

### Community 66 - "deadline_test.c"
Cohesion: 0.31
Nodes (5): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns()

### Community 69 - "Dashboard redesign and live Pi connection"
Cohesion: 0.25
Nodes (7): Dashboard redesign and live Pi connection, Graph, Live Raspberry Pi connection, Running it against the Pi, Still open, What actually ran on the Pi, What changed

### Community 75 - "beacon_cmd.c"
Cohesion: 0.36
Nodes (7): add(), handle(), is_skip(), kind_name(), main(), send_intent(), world_open()

### Community 76 - "beacon_grab.c"
Cohesion: 0.20
Nodes (4): find_eoi(), now_ns(), on_data(), write_atomic()

### Community 77 - "Mode banner (LIVE / HOLD / LOST)"
Cohesion: 0.33
Nodes (4): Mode banner (LIVE / HOLD / LOST), dev-reach.jsonl (made by make-dev-reach.js), world.sample.json, World-state JSON Message (~10 Hz)

### Community 79 - "Tip"
Cohesion: 0.48
Nodes (5): SourceSwitch(), Sidebar(), SyncMobile(), Tip(), @animate-ui/react

### Community 80 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.13
Nodes (20): QNX CamAPI Adapter (not wired yet), intent.kind Values (FIND, GO, RETURN, STOP, REPEAT, REJECT, NACK_*), CLOCK_MONOTONIC t_ns Timestamps, Per-session JSONL World-state Recording, Telemetry Format (DRAFT), UDP Port 5005 Telemetry Transport, Optional Video JPEG (~5 fps, <60 KB per datagram), Baked YOLOE Label Vocabulary (64 nouns) (+12 more)

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

### Community 85 - "beacon_law"
Cohesion: 0.29
Nodes (7): beacon_law, BEACON_LAW_LOST, BEACON_LAW_NONE, BEACON_LAW_REACH, BEACON_LAW_RETURN, BEACON_LAW_STOP, BEACON_LAW_WALK

### Community 86 - "Working notes (not shipped)"
Cohesion: 0.40
Nodes (4): Regenerating a review diff, Review verdicts, Where things are, Working notes (not shipped)

### Community 87 - "ai-import-test.sh"
Cohesion: 0.50
Nodes (3): LD_LIBRARY_PATH, PYTHONPATH, ai-import-test.sh script

### Community 88 - "Depth Anything V2 Metric Indoor Small ONNX"
Cohesion: 0.14
Nodes (14): crumbs Breadcrumb Positions, pose.T_world_from_cam (4x4 row-major, from percept VO), xyz_world Session Frame (valid only with matching pose_epoch), Depth Anything V2 Metric Indoor Small ONNX, export_depth.py Depth Export, export_yoloe.py Detector Export, MediaPipe Hand Models, yoloe26n_320.onnx (baked prompts, detect-only) (+6 more)

### Community 89 - "Clip caption table (enum beacon_clip order)"
Cohesion: 0.33
Nodes (6): deadline-test (over_period vs over_1ms), Clip caption table (enum beacon_clip order), law / cue / d_m Fields (STOP, LOST, REACH, WALK, RETURN, NONE), sim-reach-lost.jsonl Simulator Demo Replay, guided (60 Hz synthesizer: mode, bind, laws, audio, piezo), cue Object (tick rate, stereo pan, clip_ids)

### Community 90 - "camd (camera daemon)"
Cohesion: 0.20
Nodes (11): /beacon_frames Newest-wins Three-slot Ring, BMP Bring-up Frame Source (frametype 65535), camd (camera daemon), dump-frame BMP Round-trip Writer, Frame-ID Seeding Test (make test-frame-id-seed), read-frames Ring Checker, Synthetic Stub Frame Source (frametype 0), Even seq.* Values (telemd skips torn reads) (+3 more)

### Community 91 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, test

### Community 92 - "calib.json Camera Intrinsics (laptop-local, gitignored)"
Cohesion: 0.50
Nodes (4): xyz_cam OpenCV Camera Frame (+X right, +Y down, +Z forward), calib.json Camera Intrinsics (laptop-local, gitignored), calibrate_camera.py Chessboard Calibration, --fov Pinhole Guess (66 deg)

## Knowledge Gaps
- **173 isolated node(s):** `LD_LIBRARY_PATH`, `PYTHONPATH`, `ORT_LIB`, `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE` (+168 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 589 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clip caption table (enum beacon_clip order)` connect `Clip caption table (enum beacon_clip order)` to `beacon.h`, `App.jsx`?**
  _High betweenness centrality (0.399) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `LD_LIBRARY_PATH`, `PYTHONPATH`, `ORT_LIB` to the rest of the system?**
  _173 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `probe_to_world` be split into smaller, more focused modules?**
  _Cohesion score 0.05491268672417421 - nodes in this community are weakly interconnected._
- **Why does `Beacon: Nathan's revision (spec)` connect `Beacon: Nathan's revision (spec)` to `Tape-measure depth gate (>30% error mutes metres)`, `Beacon Accessibility Research`, `Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)`, `App.jsx`, `supervisor (spawn, runmasks, heartbeats, restarts)`, `guided (60 Hz cue synthesizer)`, `Merge verdict: BLOCK`, `dashboard (Vite + React + three.js remote monitor)`, `YOLOE-26n-seg (text-prompted, baked static ONNX)`, `telemd (read-only telemetry sender)`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `guided_step` be split into smaller, more focused modules?**
  _Cohesion score 0.10159817351598173 - nodes in this community are weakly interconnected._