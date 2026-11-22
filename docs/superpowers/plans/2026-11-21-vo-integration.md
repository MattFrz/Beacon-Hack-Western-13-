# VO Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A metric visual-odometry pose chain at ~10 Hz in `percept` (spec §7 Range 3 / RETURN), laptop-proven first, then on the QNX Pi behind its measured gates.

**Architecture:** Hybrid KLT front-end (approach A of the spec): corners detected once per keyframe, `calcOpticalFlowPyrLK` per VO step, depth-backed `solvePnPRansac`, §8 pose chaining, ground-height scale watchdog. Pure geometry — no models — sharing the detector's tape-gated depth. Laptop-first per repo convention: a Python core with synthetic tests, a probe over a recorded walk, then the C++ port and on-device gates.

**Tech Stack:** Python + OpenCV (probe venv) for proof; C++ + OpenCV `core/imgproc/video/calib3d` for `percept`; ONNX Runtime depth inference reused as-is from `probe_frame.py`.

**Spec:** `docs/superpowers/specs/2026-11-21-vo-integration-design.md` (approaches, algorithm, failure semantics, QNX findings F1–F9). The spec travels with this plan; executors read both.

## Global Constraints

- **No `include/beacon.h` changes.** VO uses only existing fields: `beacon_pose_t`, crumb ring, `pose_epoch`, `health`.
- **OpenCV only** (`core`, `imgproc`, `video`, `calib3d`); no new native dependencies. Python work runs with `/tmp/beacon-probe-venv/bin/python`.
- **QNX-only calls behind `#ifdef __QNX__`** so every piece also builds on a laptop.
- **This laptop has no OpenCV C++ headers.** C++ tasks verify on-device (rsync → ssh make), or on a laptop only if the executor first arranges headers (an install requiring partner approval).
- **Tape check is the only scale authority.** No VO pose is trusted for Range 3 before `tape_check.py` passes for the shared `depth_scale`. Proxy ms numbers are never QNX facts.
- **Never fake RETURN.** No breadcrumb log is ever presented as "RETURN implemented" without the live aisle numbers (spec §12).
- **Branch `nathan/vo` off `main`**, merge via PR per team convention. Outputs go to `build/` (gitignored); models stay gitignored except `labels.txt`.
- **Failure is a value, not an exception:** untrusted steps yield `pose.valid = 0`; the last pose ages; nothing extrapolates.

## Review Focus

The five inputs the spec implies but the happy path never sees; each line's test is pinned inside the owning task.

1. **Stale or repeated frame_id** — a step must be skipped silently, never double-applied. Test in Task 1 (`test_step_skips_stale_frame`).
2. **Invalid depth cells at keyframe corners** (`<= 0` / NaN) — depth gate drops those tracks; too few left means `valid = 0`, not a crash. Test in Task 1 (`test_depth_gate_rejects_invalid_cells`).
3. **Fast head turn** (median displacement > 8 px/frame) — rolling-shutter guard fires, pose is not updated, no extrapolation. Test in Task 1 (`test_fast_pan_invalidates_pose`).
4. **Floor absent** (pitched up, table edge) — watchdog returns no correction (×1.0), never a fabricated one. Test in Task 1 (`test_no_floor_no_correction`).
5. **Depth-scale error ~4×** (the known DAv2 failure) — watchdog rescales translation toward `h_chest` via the window median, and the correction rate is reported. Test in Task 1 (`test_watchdog_corrects_scale_error`).

---

### Task 1: `vo_core.py` — the geometry core with synthetic tests

**Files:**
- Create: `percept/tools/vo_core.py`
- Create: `percept/tools/vo_core_test.py`
- Modify: `percept/Makefile` (add both to `test-python` list)

