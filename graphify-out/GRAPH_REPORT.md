# Graph Report - Beacon-Hack-Western-13-  (2026-11-22)

## Corpus Check
- 145 files · ~148,260 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1713 nodes · 3842 edges · 103 communities (79 shown, 24 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 233 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- guided law and tests
- bridge package and tests
- beacon.h ABI structs
- probe_frame vision cycle
- probe_frame test suite
- USB forensics tools
- CI workflow
- dashboard App layout
- percept-head shm reader
- live_probe on-device loop
- camera calibration
- dashboard package deps
- ingest world writer
- probe_to_world tests
- merge_vo_world tests
- VO world merge tool
- dashboard world scene
- guided audio output
- deadline test and platform
- ingest supervisor tests
- ingest JSON parser
- supervisor spawn loop
- probe_to_world CLI tests
- probe_to_world emitter
- vo_core tests
- probe_frame letterbox tests
- tape_check tests
- probe test helpers
- spec and model research docs
- dashboard redesign docs
- micd USB driver
- beacon.h guided contracts
- judge-facing README docs
- bt_speaker playback
- probe_to_world slot tests
- clip generation TTS
- vo_core geometry
- camd BMP reader
- pitch and bring-up docs
- probe_frame depth sampling
- probe_frame readout
- camd frame tools
- tape_check gate
- probe_frame hand tests
- probe_frame render preview
- telemd preview JPEG
- vo_core keyframe logic
- probe_frame CLI parser
- QNX integration plan
- vo_probe CLI
- dashboard icons and scrubber
- ORT C API binding
- ORT shim and device probe
- probe_frame record tests
- voiced world_in bridge
- frame id seed tests
- dashboard panels and deps
- demo runbook evidence
- VO plan review focus
- fakeworld stand-in
- QNX apk package fetch
- telemd sender
- vo_probe tests
- ort_capi table binding
- ORT table generator
- QNX plan mechanism stubs
- VO design spec
- percept README pipeline
- agent notes and graph rule
- guided law header
- beacon_grab sensor reader
- ort_shim import path
- probe_frame calibration tests
- guided clips loader
- beacon_cmd stand-in
- accessibility evidence in README
- open-vocab model picks
- spec review blockers
- YOLOE export tool
- vo_core watchdog
- VO design open items
- beacon.h pulse codes
- demo script docs
- device live demo script
- device slay beat script
- ort_capi core
- probe_frame misc tests
- probe_frame edge tests
- device chain demo script
- depth export tool
- probe_frame parser tests
- AI import test script
- probe_frame slot tests
- integration-plan scope docs
- BT audio service
- radio auto-connect script
- Community 97
- Community 99
- Community 100
- Community 101
- Community 102

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
- `Where it lives` --references--> `Vo`  [INFERRED]
  docs/superpowers/specs/2026-11-21-vo-integration-design.md → percept/tools/vo_core.py
- `What changed` --references--> `targetObjectId()`  [INFERRED]
  docs/dashboard-redesign.md → laptop/dashboard/src/worldScene.js
- `Busy-loop cores 1-3 then 0 missed deadlines (the QNX proof)` --semantically_similar_to--> `Full loop closes on QNX (1500 loops, 0 missed, guided speaks)`  [INFERRED] [semantically similar]
  guided/PI_TEST.md → docs/pi-bringup.md
- `Self-review` --references--> `VoConfig`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/vo_core.py
- `Self-review` --references--> `VoStep`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/vo_core.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Beacon five-process QNX isolation** — docs_nathans_revision_five_process_architecture, docs_nathans_revision_supervisor, docs_nathans_revision_runmask_core0_isolation, docs_nathans_revision_seqlock, docs_nathans_revision_no_aps, docs_pi_bringup_supervisor_verified [EXTRACTED 1.00]
- **Honest cue under perception failure** — docs_nathans_revision_live_hold_lost, docs_pi_bringup_slay_beat, docs_beacon_accessibility_research_honest_lost_cue, docs_devpost_honesty_block, docs_demo_runbook_thirty_seconds [EXTRACTED 1.00]
- **Measured on the loaner (submission evidence chain)** — docs_pi_bringup_full_loop_closes, docs_pi_bringup_slay_beat, docs_pi_bringup_supervisor_verified, docs_pi_bringup_live_camera_solved, readme_qnx_story_numbers, docs_devpost_why_qnx [EXTRACTED 1.00]
- **Visual odometry integration (KLT front-end, watchdog, honest failure)** — docs_superpowers_specs_2026_11_21_vo_integration_design_visual_odometry_integration_design, docs_superpowers_specs_vo_klt_frontend, docs_superpowers_specs_vo_scale_watchdog, docs_superpowers_specs_vo_failure_semantics, docs_superpowers_plans_2026_11_21_vo_integration, percept_tools_vo_core, percept_tools_vo_probe [EXTRACTED 1.00]
- **Live telemetry pipeline: Pi telemd -> UDP 5005 -> bridge -> WebSocket 8765 -> dashboard** — telemd_readme, laptop_bridge_readme, laptop_bridge_wire_format, laptop_dashboard_readme, laptop_samples_readme [EXTRACTED 1.00]
- **Recording, replay and dashboard history** — laptop_bridge_recordings, laptop_samples_vid360_replay, laptop_samples_dev_reach, laptop_samples_rebuild_recipe [EXTRACTED 1.00]
- **percept vision pipeline (YOLOE, metric depth, hands, honest gating)** — percept_readme, models_readme_yoloe26n, models_readme_depth_anything_v2, models_readme_hand_bake, models_labels_txt, percept_readme_tape_check, percept_readme_live_probe [EXTRACTED 1.00]
- **Stand-ins feeding /beacon_world before real percept and voiced** — guided_tools_fakeworld, voiced_world_in, voiced_beacon_cmd, ingest_intent_standin, camd_bmp_bringup [INFERRED 0.85]
- **Spoken-metre gating (tape check before any distance is said aloud)** — percept_readme_tape_check, guided_flags_metres_audio, docs_nathans_revision_tape_check_gate, docs_demo_runbook_metres_decision, docs_devpost_honesty_block [EXTRACTED 1.00]

## Communities (103 total, 24 thin omitted)

### Community 0 - "guided law and tests"
Cohesion: 0.10
Nodes (69): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+61 more)

