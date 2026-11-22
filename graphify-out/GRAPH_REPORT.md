# Graph Report - beacon  (2026-11-22)

## Corpus Check
- 162 files · ~158,526 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 11, .jsonl 3, .css 2)

## Summary
- 1876 nodes · 4164 edges · 89 communities (72 shown, 17 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 251 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `03746901`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- probe_to_world
- guided_step
- App.jsx
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- probe_to_world.py
- merge_vo_world.py
- beacon_intent_kind
- Beacon landing page
- bridge.test.js
- probe_frame.py
- probe_frame.py
- audio.c
- deadline_test.c
- test_beacon.py
- telemd.c
- guided synthesizer (FIFO 58, core 0)
- argparse
- vo_core.py
- Visual odometry integration design
- beacon_pulse
- audio.c
- vo_core_test.py
- make-dev-reach.test.js
- Live Camera and 3D Work Summary
- test_ingest.py
- json.c
- probe_to_world
- unistd
- beacon.h
- 2. Plan
- ingest/src/main.c
- time
- TapeCheckTest
- cv2
- DepthStabiliser
- Scene.jsx
- beacon_intent_kind
- YOLOE-26n-seg (text-prompted, baked static ONNX)
- test_frame_id_seed.py
- main
- tape_check.py
- bt_speaker.py
- make_clips.py
- probe_frame.py
- beacon.h
- Any
- camd/src/main.c
- SlotTracker
- beacon_grab.c
- time
- Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)
- camd/src/main.c
- string
- Model Files Directory (not committed)
- 2. Plan
- Any
- ingest/src/main.c
- ProbeRuntimeTest
- fakeworld.c
- qnx_pkg_fetch.py
- telemd.c
- gen_ort_capi_table.py
- place_hand
- camd (camera daemon, Sensor Framework into the frame ring)
- Beacon five-process QNX isolation
- FakeFileCapture
- Beacon Accessibility Research
- bt_audio_service.sh
- make_clip
- .test_capture_frames_prompts_between_views
- beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)
- /beacon_frames Newest-wins Three-slot Ring
- FakeFileCapture
- Honest LOST Cue (no invented metres)
- Beacon: Nathan's revision (spec)
- run_live.sh
- test_frame_id_seed.py
- FakeInferenceSession
- Inclusive Language and Non-Cure Framing
- make-dev-reach.test.js
- beacon_pulse
- Beacon (chest-worn item-homing wearable)
- device_live_demo.sh
- device_slay_beat.sh
- device_chain_demo.sh
- supervisor tests (make test, make test-beacon: kill, stale beat, backoff reset)

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
10. `make_detection()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Where it lives` --references--> `Vo`  [INFERRED]
  docs/superpowers/specs/2026-11-21-vo-integration-design.md → percept/tools/vo_core.py
- `What changed` --references--> `targetObjectId()`  [INFERRED]
  docs/dashboard-redesign.md → laptop/dashboard/src/worldScene.js
- `Update: 3D follows the camera (branch `zain/3d-follows-camera`)` --references--> `Vo`  [INFERRED]
  docs/live-camera-3d-session-summary.md → percept/tools/vo_core.py
