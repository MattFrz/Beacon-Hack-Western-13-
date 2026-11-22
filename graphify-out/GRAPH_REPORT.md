# Graph Report - beacon  (2026-11-22)

## Corpus Check
- 143 files · ~150,307 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 11, .jsonl 3, .css 1)

## Summary
- 1722 nodes · 3870 edges · 92 communities (73 shown, 19 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 233 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f4a1ebcc`
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
- beacon.h
- probe_to_world
- telemd.c
- test_beacon.py
- Model Files Directory (not committed)
- argparse
- beacon_intent_kind
- guided synthesizer (FIFO 58, core 0)
- deadline_test.c
- telemd (read-only telemetry sender)
- beacon_pulse
- WALK Speech / REACH Ticks Audio Split
- TapeCheckTest
- guided (60 Hz guidance synthesizer)
- beacon.h
- main
- Scene.jsx
- Model Files Directory (not committed)
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- probe_frame.py
- ProbeRuntimeTest
- camd/src/main.c
- Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)
- Model Files Directory (not committed)
- vo_core.py
- time
- ingest/src/main.c
- math
- probe_frame.py
- Merge verdict: BLOCK
- Clip caption table (enum beacon_clip order)
- time
- FakeLandmarker
- SlotTracker
- ort_capi.py
- Weekend build order (geometry order)
- ProbeRuntimeTest
- Refresh the graph before a PR into main
- Weekend build order (geometry order)
- qnxpi Target (QNX 8.0 Raspberry Pi 5)
- FakeFileCapture
- Beacon: Nathan's revision (spec)
- Beacon Accessibility Research
- bt_audio_service.sh
- run-radio-auto.sh
- make_clips.ps1
- irl_test.sh
- pi_live.sh
- ingest/README.md
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
- Beacon (chest-worn item-homing wearable)
- device_live_demo.sh
- device_slay_beat.sh
- device_chain_demo.sh
- Working notes (not shipped)
- ai-import-test.sh
- Depth Anything V2 Metric Indoor Small ONNX
- gen_ort_capi_table.py
- camd (camera daemon)
- telemd (read-only telemetry to the laptop)
- probe_to_world.py World JSONL / UDP Emitter
- export_depth.py
- bt_audio_service.sh
- run-radio-auto.sh
- run_scenario.sh
- irl_test.sh
- pi_live.sh
- models/labels.txt runtime vocabulary (six nouns, committed)
- supervisor tests (make test, make test-beacon: kill, stale beat, backoff reset)

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
10. `main()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `What changed` --references--> `targetObjectId()`  [INFERRED]
  docs/dashboard-redesign.md → laptop/dashboard/src/worldScene.js
- `Where it lives` --references--> `Vo`  [INFERRED]
  docs/superpowers/specs/2026-11-21-vo-integration-design.md → percept/tools/vo_core.py
- `Busy-loop cores 1-3 then 0 missed deadlines (the QNX proof)` --semantically_similar_to--> `Full loop closes on QNX (1500 loops, 0 missed, guided speaks)`  [INFERRED] [semantically similar]
  guided/PI_TEST.md → docs/pi-bringup.md
- `Task 2: `vo_probe.py` — CLI over recorded or live walks` --references--> `make_affine()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/probe_frame.py
- `Task 2: `vo_probe.py` — CLI over recorded or live walks` --references--> `predict_depth()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/probe_frame.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Beacon five-process QNX isolation** — docs_nathans_revision_five_process_architecture, docs_nathans_revision_supervisor, docs_nathans_revision_runmask_core0_isolation, docs_nathans_revision_seqlock, docs_nathans_revision_no_aps, docs_pi_bringup_supervisor_verified [EXTRACTED 1.00]
- **Honest cue under perception failure** — docs_nathans_revision_live_hold_lost, docs_pi_bringup_slay_beat, docs_beacon_accessibility_research_honest_lost_cue, docs_devpost_honesty_block, docs_demo_runbook_thirty_seconds [EXTRACTED 1.00]
- **Live telemetry pipeline: Pi telemd -> UDP 5005 -> bridge -> WebSocket 8765 -> dashboard** — telemd_readme, laptop_bridge_readme, laptop_bridge_wire_format, laptop_dashboard_readme, laptop_samples_readme [EXTRACTED 1.00]
- **Measured on the loaner (submission evidence chain)** — docs_pi_bringup_full_loop_closes, docs_pi_bringup_slay_beat, docs_pi_bringup_supervisor_verified, docs_pi_bringup_live_camera_solved, readme_qnx_story_numbers, docs_devpost_why_qnx [EXTRACTED 1.00]
- **percept vision pipeline (YOLOE, metric depth, hands, honest gating)** — percept_readme, models_readme_yoloe26n, models_readme_depth_anything_v2, models_readme_hand_bake, models_labels_txt, percept_readme_tape_check, percept_readme_live_probe [EXTRACTED 1.00]
- **Recording, replay and dashboard history** — laptop_bridge_recordings, laptop_samples_vid360_replay, laptop_samples_dev_reach, laptop_samples_rebuild_recipe [EXTRACTED 1.00]
- **Spoken-metre gating (tape check before any distance is said aloud)** — percept_readme_tape_check, guided_flags_metres_audio, docs_nathans_revision_tape_check_gate, docs_demo_runbook_metres_decision, docs_devpost_honesty_block [EXTRACTED 1.00]
- **Visual odometry integration (KLT front-end, watchdog, honest failure)** — docs_superpowers_specs_2026_11_21_vo_integration_design_visual_odometry_integration_design, docs_superpowers_specs_vo_klt_frontend, docs_superpowers_specs_vo_scale_watchdog, docs_superpowers_specs_vo_failure_semantics, docs_superpowers_plans_2026_11_21_vo_integration, percept_tools_vo_core, percept_tools_vo_probe [EXTRACTED 1.00]
- **Stand-ins feeding /beacon_world before real percept and voiced** — guided_tools_fakeworld, voiced_world_in, voiced_beacon_cmd, ingest_intent_standin, camd_bmp_bringup [INFERRED 0.85]

## Communities (92 total, 19 thin omitted)

### Community 0 - "tempfile"
Cohesion: 0.10
Nodes (69): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+61 more)