### Community 1 - "bridge package and tests"
Cohesion: 0.05
Nodes (42): adapterFor(), gapMs(), isV4(), laptopAddresses(), loadReplay(), parseWorld(), startBridge(), collect() (+34 more)

### Community 2 - "beacon.h ABI structs"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 3 - "probe_frame vision cycle"
Cohesion: 0.09
Nodes (19): MediaPipe hand_landmarker.task probe (broken pybind11 on QNX), Per-slot depth median stabilisation (IoU slots, jump/evict/recover gates), Affine, _central_bounds(), crop_depth_padding(), depth_at_box(), depth_at_full(), depth_at_patch() (+11 more)

### Community 4 - "probe_frame test suite"
Cohesion: 0.14
Nodes (6): prepare(), probe_once(), ProbeRuntimeTest, fake_encode(), synthetic_probe_modules(), synthetic_video_modules()

### Community 5 - "USB forensics tools"
Cohesion: 0.10
Nodes (12): dump_ep_ctx(), ep_type_name(), main(), map_mmio(), dump(), main(), main(), mp() (+4 more)

### Community 6 - "CI workflow"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 7 - "dashboard App layout"
Cohesion: 0.13
Nodes (35): Dashboard layout (floating top bar, sliding panels, replay scrubber, reduced-motion), Ago(), agoText(), App(), BOTH, Camera(), Caption(), DataSource() (+27 more)

### Community 8 - "percept-head shm reader"
Cohesion: 0.07
Nodes (26): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+18 more)

### Community 9 - "live_probe on-device loop"
Cohesion: 0.09
Nodes (13): build_parser(), capture_memory(), gate_by_depth(), inject_memory(), _install_depth_capture(), lift_hand(), main(), _make_vo() (+5 more)

### Community 10 - "camera calibration"
Cohesion: 0.09
Nodes (11): build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest, synthetic_view() (+3 more)

### Community 11 - "dashboard package deps"
Cohesion: 0.08
Nodes (32): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, @fontsource/ibm-plex-mono@^5.3.0, @fontsource/ibm-plex-sans@^5.3.0, motion@^14.14.0, react-aria-components@^1.22.1, react-dom@^19.3.1 (+24 more)

