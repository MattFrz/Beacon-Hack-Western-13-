# Graph Report - Beacon-Hack-Western-13-  (2026-11-22)

## Corpus Check
- 145 files · ~148,260 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 11, .jsonl 3, .css 1)

## Summary
- 1752 nodes · 3928 edges · 86 communities (70 shown, 16 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 244 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- probe_to_world record tests
- probe_frame test suite
- guided law and tests
- vo_core and tests
- bridge package and tests
- beacon.h ABI structs
- merge_vo_world tests
- tape check and calibration tools
- clip generation and ingest tests
- ORT C API shim
- probe_frame cycle internals
- CI workflow
- guided audio output
- supervisor spawn loop
- USB forensics tools
- dashboard App layout
- percept tooling misc
- percept-head shm reader
- live_probe on-device loop
- dashboard package deps
- camera calibration tests
- camd frame pipeline
- dashboard world scene
- ingest JSON parser
- deadline test and platform
- tape_check tests
- bt_speaker playback
- probe_frame sampling tests
- judge-facing docs and pitch
- demo runbook floor pass
- micd USB driver
- probe_frame render preview
- probe_frame record tests
- spec and model research docs
- camd BMP reader
- probe_frame depth sampling
- telemd preview JPEG
- demo runbook live pass
- demo runbook metres and vocab
- QNX integration plan
- dashboard icons and scrubber
- voiced world_in bridge
- guided audio_out PWM
- VO design spec
- dashboard panels and deps
- probe_frame calibration tests
- accessibility evidence docs
- dashboard redesign docs
- beacon_grab sensor reader
- beacon.h pulse codes
- telemd sender
- ingest world writer
- pi bringup and workflow docs
- beacon_cmd stand-in
- QNX plan mechanism stubs
- judge-facing README
- guided law header
- fakeworld stand-in
- probe_frame misc tests
- probe_frame edge tests
- pi test evidence docs
- guided clips loader
- VO plan review focus
- beacon.h guided contracts
- vo_probe tests
- spec review blockers
- dashboard redesign doc
- VO design open items
- device live demo script
- device slay beat script
- probe_frame parser tests
- probe_frame slot tests
- demo runbook failure plays
- device chain demo script
- AI import test script
- depth export tool
- BT audio service
- radio auto-connect script
- run_scenario script
- irl_test script
- pi_live script
- README cross-link
- README cross-link

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
- `Task 2: `vo_probe.py` — CLI over recorded or live walks` --references--> `make_affine()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/probe_frame.py
- `Task 2: `vo_probe.py` — CLI over recorded or live walks` --references--> `predict_depth()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/probe_frame.py
- `Busy-loop cores 1-3 then 0 missed deadlines (the QNX proof)` --semantically_similar_to--> `Full loop closes on QNX (1500 loops, 0 missed, guided speaks)`  [INFERRED] [semantically similar]
  guided/PI_TEST.md → docs/pi-bringup.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Beacon five-process QNX isolation** — docs_nathans_revision_five_process_architecture, docs_nathans_revision_supervisor, docs_nathans_revision_runmask_core0_isolation, docs_nathans_revision_seqlock, docs_nathans_revision_no_aps, docs_pi_bringup_supervisor_verified [EXTRACTED 1.00]
- **Floor pass insurance video path** — docs_demo_runbook_floor_pass, docs_demo_runbook_device_chain_demo_script, docs_demo_runbook_device_slay_beat_script, docs_demo_runbook_thirty_seconds [EXTRACTED 1.00]
- **Live telemetry pipeline: Pi telemd -> UDP 5005 -> bridge -> WebSocket 8765 -> dashboard** — telemd_readme, laptop_bridge_readme, laptop_bridge_wire_format, laptop_dashboard_readme, laptop_samples_readme [EXTRACTED 1.00]
- **Measured on the loaner (submission evidence chain)** — docs_pi_bringup_full_loop_closes, docs_pi_bringup_slay_beat, docs_pi_bringup_supervisor_verified, docs_pi_bringup_live_camera_solved, readme_qnx_story_numbers, docs_devpost_why_qnx [EXTRACTED 1.00]
- **percept vision pipeline (YOLOE, metric depth, hands, honest gating)** — percept_readme, models_readme_yoloe26n, models_readme_depth_anything_v2, models_readme_hand_bake, models_labels_txt, percept_readme_tape_check, percept_readme_live_probe [EXTRACTED 1.00]
- **Recording, replay and dashboard history** — laptop_bridge_recordings, laptop_samples_vid360_replay, laptop_samples_dev_reach, laptop_samples_rebuild_recipe [EXTRACTED 1.00]
- **Spoken-metre gating (tape check before any distance is said aloud)** — percept_readme_tape_check, guided_flags_metres_audio, docs_nathans_revision_tape_check_gate, docs_demo_runbook_metres_decision, docs_devpost_honesty_block [EXTRACTED 1.00]
- **Visual odometry integration (KLT front-end, watchdog, honest failure)** — docs_superpowers_specs_2026_11_21_vo_integration_design_visual_odometry_integration_design, docs_superpowers_specs_vo_klt_frontend, docs_superpowers_specs_vo_scale_watchdog, docs_superpowers_specs_vo_failure_semantics, docs_superpowers_plans_2026_11_21_vo_integration, percept_tools_vo_core, percept_tools_vo_probe [EXTRACTED 1.00]
- **Metres honesty gate before recording** — docs_demo_runbook_metres_decision, docs_demo_runbook_tape_check_option, docs_demo_runbook_metres_removal_option, docs_nathans_revision_tape_check_gate, docs_devpost_honesty_block, guided_flags_metres_audio [INFERRED 0.85]
- **Stand-ins feeding /beacon_world before real percept and voiced** — guided_tools_fakeworld, voiced_world_in, voiced_beacon_cmd, ingest_intent_standin, camd_bmp_bringup [INFERRED 0.85]

## Communities (86 total, 16 thin omitted)

### Community 0 - "probe_to_world record tests"
Cohesion: 0.06
Nodes (22): build_parser(), format_readout(), load_target_names(), main(), _ns(), _number(), _output(), parse_udp_target() (+14 more)

### Community 1 - "probe_frame test suite"
Cohesion: 0.06
Nodes (17): build_parser(), load_yolo_session(), main(), _positive_float_arg(), _positive_int_arg(), parse(), prepare(), probe_once() (+9 more)

### Community 2 - "guided law and tests"
Cohesion: 0.10
Nodes (69): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+61 more)

