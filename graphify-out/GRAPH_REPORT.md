# Graph Report - Beacon-Hack-Western-13-  (2026-11-21)

## Corpus Check
- Corpus is ~46,975 words - fits in a single context window. You may not need a graph.

## Summary
- 643 nodes · 1180 edges · 34 communities (31 shown, 3 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 113 edges (avg confidence: 0.85)
- Token cost: 338,816 input · 0 output

## Community Hubs (Navigation)
- System Overview (READMEs)
- Guided Law Engine
- Dashboard UI and Deps
- Bridge and Caption Clips
- Voice Clip Enum
- CI Workflow
- Guided Audio and CLI
- Python Tools and Tests
- Accessibility Research Papers
- Pi Dev Workflow
- Shared-Memory Structs
- Open-Vocab Model Choices
- Guidance Laws and Pulses
- Spec Documents Lineage
- Camera and Bring-Up Gates
- Spec Review Verdict
- Geometry and Reach Audio
- WorldState Shared Memory
- Guided Synthesizer and QNX IPC
- Navigation Research and Build Order
- Team Owners and Laptop Tools
- Audio Guidance Design
- telemd Sender
- Intent Kinds
- Perception Pipeline Budget
- fakeworld Simulator
- Shared-Memory Openers
- Speech Query and POI Store
- Vision Model Stack
- JPEG Encoder Callbacks
- Mode Enum
- No-Tag Homing

## God Nodes (most connected - your core abstractions)
1. `guided_step()` - 32 edges
2. `beacon_clip` - 31 edges
3. `main()` - 20 edges
4. `Beacon: Nathan's revision (spec)` - 15 edges
5. `Beacon (chest-worn item-homing wearable)` - 15 edges
6. `guided_state_t` - 14 edges
7. `reset()` - 14 edges
8. `main()` - 14 edges
9. `telemd (read-only telemetry sender)` - 14 edges
10. `guided_out_t` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Newest-wins Dashboard Backpressure (skip clients >1 MB behind)` --semantically_similar_to--> `/beacon_frames Newest-wins Three-slot Ring`  [INFERRED] [semantically similar]
  laptop/bridge/README.md → camd/README.md
- `Processes Panel (heartbeat age, down at >=1 s)` --semantically_similar_to--> `NO DATA Staleness Indicator (1 s)`  [INFERRED] [semantically similar]
  telemd/README.md → laptop/dashboard/README.md
- `Heartbeat Fault Detection and Restart with Backoff` --semantically_similar_to--> `Processes Panel (heartbeat age, down at >=1 s)`  [INFERRED] [semantically similar]
  supervisor/README.md → telemd/README.md
- `secs()` --calls--> `beacon_now_ns()`  [INFERRED]
  guided/src/audio.c → include/beacon.h
- `audio_main()` --calls--> `beacon_seq_read()`  [INFERRED]
  guided/src/audio.c → include/beacon.h

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Five QNX processes of the isolation contract** — docs_nathans_revision_supervisor, docs_nathans_revision_camd, docs_nathans_revision_guided, docs_nathans_revision_percept, docs_nathans_revision_voiced [EXTRACTED 1.00]
- **Seqlocked shared-memory regions** — docs_nathans_revision_beacon_frames, docs_nathans_revision_beacon_depth, docs_nathans_revision_beacon_world, docs_nathans_revision_seqlock [EXTRACTED 1.00]
- **Kill-percept HOLD/LOST failure path** — docs_nathans_revision_slay_percept_demo, docs_nathans_revision_mode_live_hold_lost, docs_nathans_revision_supervisor, docs_nathans_revision_guided, docs_nathans_revision_gpio_piezo [EXTRACTED 1.00]
- **Beacon On-Pi Process Set Spawned by supervisor** — docs_team_plan_supervisor, docs_team_plan_camd, docs_team_plan_percept, docs_team_plan_guided, docs_team_plan_voiced, docs_team_plan_telemd [EXTRACTED 1.00]
- **Laptop Telemetry and Replay Path** — docs_team_plan_telemd, docs_team_plan_bridge, docs_team_plan_dashboard, docs_team_plan_replay_generator [EXTRACTED 1.00]
- **Evidence-Backed Audio UX for a Chest-Worn Homing Device** — docs_beacon_accessibility_research_walk_speech_reach_ticks, docs_beacon_accessibility_research_tick_rate_distance_encoding, docs_beacon_accessibility_research_off_axis_search_cue, docs_beacon_accessibility_research_honest_lost_cue, docs_beacon_accessibility_research_open_ear_audio, docs_beacon_accessibility_research_parsimonious_instructions [EXTRACTED 1.00]
- **Beacon On-device QNX Processes** — supervisor_readme_supervisor, camd_readme_camd, guided_readme_guided, percept_readme_percept, voiced_readme_voiced, telemd_readme_telemd [EXTRACTED 1.00]
- **Telemetry Monitoring Pipeline (telemd -> bridge -> dashboard)** — telemd_readme_telemd, laptop_bridge_readme_bridge, laptop_dashboard_readme_dashboard, laptop_samples_readme_telemetry_format [EXTRACTED 1.00]
- **Newest-wins Buffering Pattern** — camd_readme_beacon_frames_ring, laptop_bridge_readme_newest_wins_backpressure, guided_readme_audio_thread [INFERRED 0.75]

## Communities (34 total, 3 thin omitted)

### Community 0 - "System Overview (READMEs)"
Cohesion: 0.06
Nodes (57): /beacon_frames Newest-wins Three-slot Ring, camd (camera daemon), guided Audio Thread (speech ring + newest-wins tick/tone slot), beacon.h ADDITIONs (objects[].used, hand.valid, hand.pose_epoch, intent.utterance_id, target.bound, display/stats blocks), beacon_mode() LIVE/HOLD/LOST Tracking Mode, /beacon_world Shared Memory, fakeworld (scripted percept/voiced stand-in), guided (60 Hz cue synthesizer) (+49 more)

### Community 1 - "Guided Law Engine"
Cohesion: 0.10
Nodes (60): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_kind, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE (+52 more)

### Community 2 - "Dashboard UI and Deps"
Cohesion: 0.06
Nodes (48): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, motion@^14.14.0, react@^19.3.1, react-dom@^19.3.1, @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2 (+40 more)

### Community 3 - "Bridge and Caption Clips"
Cohesion: 0.07
Nodes (23): gapMs(), loadReplay(), parseWorld(), startBridge(), sampleFile, dependencies, ws@^8.23.0, name (+15 more)

### Community 4 - "Voice Clip Enum"
Cohesion: 0.06
Nodes (31): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+23 more)

### Community 5 - "CI Workflow"
Cohesion: 0.08
Nodes (27): concurrency, cancel-in-progress, group, jobs, laptop, native, name, runs-on (+19 more)

### Community 6 - "Guided Audio and CLI"
Cohesion: 0.13
Nodes (15): audio_dropped_speech(), audio_main(), audio_start(), audio_stop(), law_name(), mode_name(), print_say(), secs() (+7 more)

### Community 7 - "Python Tools and Tests"
Cohesion: 0.13
Nodes (5): main(), make_inflect(), to_clip(), supervise(), wait_for()

### Community 8 - "Accessibility Research Papers"
Cohesion: 0.12
Nodes (17): Beacon Accessibility Research, Visualization for the Blind: Parachute-Design Criticism (ACM Interactions), AI Proposes, High-Priority Thread Disposes, Misfitting With AI: How Blind People Verify and Contest AI Errors (ASSETS 2024), CHI 2025: BLV Object-Recognition Technologies in India, CNIB Inclusive Language Guidelines, Designing for Independence for People with Visual Impairments (CSCW 2021), Multi-Purpose Camera Apps (Seeing AI, Lookout, Be My Eyes, Envision) (+9 more)

### Community 9 - "Pi Dev Workflow"
Cohesion: 0.13
Nodes (14): Pi Development Workflow (QNX 8.0 on Raspberry Pi 5), Before-Demo Checklist, CRLF Line Endings Break onboot, Default qnxuser Password Risk, Network Diagnostics Ladder, Read-Only IFS Image (qnx_sdp.ifs), QNX Process Idioms (pidin, slay), QNXE-1894 Wi-Fi Settings Copy Bug (+6 more)

### Community 10 - "Shared-Memory Structs"
Cohesion: 0.14
Nodes (19): audio_publish_stats(), audio_submit(), test_seq_writer_restart(), say_intent(), beacon_crumb_t, beacon_depth_t, beacon_frame_slot_t, beacon_guided_block_t (+11 more)

### Community 12 - "Open-Vocab Model Choices"
Cohesion: 0.17
Nodes (11): Find My Things (Morrison et al., ASSETS 2023), Open-Vocabulary Models on Pi 5 Research, Ultralytics AGPL-3.0 Licence Risk, CLIP / MobileCLIP2 Region Retrieval, CLIP / MobileCLIP Pi 5 Timing Study (arXiv 2610.05764), ONNX Runtime 1.24.4 on QNX, Ultralytics YOLOE Docs, YOLO-World INT8 TFLite (+3 more)

### Community 13 - "Guidance Laws and Pulses"
Cohesion: 0.12
Nodes (15): beacon_law, BEACON_LAW_LOST, BEACON_LAW_NONE, BEACON_LAW_REACH, BEACON_LAW_RETURN, BEACON_LAW_STOP, BEACON_LAW_WALK, beacon_pulse (+7 more)

### Community 14 - "Spec Documents Lineage"
Cohesion: 0.18
Nodes (9): Beacon spec adversarial review, Beacon session-homing design draft (docs/superpowers/specs, 2026-11-21), Beacon: Nathan's revision (spec), Beacon accessibility research (docs/beacon-accessibility-research.md), Beacon (chest-worn named-object homing device), Henomaly (process split + ORT on Pi 5 QNX), Open-vocab Pi model brief (docs/beacon-open-vocab-pi-models.md), Team ops plan (docs/team-plan.md) (+1 more)

### Community 15 - "Camera and Bring-Up Gates"
Cohesion: 0.21
Nodes (11): First empirical gates (busy-loop, tape, YOLOE p95, MediaPipe hit rate, synonym table), Busy-loop core 0 deadline test, camd camera daemon (FIFO 50, core 0), CamAPI focus-lock step-2 gate, Ground-plane fallback (WALK distances only), Loaner bring-up checklist (QNX image), QNX AI Camera App, QNX Sensor Framework / CamAPI (Camera Module 3) (+3 more)

### Community 16 - "Spec Review Verdict"
Cohesion: 0.21
Nodes (5): AprilTag fob (rejected physical tag identity), 30-second Sunday demo script, Nov 20 Beacon build plan (superseded, removed), Range 2: object still in view (walk while looking, no VO), RETURN ('take me back') breadcrumb retrace

### Community 17 - "Geometry and Reach Audio"
Cohesion: 0.17
Nodes (8): Wearer-facing audio UX, 12-person BLV hand-steering study, Letterbox / crop inverse mapping, MediaPipe hands (palm + landmark lite), QNX AI workshop (MediaPipe hands on Pi), Range 1: same camera frame (tabletop reach, no VO), Pinhole unprojection to p_cam / p_world, USB headset audio (off-thread playback)

### Community 18 - "WorldState Shared Memory"
Cohesion: 0.27
Nodes (11): /beacon_depth depth slot (shm), /beacon_frames newest-frame ring (shm), /beacon_world WorldState (shm), crumbs[512] breadcrumb trail, objects[32] session POI store, OpenCV 4.12 (features2d + calib3d), percept vision process (RR 22, cores 1-3), pose_epoch (+3 more)

### Community 19 - "Guided Synthesizer and QNX IPC"
Cohesion: 0.19
Nodes (11): GPIO piezo (cannot-fail actuator), 16.67 ms CLOCK_MONOTONIC guidance loop, guided synthesizer (FIFO 58, core 0), Heartbeat pulses and supervisor 50 ms timer, intent (voiced-owned job + candidate names), procmgr_ability priority ability and root drop, REPEAT and REJECT commands, supervisor process (FIFO 63, core 0) (+3 more)

### Community 20 - "Navigation Research and Build Order"
Cohesion: 0.17
Nodes (9): Aural and Haptic Feedback for Visually Impaired People on a Track (ICHI), NavCog / NavCog3 (CMU), NavGraph Parsimonious Instructions, Less is More (VIA-Agent) PVI Study, Beacon Team Plan, Saturday Build Order (spec section 13, steps 1-6), Hardware Request (Camera Module 3, USB headset, piezo), Piezo Fault Path (cannot-fail actuator) (+1 more)

### Community 21 - "Team Owners and Laptop Tools"
Cohesion: 0.23
Nodes (10): Privacy Concerns with Be My Eyes / Aira (SOUPS 2019 poster), include/beacon.h Shared Header, bridge (UDP-to-WebSocket laptop relay), 3D Dashboard (Vite + React + three.js), Matt (supervisor, telemd and demo owner), Munadir (guidance and voice owner), Replay Generator (.jsonl samples), Seqlock Shared Memory (/beacon_world, /beacon_frames) (+2 more)

### Community 22 - "Audio Guidance Design"
Cohesion: 0.20
Nodes (6): Auditory Hand-Steering Guidance for BLV People (CHI 2026), HoldLight (BLV climbers), Evaluation of Short-Range Depth Sonifications (IEEE THMS), UI Preferences for a Camera-Based Wayfinding Aid (JVIB), Guidance Laws (STOP, LOST, REACH, WALK, RETURN), REPEAT / REJECT Intents

### Community 23 - "telemd Sender"
Cohesion: 0.25
Nodes (5): escape_name(), heartbeat_alive(), main(), snapshot(), vector_json()

### Community 24 - "Intent Kinds"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

### Community 25 - "Perception Pipeline Budget"
Cohesion: 0.31
Nodes (10): Pi 5 CPU Frame Budget (YOLO11n 168 ms + depth 120 ms), camd (camera process), 30-Second Demo Script (spec section 12), Depth Anything V2 Metric Indoor Small, Guidance Modes LIVE / HOLD / LOST, guided (60 Hz guidance synthesizer), MediaPipe Hands, Nathan (hardware and perception owner) (+2 more)

### Community 26 - "fakeworld Simulator"
Cohesion: 0.38
Nodes (8): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), set_pose_yaw(), world_from_cam()

### Community 27 - "Shared-Memory Openers"
Cohesion: 0.22
Nodes (9): open_world(), beacon_frames_t, beacon_now_ns(), beacon_world_t, main(), open_world(), preview_tick(), sample_frame() (+1 more)

### Community 28 - "Speech Query and POI Store"
Cohesion: 0.29
Nodes (6): Embedding Pose Graph, llama.cpp + Qwen2.5-0.5B GGUF Fallback Remap, LOST-3DSG, NLMap, voiced (speech intent process), whisper.cpp tiny.en

### Community 29 - "Vision Model Stack"
Cohesion: 0.29
Nodes (4): Depth Anything V2 Metric Indoor Small INT8, llama.cpp ~0.5B remap (table miss only), onnxruntime 1.24.4 (QNX), YOLOE-26n baked detect-only ONNX detector

### Community 30 - "JPEG Encoder Callbacks"
Cohesion: 0.33
Nodes (3): destination_full(), destination_ready(), skip_jpeg()

### Community 31 - "Mode Enum"
Cohesion: 0.40
Nodes (5): beacon_mode, BEACON_MODE_HOLD, BEACON_MODE_LIVE, BEACON_MODE_LOST, BEACON_MODE_NONE

## Knowledge Gaps
- **105 isolated node(s):** `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK`, `GUIDED_CMD_TONE_ON`, `GUIDED_CMD_TONE_OFF` (+100 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 202 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Beacon: Nathan's revision (spec)` connect `Spec Documents Lineage` to `Accessibility Research Papers`, `Pi Dev Workflow`, `Open-Vocab Model Choices`, `Spec Review Verdict`, `Navigation Research and Build Order`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK` to the rest of the system?**
  _105 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `System Overview (READMEs)` be split into smaller, more focused modules?**
  _Cohesion score 0.05920745920745921 - nodes in this community are weakly interconnected._
- **Why does `Beacon Team Plan` connect `Navigation Research and Build Order` to `System Overview (READMEs)`, `Pi Dev Workflow`, `Spec Documents Lineage`, `Perception Pipeline Budget`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `main()` (e.g. with `audio_dropped_speech()` and `audio_publish_stats()`) actually correct?**
  _`main()` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Should `Guided Law Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.10138248847926268 - nodes in this community are weakly interconnected._