### Community 12 - "ingest world writer"
Cohesion: 0.10
Nodes (30): audio_publish_stats(), audio_submit(), test_seq_writer_restart(), beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t, beacon_guided_stats_t (+22 more)

### Community 13 - "probe_to_world tests"
Cohesion: 0.18
Nodes (6): probe_to_world(), make_detection(), make_last_bottle(), make_probe(), ProbeToWorldTest, fake_probe_once()

### Community 14 - "merge_vo_world tests"
Cohesion: 0.18
Nodes (8): MergeTests, rec(), person_at(), record_with(), T(), vo_record(), world_record(), write_jsonl()

### Community 15 - "VO world merge tool"
Cohesion: 0.11
Nodes (13): Replay rebuild recipe (probe_to_world + vo_probe + merge_vo_world, rebase t_ns), Anchor, blend_pose(), build_crumbs(), component_median(), first_frame_id(), main(), median() (+5 more)

### Community 16 - "dashboard world scene"
Cohesion: 0.21
Nodes (22): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+14 more)

### Community 17 - "guided audio output"
Cohesion: 0.14
Nodes (21): audio_main(), law_name(), mode_name(), audio_out_close(), audio_out_open(), audio_out_paced(), audio_out_write(), fifo_try_open() (+13 more)

### Community 18 - "deadline test and platform"
Cohesion: 0.11
Nodes (14): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), audio_dropped_speech(), audio_start(), audio_stop() (+6 more)

### Community 19 - "ingest supervisor tests"
Cohesion: 0.18
Nodes (14): free_udp_port(), hand_at(), main(), find(), record(), wait_for_exit(), alive(), lines() (+6 more)

### Community 20 - "ingest JSON parser"
Cohesion: 0.30
Nodes (21): jalloc(), jarr_at(), jarray(), jis(), jnew(), jnum(), jnumber(), jobj_get() (+13 more)

### Community 21 - "supervisor spawn loop"
Cohesion: 0.16
Nodes (15): add_argv(), add_argv_line(), allow_priorities(), beacon_children(), create_region(), depth_name(), describe(), ensure_regions() (+7 more)

### Community 22 - "probe_to_world CLI tests"
Cohesion: 0.17
Nodes (4): main(), parse_udp_target(), UdpEmitTest, fake_emit_lines()

### Community 23 - "probe_to_world emitter"
Cohesion: 0.16
Nodes (9): format_readout(), _ns(), _number(), _output(), _stable_id(), ReadoutTest, _timing(), _vec3() (+1 more)

### Community 24 - "vo_core tests"
Cohesion: 0.22
Nodes (9): keyframe_due(), camera_matrix(), make_metres(), make_texture(), make_vo(), rotation_angle_deg(), VoCoreTests, warp_for_rotation() (+1 more)

### Community 25 - "probe_frame letterbox tests"
Cohesion: 0.19
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 26 - "tape_check tests"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 28 - "spec and model research docs"
Cohesion: 0.12
Nodes (14): Beacon Accessibility Research (BLV evidence brief), Open-vocab model research for Pi 5 CPU, Demo runbook: Best Use of QNX (floor pass, live pass, failure plays), Devpost paste-ready description, Beacon (chest-worn named-object homing device), Pitch language table (no cure framing, supplement to the cane, sighted team), Saturday Build Order (spec section 13, steps 1-6), Beacon: Nathan's revision (spec) (+6 more)

### Community 29 - "dashboard redesign docs"
Cohesion: 0.13
Nodes (17): Dashboard redesign and live Pi connection, Graph, Live Raspberry Pi connection, Live | Replay bridge switching (UDP 5005 always open, status frame once a second), Running it against the Pi, Still open, What actually ran on the Pi, What changed (+9 more)

### Community 30 - "micd USB driver"
Cohesion: 0.24
Nodes (14): completion(), desc_at(), find_audio_stream(), insertion(), logf_(), main(), now_elapsed(), put16() (+6 more)

### Community 31 - "beacon.h guided contracts"
Cohesion: 0.10
Nodes (19): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+11 more)