### Community 1 - "App.jsx"
Cohesion: 0.05
Nodes (42): adapterFor(), gapMs(), isV4(), laptopAddresses(), loadReplay(), parseWorld(), startBridge(), collect() (+34 more)

### Community 2 - "guided_step"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.12
Nodes (14): Affine, _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip() (+6 more)

### Community 4 - "make-dev-reach.test.js"
Cohesion: 0.16
Nodes (6): prepare(), probe_once(), fake_encode(), synthetic_probe_modules(), synthetic_video_modules(), emit_lines()

### Community 5 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.10
Nodes (12): dump_ep_ctx(), ep_type_name(), main(), map_mmio(), dump(), main(), main(), mp() (+4 more)

### Community 6 - "probe_to_world"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 7 - "with"
Cohesion: 0.13
Nodes (36): Dashboard layout (floating top bar, sliding panels, replay scrubber, reduced-motion), Ago(), agoText(), App(), BOTH, Camera(), Caption(), DataSource() (+28 more)

### Community 8 - "head.cpp"
Cohesion: 0.07
Nodes (25): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+17 more)

### Community 9 - "probe_frame.py"
Cohesion: 0.10
Nodes (12): build_parser(), capture_memory(), gate_by_depth(), inject_memory(), _install_depth_capture(), lift_hand(), main(), _open_sock() (+4 more)

### Community 10 - "Any"
Cohesion: 0.09
Nodes (12): calibrate_camera.py chessboard calibration (calib.json is laptop-local, never beacon.h), build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest (+4 more)

### Community 11 - "audio.c"
Cohesion: 0.08
Nodes (32): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, @fontsource/ibm-plex-mono@^5.3.0, @fontsource/ibm-plex-sans@^5.3.0, motion@^14.14.0, react-aria-components@^1.22.1, react-dom@^19.3.1 (+24 more)

