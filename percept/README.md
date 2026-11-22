# percept

Owner: Nathan. C++, cores 1-3 (`0xe`), `SCHED_RR` 22. YOLOE-26n, Depth Anything V2, MediaPipe hands, unproject, VO. Writes `/beacon_depth` and the percept-owned part of `/beacon_world`. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5, §7, §8.

Laptop stand-in: `tools/probe_frame.py`. It is Python and runs on a laptop only. It checks letterbox inverses, full-frame landmark 8, and metric depth before any QNX code is written.

World JSONL: `tools/probe_to_world.py` wraps the same probe and prints one dashboard line per frame. Target priority is `models/labels.txt` order, with `keys`, `keychain`, `bottle` first; every baked noun can become the target. For a single image:

```sh
python3 percept/tools/probe_to_world.py \
  --image /tmp/keys.jpg \
  --yolo models/yoloe26n_320.onnx \
  --depth models/depth_anything_v2_metric_indoor_small.onnx \
  --hands --hand-model models/hand_landmarker.task \
  --fov \
  --out /tmp/beacon-live.jsonl
```

Omit `--image` to loop a webcam until Ctrl-C, or add `--once` for one capture. `--video PATH` runs the same pipeline over a prerecorded file frame by frame and stops at EOF (mutually exclusive with `--image`); `--jpeg` works the same way on those frames. `--out -` writes to stdout. `--fov` (bare flag = 66°) guesses a pinhole so `xyz_cam` exists without a chessboard. Pass `--calib models/calib.json` instead if you have one. Without either, boxes still emit but `xyz_cam`/`xyz_world` are omitted. Guessed or chessboard geometry still needs a tape check before spoken metres. Replay with `cd laptop/bridge && node main.js /tmp/beacon-live.jsonl`.

Live webcam to the dashboard: UDP, one world object per datagram, no replay file needed. Three terminals, from the repo root:

```sh
cd laptop/bridge && npm start
cd laptop/dashboard && npm run dev
/tmp/beacon-probe-venv/bin/python percept/tools/probe_to_world.py \
  --yolo models/yoloe26n_320.onnx \
  --depth models/depth_anything_v2_metric_indoor_small.onnx \
  --hands --hand-model models/hand_landmarker.task \
  --fov \
  --udp --jpeg
```

Bare `--udp` targets `127.0.0.1:5005`; use `--udp HOST:PORT` for another bridge. `--out /tmp/beacon-live.jsonl` may be combined with `--udp` to record while streaming. No `--out` is needed for live-only use.

`--jpeg` also sends one downscaled JPEG per frame as a separate raw UDP datagram (not written to `--out` or to the world record); the bridge forwards it to the dashboard Camera panel. It requires `--udp`. Defaults are `--jpeg-width 320`, `--jpeg-quality 60`, `--jpeg-every 1`; raise `--jpeg-every` to lower the preview rate. Frames over 60 KB are dropped with one warning.

The probe opens the camera and creates both ORT sessions and the hand landmarker once per process, then reuses them across frames. `--ort-intra N` (laptop default 4) sets ORT intra-op threads and `--ort-parallel` enables ORT parallel mode; these are laptop-only knobs, not QNX settings. Each record's `last_seen_ns` is the frame capture time; held HOLD data keeps its original timestamp.

Detection depth is the median over the central half of the valid box interior (`box_median`, at least four cells); fingertips use a 3x3 patch median. Bearings still come from `center_px`; the sampler name and `depth_scale` are recorded in `depth_grid`. This is noise rejection, not calibration: `tape_check.py` remains the only absolute-depth gate.

The laptop path needs `--depth-scale 0.25` with the exported indoor model, which overestimates depth about 4x on this camera. Scale is still a manual, tape-gated correction, not a new default; `tape_check.py` is the only pass/fail authority and spoken metres stay off until it passes. Depth is median-stabilised per tracked instance slot, keyed by `(name, slot)` (`--depth-window 5`, `--depth-jump 0.6`, `--depth-evict 10`, `--depth-recover 3` by default), with the unsmoothed sample kept as `z_raw` in probe JSON. Box IoU greedily associates detections with slots across frames (`--slot-iou 0.30` by default, with a centre-distance fallback for degenerate boxes); the assigned `slot` is included in each probe detection for debugging but is not copied into the world record. Unmatched detections get a fresh slot and first sample; slots unseen beyond `--depth-evict` drop their geometry and median history. A genuinely ambiguous match is marked `z_ambiguous` and emits only that frame's raw depth without touching any slot history. A frame with no valid depth sample publishes no `Z_m` and no `xyz_cam`, even for a previously tracked slot.

Live readout: while the probe runs, watch stderr for one compact `seq=... mode=... name=... range_m=... d_m=... objects=...` line per record (`range_m=|xyz_cam|`, unknown values omitted); JSONL/UDP are unchanged.

Mode is LIVE when this record has the target in its latest boxes, HOLD while a missing target is under 1.5 s old, and LOST otherwise (no `d_m`).
HOLD replays the last LIVE objects and target with `in_latest_boxes=false` for a fading dashboard cloud; LOST clears that replay.

Optional chessboard calibration for a better left/right pinhole. Use a Python with OpenCV (this laptop: `/tmp/beacon-probe-venv/bin/python`). You do not need a printer: write a checkerboard, open it fullscreen, then photograph it from several angles.

```sh
/tmp/beacon-probe-venv/bin/python percept/tools/calibrate_camera.py \
  --write-board /tmp/beacon-chessboard.png
# open that PNG fullscreen, measure one square with a ruler, then either:
/tmp/beacon-probe-venv/bin/python percept/tools/calibrate_camera.py \
  --camera 0 --rows 6 --cols 9 --square-m 0.025 \
  --out models/calib.json
# --camera waits for Enter between shots so you can move the board.
# or save 8+ photos and pass --images '/tmp/beacon-chess/*.jpg'
```

`--square-m` is the real size of one square, not a default to trust. On a laptop screen it is usually smaller than 0.025 m. Capture at the same resolution the probe will use. `calib.json` is laptop-local and gitignored. It does not make spoken metres legal without a tape check.

Tape check: with a recorded world/probe JSON (or JSONL from the live probe) and a human-measured distance, run:

```sh
/tmp/beacon-probe-venv/bin/python percept/tools/tape_check.py \
  --json /tmp/beacon-live.jsonl --tape-m 1.0 --name bottle
```

It prints one JSON result with `error_pct`; exit 0 passes, 1 exceeds the default 30% limit, 2 means missing/invalid input. Use `--kind d_m` to check a same-frame hand-to-target `d_m` instead of `|xyz_cam|`. Override the gate with `--limit`; use `--json -` for stdin. A failed check keeps spoken metres and VO off. No camera runs here.

Probe Python tests from the repo root: `make -C percept test-python PYTHON=/tmp/beacon-probe-venv/bin/python`.

Shm reader: `src/head.cpp` builds as `percept-head`. It reads the newest `/beacon_frames` slot, prints the YOLO and depth letterbox affines, and initialises only the ABI fields of `/beacon_depth` and `/beacon_world`. No model runs yet. It writes no detections, depth, hand, or pose data.

Build and check with `camd` running:

```sh
cd camd && make && ./camd --stub --once && cd ../percept && make && ./percept-head --once
```