### Community 32 - "judge-facing README docs"
Cohesion: 0.12
Nodes (9): Floor pass: insurance video from device_chain_demo.sh and device_slay_beat.sh, Remembered-row bind window (20 s, amended 2026-11-22), Full loop closes on QNX (1500 loops, 0 missed, guided speaks), Bluetooth HFP capture as the working mic path (GPIO28 is the Wi-Fi rail, never toggle), The QNX beat on hardware (slay ingest, LOST, recovery, guided never restarted), micd (C270 UAC1 mic capture on QNX, work in progress), Running the demo scripts (README section), Status: what runs on the loaner and what does not (README section) (+1 more)

### Community 33 - "bt_speaker playback"
Cohesion: 0.16
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 34 - "probe_to_world slot tests"
Cohesion: 0.14
Nodes (4): build_parser(), emit_lines(), fake_probe_once(), fake_probe_once()

### Community 35 - "clip generation TTS"
Cohesion: 0.18
Nodes (7): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips()

### Community 36 - "vo_core geometry"
Cohesion: 0.22
Nodes (6): Task 6: Integration into the percept cycle and the measured gates, backproject(), chain(), Vo, vo_pts_to_full(), VoStep

### Community 37 - "camd BMP reader"
Cohesion: 0.23
Nodes (13): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+5 more)

### Community 38 - "pitch and bring-up docs"
Cohesion: 0.14
Nodes (9): Open items before the runbook is fully true (A3 pidin ar, A5 kill the producer, A6 metres), How QNX is used (Devpost section with measured numbers), Supervisor contract (spawn with scheduler attributes, 50 ms pulse heartbeat, respawn backoff), BTstack A2DP bridge to JBL Go 3 (validated, boot-persistent), Device facts (QNX 8.0.0 Pi 5, runmask support, 1 ms clock), Supervisor to spec, verified on the loaner (58f/40f/22r, respawn ~100 ms), guided Pi validation sequence (build, silent run, JBL, timing under load), guided (60 Hz guidance synthesizer: mode, bind, laws, audio) (+1 more)

### Community 39 - "probe_frame depth sampling"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 40 - "probe_frame readout"
Cohesion: 0.15
Nodes (5): load_depth_session(), load_labels(), load_yolo(), load_yolo_session(), ProbeResources

### Community 41 - "camd frame tools"
Cohesion: 0.20
Nodes (7): main(), put_u16(), put_u32(), write_bmp(), main(), beacon_frame_slot_t, world_open()

### Community 42 - "tape_check gate"
Cohesion: 0.24
Nodes (8): Range 1 tabletop proof gate (same frame_id, tape-checked d_m), build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 43 - "probe_frame hand tests"
Cohesion: 0.22
Nodes (6): Calibration, guess_calibration(), load_calibration(), resolve_calibration(), GuessCalibrationTest, unproject()

### Community 45 - "telemd preview JPEG"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 46 - "vo_core keyframe logic"
Cohesion: 0.20
Nodes (6): VO task order: laptop-first core, probe, recorded walk, C++ port, percept cycle, _camera_matrix(), lk_track(), PoseResult, solve_pose(), VoConfig

### Community 47 - "probe_frame CLI parser"
Cohesion: 0.16
Nodes (6): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), _unit_float_arg()

### Community 48 - "QNX integration plan"
Cohesion: 0.15
Nodes (13): 1.3 QNX-mechanism stubs (the pitch vs the code), 2. Plan, Step 0 — Mentor ask (Nathan, 15 min, now, blocks everything), Step 1 — Runtime on the Pi (Nathan, 45 min hard box), Step 2 — A real frame into `/beacon_frames` (Nathan, 60 min), Step 3 — `percept` on the Pi (Nathan, 60 min), Step 4 — `ingest`: the missing wire (Munadir or Nathan, 60 min, can start on laptop now), Step 5 — Audio out + piezo (Munadir + Matt, parallel, 60 min) (+5 more)

### Community 49 - "vo_probe CLI"
Cohesion: 0.24
Nodes (8): Task 2: `vo_probe.py` — CLI over recorded or live walks, make_affine(), parse_csv3(), build_parser(), iter_frames(), main(), frames(), record_frames()

