# Graph Report - beacon  (2026-11-22)

## Corpus Check
- 150 files · ~157,262 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 11, .jsonl 3, .css 1)

## Summary
- 1832 nodes · 4109 edges · 95 communities (74 shown, 21 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 251 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d59a25c6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- probe_to_world
- App.jsx
- guided_step
- vo_core_test.py
- bridge.test.js
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- probe_to_world
- cv2
- make_clips.py
- probe_frame.py
- probe_frame.py
- audio.c
- audio.c
- probe_to_world
- telemd.c
- test_beacon.py
- test_frame_id_seed.py
- argparse
- beacon_intent_kind
- guided synthesizer (FIFO 58, core 0)
- deadline_test.c
- beacon_intent_kind
- beacon_pulse
- json.c
- string
- TapeCheckTest
- bt_speaker.py
- DepthStabiliser
- beacon.h
- main
- Scene.jsx
- merge_vo_world.py
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- probe_frame.py
- camd/src/main.c
- Any
- camd/src/main.c
- Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)
- Model Files Directory (not committed)
- 2. Plan
- time
- ingest/src/main.c
- tape_check.py
- beacon.h
- audio_out.c
- gen_ort_capi_table.py
- time
- Live Camera and 3D Work Summary
- telemd.c
- os
- ProbeRuntimeTest
- ingest/src/main.c
- probe_once
- ProbeRuntimeTest
- ort_shim.py
- qnx_pkg_fetch.py
- qnxpi Target (QNX 8.0 Raspberry Pi 5)
- fakeworld.c
- FakeFileCapture
- Beacon: Nathan's revision (spec)
- Beacon Accessibility Research
- bt_audio_service.sh
- test_ingest.py
- Beacon five-process QNX isolation
- Anchor
- Review Focus
- place_hand
- make-dev-reach.test.js
- .test_capture_frames_prompts_between_views
- beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)
- /beacon_frames Newest-wins Three-slot Ring
- FakeFileCapture
- export_yoloe.py
- Honest LOST Cue (no invented metres)
- test_frame_id_seed.py
- make_clip
- Inclusive Language and Non-Cure Framing
- make-dev-reach.test.js
- beacon_pulse
- Beacon (chest-worn item-homing wearable)
- device_live_demo.sh
- device_slay_beat.sh
- device_chain_demo.sh
- supervisor tests (make test, make test-beacon: kill, stale beat, backoff reset)
- math
- beacon_grab.c
- SlotTracker
- run_live.sh
- camd (camera daemon, Sensor Framework into the frame ring)
- Visual odometry integration design
- vo_core.py
- build_parser
- FakeInferenceSession

## God Nodes (most connected - your core abstractions)
1. `beacon_clip` - 60 edges
2. `probe_to_world()` - 47 edges
3. `guided_step()` - 43 edges
4. `probe_once()` - 38 edges
5. `make_probe()` - 37 edges
6. `ProbeRuntimeTest` - 34 edges
7. `ProbeToWorldTest` - 33 edges
8. `App()` - 32 edges
9. `prepare()` - 27 edges
10. `main()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `What changed` --references--> `targetObjectId()`  [INFERRED]
  docs/dashboard-redesign.md → laptop/dashboard/src/worldScene.js
- `Where it lives` --references--> `Vo`  [INFERRED]
  docs/superpowers/specs/2026-11-21-vo-integration-design.md → percept/tools/vo_core.py
- `Update: 3D follows the camera (branch `zain/3d-follows-camera`)` --references--> `LiveVo`  [INFERRED]
  docs/live-camera-3d-session-summary.md → percept/tools/live_vo.py
- `Update: 3D follows the camera (branch `zain/3d-follows-camera`)` --references--> `apply_pose()`  [INFERRED]
  docs/live-camera-3d-session-summary.md → percept/tools/live_vo.py
- `Task 2: `vo_probe.py` — CLI over recorded or live walks` --references--> `make_affine()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/probe_frame.py

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