### Community 12 - "beacon.h"
Cohesion: 0.08
Nodes (25): main(), put_u16(), put_u32(), write_bmp(), beacon_crumb_t, beacon_depth_t, beacon_frame_slot_t, beacon_guided_block_t (+17 more)

### Community 13 - "probe_to_world"
Cohesion: 0.06
Nodes (22): build_parser(), format_readout(), load_target_names(), main(), _ns(), _number(), _output(), parse_udp_target() (+14 more)

### Community 14 - "telemd.c"
Cohesion: 0.08
Nodes (21): Replay rebuild recipe (probe_to_world + vo_probe + merge_vo_world, rebase t_ns), Anchor, blend_pose(), build_crumbs(), component_median(), first_frame_id(), main(), median() (+13 more)

### Community 15 - "test_beacon.py"
Cohesion: 0.42
Nodes (6): alive(), lines(), main(), pids(), wait_for(), wait_for_pid()

### Community 16 - "Model Files Directory (not committed)"
Cohesion: 0.21
Nodes (22): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+14 more)

### Community 17 - "argparse"
Cohesion: 0.13
Nodes (22): audio_main(), audio_start(), law_name(), mode_name(), audio_out_close(), audio_out_open(), audio_out_paced(), audio_out_write() (+14 more)

### Community 18 - "beacon_intent_kind"
Cohesion: 0.11
Nodes (15): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), main(), audio_dropped_speech(), audio_stop() (+7 more)

### Community 19 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.22
Nodes (8): free_udp_port(), hand_at(), main(), find(), record(), wait_for_exit(), supervise(), wait_for()

### Community 20 - "deadline_test.c"
Cohesion: 0.30
Nodes (21): jalloc(), jarr_at(), jarray(), jis(), jnew(), jnum(), jnumber(), jobj_get() (+13 more)

### Community 21 - "telemd (read-only telemetry sender)"
Cohesion: 0.16
Nodes (15): add_argv(), add_argv_line(), allow_priorities(), beacon_children(), create_region(), depth_name(), describe(), ensure_regions() (+7 more)

### Community 22 - "beacon_pulse"
Cohesion: 0.25
Nodes (8): beacon_pulse, BEACON_PULSE_AUDIO_UNDERRUN, BEACON_PULSE_HB_CAMD, BEACON_PULSE_HB_GUIDED, BEACON_PULSE_HB_PERCEPT, BEACON_PULSE_HB_VOICED, BEACON_PULSE_INTENT_EDGE, BEACON_PULSE_SUP_TICK

### Community 24 - "WALK Speech / REACH Ticks Audio Split"
Cohesion: 0.14
Nodes (12): make_affine(), fit_ground_height(), keyframe_due(), scale_correction(), camera_matrix(), make_metres(), make_texture(), make_vo() (+4 more)

### Community 25 - "TapeCheckTest"
Cohesion: 0.19
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 26 - "guided (60 Hz guidance synthesizer)"
Cohesion: 0.28
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 28 - "beacon.h"
Cohesion: 0.12
Nodes (14): Beacon Accessibility Research (BLV evidence brief), Open-vocab model research for Pi 5 CPU, Demo runbook: Best Use of QNX (floor pass, live pass, failure plays), Devpost paste-ready description, Beacon (chest-worn named-object homing device), Pitch language table (no cure framing, supplement to the cane, sighted team), Saturday Build Order (spec section 13, steps 1-6), Beacon: Nathan's revision (spec) (+6 more)

### Community 29 - "main"
Cohesion: 0.13
Nodes (17): Dashboard redesign and live Pi connection, Graph, Live Raspberry Pi connection, Live | Replay bridge switching (UDP 5005 always open, status frame once a second), Running it against the Pi, Still open, What actually ran on the Pi, What changed (+9 more)

### Community 30 - "Scene.jsx"
Cohesion: 0.24
Nodes (14): completion(), desc_at(), find_audio_stream(), insertion(), logf_(), main(), now_elapsed(), put16() (+6 more)

### Community 31 - "Model Files Directory (not committed)"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