### Community 3 - "vo_core and tests"
Cohesion: 0.07
Nodes (26): Self-review, Task 6: Integration into the percept cycle and the measured gates, make_affine(), backproject(), _camera_matrix(), chain(), crumb_due(), fit_ground_height() (+18 more)

### Community 4 - "bridge package and tests"
Cohesion: 0.05
Nodes (42): adapterFor(), gapMs(), isV4(), laptopAddresses(), loadReplay(), parseWorld(), startBridge(), collect() (+34 more)

### Community 5 - "beacon.h ABI structs"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 6 - "merge_vo_world tests"
Cohesion: 0.08
Nodes (21): Replay rebuild recipe (probe_to_world + vo_probe + merge_vo_world, rebase t_ns), Anchor, blend_pose(), build_crumbs(), component_median(), first_frame_id(), main(), median() (+13 more)

### Community 7 - "tape check and calibration tools"
Cohesion: 0.08
Nodes (16): World-frame 3D dots plan (dashboard session map), Range 1 tabletop proof gate (same frame_id, tape-checked d_m), vid360 look-around replay (249 lines, real VO pose, six-noun bake), build_parser(), main(), write_calibration(), main(), read_labels() (+8 more)

### Community 8 - "clip generation and ingest tests"
Cohesion: 0.09
Nodes (21): free_udp_port(), hand_at(), main(), find(), record(), wait_for_exit(), main(), make_inflect() (+13 more)

### Community 9 - "ORT C API shim"
Cohesion: 0.06
Nodes (13): api(), _check(), _find_library(), _OrtApiBase, OrtError, _read_ptr(), Session, TensorInfo (+5 more)

### Community 10 - "probe_frame cycle internals"
Cohesion: 0.07
Nodes (22): Task 2: `vo_probe.py` — CLI over recorded or live walks, VO task order: laptop-first core, probe, recorded walk, C++ port, percept cycle, MediaPipe hand_landmarker.task probe (broken pybind11 on QNX), Per-slot depth median stabilisation (IoU slots, jump/evict/recover gates), _box_bounds(), _box_iou(), Calibration, guess_calibration() (+14 more)

### Community 11 - "CI workflow"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 12 - "guided audio output"
Cohesion: 0.11
Nodes (30): audio_dropped_speech(), audio_main(), audio_publish_stats(), audio_start(), audio_stop(), audio_submit(), law_name(), mode_name() (+22 more)