## Communities (95 total, 21 thin omitted)

### Community 0 - "probe_to_world"
Cohesion: 0.06
Nodes (22): build_parser(), format_readout(), load_target_names(), main(), _ns(), _number(), _output(), parse_udp_target() (+14 more)

### Community 1 - "App.jsx"
Cohesion: 0.12
Nodes (6): prepare(), ProbeRuntimeTest, fake_encode(), synthetic_probe_modules(), synthetic_video_modules(), emit_lines()

### Community 2 - "guided_step"
Cohesion: 0.10
Nodes (69): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_t, guided_default_cfg(), guided_dir_cat() (+61 more)

### Community 3 - "vo_core_test.py"
Cohesion: 0.18
Nodes (10): make_affine(), keyframe_due(), camera_matrix(), make_metres(), make_texture(), make_vo(), rotation_angle_deg(), VoCoreTests (+2 more)

### Community 4 - "bridge.test.js"
Cohesion: 0.08
Nodes (30): adapterFor(), gapMs(), isV4(), laptopAddresses(), loadReplay(), parseWorld(), startBridge(), collect() (+22 more)

### Community 5 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 6 - "probe_to_world"
Cohesion: 0.21
Nodes (7): MergeTests, rec(), person_at(), record_with(), T(), vo_record(), world_record()

### Community 7 - "cv2"
Cohesion: 0.09
Nodes (9): main(), apply_pose(), LiveVo, ApplyPose, FollowsCamera, _to_world(), load(), main() (+1 more)

### Community 8 - "make_clips.py"
Cohesion: 0.18
Nodes (7): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips()

### Community 9 - "probe_frame.py"
Cohesion: 0.07
Nodes (12): api(), _check(), _find_library(), _OrtApiBase, OrtError, _read_ptr(), Session, TensorInfo (+4 more)

### Community 10 - "probe_frame.py"
Cohesion: 0.09
Nodes (20): Task 2: `vo_probe.py` — CLI over recorded or live walks, VO task order: laptop-first core, probe, recorded walk, C++ port, percept cycle, MediaPipe hand_landmarker.task probe (broken pybind11 on QNX), Per-slot depth median stabilisation (IoU slots, jump/evict/recover gates), Calibration, guess_calibration(), load_calibration(), load_depth_session() (+12 more)

### Community 11 - "audio.c"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 12 - "audio.c"
Cohesion: 0.13
Nodes (29): publish_frame(), audio_dropped_speech(), audio_main(), audio_publish_stats(), audio_start(), audio_stop(), audio_submit(), law_name() (+21 more)

### Community 13 - "probe_to_world"
Cohesion: 0.16
Nodes (15): add_argv(), add_argv_line(), allow_priorities(), beacon_children(), create_region(), depth_name(), describe(), ensure_regions() (+7 more)

### Community 14 - "telemd.c"
Cohesion: 0.11
Nodes (10): dump_ep_ctx(), ep_type_name(), main(), map_mmio(), main(), mp(), main(), mp() (+2 more)

### Community 15 - "test_beacon.py"
Cohesion: 0.12
Nodes (37): Dashboard layout (floating top bar, sliding panels, replay scrubber, reduced-motion), Ago(), agoText(), App(), BOTH, Camera(), Caption(), DataSource() (+29 more)

### Community 16 - "test_frame_id_seed.py"
Cohesion: 0.29
Nodes (7): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout()

### Community 17 - "argparse"
Cohesion: 0.07
Nodes (27): beacon_frames_t, Affine, full_h, full_w, net_h, net_w, pad_x, pad_y (+19 more)

### Community 18 - "beacon_intent_kind"
Cohesion: 0.07
Nodes (17): build_parser(), capture_memory(), drop_hand_lookalikes(), gate_by_depth(), inject_memory(), _install_depth_capture(), _iou(), lift_hand() (+9 more)