### Community 32 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.12
Nodes (9): Floor pass: insurance video from device_chain_demo.sh and device_slay_beat.sh, Remembered-row bind window (20 s, amended 2026-11-22), Full loop closes on QNX (1500 loops, 0 missed, guided speaks), Bluetooth HFP capture as the working mic path (GPIO28 is the Wi-Fi rail, never toggle), The QNX beat on hardware (slay ingest, LOST, recovery, guided never restarted), micd (C270 UAC1 mic capture on QNX, work in progress), Running the demo scripts (README section), Status: what runs on the loaner and what does not (README section) (+1 more)

### Community 33 - "probe_frame.py"
Cohesion: 0.16
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 35 - "ProbeRuntimeTest"
Cohesion: 0.19
Nodes (7): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips()

### Community 36 - "camd/src/main.c"
Cohesion: 0.12
Nodes (11): Self-review, Task 6: Integration into the percept cycle and the measured gates, _make_vo(), backproject(), chain(), crumb_due(), lk_track(), Vo (+3 more)

### Community 37 - "Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)"
Cohesion: 0.21
Nodes (14): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+6 more)

### Community 38 - "Model Files Directory (not committed)"
Cohesion: 0.14
Nodes (9): Open items before the runbook is fully true (A3 pidin ar, A5 kill the producer, A6 metres), How QNX is used (Devpost section with measured numbers), Supervisor contract (spawn with scheduler attributes, 50 ms pulse heartbeat, respawn backoff), BTstack A2DP bridge to JBL Go 3 (validated, boot-persistent), Device facts (QNX 8.0.0 Pi 5, runmask support, 1 ms clock), Supervisor to spec, verified on the loaner (58f/40f/22r, respawn ~100 ms), guided Pi validation sequence (build, silent run, JBL, timing under load), guided (60 Hz guidance synthesizer: mode, bind, laws, audio) (+1 more)

### Community 39 - "vo_core.py"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 40 - "time"
Cohesion: 0.16
Nodes (4): Accuracy ruling (Nathan, 2026-11-21, after the 360-degree clip demo), Open items (builder calls, marked at implementation), load_yolo_session(), ProbeResources

### Community 41 - "ingest/src/main.c"
Cohesion: 0.21
Nodes (9): beacon_world_t, apply_sched(), attach_block(), main(), open_world(), parse_intent(), usage(), write_intent() (+1 more)

### Community 42 - "math"
Cohesion: 0.11
Nodes (11): World-frame 3D dots plan (dashboard session map), Range 1 tabletop proof gate (same frame_id, tape-checked d_m), vid360 look-around replay (249 lines, real VO pose, six-noun bake), FakeSessionOptions, build_parser(), evaluate(), load_record(), main() (+3 more)

### Community 43 - "probe_frame.py"
Cohesion: 0.06
Nodes (25): Task 2: `vo_probe.py` — CLI over recorded or live walks, MediaPipe hand_landmarker.task probe (broken pybind11 on QNX), Per-slot depth median stabilisation (IoU slots, jump/evict/recover gates), build_parser(), Calibration, guess_calibration(), load_calibration(), load_depth_session() (+17 more)

### Community 44 - "Merge verdict: BLOCK"
Cohesion: 0.18
Nodes (4): crop_depth_padding(), _draw_boxes(), render_preview(), RenderPreviewTest

### Community 45 - "Clip caption table (enum beacon_clip order)"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 46 - "time"
Cohesion: 0.14
Nodes (5): VO task order: laptop-first core, probe, recorded walk, C++ port, percept cycle, main(), _camera_matrix(), PoseResult, solve_pose()

### Community 48 - "FakeLandmarker"
Cohesion: 0.15
Nodes (13): 1.3 QNX-mechanism stubs (the pitch vs the code), 2. Plan, Step 0 — Mentor ask (Nathan, 15 min, now, blocks everything), Step 1 — Runtime on the Pi (Nathan, 45 min hard box), Step 2 — A real frame into `/beacon_frames` (Nathan, 60 min), Step 3 — `percept` on the Pi (Nathan, 60 min), Step 4 — `ingest`: the missing wire (Munadir or Nathan, 60 min, can start on laptop now), Step 5 — Audio out + piezo (Munadir + Matt, parallel, 60 min) (+5 more)

