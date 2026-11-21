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

Omit `--image` to loop a webcam until Ctrl-C, or add `--once` for one capture. `--out -` writes to stdout. `--fov` (bare flag = 66°) guesses a pinhole so `xyz_cam` exists without a chessboard. Pass `--calib models/calib.json` instead if you have one. Without either, boxes still emit but `xyz_cam`/`xyz_world` are omitted. Guessed or chessboard geometry still needs a tape check before spoken metres. Replay with `cd laptop/bridge && node main.js /tmp/beacon-live.jsonl`.

Live webcam to the dashboard: UDP, one world object per datagram, no replay file needed. Three terminals, from the repo root:

```sh
cd laptop/bridge && npm start
cd laptop/dashboard && npm run dev
/tmp/beacon-probe-venv/bin/python percept/tools/probe_to_world.py \
  --yolo models/yoloe26n_320.onnx \
  --depth models/depth_anything_v2_metric_indoor_small.onnx \
  --hands --hand-model models/hand_landmarker.task \
  --fov \
  --udp
```

Bare `--udp` targets `127.0.0.1:5005`; use `--udp HOST:PORT` for another bridge. `--out /tmp/beacon-live.jsonl` may be combined with `--udp` to record while streaming. No `--out` is needed for live-only use.

Live readout: while the probe runs, watch stderr for one compact `seq=... mode=... name=... range_m=... d_m=... objects=...` line per record (`range_m=|xyz_cam|`, unknown values omitted); JSONL/UDP are unchanged.

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

Shm reader: `src/head.cpp` builds as `percept-head`. It reads the newest `/beacon_frames` slot, prints the YOLO and depth letterbox affines, and initialises only the ABI fields of `/beacon_depth` and `/beacon_world`. No model runs yet. It writes no detections, depth, hand, or pose data.

Build and check with `camd` running:

```sh
cd camd && make && ./camd --stub --once && cd ../percept && make && ./percept-head --once
```