### Community 19 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.08
Nodes (34): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, @fontsource/ibm-plex-mono@^5.3.0, @fontsource/ibm-plex-sans@^5.3.0, motion@^14.14.0, react@^19.3.1, react-aria-components@^1.22.1 (+26 more)

### Community 20 - "deadline_test.c"
Cohesion: 0.10
Nodes (8): calibrate_images(), capture_frames(), find_corners(), make_calibration(), CalibrateCameraTest, synthetic_view(), write_synthetic_views(), write_board()

### Community 21 - "beacon_intent_kind"
Cohesion: 0.07
Nodes (26): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+18 more)

### Community 22 - "beacon_pulse"
Cohesion: 0.18
Nodes (27): COLORS, Frustum(), isNum(), LabelVisibility(), Marker(), norm(), Scene(), crumbsToScene() (+19 more)

### Community 23 - "json.c"
Cohesion: 0.30
Nodes (21): jalloc(), jarr_at(), jarray(), jis(), jnew(), jnum(), jnumber(), jobj_get() (+13 more)

### Community 24 - "string"
Cohesion: 0.14
Nodes (11): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), main(), platform_heartbeat(), platform_piezo_init() (+3 more)

### Community 25 - "TapeCheckTest"
Cohesion: 0.28
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 26 - "bt_speaker.py"
Cohesion: 0.13
Nodes (10): BTstack A2DP bridge to JBL Go 3 (validated, boot-persistent), main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm() (+2 more)

### Community 27 - "DepthStabiliser"
Cohesion: 0.22
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 28 - "beacon.h"
Cohesion: 0.12
Nodes (9): Metres option 2: remove --metres from the three scripts and speak bearing only, Metres option 1: tape check at 1 m, accept under 30 percent error, Remembered-row bind window (20 s, amended 2026-11-22), 30-second Sunday demo script (spec section 12), The QNX beat on hardware (slay ingest, LOST, recovery, guided never restarted), guided --metres (tape-gated) and --audio outputs (none, wav, fifo, qnx), Depth Anything V2 Metric Indoor Small ONNX (static 210x210, external .onnx.data), beacon_cmd typed-command stand-in (writes exactly what voiced will write) (+1 more)

### Community 29 - "main"
Cohesion: 0.17
Nodes (17): Demo runbook: Best Use of QNX, A3 open: pidin ar captured with ORT live and saved to docs/pi-bringup.md, A5: slay live_probe perception producer; guided goes HOLD then LOST with deadline record unbroken, A5 open: live perception producer killed twice on hardware, A6 open: metres decision executed, tape check logged or --metres removed from three scripts, BT service kill/restart rehearsal open: speaker comes back on its own in a run, C270 one-time sensor setup: usb_camera jpeg, no create_window, memory_allocator_type from_sensor, Two passes, floor first: floor pass on the Pi (+9 more)

### Community 30 - "Scene.jsx"
Cohesion: 0.24
Nodes (14): completion(), desc_at(), find_audio_stream(), insertion(), logf_(), main(), now_elapsed(), put16() (+6 more)

### Community 31 - "merge_vo_world.py"
Cohesion: 0.19
Nodes (11): Replay rebuild recipe (probe_to_world + vo_probe + merge_vo_world, rebase t_ns), blend_pose(), build_crumbs(), first_frame_id(), main(), median(), merge(), read_jsonl() (+3 more)

### Community 32 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.18
Nodes (4): crop_depth_padding(), _draw_boxes(), render_preview(), RenderPreviewTest

### Community 33 - "probe_frame.py"
Cohesion: 0.08
Nodes (19): Beacon Accessibility Research (BLV evidence brief), Open-vocab model research for Pi 5 CPU, Beacon spec adversarial review, Merge verdict: BLOCK, Devpost paste-ready description, Beacon (chest-worn named-object homing device), Pitch language table (no cure framing, supplement to the cane, sighted team), Saturday Build Order (spec section 13, steps 1-6) (+11 more)

### Community 34 - "camd/src/main.c"
Cohesion: 0.27
Nodes (10): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), read_le32(), seed_next_frame_id(), set_fifo() (+2 more)