### Community 50 - "dashboard icons and scrubber"
Cohesion: 0.32
Nodes (11): ChevronLeft(), ChevronRight(), Collapse(), Expand(), Icon(), Panel(), PanelLeftClose(), PanelLeftOpen() (+3 more)

### Community 51 - "ORT C API binding"
Cohesion: 0.15
Nodes (5): _find_library(), _OrtApiBase, _read_ptr(), TensorInfo, AI on the device (README section)

### Community 52 - "ORT shim and device probe"
Cohesion: 0.15
Nodes (3): version(), install(), SessionOptions

### Community 54 - "voiced world_in bridge"
Cohesion: 0.33
Nodes (11): apply(), find_key(), get_id(), get_num(), get_str(), get_vecn(), main(), publish() (+3 more)

### Community 55 - "frame id seed tests"
Cohesion: 0.29
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 56 - "dashboard panels and deps"
Cohesion: 0.26
Nodes (9): react@^19.3.1, SourceSwitch(), clock(), Events(), Sidebar(), SyncMobile(), Tip(), @animate-ui/react (+1 more)

### Community 57 - "demo runbook evidence"
Cohesion: 0.18
Nodes (8): camd (camera daemon, Sensor Framework into the frame ring), Failure plays (usb_start.sh, VBUS power-cycle, BT service restart, replay fallback), Three ranges (REACH ships without VO; Range 3 needs pose), World-frame 3D dots plan (dashboard session map), QNX findings F1-F9 (OpenCV module gate, keyframe from in-process copy, 1 ms clock), vid360 look-around replay (249 lines, real VO pose, six-noun bake), micd gotchas (TRB ring leak on resubmit, VBUS power-cycle, QNX getopt parsing), telemd-preview (optional downscaled JPEG path, expires without the camera)

### Community 58 - "VO plan review focus"
Cohesion: 0.18
Nodes (9): Global Constraints, Review Focus, Self-review, Task 1: `vo_core.py` — the geometry core with synthetic tests, Task 3: Record a real L-walk and tune, Task 4: On-device OpenCV gate — the A/B decision (spec F1), Task 5: `vo.hpp` / `vo.cpp` — the C++ port, VO Integration Implementation Plan (+1 more)

### Community 59 - "fakeworld stand-in"
Cohesion: 0.35
Nodes (9): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+1 more)

### Community 60 - "QNX apk package fetch"
Cohesion: 0.25
Nodes (4): dep_names(), main(), parse_index(), version_gt()

### Community 61 - "telemd sender"
Cohesion: 0.33
Nodes (8): beacon_live_max_ns(), append(), append_scene(), escape_name(), heartbeat_alive(), main(), snapshot(), vector_json()

### Community 63 - "ort_capi table binding"
Cohesion: 0.33
Nodes (3): api(), _check(), OrtError

### Community 64 - "ORT table generator"
Cohesion: 0.33
Nodes (5): clean(), ctype_of(), expand(), main(), split_args()

### Community 65 - "QNX plan mechanism stubs"
Cohesion: 0.20
Nodes (9): 1.1 What laptop work has achieved (all true, all on the wrong machine), 1.2 Gap table against the prize hard requirements, 1.4 The real-time claim needs re-scoping, 1.5 Cuts already made or to be made now, 1.6 Small risks that will burn an hour at the worst moment, 1. Findings, 3. Ownership + order of attack (parallel tracks), 4. What "done" means at 8 am Sunday (+1 more)

### Community 66 - "VO design spec"
Cohesion: 0.20
Nodes (10): Accuracy ruling (Nathan, 2026-11-21, after the 360-degree clip demo), Anti-goals (what would make this a failure even if it works), Approaches considered (team decision 2026-11-21), Constraints (measured facts, not targets), Goals, Intent, Non-goals, Open items (builder calls, marked at implementation) (+2 more)

### Community 67 - "percept README pipeline"
Cohesion: 0.18
Nodes (6): Build / test, ingest, Known limits (deliberate), Usage, What it writes (and never writes), load_target_names()

### Community 68 - "agent notes and graph rule"
Cohesion: 0.22
Nodes (7): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), BMP bring-up frame source (frametype 65535, not a camera driver), CLAUDE.md (imports AGENTS.md), Loaner Pi bring-up log (dated evidence rows), Pi development workflow (QNX 8.0 read-only IFS, /data survives), Gap table against the prize hard requirements