### Community 50 - "SlotTracker"
Cohesion: 0.32
Nodes (11): ChevronLeft(), ChevronRight(), Collapse(), Expand(), Icon(), Panel(), PanelLeftClose(), PanelLeftOpen() (+3 more)

### Community 51 - "ort_capi.py"
Cohesion: 0.07
Nodes (12): api(), _check(), _find_library(), _OrtApiBase, OrtError, _read_ptr(), Session, TensorInfo (+4 more)

### Community 53 - "ProbeRuntimeTest"
Cohesion: 0.11
Nodes (3): ProbeRuntimeTest, fake_detect(), fake_predict_depth()

### Community 54 - "Refresh the graph before a PR into main"
Cohesion: 0.33
Nodes (11): apply(), find_key(), get_id(), get_num(), get_str(), get_vecn(), main(), publish() (+3 more)

### Community 55 - "Weekend build order (geometry order)"
Cohesion: 0.29
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 56 - "qnxpi Target (QNX 8.0 Raspberry Pi 5)"
Cohesion: 0.26
Nodes (9): react@^19.3.1, SourceSwitch(), clock(), Events(), Sidebar(), SyncMobile(), Tip(), @animate-ui/react (+1 more)

### Community 58 - "FakeFileCapture"
Cohesion: 0.25
Nodes (7): Global Constraints, Review Focus, Task 1: `vo_core.py` — the geometry core with synthetic tests, Task 3: Record a real L-walk and tune, Task 4: On-device OpenCV gate — the A/B decision (spec F1), Task 5: `vo.hpp` / `vo.cpp` — the C++ port, VO Integration Implementation Plan

### Community 59 - "Beacon: Nathan's revision (spec)"
Cohesion: 0.22
Nodes (16): audio_publish_stats(), audio_submit(), test_seq_writer_restart(), drop_crumb(), lerp(), main(), publish_percept(), put_hand() (+8 more)

### Community 60 - "Beacon Accessibility Research"
Cohesion: 0.25
Nodes (4): dep_names(), main(), parse_index(), version_gt()

### Community 61 - "bt_audio_service.sh"
Cohesion: 0.33
Nodes (8): beacon_live_max_ns(), append(), append_scene(), escape_name(), heartbeat_alive(), main(), snapshot(), vector_json()

### Community 64 - "make_clips.ps1"
Cohesion: 0.33
Nodes (5): clean(), ctype_of(), expand(), main(), split_args()

### Community 65 - "irl_test.sh"
Cohesion: 0.20
Nodes (9): 1.1 What laptop work has achieved (all true, all on the wrong machine), 1.2 Gap table against the prize hard requirements, 1.4 The real-time claim needs re-scoping, 1.5 Cuts already made or to be made now, 1.6 Small risks that will burn an hour at the worst moment, 1. Findings, 3. Ownership + order of attack (parallel tracks), 4. What "done" means at 8 am Sunday (+1 more)

### Community 66 - "pi_live.sh"
Cohesion: 0.20
Nodes (9): Three ranges (REACH ships without VO; Range 3 needs pose), Anti-goals (what would make this a failure even if it works), Approaches considered (team decision 2026-11-21), Constraints (measured facts, not targets), Goals, Intent, Non-goals, QNX track review (2026-11-21, against `pi-dev-workflow.md` and `pi-bringup.md`) (+1 more)

### Community 67 - "ingest/README.md"
Cohesion: 0.29
Nodes (6): Build / test, ingest, Known limits (deliberate), Usage, What it writes (and never writes), world_in fallback bridge (laptop probe drives guided on the Pi)

### Community 68 - ".test_capture_frames_prompts_between_views"
Cohesion: 0.22
Nodes (7): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), BMP bring-up frame source (frametype 65535, not a camera driver), CLAUDE.md (imports AGENTS.md), Loaner Pi bring-up log (dated evidence rows), Pi development workflow (QNX 8.0 read-only IFS, /data survives), Gap table against the prize hard requirements