### Community 35 - "Any"
Cohesion: 0.11
Nodes (15): Affine, _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), detect(), detect_yolo_ort(), find_fingertip() (+7 more)

### Community 36 - "camd/src/main.c"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 37 - "Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)"
Cohesion: 0.29
Nodes (7): 0 to 8s: FIND arrives as a record on the laptop and JBL speaks bearing; earns S7, S8, 8 to 16s: wearer walks toward object and cue repeats from sensors; earns S2, S6, 16 to 24s: slay the perception producer, cue holds then says I lost the target, no distance spoken; earns S1, S4, 24 to 30s: supervisor respawns producer and cue returns, then BT audio service is killed and returns on its own; earns S1, S6, Camera table setup: phone on tripod, JBL Go 3, wearer's hand, SSH terminal visible; JBL audible in recording, The 30 seconds: demo and Devpost video beats, guided 16.67 ms synthesizer loop (CLOCK_MONOTONIC, no blocking writes)

### Community 38 - "Model Files Directory (not committed)"
Cohesion: 0.19
Nodes (11): Ultralytics AGPL-3.0 licence risk (fine for a hackathon build, say so if asked), Chain replay expected: WALK cue three times, mode LIVE then HOLD, 1500 loops, 0 missed deadlines, worst 4.7 ms, p95 1.9 ms, sh ingest/tools/device_chain_demo.sh /tmp/replay.avi bottle, sh ingest/tools/device_slay_beat.sh /tmp/long.avi bottle, Replay clip re-record open: clear object at about 1 m that clears conf 0.15 at default lighting, Target must be in the six-noun bake: bottle, can, keys, phone, box, mouse, Slay-beat expected records: 1800 loops and 0 missed before, 2100 loops and 0 missed with p95 2.05 ms after fresh ingest, Slay-beat sequence A-D: live cue, slay ingest and lost target, post-death readout, fresh ingest restores cue with guided never restarted (+3 more)

### Community 39 - "2. Plan"
Cohesion: 0.06
Nodes (30): 1.1 What laptop work has achieved (all true, all on the wrong machine), 1.2 Gap table against the prize hard requirements, 1.3 QNX-mechanism stubs (the pitch vs the code), 1.4 The real-time claim needs re-scoping, 1.5 Cuts already made or to be made now, 1.6 Small risks that will burn an hour at the worst moment, 1. Findings, 2. Plan (+22 more)

### Community 40 - "time"
Cohesion: 0.19
Nodes (17): SourceSwitch(), ChevronLeft(), ChevronRight(), Collapse(), Expand(), Icon(), Panel(), PanelLeftClose() (+9 more)

### Community 41 - "ingest/src/main.c"
Cohesion: 0.33
Nodes (11): apply(), find_key(), get_id(), get_num(), get_str(), get_vecn(), main(), publish() (+3 more)

### Community 42 - "tape_check.py"
Cohesion: 0.26
Nodes (8): Range 1 tabletop proof gate (same frame_id, tape-checked d_m), build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction(), _vec3()

### Community 43 - "beacon.h"
Cohesion: 0.10
Nodes (19): main(), put_u16(), put_u32(), write_bmp(), beacon_crumb_t, beacon_depth_t, beacon_frame_slot_t, beacon_guided_block_t (+11 more)

### Community 44 - "audio_out.c"
Cohesion: 0.29
Nodes (9): audio_out_close(), audio_out_open(), audio_out_write(), fifo_try_open(), fifo_write(), put16(), put32(), qnx_open() (+1 more)

### Community 45 - "gen_ort_capi_table.py"
Cohesion: 0.33
Nodes (5): clean(), ctype_of(), expand(), main(), split_args()