### Community 69 - "guided law header"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 70 - "beacon_grab sensor reader"
Cohesion: 0.31
Nodes (4): find_eoi(), now_ns(), on_data(), write_atomic()

### Community 73 - "guided clips loader"
Cohesion: 0.43
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 74 - "beacon_cmd stand-in"
Cohesion: 0.43
Nodes (6): add(), handle(), is_skip(), kind_name(), main(), send_intent()

### Community 75 - "accessibility evidence in README"
Cohesion: 0.25
Nodes (4): guided audio thread (prio 40, speech ring, newest-wins tick/tone slot), Kokoro-82M voice clips rendered by llama.cpp TTS (make_clips.py), Turn-toward orientation pips and rising chime (guided ADDITION), sounds (pre-rendered 16 kHz clip set, one WAV per clip id)

### Community 76 - "open-vocab model picks"
Cohesion: 0.29
Nodes (6): Ultralytics AGPL-3.0 licence risk (fine for a hackathon build, say so if asked), Baked noun list (6 today, 64 max, no runtime retraining), Seven-noun vocabulary with the hand class, Six-noun baked vocabulary (bottle, can, keys, phone, box, mouse), YOLOE-26n baked detect-only ONNX detector (six-noun bake, 9.3 MB, no NMS), live_probe.py on-device loop (grabber to latest.jpg, UDP 5006, --max-depth gate)

### Community 77 - "spec review blockers"
Cohesion: 0.25
Nodes (6): Beacon spec adversarial review, Merge verdict: BLOCK, Regenerating a review diff, Review verdicts, Where things are, Working notes (not shipped)

### Community 80 - "VO design open items"
Cohesion: 0.29
Nodes (7): Failure semantics (unchanged from §8, restated as contract), Per VO step (~every 100 ms; every 3rd ring frame at 30 fps), Scheduling, State (per-process, not shm), The design, What "done and trusted" means (acceptance gates), Where it lives

### Community 81 - "beacon.h pulse codes"
Cohesion: 0.29
Nodes (7): beacon_law, BEACON_LAW_LOST, BEACON_LAW_NONE, BEACON_LAW_REACH, BEACON_LAW_RETURN, BEACON_LAW_STOP, BEACON_LAW_WALK

### Community 82 - "demo script docs"
Cohesion: 0.33
Nodes (3): guided --metres (tape-gated) and --audio outputs (none, wav, fifo, qnx), Depth Anything V2 Metric Indoor Small ONNX (static 210x210, external .onnx.data), irl_test.sh: recorded clip through world_in into guided, wearer audio to WAV

### Community 83 - "device live demo script"
Cohesion: 0.40
Nodes (5): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_live_demo.sh script, slay_matching()

### Community 84 - "device slay beat script"
Cohesion: 0.40
Nodes (5): kill_matching(), LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_slay_beat.sh script

### Community 88 - "device chain demo script"
Cohesion: 0.40
Nodes (4): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_chain_demo.sh script

### Community 91 - "AI import test script"
Cohesion: 0.50
Nodes (3): LD_LIBRARY_PATH, PYTHONPATH, ai-import-test.sh script

## Knowledge Gaps
- **156 isolated node(s):** `telemd-preview (optional downscaled JPEG path, expires without the camera)`, `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK`, `GUIDED_CMD_TONE_ON` (+151 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 583 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Telemetry format (world state ~10 Hz + JPEG ~5 fps to UDP 5005)` connect `dashboard redesign docs` to `ingest world writer`?**
  _High betweenness centrality (0.202) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `telemd-preview (optional downscaled JPEG path, expires without the camera)`, `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY` to the rest of the system?**
  _156 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `guided law and tests` be split into smaller, more focused modules?**
  _Cohesion score 0.10367762128325508 - nodes in this community are weakly interconnected._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `bridge package and tests` be split into smaller, more focused modules?**
  _Cohesion score 0.05257936507936508 - nodes in this community are weakly interconnected._
- **Should `beacon.h ABI structs` be split into smaller, more focused modules?**
  _Cohesion score 0.03333333333333333 - nodes in this community are weakly interconnected._