**Interfaces (produced; later tasks and Task 5's C++ mirror these):**

```python
# all in percept/tools/vo_core.py; np = numpy, reuses probe_frame.Affine / Calibration
VO_MAX_DISP_PX = 8.0        # rolling-shutter guard threshold
VO_MIN_TRACKS = 60          # below this a step is untrusted
VO_MIN_INLIERS = 15         # solvePnPRansac inlier floor
VO_FB_ERR_PX = 1.0          # forward-backward rejection threshold

def vo_pts_to_full(pts, vo_w, vo_h, cam_w, cam_h) -> np.ndarray          # (N,2) VO-scale -> full-frame px
def lk_track(prev_gray, cur_gray, pts, fb_err_px=VO_FB_ERR_PX,
             win=(21, 21), max_level=2) -> (tracked_pts, ok_mask, median_disp_px)
def backproject(pts_full, metres, affine, calib, scale) -> (pts3d, valid_mask)
    # pts_full: (N,2) full-frame px; metres: depth grid; affine: depth Affine;
    # per-point depth via probe_frame.depth_at_full + 3x3 patch median, then probe_frame.unproject
def solve_pose(pts3d, pts2d, calib) -> Optional[PoseResult]   # None below VO_MIN_INLIERS
    # @dataclass PoseResult: T_F_from_K (4x4), inliers:int, repro_px:float
    # cv2.solvePnPRansac, flags=SOLVEPNP_EPNP, reprojectionError=2.0, confidence=0.99, iterationsCount=200
def chain(T_world_from_K, T_F_from_K) -> np.ndarray            # T_world_from_F
def fit_ground_height(pts3d_cam, calib, min_pts=20, up_tol_deg=30.0) -> Optional[float]
    # least-squares plane over below-horizon points; h_est in metres; None if unfittable
def scale_correction(h_est, h_chest, window, tol=0.25) -> float
    # appends h_est to the deque; returns h_chest/h_est window median when the
    # latest ratio exceeds tol, else 1.0; h_est None -> 1.0 and window untouched
def keyframe_due(T_rel, n_tracks, moved_m=0.10, rot_deg=15.0,
                 min_tracks=VO_MIN_TRACKS) -> bool              # T_rel: 4x4 K->F
def crumb_due(last_crumb_ns, now_ns, moved_since_crumb_m,
              min_dt_ns=400_000_000, min_move_m=0.05) -> bool
```

- [ ] **Step 1: Commit the design docs onto the branch**

```bash
git checkout -b nathan/vo
git add docs/superpowers/specs/2026-11-21-vo-integration-design.md docs/superpowers/plans/2026-11-21-vo-integration.md
git commit -m "docs: VO integration spec and implementation plan"
```

- [ ] **Step 2: Write the failing tests** in `vo_core_test.py` (unittest, same style as `probe_frame_test.py`). Synthetic frames are a random-texture `np.uint8` image; known motions come from `cv2.warpAffine`. The suite must cover all five Review Focus lines plus the bookkeeping:

```python
def test_pure_translation_recovered():      # 0.30 m forward-shifted texture, synthetic depth plane;
    # chain() recovers |t| within 5%, direction within 5 deg
def test_pure_rotation_recovered():         # 10 deg yaw warp; recovered angle within 2 deg
def test_step_skips_stale_frame():          # same frame_id twice -> second call is a no-op (Review Focus 1)
def test_depth_gate_rejects_invalid_cells():  # NaN depth region; valid_mask excludes it; too few -> no pose (RF 2)
def test_fast_pan_invalidates_pose():       # warp ~15 px/frame -> guard: valid=False, pose unchanged (RF 3)
def test_no_floor_no_correction():         # all synthetic points above horizon -> fit_ground_height None,
    # scale_correction 1.0, no exception (RF 4)
def test_watchdog_corrects_scale_error():   # floor plane at 0.25x height -> correction ~4x toward h_chest (RF 5)
def test_keyframe_due_thresholds():         # 10 cm / 15 deg / track-starvation all flip the decision
def test_crumb_due_gates():                # neither <0.4 s nor <5 cm alone is enough
```

- [ ] **Step 3: Run to verify failure**

Run: `/tmp/beacon-probe-venv/bin/python -m unittest percept.tools.vo_core_test -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'percept.tools.vo_core'`

- [ ] **Step 4: Implement `vo_core.py`** to the Interfaces block above. One choice the signatures leave open, decided here: `median_disp_px` is the median over *surviving* fb-checked tracks, computed before the depth gate.

- [ ] **Step 5: Run the tests to verify pass**

Run: `/tmp/beacon-probe-venv/bin/python -m unittest percept.tools.vo_core_test -v`
Expected: PASS (9 tests)

- [ ] **Step 6: Add to `percept/Makefile` `test-python` list and run the whole suite**

Run: `make -C percept test-python PYTHON=/tmp/beacon-probe-venv/bin/python`
Expected: PASS including the existing probe tests

- [ ] **Step 7: Commit**

```bash
git add percept/tools/vo_core.py percept/tools/vo_core_test.py percept/Makefile
git commit -m "feat(percept): VO geometry core with synthetic tests"
```

### Task 2: `vo_probe.py` — CLI over recorded or live walks

**Files:**
- Create: `percept/tools/vo_probe.py`
- Create: `percept/tools/vo_probe_test.py`
- Modify: `percept/Makefile` (test-python list)

**Interfaces:**
- Consumes: everything in Task 1's block; `probe_frame.predict_depth`, `probe_frame.load_depth_session`, `probe_frame.resolve_calibration`, `probe_frame.guess_calibration`, `probe_frame.make_affine` (reuse, do not re-implement).
- Produces: CLI with modes — `--record OUT_DIR [--seconds 30]` (cv2.VideoCapture → PNG frames; replaces the deleted `webcam-record/`), `--video PATH` (frame directory or AVI), `--camera N` (live); `--depth models/depth_anything_v2_metric_indoor_small.onnx`, `--depth-scale 0.25`, `--fov` / `--calib models/calib.json`, `--h-chest M` (required for the watchdog; no default), `--stride N` (default 3), `--out PATH.jsonl`. Per-step stderr line: `frame=... inliers=... disp_px=... h_est=... scale=... valid=... t=[x,y,z]`. Summary at exit: JSON with `frames`, `valid_fraction`, `correction_rate`, `final_t_m`.

- [ ] **Step 1: Write the failing test** `vo_probe_test.py`: build a 40-frame synthetic clip (texture translated per frame, synthetic flat depth at 2.0 m, floor points included) with `cv2.VideoWriter` into a temp AVI; run the CLI as a subprocess (`--h-chest 1.4 --fov`); parse the summary JSON; assert `valid_fraction >= 0.9` and `final_t_m` within 5% of the clip's scripted displacement.

- [ ] **Step 2: Run to verify failure**

Run: `/tmp/beacon-probe-venv/bin/python -m unittest percept.tools.vo_probe_test -v`
Expected: FAIL (no `vo_probe.py`)

- [ ] **Step 3: Implement `vo_probe.py`.** Keyframe logic per spec §design: keyframe gray+depth taken from the frame being processed at swap time (in-memory, never re-read for keyframe material — spec F9); `--depth-scale` applies only to depth values, one scale authority. The probe never writes shm.

- [ ] **Step 4: Run the test to verify pass**

Run: `/tmp/beacon-probe-venv/bin/python -m unittest percept.tools.vo_probe_test -v` then `make -C percept test-python PYTHON=/tmp/beacon-probe-venv/bin/python`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add percept/tools/vo_probe.py percept/tools/vo_probe_test.py percept/Makefile
git commit -m "feat(percept): VO probe CLI over recorded and live walks"
```

### Task 3: Record a real L-walk and tune

**Files:**
- Modify: `docs/superpowers/specs/2026-11-21-vo-integration-design.md` (Open items section only)
- No code. Hardware: a laptop webcam and ~8 m of floor with one 90° turn.

**Interfaces:**
- Consumes: Task 2's CLI including `--record`.
- Produces: measured `--stride`, watchdog thresholds, working scale; numbers recorded in the spec's Open items.

- [ ] **Step 1: Record the walk**

```sh
/tmp/beacon-probe-venv/bin/python percept/tools/vo_probe.py --record /tmp/beacon-l-walk --seconds 25
# walk: ~6 m forward, 90 deg left turn, ~3 m, stop; camera at chest height
```

- [ ] **Step 2: Run the probe over the recording, first without the watchdog**

```sh
/tmp/beacon-probe-venv/bin/python percept/tools/vo_probe.py \
  --video /tmp/beacon-l-walk --depth models/depth_anything_v2_metric_indoor_small.onnx \
  --depth-scale 0.25 --fov --h-chest 1.4
```

Expected: valid_fraction and final endpoint readout on stderr. If valid_fraction < 0.9 or the endpoint is off by more than the tape-measured truth, tune stride/watchdog and re-run; record what moved the needle.

- [ ] **Step 3: Record the choices** in the spec's Open items: chosen `--stride`, final thresholds, endpoint error vs tape-measured truth, watchdog correction rate. These are the values Task 5 hard-codes as defaults.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-11-21-vo-integration-design.md
git commit -m "docs: VO probe walk measurements and tuned thresholds"
```

### Task 4: On-device OpenCV gate — the A/B decision (spec F1)

**Files:**
- Modify: `docs/superpowers/specs/2026-11-21-vo-integration-design.md` (QNX findings + status line)

**Interfaces:**
- Produces: a recorded decision — approach A (OpenCV `video` present) or B (fallback to per-frame ORB, `features2d` only) — that Task 5 builds against.

- [ ] **Step 1: On the Pi (when reachable), check the package and its modules**

```sh
ssh qnxpi 'ls /usr/lib | grep -i opencv; find /data/home/qnxuser -iname "*opencv*" 2>/dev/null'
ssh qnxpi 'grep -l video /usr/lib/libopencv_video* 2>/dev/null && echo VIDEO-PRESENT'
```

- [ ] **Step 2: Decide and record.** `libopencv_video` present → A, proceed to Task 5 as written. Absent or the package won't install from `oss.qnx.com` → B: flip Task 5's tracker to per-frame ORB (`ORB.detectAndCompute` + Lowe-ratio match against the keyframe's descriptors, everything else unchanged), accept the measured CPU cost, and note the decision with a timestamp in the spec's F1 entry. If the Pi is unreachable, the default is to write Task 5 against A and re-decide at Saturday integration.

- [ ] **Step 3: Commit the recorded decision**

```bash
git add docs/superpowers/specs/2026-11-21-vo-integration-design.md
git commit -m "docs: QNX OpenCV package check result, VO approach decision"
```

### Task 5: `vo.hpp` / `vo.cpp` — the C++ port

**Files:**
- Create: `percept/src/vo.hpp`, `percept/src/vo.cpp`
- Create: `percept/src/vo_selftest.cpp`
- Modify: `percept/Makefile` (targets `vo-selftest`, guarded)

**Interfaces:**
- Consumes: Task 1's algorithms and Task 3's tuned constants; `include/beacon.h` types only as plain data (no shm writes here).
- Produces (Task 6 links against these exactly):

```cpp
// percept/src/vo.hpp
namespace beacon {
struct VoConfig {            // defaults = Task 3's recorded values
    float h_chest_m = 1.4f;
    int   max_corners = 300;
    float fb_err_px = 1.0f, max_disp_px = 8.0f;
    float moved_m = 0.10f, rot_deg = 15.0f;
    int   min_tracks = 60, min_inliers = 15;
};
struct VoStep {               // returned by Vo::step
    bool   valid;
    double T_world_from_cam[16];   // row-major 4x4, same convention as beacon_pose_t
    int    inliers; float h_est, scale_mult, median_disp_px;
    uint64_t t_ns;                 // of the frame that produced this pose
};
class Vo {
public:
    explicit Vo(const VoConfig& cfg);
    void set_intrinsics(const float K[9], int cam_w, int cam_h, int vo_w, int vo_h);
    // keyframe material: percept's in-process copy (spec F9), never the ring
    bool on_depth_frame(const uint8_t* gray_vo, const float* metres, int w_d, int h_d,
                        const beacon_letterbox_t& depth_affine, uint64_t frame_id, uint64_t t_ns);
    std::optional<VoStep> step(const uint8_t* gray_vo, uint64_t frame_id, uint64_t t_ns);
    bool crumb_due(uint64_t now_ns, float moved_since_crumb_m) const;
};
}
```

- [ ] **Step 1: Write `vo_selftest.cpp`** asserting the Task 1 behaviours in C++: pure translation within 5%, fast pan invalidates, invalid depth cells drop tracks, watchdog corrects the 4× case. Synthetic frames built with `cv::randu` + `cv::warpAffine`, no files needed.

- [ ] **Step 2: Extend `percept/Makefile`** — `vo-selftest` builds from `vo.cpp` + `vo_selftest.cpp` against OpenCV (`-lopencv_core -lopencv_imgproc -lopencv_video -lopencv_calib3d`; on-device uses whatever link names Task 4 confirmed). Guard: if no OpenCV is found, `make` prints "vo-selftest needs OpenCV; skipping" and still builds `percept-head`.

- [ ] **Step 3: Build and run wherever OpenCV exists** — on-device loop by default:

```sh
rsync -az --delete ./percept/ qnxpi:/data/home/qnxuser/app/percept/
ssh qnxpi 'cd /data/home/qnxuser/app/percept && make vo-selftest && ./vo-selftest'
```

Expected: `vo-selftest: PASS`. If Task 4 chose B, same selftest, ORB tracker swap.

- [ ] **Step 4: Commit**

```bash
git add percept/src/vo.hpp percept/src/vo.cpp percept/src/vo_selftest.cpp percept/Makefile
git commit -m "feat(percept): C++ VO module with on-device selftest"
```

### Task 6: Integration into the percept cycle and the measured gates

**Files:**
- Modify: `percept/src/head.cpp` (evolves into the cycle's VO wiring point) — or the real percept loop file if it has landed by then; the Interfaces below hold either way
- Modify: `percept/Makefile`

**Interfaces:**
- Consumes: `beacon::Vo` exactly as Task 5 defines it; the frame-ring seqlock reader pattern already in `head.cpp`; percept's in-process last-processed frame (gray + depth grid + affine) per spec F9.
- Produces: pose, crumbs, `pose_epoch` handling folded into percept's existing `seq_percept` write; the spec's acceptance numbers.

- [ ] **Step 1: Wire the step.** Every `--stride`-th ring frame: read newest slot (skip if `frame_id` not newer — Review Focus 1), gray-convert, `Vo::step`; on keyframe-due call `Vo::on_depth_frame` with the in-process copy. Fold the returned pose (valid flag, `t_ns`, `age_ns`) and crumbs per `crumb_due` into the next `seq_percept` write. `pose_epoch` bumps on percept start per existing contract; first successful keyframe is world origin `T = I`.

- [ ] **Step 2: Laptop build sanity** (`percept-head` still builds without OpenCV via the Makefile guard) and full Python suite:

```sh
make -C percept && /tmp/beacon-probe-venv/bin/python -m unittest percept.tools.vo_core_test percept.tools.vo_probe_test -v
```

Expected: PASS, `percept-head` binary unchanged in behaviour without the VO flag.

- [ ] **Step 3: On-device acceptance, in order, all recorded (spec "done and trusted"):**

1. VO step p50/p95 under three hogs on cores 1–3 with `guided` live — deadline-test style counters, never single-shot clocks.
2. Stride N re-derived from the real decoded frame rate (spec F8), not assumed 30 fps.
3. Three live L-shaped returns; endpoint error on the dashboard; valid-pose fraction ≥ 90%.
4. `slay percept` mid-walk → `pose.valid = 0`, RETURN refuses with the `CANNOT_RETRACE` clip.
5. VO pose for Range 3 stays off until `tape_check.py` passes — one gate with spoken metres.

- [ ] **Step 4: Record the numbers in the spec's Open items and commit**

```bash
git add percept/src/head.cpp percept/Makefile docs/superpowers/specs/2026-11-21-vo-integration-design.md
git commit -m "feat(percept): VO in the percept cycle with measured QNX gates"
```

---

## Self-review

- **Spec coverage:** 10 Hz pose (T6), hybrid front-end (T1/T5), watchdog (T1 tests, T5 selftest, T3 tuning), crumbs (T1 `crumb_due`, T6 wiring), honest failure (RF 1–5 tests + T6 gate 4), laptop-first convention (T1–T3 precede all C++), F1 decision (T4), F9 in-process keyframe copy (T2 Step 3, T5 interface, T6 Step 1), F8 stride from real rate (T6 gate 2), no-ABI-change (constraint, verified by task file lists). The spec's B-fallback is realized as Task 4 Step 2's recorded flip. Gaps: none open.
- **Type consistency:** `vo_core` signatures in T1 match T2's consumed list; `VoConfig`/`VoStep` names in T5 match T6's Consumes block.
- **Proportion:** the plan is shorter than the spec + code it describes; bodies are left to signatures and tests except where the spec pins values.