### Community 46 - "time"
Cohesion: 0.15
Nodes (11): A2: slay the BT audio service process and the service script brings the speaker back, C270 wedged after USB crash: power-cycle with sudo -n gpio-rp1 set 42 op pn dl, wait about 5 s, then set 42 a2 pn / set 43 a2 pu, Dashboard dies: irrelevant to the demo; do not stop, Failure plays: things that have already broken once, with the fix that worked, JBL silent: check the BT service bt_speaker.py path before judging and keep the slay-restart beat, Live perception too slow or missing frames: fall back to replay clip scripts, USB stack dies: sudo -n sh /usr/etc/usb_start.sh, restart sensor and beacon_grab; no reboot, guided audio thread (prio 40, speech ring, newest-wins tick/tone slot) (+3 more)

### Community 47 - "Live Camera and 3D Work Summary"
Cohesion: 0.08
Nodes (25): Dashboard redesign and live Pi connection, Graph, Live Raspberry Pi connection, Live | Replay bridge switching (UDP 5005 always open, status frame once a second), Running it against the Pi, Still open, What actually ran on the Pi, What changed (+17 more)

### Community 48 - "telemd.c"
Cohesion: 0.35
Nodes (8): beacon_live_max_ns(), append(), append_scene(), escape_name(), heartbeat_alive(), main(), snapshot(), vector_json()

### Community 49 - "os"
Cohesion: 0.40
Nodes (6): alive(), lines(), main(), pids(), wait_for(), wait_for_pid()

### Community 51 - "ingest/src/main.c"
Cohesion: 0.14
Nodes (11): open_world(), sleep_until(), beacon_world_t, apply_sched(), attach_block(), main(), open_world(), parse_intent() (+3 more)

### Community 53 - "ProbeRuntimeTest"
Cohesion: 0.35
Nodes (9): add(), handle(), html_escape(), is_skip(), kind_name(), main(), send_all(), serve_http() (+1 more)

### Community 55 - "qnx_pkg_fetch.py"
Cohesion: 0.25
Nodes (4): dep_names(), main(), parse_index(), version_gt()

### Community 56 - "qnxpi Target (QNX 8.0 Raspberry Pi 5)"
Cohesion: 0.22
Nodes (9): guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH, GUIDED_CMD_NONE, GUIDED_CMD_PIP, GUIDED_CMD_SAY, GUIDED_CMD_TICK, GUIDED_CMD_TONE_OFF (+1 more)

### Community 57 - "fakeworld.c"
Cohesion: 0.42
Nodes (7): drop_crumb(), lerp(), main(), put_hand(), put_object(), set_pose_yaw(), world_from_cam()

### Community 60 - "Beacon Accessibility Research"
Cohesion: 0.20
Nodes (5): Early safety disclosure: supplement to the cane, not a replacement, Full loop closes on QNX (1500 loops, 0 missed, guided speaks), Bluetooth HFP capture as the working mic path (GPIO28 is the Wi-Fi rail, never toggle), micd (C270 UAC1 mic capture on QNX, work in progress), Status: what runs on the loaner and what does not (README section)

### Community 61 - "bt_audio_service.sh"
Cohesion: 0.43
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 62 - "test_ingest.py"
Cohesion: 0.22
Nodes (8): free_udp_port(), hand_at(), main(), find(), record(), wait_for_exit(), supervise(), wait_for()

### Community 63 - "Beacon five-process QNX isolation"
Cohesion: 0.28
Nodes (4): How QNX is used (Devpost section with measured numbers), Supervisor contract (spawn with scheduler attributes, 50 ms pulse heartbeat, respawn backoff), Supervisor to spec, verified on the loaner (58f/40f/22r, respawn ~100 ms), supervisor --beacon (spawn table, pulse timer, respawn backoff)

### Community 65 - "Review Focus"
Cohesion: 0.29
Nodes (7): Global Constraints, Review Focus, Task 1: `vo_core.py` — the geometry core with synthetic tests, Task 3: Record a real L-walk and tune, Task 4: On-device OpenCV gate — the A/B decision (spec F1), Task 5: `vo.hpp` / `vo.cpp` — the C++ port, VO Integration Implementation Plan