- `Task 2: `vo_probe.py` — CLI over recorded or live walks` --references--> `make_affine()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-vo-integration.md → percept/tools/probe_frame.py
- `Task 2: `vo_probe.py` — CLI over recorded or live walks` --references--> `predict_depth()`  [INFERRED]
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

## Communities (89 total, 17 thin omitted)

### Community 0 - "probe_to_world"
Cohesion: 0.06
Nodes (22): build_parser(), format_readout(), load_target_names(), main(), _ns(), _number(), _output(), parse_udp_target() (+14 more)

### Community 1 - "guided_step"
Cohesion: 0.08
Nodes (78): bind_target(), cam_from_world(), clampf(), copy_target_from(), guided_cfg_t, guided_cmd_kind, GUIDED_CMD_CHIME, GUIDED_CMD_FLUSH_SPEECH (+70 more)

### Community 2 - "App.jsx"
Cohesion: 0.06
Nodes (15): build_parser(), _positive_float_arg(), _positive_int_arg(), parse(), prepare(), probe_once(), ProbeResources, ProbeRuntimeTest (+7 more)

### Community 3 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.03
Nodes (60): beacon_clip, BEACON_CLIP_A_LITTLE, BEACON_CLIP_ABOUT, BEACON_CLIP_AHEAD, BEACON_CLIP_CANNOT_HELP, BEACON_CLIP_CANNOT_RETRACE, BEACON_CLIP_COUNT, BEACON_CLIP_DID_NOT_CATCH (+52 more)

### Community 4 - "probe_to_world.py"
Cohesion: 0.07
Nodes (10): World-frame 3D dots plan (dashboard session map), vid360 look-around replay (249 lines, real VO pose, six-noun bake), SessionOptions, main(), _open_sock(), main(), FakeSessionOptions, load() (+2 more)

### Community 5 - "merge_vo_world.py"
Cohesion: 0.08
Nodes (21): Replay rebuild recipe (probe_to_world + vo_probe + merge_vo_world, rebase t_ns), Anchor, blend_pose(), build_crumbs(), component_median(), first_frame_id(), main(), median() (+13 more)

### Community 6 - "beacon_intent_kind"
Cohesion: 0.07
Nodes (16): build_parser(), capture_memory(), drop_hand_lookalikes(), gate_by_depth(), inject_memory(), _install_depth_capture(), _iou(), lift_hand() (+8 more)

### Community 7 - "Beacon landing page"
Cohesion: 0.06
Nodes (42): RGB camera test with bottle and box detections, Spoken directions toward the bottle, Narrated camera test with bottle guidance, Spoken step and arm's-reach cues, Spoken tracking loss during the camera test, RGB crop of the 1.60-metre black bottle, Colorized depth map showing bottle at 1.60 metres, Recorded lost-target speech cue (+34 more)

### Community 8 - "bridge.test.js"
Cohesion: 0.08
Nodes (30): adapterFor(), gapMs(), isV4(), laptopAddresses(), loadReplay(), parseWorld(), startBridge(), collect() (+22 more)

### Community 9 - "probe_frame.py"
Cohesion: 0.07
Nodes (12): api(), _check(), _find_library(), _OrtApiBase, OrtError, _read_ptr(), Session, TensorInfo (+4 more)

### Community 10 - "probe_frame.py"
Cohesion: 0.09
Nodes (21): Task 2: `vo_probe.py` — CLI over recorded or live walks, VO task order: laptop-first core, probe, recorded walk, C++ port, percept cycle, MediaPipe hand_landmarker.task probe (broken pybind11 on QNX), Per-slot depth median stabilisation (IoU slots, jump/evict/recover gates), Calibration, guess_calibration(), load_calibration(), load_depth_session() (+13 more)

### Community 11 - "audio.c"
Cohesion: 0.06
Nodes (39): concurrency, cancel-in-progress, group, if, name, runs-on, steps, jobs (+31 more)

### Community 12 - "deadline_test.c"
Cohesion: 0.09
Nodes (12): calibrate_camera.py chessboard calibration (calib.json is laptop-local, never beacon.h), build_parser(), calibrate_images(), capture_frames(), find_corners(), main(), make_calibration(), CalibrateCameraTest (+4 more)

### Community 13 - "test_beacon.py"
Cohesion: 0.12
Nodes (37): Dashboard layout (floating top bar, sliding panels, replay scrubber, reduced-motion), Ago(), agoText(), App(), BOTH, Camera(), Caption(), DataSource() (+29 more)

### Community 14 - "telemd.c"
Cohesion: 0.11
Nodes (12): dump_ep_ctx(), ep_type_name(), main(), map_mmio(), dump(), main(), main(), mp() (+4 more)

### Community 15 - "guided synthesizer (FIFO 58, core 0)"
Cohesion: 0.08
Nodes (34): dependencies, @animate-ui/react@^2.4.6, @base-ui/react@^1.9.0, @fontsource/ibm-plex-mono@^5.3.0, @fontsource/ibm-plex-sans@^5.3.0, motion@^14.14.0, react@^19.3.1, react-aria-components@^1.22.1 (+26 more)

### Community 16 - "argparse"
Cohesion: 0.07
Nodes (25): Affine, full_h, full_w, net_h, net_w, pad_x, pad_y, scale (+17 more)

### Community 17 - "vo_core.py"
Cohesion: 0.11
Nodes (13): Self-review, Task 6: Integration into the percept cycle and the measured gates, backproject(), _camera_matrix(), chain(), crumb_due(), lk_track(), PoseResult (+5 more)

### Community 18 - "Visual odometry integration design"
Cohesion: 0.06
Nodes (31): Beacon spec adversarial review, Merge verdict: BLOCK, Three ranges (REACH ships without VO; Range 3 needs pose), Global Constraints, Review Focus, Task 1: `vo_core.py` — the geometry core with synthetic tests, Task 3: Record a real L-walk and tune, Task 4: On-device OpenCV gate — the A/B decision (spec F1) (+23 more)

### Community 19 - "beacon_pulse"
Cohesion: 0.18
Nodes (27): COLORS, Frustum(), isNum(), LabelVisibility(), Marker(), norm(), Scene(), crumbsToScene() (+19 more)

### Community 20 - "audio.c"
Cohesion: 0.12
Nodes (24): audio_dropped_speech(), audio_main(), audio_start(), audio_stop(), law_name(), mode_name(), audio_out_close(), audio_out_open() (+16 more)

### Community 21 - "vo_core_test.py"
Cohesion: 0.14
Nodes (12): make_affine(), fit_ground_height(), keyframe_due(), scale_correction(), camera_matrix(), make_metres(), make_texture(), make_vo() (+4 more)

### Community 22 - "make-dev-reach.test.js"
Cohesion: 0.11
Nodes (16): captionFromClips(), CLIP_NAMES, CLIPS, clock(), Events(), eventsFromLog(), texts(), bounds (+8 more)

### Community 23 - "Live Camera and 3D Work Summary"
Cohesion: 0.09
Nodes (24): Dashboard redesign and live Pi connection, Graph, Live Raspberry Pi connection, Live | Replay bridge switching (UDP 5005 always open, status frame once a second), Running it against the Pi, Still open, What actually ran on the Pi, What changed (+16 more)

### Community 24 - "test_ingest.py"
Cohesion: 0.17
Nodes (14): free_udp_port(), hand_at(), main(), find(), record(), wait_for_exit(), alive(), lines() (+6 more)

### Community 25 - "json.c"
Cohesion: 0.30
Nodes (21): jalloc(), jarr_at(), jarray(), jis(), jnew(), jnum(), jnumber(), jobj_get() (+13 more)

### Community 26 - "probe_to_world"
Cohesion: 0.16
Nodes (15): add_argv(), add_argv_line(), allow_priorities(), beacon_children(), create_region(), depth_name(), describe(), ensure_regions() (+7 more)

### Community 27 - "unistd"
Cohesion: 0.14
Nodes (8): main(), put_u16(), put_u32(), write_bmp(), main(), sleep_until(), beacon_frame_slot_t, world_open()

### Community 28 - "beacon.h"
Cohesion: 0.09
Nodes (20): beacon_crumb_t, beacon_depth_t, beacon_guided_block_t, beacon_guided_display_t, beacon_guided_stats_t, beacon_hand_t, beacon_law, BEACON_LAW_LOST (+12 more)

### Community 29 - "2. Plan"
Cohesion: 0.09
Nodes (22): 1.1 What laptop work has achieved (all true, all on the wrong machine), 1.2 Gap table against the prize hard requirements, 1.3 QNX-mechanism stubs (the pitch vs the code), 1.4 The real-time claim needs re-scoping, 1.5 Cuts already made or to be made now, 1.6 Small risks that will burn an hour at the worst moment, 1. Findings, 2. Plan (+14 more)

### Community 30 - "ingest/src/main.c"
Cohesion: 0.19
Nodes (19): audio_publish_stats(), audio_submit(), main(), open_world(), test_seq_writer_restart(), beacon_now_ns(), beacon_seq_read(), beacon_seq_t (+11 more)

### Community 31 - "time"
Cohesion: 0.19
Nodes (17): SourceSwitch(), ChevronLeft(), ChevronRight(), Collapse(), Expand(), Icon(), Panel(), PanelLeftClose() (+9 more)

### Community 32 - "TapeCheckTest"
Cohesion: 0.30
Nodes (3): expected_result(), range_record(), TapeCheckTest

### Community 33 - "cv2"
Cohesion: 0.15
Nodes (7): Testing the live path without the Pi, Update: 3D follows the camera (branch `zain/3d-follows-camera`), apply_pose(), LiveVo, ApplyPose, FollowsCamera, _to_world()

### Community 34 - "DepthStabiliser"
Cohesion: 0.20
Nodes (3): DepthStabiliser, _DepthState, DepthStabiliserTest

### Community 35 - "Scene.jsx"
Cohesion: 0.24
Nodes (14): completion(), desc_at(), find_audio_stream(), insertion(), logf_(), main(), now_elapsed(), put16() (+6 more)

### Community 36 - "beacon_intent_kind"
Cohesion: 0.10
Nodes (19): beacon_intent_kind, BEACON_INTENT_FIND, BEACON_INTENT_GO, BEACON_INTENT_NACK_CANT, BEACON_INTENT_NACK_UNHEARD, BEACON_INTENT_NACK_UNSEEN, BEACON_INTENT_NONE, BEACON_INTENT_REJECT (+11 more)

### Community 37 - "YOLOE-26n-seg (text-prompted, baked static ONNX)"
Cohesion: 0.18
Nodes (4): crop_depth_padding(), _draw_boxes(), render_preview(), RenderPreviewTest

### Community 38 - "test_frame_id_seed.py"
Cohesion: 0.18
Nodes (9): Frames, FrameSlot, main(), plant_non_newest_high_id(), published_frame_id(), run(), verify_layout(), main() (+1 more)

### Community 39 - "main"
Cohesion: 0.20
Nodes (17): Demo runbook: Best Use of QNX, A3 open: pidin ar captured with ORT live and saved to docs/pi-bringup.md, A5: slay live_probe perception producer; guided goes HOLD then LOST with deadline record unbroken, A5 open: live perception producer killed twice on hardware, A6 open: metres decision executed, tape check logged or --metres removed from three scripts, BT service kill/restart rehearsal open: speaker comes back on its own in a run, C270 one-time sensor setup: usb_camera jpeg, no create_window, memory_allocator_type from_sensor, Two passes, floor first: floor pass on the Pi (+9 more)

### Community 40 - "tape_check.py"
Cohesion: 0.20
Nodes (9): Range 1 tabletop proof gate (same frame_id, tape-checked d_m), _median_depth(), build_parser(), evaluate(), load_record(), main(), _number(), _range_prediction() (+1 more)

### Community 41 - "bt_speaker.py"
Cohesion: 0.16
Nodes (7): main(), _mono_samples(), pcm_chunks(), play_wav(), counted(), _resample(), send_pcm()

### Community 42 - "make_clips.py"
Cohesion: 0.18
Nodes (7): main(), make_inflect(), render(), make_llamacpp(), render(), to_clip(), wanted_clips()

### Community 43 - "probe_frame.py"
Cohesion: 0.12
Nodes (12): Beacon Accessibility Research (BLV evidence brief), Open-vocab model research for Pi 5 CPU, Devpost paste-ready description, Beacon (chest-worn named-object homing device), Pitch language table (no cure framing, supplement to the cane, sighted team), Saturday Build Order (spec section 13, steps 1-6), Beacon: Nathan's revision (spec), QNXE-1894 Wi-Fi settings copy gate (workaround: cat provisioning copies onto /data every boot) (+4 more)

### Community 44 - "beacon.h"
Cohesion: 0.12
Nodes (8): Metres option 2: remove --metres from the three scripts and speak bearing only, Early safety disclosure: supplement to the cane, not a replacement, Metres option 1: tape check at 1 m, accept under 30 percent error, Remembered-row bind window (20 s, amended 2026-11-22), guided --metres (tape-gated) and --audio outputs (none, wav, fifo, qnx), Depth Anything V2 Metric Indoor Small ONNX (static 210x210, external .onnx.data), beacon_cmd typed-command stand-in (writes exactly what voiced will write), irl_test.sh: recorded clip through world_in into guided, wearer audio to WAV

### Community 45 - "Any"
Cohesion: 0.16
Nodes (5): _central_bounds(), depth_at_box(), depth_at_full(), depth_at_patch(), DepthSamplingTest

### Community 46 - "camd/src/main.c"
Cohesion: 0.23
Nodes (13): fill_stub_frame(), load_bmp(), main(), open_frames(), pin_core0(), publish_frame(), read_le32(), seed_next_frame_id() (+5 more)

### Community 47 - "SlotTracker"
Cohesion: 0.17
Nodes (6): _box_bounds(), _box_iou(), _slot_match_score(), _SlotState, SlotTracker, SlotTrackerTest

### Community 48 - "beacon_grab.c"
Cohesion: 0.16
Nodes (8): camd (camera daemon, Sensor Framework into the frame ring), QNX findings F1-F9 (OpenCV module gate, keyframe from in-process copy, 1 ms clock), find_eoi(), now_ns(), on_data(), write_atomic(), micd gotchas (TRB ring leak on resubmit, VBUS power-cycle, QNX getopt parsing), telemd-preview (optional downscaled JPEG path, expires without the camera)

### Community 49 - "time"
Cohesion: 0.15
Nodes (11): A2: slay the BT audio service process and the service script brings the speaker back, C270 wedged after USB crash: power-cycle with sudo -n gpio-rp1 set 42 op pn dl, wait about 5 s, then set 42 a2 pn / set 43 a2 pu, Dashboard dies: irrelevant to the demo; do not stop, Failure plays: things that have already broken once, with the fix that worked, JBL silent: check the BT service bt_speaker.py path before judging and keep the slay-restart beat, Live perception too slow or missing frames: fall back to replay clip scripts, USB stack dies: sudo -n sh /usr/etc/usb_start.sh, restart sensor and beacon_grab; no reboot, guided audio thread (prio 40, speech ring, newest-wins tick/tone slot) (+3 more)

### Community 50 - "Pi Development Workflow (QNX 8.0 on Raspberry Pi 5)"
Cohesion: 0.19
Nodes (7): 0 to 8s: FIND arrives as a record on the laptop and JBL speaks bearing; earns S7, S8, 8 to 16s: wearer walks toward object and cue repeats from sensors; earns S2, S6, 16 to 24s: slay the perception producer, cue holds then says I lost the target, no distance spoken; earns S1, S4, 24 to 30s: supervisor respawns producer and cue returns, then BT audio service is killed and returns on its own; earns S1, S6, Camera table setup: phone on tripod, JBL Go 3, wearer's hand, SSH terminal visible; JBL audible in recording, The 30 seconds: demo and Devpost video beats, guided 16.67 ms synthesizer loop (CLOCK_MONOTONIC, no blocking writes)

### Community 51 - "camd/src/main.c"
Cohesion: 0.19
Nodes (6): destination_full(), destination_ready(), preview_tick(), sample_frame(), send_jpeg(), skip_jpeg()

### Community 52 - "string"
Cohesion: 0.22
Nodes (8): hog(), main(), pin_cpu(), set_fifo(), sleep_until_ns(), platform_heartbeat(), platform_piezo_init(), platform_supervisor_connect()

### Community 53 - "Model Files Directory (not committed)"
Cohesion: 0.18
Nodes (12): Ultralytics AGPL-3.0 licence risk (fine for a hackathon build, say so if asked), Chain replay expected: WALK cue three times, mode LIVE then HOLD, 1500 loops, 0 missed deadlines, worst 4.7 ms, p95 1.9 ms, sh ingest/tools/device_chain_demo.sh /tmp/replay.avi bottle, sh ingest/tools/device_slay_beat.sh /tmp/long.avi bottle, Replay clip re-record open: clear object at about 1 m that clears conf 0.15 at default lighting, Target must be in the six-noun bake: bottle, can, keys, phone, box, mouse, Slay-beat expected records: 1800 loops and 0 missed before, 2100 loops and 0 missed with p95 2.05 ms after fresh ingest, Slay-beat sequence A-D: live cue, slay ingest and lost target, post-death readout, fresh ingest restores cue with guided never restarted (+4 more)

### Community 54 - "2. Plan"
Cohesion: 0.14
Nodes (12): Supervisor contract (spawn with scheduler attributes, 50 ms pulse heartbeat, respawn backoff), BTstack A2DP bridge to JBL Go 3 (validated, boot-persistent), guided Pi validation sequence (build, silent run, JBL, timing under load), guided (60 Hz guidance synthesizer: mode, bind, laws, audio), Build / test, ingest, Known limits (deliberate), Usage (+4 more)

### Community 55 - "Any"
Cohesion: 0.31
Nodes (8): Affine, detect(), detect_yolo_ort(), find_fingertip(), letterbox(), predict_depth(), tensor_scalar(), process()

### Community 56 - "ingest/src/main.c"
Cohesion: 0.33
Nodes (11): apply(), find_key(), get_id(), get_num(), get_str(), get_vecn(), main(), publish() (+3 more)

### Community 57 - "ProbeRuntimeTest"
Cohesion: 0.32
Nodes (10): add(), handle(), html_escape(), is_skip(), kind_name(), main(), send_all(), send_intent() (+2 more)

### Community 58 - "fakeworld.c"
Cohesion: 0.35
Nodes (9): drop_crumb(), lerp(), main(), publish_percept(), put_hand(), put_object(), say_intent(), set_pose_yaw() (+1 more)

### Community 59 - "qnx_pkg_fetch.py"
Cohesion: 0.25
Nodes (4): dep_names(), main(), parse_index(), version_gt()

### Community 60 - "telemd.c"
Cohesion: 0.35
Nodes (8): beacon_live_max_ns(), append(), append_scene(), escape_name(), heartbeat_alive(), main(), snapshot(), vector_json()

### Community 61 - "gen_ort_capi_table.py"
Cohesion: 0.33
Nodes (5): clean(), ctype_of(), expand(), main(), split_args()

### Community 62 - "place_hand"
Cohesion: 0.31
Nodes (4): _boxes_touch(), place_hand(), PlaceHandTest, world()

### Community 63 - "camd (camera daemon, Sensor Framework into the frame ring)"
Cohesion: 0.22
Nodes (7): AGENTS.md: Beacon notes for coding agents, Committed graph artifacts (GRAPH_REPORT.md, graph.json, graph.html), BMP bring-up frame source (frametype 65535, not a camera driver), CLAUDE.md (imports AGENTS.md), Loaner Pi bring-up log (dated evidence rows), Pi development workflow (QNX 8.0 read-only IFS, /data survives), Gap table against the prize hard requirements

### Community 64 - "Beacon five-process QNX isolation"
Cohesion: 0.25
Nodes (4): How QNX is used (Devpost section with measured numbers), 30-second Sunday demo script (spec section 12), The QNX beat on hardware (slay ingest, LOST, recovery, guided never restarted), Supervisor to spec, verified on the loaner (58f/40f/22r, respawn ~100 ms)

### Community 66 - "Beacon Accessibility Research"
Cohesion: 0.29
Nodes (4): Full loop closes on QNX (1500 loops, 0 missed, guided speaks), Bluetooth HFP capture as the working mic path (GPIO28 is the Wi-Fi rail, never toggle), micd (C270 UAC1 mic capture on QNX, work in progress), Status: what runs on the loaner and what does not (README section)

### Community 67 - "bt_audio_service.sh"
Cohesion: 0.43
Nodes (6): clips_find(), clips_load(), clips_playlist(), load_one(), rd16(), rd32()

### Community 69 - ".test_capture_frames_prompts_between_views"
Cohesion: 0.40
Nodes (5): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_live_demo.sh script, slay_matching()

### Community 70 - "beacon.h Shared Contract (shm layouts, seqs, intent.kind, pulse codes)"
Cohesion: 0.40
Nodes (5): kill_matching(), LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_slay_beat.sh script

### Community 73 - "Honest LOST Cue (no invented metres)"
Cohesion: 0.40
Nodes (4): LD_LIBRARY_PATH, ORT_LIB, PYTHONPATH, device_chain_demo.sh script

### Community 75 - "run_live.sh"
Cohesion: 0.40
Nodes (4): BEACON_CMD, PERCEPT, REPO, run_live.sh script

### Community 76 - "test_frame_id_seed.py"
Cohesion: 0.50
Nodes (3): LD_LIBRARY_PATH, PYTHONPATH, ai-import-test.sh script

## Knowledge Gaps
- **170 isolated node(s):** `full_h`, `full_w`, `net_h`, `net_w`, `pad_x` (+165 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 637 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `bridge (Node UDP-to-WebSocket relay and recorder)` connect `Live Camera and 3D Work Summary` to `camd (camera daemon, Sensor Framework into the frame ring)`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `guided_step()` (e.g. with `beacon_live_max_ns()` and `beacon_mode`) actually correct?**
  _`guided_step()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `full_h`, `full_w`, `net_h` to the rest of the system?**
  _170 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `probe_to_world` be split into smaller, more focused modules?**
  _Cohesion score 0.056179775280898875 - nodes in this community are weakly interconnected._
- **Why does `Telemetry format (world state ~10 Hz + JPEG ~5 fps to UDP 5005)` connect `Live Camera and 3D Work Summary` to `beacon.h`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `probe_once()` (e.g. with `.depth_session()` and `.read_frame()`) actually correct?**
  _`probe_once()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `guided_step` be split into smaller, more focused modules?**
  _Cohesion score 0.08456790123456791 - nodes in this community are weakly interconnected._