### Community 13 - "supervisor spawn loop"
Cohesion: 0.09
Nodes (21): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), CLAUDE.md (imports AGENTS.md), How QNX is used (Devpost section with measured numbers), Supervisor contract (spawn with scheduler attributes, 50 ms pulse heartbeat, respawn backoff), Supervisor to spec, verified on the loaner (58f/40f/22r, respawn ~100 ms), add_argv(), add_argv_line() (+13 more)

### Community 14 - "USB forensics tools"
Cohesion: 0.11
Nodes (10): dump_ep_ctx(), ep_type_name(), main(), map_mmio(), main(), mp(), main(), mp() (+2 more)

### Community 15 - "dashboard App layout"
Cohesion: 0.13
Nodes (35): Dashboard layout (floating top bar, sliding panels, replay scrubber, reduced-motion), Ago(), agoText(), App(), BOTH, Camera(), Caption(), DataSource() (+27 more)

### Community 16 - "percept tooling misc"
Cohesion: 0.09
Nodes (16): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout(), clean() (+8 more)

### Community 17 - "percept-head shm reader"
Cohesion: 0.07
Nodes (26): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+18 more)

### Community 18 - "live_probe on-device loop"
Cohesion: 0.09
Nodes (13): build_parser(), capture_memory(), gate_by_depth(), inject_memory(), _install_depth_capture(), lift_hand(), main(), _make_vo() (+5 more)

### Community 19 - "dashboard package deps"
Cohesion: 0.08
Nodes (32): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, @fontsource/ibm-plex-mono@^5.3.0, @fontsource/ibm-plex-sans@^5.3.0, motion@^14.14.0, react-aria-components@^1.22.1, react-dom@^19.3.1 (+24 more)

### Community 20 - "camera calibration tests"
Cohesion: 0.10
Nodes (8): calibrate_images(), capture_frames(), find_corners(), make_calibration(), CalibrateCameraTest, synthetic_view(), write_synthetic_views(), write_board()

### Community 21 - "camd frame pipeline"
Cohesion: 0.08
Nodes (26): main(), put_u16(), put_u32(), write_bmp(), beacon_crumb_t, beacon_depth_t, beacon_frame_slot_t, beacon_guided_block_t (+18 more)

### Community 22 - "dashboard world scene"
Cohesion: 0.21
Nodes (22): COLORS, Frustum(), isNum(), Marker(), norm(), Scene(), crumbsToScene(), displayPose() (+14 more)

### Community 23 - "ingest JSON parser"
Cohesion: 0.30
Nodes (21): jalloc(), jarr_at(), jarray(), jis(), jnew(), jnum(), jnumber(), jobj_get() (+13 more)

### Community 24 - "deadline test and platform"
Cohesion: 0.14
Nodes (11): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), main(), platform_heartbeat(), platform_piezo_init() (+3 more)

### Community 25 - "tape_check tests"
Cohesion: 0.28
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 26 - "bt_speaker playback"
Cohesion: 0.13
Nodes (10): BTstack A2DP bridge to JBL Go 3 (validated, boot-persistent), main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm() (+2 more)

### Community 27 - "probe_frame sampling tests"
Cohesion: 0.20
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 28 - "judge-facing docs and pitch"
Cohesion: 0.11
Nodes (10): Metres option 2: remove --metres from the three scripts and speak bearing only, Early safety disclosure: supplement to the cane, not a replacement, Metres option 1: tape check at 1 m, accept under 30 percent error, Remembered-row bind window (20 s, amended 2026-11-22), 30-second Sunday demo script (spec section 12), The QNX beat on hardware (slay ingest, LOST, recovery, guided never restarted), guided --metres (tape-gated) and --audio outputs (none, wav, fifo, qnx), Depth Anything V2 Metric Indoor Small ONNX (static 210x210, external .onnx.data) (+2 more)

### Community 29 - "demo runbook floor pass"
Cohesion: 0.19
Nodes (17): Demo runbook: Best Use of QNX, A3 open: pidin ar captured with ORT live and saved to docs/pi-bringup.md, A5: slay live_probe perception producer; guided goes HOLD then LOST with deadline record unbroken, A5 open: live perception producer killed twice on hardware, A6 open: metres decision executed, tape check logged or --metres removed from three scripts, C270 one-time sensor setup: usb_camera jpeg, no create_window, memory_allocator_type from_sensor, Two passes, floor first: floor pass on the Pi, Floor video open: a take exists with the JBL audible (+9 more)