### Community 66 - "place_hand"
Cohesion: 0.31
Nodes (4): _boxes_touch(), place_hand(), PlaceHandTest, world()

### Community 67 - "make-dev-reach.test.js"
Cohesion: 0.11
Nodes (16): captionFromClips(), CLIP_NAMES, CLIPS, clock(), Events(), eventsFromLog(), texts(), bounds (+8 more)

### Community 68 - ".test_capture_frames_prompts_between_views"
Cohesion: 0.40
Nodes (5): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_live_demo.sh script, slay_matching()

### Community 69 - "beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)"
Cohesion: 0.40
Nodes (5): kill_matching(), LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_slay_beat.sh script

### Community 73 - "Honest LOST Cue (no invented metres)"
Cohesion: 0.40
Nodes (4): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_chain_demo.sh script

### Community 74 - "test_frame_id_seed.py"
Cohesion: 0.50
Nodes (3): LD_LIBRARY_PATH, PYTHONPATH, ai-import-test.sh script

### Community 87 - "math"
Cohesion: 0.12
Nodes (7): World-frame 3D dots plan (dashboard session map), vid360 look-around replay (249 lines, real VO pose, six-noun bake), build_parser(), main(), write_calibration(), write_jsonl(), FakeSessionOptions

### Community 88 - "beacon_grab.c"
Cohesion: 0.31
Nodes (4): find_eoi(), now_ns(), on_data(), write_atomic()

### Community 89 - "SlotTracker"
Cohesion: 0.19
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 91 - "run_live.sh"
Cohesion: 0.40
Nodes (4): BEACON_CMD, PERCEPT, REPO, run_live.sh script

### Community 92 - "camd (camera daemon, Sensor Framework into the frame ring)"
Cohesion: 0.13
Nodes (11): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), BMP bring-up frame source (frametype 65535, not a camera driver), camd (camera daemon, Sensor Framework into the frame ring), CLAUDE.md (imports AGENTS.md), Loaner Pi bring-up log (dated evidence rows), Pi development workflow (QNX 8.0 read-only IFS, /data survives), Gap table against the prize hard requirements (+3 more)

### Community 95 - "Visual odometry integration design"
Cohesion: 0.11
Nodes (18): Three ranges (REACH ships without VO; Range 3 needs pose), Accuracy ruling (Nathan, 2026-11-21, after the 360-degree clip demo), Anti-goals (what would make this a failure even if it works), Approaches considered (team decision 2026-11-21), Constraints (measured facts, not targets), Failure semantics (unchanged from §8, restated as contract), Goals, Intent (+10 more)

### Community 97 - "vo_core.py"
Cohesion: 0.10
Nodes (15): Self-review, Task 6: Integration into the percept cycle and the measured gates, backproject(), _camera_matrix(), chain(), crumb_due(), fit_ground_height(), lk_track() (+7 more)

### Community 99 - "build_parser"
Cohesion: 0.14
Nodes (6): build_parser(), main(), _positive_float_arg(), _positive_int_arg(), parse(), _unit_float_arg()

## Knowledge Gaps
- **160 isolated node(s):** `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK`, `GUIDED_CMD_TONE_ON`, `GUIDED_CMD_TONE_OFF` (+155 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 615 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `bridge (Node UDP-to-WebSocket relay and recorder)` connect `Live Camera and 3D Work Summary` to `probe_frame.py`, `camd (camera daemon, Sensor Framework into the frame ring)`?**
  _High betweenness centrality (0.217) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GUIDED_CMD_NONE`, `GUIDED_CMD_SAY`, `GUIDED_CMD_TICK` to the rest of the system?**
  _160 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `probe_to_world` be split into smaller, more focused modules?**
  _Cohesion score 0.056179775280898875 - nodes in this community are weakly interconnected._
- **Why does `Beacon dashboard index.html` connect `Live Camera and 3D Work Summary` to `test_beacon.py`?**
  _High betweenness centrality (0.207) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.12156448202959831 - nodes in this community are weakly interconnected._