### Community 69 - "beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 70 - "/beacon_frames Newest-wins Three-slot Ring"
Cohesion: 0.15
Nodes (9): camd (camera daemon, Sensor Framework into the frame ring), Failure plays (usb_start.sh, VBUS power-cycle, BT service restart, replay fallback), QNX findings F1-F9 (OpenCV module gate, keyframe from in-process copy, 1 ms clock), find_eoi(), now_ns(), on_data(), write_atomic(), micd gotchas (TRB ring leak on resubmit, VBUS power-cycle, QNX getopt parsing) (+1 more)

### Community 73 - "Honest LOST Cue (no invented metres)"
Cohesion: 0.43
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 74 - "test_frame_id_seed.py"
Cohesion: 0.32
Nodes (10): add(), handle(), html_escape(), is_skip(), kind_name(), main(), send_all(), send_intent() (+2 more)

### Community 75 - "beacon_cmd.c"
Cohesion: 0.25
Nodes (4): guided audio thread (prio 40, speech ring, newest-wins tick/tone slot), Kokoro-82M voice clips rendered by llama.cpp TTS (make_clips.py), Turn-toward orientation pips and rising chime (guided ADDITION), sounds (pre-rendered 16 kHz clip set, one WAV per clip id)

### Community 76 - "Inclusive Language and Non-Cure Framing"
Cohesion: 0.29
Nodes (6): Ultralytics AGPL-3.0 licence risk (fine for a hackathon build, say so if asked), Baked noun list (6 today, 64 max, no runtime retraining), Seven-noun vocabulary with the hand class, Six-noun baked vocabulary (bottle, can, keys, phone, box, mouse), YOLOE-26n baked detect-only ONNX detector (six-noun bake, 9.3 MB, no NMS), live_probe.py on-device loop (grabber to latest.jpg, UDP 5006, --max-depth gate)

### Community 77 - "make-dev-reach.test.js"
Cohesion: 0.29
Nodes (6): Beacon spec adversarial review, Merge verdict: BLOCK, Regenerating a review diff, Review verdicts, Where things are, Working notes (not shipped)

### Community 80 - "Beacon (chest-worn item-homing wearable)"
Cohesion: 0.29
Nodes (7): Failure semantics (unchanged from §8, restated as contract), Per VO step (~every 100 ms; every 3rd ring frame at 30 fps), Scheduling, State (per-process, not shm), The design, What "done and trusted" means (acceptance gates), Where it lives

### Community 82 - "device_live_demo.sh"
Cohesion: 0.33
Nodes (3): guided --metres (tape-gated) and --audio outputs (none, wav, fifo, qnx), Depth Anything V2 Metric Indoor Small ONNX (static 210x210, external .onnx.data), irl_test.sh: recorded clip through world_in into guided, wearer audio to WAV

### Community 83 - "device_slay_beat.sh"
Cohesion: 0.40
Nodes (5): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_live_demo.sh script, slay_matching()

### Community 84 - "device_chain_demo.sh"
Cohesion: 0.40
Nodes (5): kill_matching(), LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_slay_beat.sh script

### Community 88 - "Depth Anything V2 Metric Indoor Small ONNX"
Cohesion: 0.40
Nodes (4): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_chain_demo.sh script

### Community 91 - "telemd (read-only telemetry to the laptop)"
Cohesion: 0.50
Nodes (3): LD_LIBRARY_PATH, PYTHONPATH, ai-import-test.sh script

## Knowledge Gaps
- **155 isolated node(s):** `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK`, `GUIDED_CMD_TONE_ON`, `GUIDED_CMD_TONE_OFF` (+150 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 585 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `bridge (Node UDP-to-WebSocket relay and recorder)` connect `main` to `.test_capture_frames_prompts_between_views`?**
  _High betweenness centrality (0.205) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK` to the rest of the system?**
  _155 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `tempfile` be split into smaller, more focused modules?**
  _Cohesion score 0.10367762128325508 - nodes in this community are weakly interconnected._
- **Why does `Telemetry format (world state ~10 Hz + JPEG ~5 fps to UDP 5005)` connect `main` to `beacon.h`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05257936507936508 - nodes in this community are weakly interconnected._