### Community 30 - "micd USB driver"
Cohesion: 0.24
Nodes (14): completion(), desc_at(), find_audio_stream(), insertion(), logf_(), main(), now_elapsed(), put16() (+6 more)

### Community 31 - "probe_frame render preview"
Cohesion: 0.15
Nodes (6): _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), _median_depth(), DepthSamplingTest

### Community 32 - "probe_frame record tests"
Cohesion: 0.18
Nodes (4): crop_depth_padding(), _draw_boxes(), render_preview(), RenderPreviewTest

### Community 33 - "spec and model research docs"
Cohesion: 0.11
Nodes (13): Beacon Accessibility Research (BLV evidence brief), Open-vocab model research for Pi 5 CPU, Devpost paste-ready description, Beacon (chest-worn named-object homing device), Pitch language table (no cure framing, supplement to the cane, sighted team), Saturday Build Order (spec section 13, steps 1-6), Beacon: Nathan's revision (spec), QNXE-1894 Wi-Fi settings copy gate (workaround: cat provisioning copies onto /data every boot) (+5 more)

### Community 34 - "camd BMP reader"
Cohesion: 0.25
Nodes (12): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+4 more)

### Community 35 - "probe_frame depth sampling"
Cohesion: 0.28
Nodes (8): Affine, detect(), detect_yolo_ort(), find_fingertip(), letterbox(), predict_depth(), tensor_scalar(), process()

### Community 36 - "telemd preview JPEG"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 37 - "demo runbook live pass"
Cohesion: 0.20
Nodes (7): 0 to 8s: FIND arrives as a record on the laptop and JBL speaks bearing; earns S7, S8, 8 to 16s: wearer walks toward object and cue repeats from sensors; earns S2, S6, 16 to 24s: slay the perception producer, cue holds then says I lost the target, no distance spoken; earns S1, S4, 24 to 30s: supervisor respawns producer and cue returns, then BT audio service is killed and returns on its own; earns S1, S6, Camera table setup: phone on tripod, JBL Go 3, wearer's hand, SSH terminal visible; JBL audible in recording, The 30 seconds: demo and Devpost video beats, guided 16.67 ms synthesizer loop (CLOCK_MONOTONIC, no blocking writes)

### Community 38 - "demo runbook metres and vocab"
Cohesion: 0.19
Nodes (11): Ultralytics AGPL-3.0 licence risk (fine for a hackathon build, say so if asked), Chain replay expected: WALK cue three times, mode LIVE then HOLD, 1500 loops, 0 missed deadlines, worst 4.7 ms, p95 1.9 ms, sh ingest/tools/device_chain_demo.sh /tmp/replay.avi bottle, sh ingest/tools/device_slay_beat.sh /tmp/long.avi bottle, Target must be in the six-noun bake: bottle, can, keys, phone, box, mouse, Slay-beat expected records: 1800 loops and 0 missed before, 2100 loops and 0 missed with p95 2.05 ms after fresh ingest, Slay-beat sequence A-D: live cue, slay ingest and lost target, post-death readout, fresh ingest restores cue with guided never restarted, Baked noun list (6 today, 64 max, no runtime retraining) (+3 more)

### Community 39 - "QNX integration plan"
Cohesion: 0.15
Nodes (13): 1.3 QNX-mechanism stubs (the pitch vs the code), 2. Plan, Step 0 — Mentor ask (Nathan, 15 min, now, blocks everything), Step 1 — Runtime on the Pi (Nathan, 45 min hard box), Step 2 — A real frame into `/beacon_frames` (Nathan, 60 min), Step 3 — `percept` on the Pi (Nathan, 60 min), Step 4 — `ingest`: the missing wire (Munadir or Nathan, 60 min, can start on laptop now), Step 5 — Audio out + piezo (Munadir + Matt, parallel, 60 min) (+5 more)

### Community 40 - "dashboard icons and scrubber"
Cohesion: 0.32
Nodes (11): ChevronLeft(), ChevronRight(), Collapse(), Expand(), Icon(), Panel(), PanelLeftClose(), PanelLeftOpen() (+3 more)

### Community 41 - "voiced world_in bridge"
Cohesion: 0.33
Nodes (11): apply(), find_key(), get_id(), get_num(), get_str(), get_vecn(), main(), publish() (+3 more)

### Community 42 - "guided audio_out PWM"
Cohesion: 0.29
Nodes (9): audio_out_close(), audio_out_open(), audio_out_write(), fifo_try_open(), fifo_write(), put16(), put32(), qnx_open() (+1 more)

