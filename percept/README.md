# percept

Owner: Nathan. C++, cores 1-3 (`0xe`), `SCHED_RR` 22. YOLOE-26n, Depth Anything V2, MediaPipe hands, unproject, VO. Writes `/beacon_depth` and the percept-owned part of `/beacon_world`. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5, §7, §8.

Laptop stand-in: `tools/probe_frame.py`. It is Python and runs on a laptop only. It checks letterbox inverses, full-frame landmark 8, and metric depth before any QNX code is written.

World JSONL: `tools/probe_to_world.py` wraps the same probe and prints one dashboard line per frame. For a single image:

```sh
python3 percept/tools/probe_to_world.py \
  --image /tmp/keys.jpg \
  --yolo models/yoloe26n_320.onnx \
  --depth models/depth_anything_v2_metric_indoor_small.onnx \
  --hands --hand-model models/hand_landmarker.task \
  --calib models/calib.json \
  --out /tmp/beacon-live.jsonl
```

Omit `--image` to loop a webcam until Ctrl-C, or add `--once` for one capture. `--out -` writes to stdout. Without `--calib`, boxes still emit but `xyz_cam`/`xyz_world` are omitted. Replay with `cd laptop/bridge && node main.js /tmp/beacon-live.jsonl`.

Live webcam to the dashboard: UDP, one world object per datagram, no replay file needed. Start the bridge and dashboard first, then the probe:

```sh
cd laptop/bridge && npm start
cd laptop/dashboard && npm run dev
/tmp/beacon-probe-venv/bin/python percept/tools/probe_to_world.py \
  --yolo models/yoloe26n_320.onnx \
  --depth models/depth_anything_v2_metric_indoor_small.onnx \
  --hands --hand-model models/hand_landmarker.task \
  --calib models/calib.json \
  --udp
```

Bare `--udp` targets `127.0.0.1:5005`; use `--udp HOST:PORT` for another bridge. `--out /tmp/beacon-live.jsonl` may be combined with `--udp` to record while streaming. No `--out` is needed for live-only use.

Laptop-only camera calibration (9x6 inner corners, measured square side):

```sh
python3 percept/tools/calibrate_camera.py \
  --images '/tmp/beacon-chess/*.jpg' \
  --rows 6 --cols 9 --square-m 0.025 \
  --out models/calib.json
```

Capture at the exact resolution used by the probe; `calib.json` is laptop-local
and gitignored, and does not make metric depth spoken without a tape check.

Shm reader: `src/head.cpp` builds as `percept-head`. It reads the newest `/beacon_frames` slot, prints the YOLO and depth letterbox affines, and initialises only the ABI fields of `/beacon_depth` and `/beacon_world`. No model runs yet. It writes no detections, depth, hand, or pose data.

Build and check with `camd` running:

```sh
cd camd && make && ./camd --stub --once && cd ../percept && make && ./percept-head --once
```