### Community 43 - "VO design spec"
Cohesion: 0.17
Nodes (11): Three ranges (REACH ships without VO; Range 3 needs pose), Accuracy ruling (Nathan, 2026-11-21, after the 360-degree clip demo), Anti-goals (what would make this a failure even if it works), Approaches considered (team decision 2026-11-21), Constraints (measured facts, not targets), Goals, Intent, Non-goals (+3 more)

### Community 44 - "dashboard panels and deps"
Cohesion: 0.26
Nodes (9): react@^19.3.1, SourceSwitch(), clock(), Events(), Sidebar(), SyncMobile(), Tip(), @animate-ui/react (+1 more)

### Community 45 - "probe_frame calibration tests"
Cohesion: 0.23
Nodes (3): _SlotState, SlotTracker, SlotTrackerTest

### Community 46 - "accessibility evidence docs"
Cohesion: 0.20
Nodes (7): A2: slay the BT audio service process and the service script brings the speaker back, BT service kill/restart rehearsal open: speaker comes back on its own in a run, JBL silent: check the BT service bt_speaker.py path before judging and keep the slay-restart beat, guided audio thread (prio 40, speech ring, newest-wins tick/tone slot), Kokoro-82M voice clips rendered by llama.cpp TTS (make_clips.py), Turn-toward orientation pips and rising chime (guided ADDITION), sounds (pre-rendered 16 kHz clip set, one WAV per clip id)

### Community 47 - "dashboard redesign docs"
Cohesion: 0.27
Nodes (9): Live | Replay bridge switching (UDP 5005 always open, status frame once a second), bridge (Node UDP-to-WebSocket relay and recorder), Session recording to recordings/<UTC>.jsonl (video never written to disk), Beacon dashboard index.html, dashboard (Vite + React + three.js remote monitor), dev-reach.jsonl (walk, reach, slay percept -> HOLD -> LOST stopgap replay), Field notes (t_ns is CLOCK_MONOTONIC, mode recomputed by telemd, guided owns target), Telemetry format (world state ~10 Hz + JPEG ~5 fps to UDP 5005) (+1 more)

### Community 48 - "beacon_grab sensor reader"
Cohesion: 0.24
Nodes (4): find_eoi(), now_ns(), on_data(), write_atomic()

### Community 49 - "beacon.h pulse codes"
Cohesion: 0.18
Nodes (11): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+3 more)

### Community 50 - "telemd sender"
Cohesion: 0.33
Nodes (8): beacon_live_max_ns(), append(), append_scene(), escape_name(), heartbeat_alive(), main(), snapshot(), vector_json()

### Community 51 - "ingest world writer"
Cohesion: 0.33
Nodes (8): beacon_world_t, apply_sched(), attach_block(), main(), open_world(), parse_intent(), usage(), write_intent()

### Community 52 - "pi bringup and workflow docs"
Cohesion: 0.20
Nodes (8): BMP bring-up frame source (frametype 65535, not a camera driver), camd (camera daemon, Sensor Framework into the frame ring), Loaner Pi bring-up log (dated evidence rows), Pi development workflow (QNX 8.0 read-only IFS, /data survives), Gap table against the prize hard requirements, QNX findings F1-F9 (OpenCV module gate, keyframe from in-process copy, 1 ms clock), micd gotchas (TRB ring leak on resubmit, VBUS power-cycle, QNX getopt parsing), telemd-preview (optional downscaled JPEG path, expires without the camera)

### Community 53 - "beacon_cmd stand-in"
Cohesion: 0.31
Nodes (6): add(), handle(), is_skip(), kind_name(), main(), world_open()

### Community 54 - "QNX plan mechanism stubs"
Cohesion: 0.20
Nodes (9): 1.1 What laptop work has achieved (all true, all on the wrong machine), 1.2 Gap table against the prize hard requirements, 1.4 The real-time claim needs re-scoping, 1.5 Cuts already made or to be made now, 1.6 Small risks that will burn an hour at the worst moment, 1. Findings, 3. Ownership + order of attack (parallel tracks), 4. What "done" means at 8 am Sunday (+1 more)

### Community 55 - "judge-facing README"
Cohesion: 0.20
Nodes (8): Build / test, ingest, Known limits (deliberate), Usage, What it writes (and never writes), live_probe.py on-device loop (grabber to latest.jpg, UDP 5006, --max-depth gate), supervisor --beacon (spawn table, pulse timer, respawn backoff), world_in fallback bridge (laptop probe drives guided on the Pi)

### Community 56 - "guided law header"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 57 - "fakeworld stand-in"
Cohesion: 0.42
Nodes (7): drop_crumb(), lerp(), main(), put_hand(), put_object(), set_pose_yaw(), world_from_cam()

### Community 60 - "pi test evidence docs"
Cohesion: 0.29
Nodes (4): Full loop closes on QNX (1500 loops, 0 missed, guided speaks), Bluetooth HFP capture as the working mic path (GPIO28 is the Wi-Fi rail, never toggle), micd (C270 UAC1 mic capture on QNX, work in progress), Status: what runs on the loaner and what does not (README section)

### Community 61 - "guided clips loader"
Cohesion: 0.43
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 62 - "VO plan review focus"
Cohesion: 0.25
Nodes (7): Global Constraints, Review Focus, Task 1: `vo_core.py` — the geometry core with synthetic tests, Task 3: Record a real L-walk and tune, Task 4: On-device OpenCV gate — the A/B decision (spec F1), Task 5: `vo.hpp` / `vo.cpp` — the C++ port, VO Integration Implementation Plan

### Community 63 - "beacon.h guided contracts"
Cohesion: 0.25
Nodes (8): beacon_pulse, BEACON_PULSE_AUDIO_UNDERRUN, BEACON_PULSE_HB_CAMD, BEACON_PULSE_HB_GUIDED, BEACON_PULSE_HB_PERCEPT, BEACON_PULSE_HB_VOICED, BEACON_PULSE_INTENT_EDGE, BEACON_PULSE_SUP_TICK

### Community 65 - "spec review blockers"
Cohesion: 0.29
Nodes (6): Beacon spec adversarial review, Merge verdict: BLOCK, Regenerating a review diff, Review verdicts, Where things are, Working notes (not shipped)

### Community 66 - "dashboard redesign doc"
Cohesion: 0.29
Nodes (7): Dashboard redesign and live Pi connection, Graph, Live Raspberry Pi connection, Running it against the Pi, Still open, What actually ran on the Pi, What changed

### Community 67 - "VO design open items"
Cohesion: 0.29
Nodes (7): Failure semantics (unchanged from §8, restated as contract), Per VO step (~every 100 ms; every 3rd ring frame at 30 fps), Scheduling, State (per-process, not shm), The design, What "done and trusted" means (acceptance gates), Where it lives

### Community 68 - "device live demo script"
Cohesion: 0.40
Nodes (5): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_live_demo.sh script, slay_matching()

### Community 69 - "device slay beat script"
Cohesion: 0.40
Nodes (5): kill_matching(), LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_slay_beat.sh script

### Community 72 - "demo runbook failure plays"
Cohesion: 0.50
Nodes (5): C270 wedged after USB crash: power-cycle with sudo -n gpio-rp1 set 42 op pn dl, wait about 5 s, then set 42 a2 pn / set 43 a2 pu, Dashboard dies: irrelevant to the demo; do not stop, Failure plays: things that have already broken once, with the fix that worked, Live perception too slow or missing frames: fall back to replay clip scripts, USB stack dies: sudo -n sh /usr/etc/usb_start.sh, restart sensor and beacon_grab; no reboot

### Community 73 - "device chain demo script"
Cohesion: 0.40
Nodes (4): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_chain_demo.sh script

### Community 74 - "AI import test script"
Cohesion: 0.50
Nodes (3): LD_LIBRARY_PATH, PYTHONPATH, ai-import-test.sh script

## Knowledge Gaps
- **157 isolated node(s):** `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE`, `BEACON_MODE_LOST`, `BEACON_MODE_NONE`, `BEACON_CLIP_A_LITTLE` (+152 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 586 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `bridge (Node UDP-to-WebSocket relay and recorder)` connect `dashboard redesign docs` to `spec and model research docs`, `pi bringup and workflow docs`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BEACON_MODE_HOLD`, `BEACON_MODE_LIVE`, `BEACON_MODE_LOST` to the rest of the system?**
  _157 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `probe_to_world record tests` be split into smaller, more focused modules?**
  _Cohesion score 0.056179775280898875 - nodes in this community are weakly interconnected._
- **Why does `Beacon dashboard index.html` connect `dashboard redesign docs` to `dashboard App layout`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `probe_frame test suite` be split into smaller, more focused modules?**
  _Cohesion score 0.05864197530864197 - nodes in this community are weakly interconnected._