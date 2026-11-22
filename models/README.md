# models

Large files are not committed (see `.gitignore`). Owner: Nathan. Bake list and export rules: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §9. Expected here:

- `yoloe26n_320.onnx` (baked prompts, detect-only) and `labels.txt`. The labels file is the runtime vocabulary and is committed.
- Depth Anything V2 Metric Indoor Small ONNX
- MediaPipe hand models (`hand_landmarker.task` for the Tasks API, or the legacy palm/landmark TFLite pair)
- whisper.cpp `ggml-tiny.en.bin`, optional llama.cpp GGUF

Note where each file came from here so anyone can rebuild the folder.

Laptop geometry probe: `percept/tools/probe_frame.py`. It reads one frame and prints full-frame boxes, metric depth, and landmark 8. Run `python3 percept/tools/probe_frame.py --help` for the model paths and calibration options.

`calib.json` is laptop-local (gitignored), written by `percept/tools/calibrate_camera.py` with `{fx, fy, cx, cy, W, H, width, height}` for the C270/probe resolution. It is not a model file, and it is never copied into `include/beacon.h`.

Export the baked detector with:

```sh
python3 percept/tools/export_yoloe.py --out models/yoloe26n_320.onnx
```

Verified export on 2026-11-21 with Ultralytics 8.4.216 and checkpoint
`yoloe-26n-seg.pt` from the 8.4.0 assets (local copy
`/tmp/beacon-model-export/yoloe-26n-seg.pt`). The first `set_classes()` call
uses export-only `mobileclip2_b.ts`. Re-exported 2026-11-21 19:20 UTC after
expanding `labels.txt` to 64 single-token names: detect-only static ONNX, 9.3
MB, SHA-256
`f1cef138ab5d59a42b916079374fae27fd1fe426abb84d7c9598ca379a56523b`, output
`(1, 68, 2100)` (4 box coords + 64 labels, 2100 raw proposals). The ONNX has no
NMS; QNX must letterbox, decode, and NMS the raw output. `probe_frame.py` uses
its own ONNX Runtime path for that by default. After this bake, a frame at 2 s
from `/home/nate/Downloads/20261121_135348.mp4` at `--conf 0.15` found `person`
at 0.68/0.37/0.36, `mouse` at 0.65/0.28, `chair` at 0.48/0.32, `tv` at 0.48,
`laptop` at 0.42, `bottle` at 0.40, `handbag` at 0.27, `wallet` at 0.18, and
`remote` at 0.16. `--yolo-runtime ultralytics` remains available as a
comparison path where the Ultralytics package is installed.

Export depth with:

```sh
python3 percept/tools/export_depth.py --out models/depth_anything_v2_metric_indoor_small.onnx
```

Verified with Transformers 5.24.0 and ONNX Runtime 1.32.0 on the laptop. The
static input is `(1, 3, 210, 210)` and the output is metric depth `(1, 210, 210)`.
`probe_frame.py` combined it with the raw-decoded baked YOLOE ONNX on `bus.jpg`
and sampled 6.1 to 10.3 m at the detected person centres (17-label bake, no
`--fov`). After the 32-label re-export, the same image with `--fov` sampled
6.1 to 10.4 m. Those are model outputs that still need a tape check before
spoken metres are allowed.

Hand model downloaded from:

```sh
curl -fsSL -o models/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

SHA-256 `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`.
On this NixOS laptop, MediaPipe Tasks needed `libEGL.so.1` from `libglvnd` on
`LD_LIBRARY_PATH`. With that set, `probe_frame.py --hands --hand-model
models/hand_landmarker.task` found a fingertip in the MediaPipe `woman_hands.jpg`
sample.

Demo-class probes on 2026-11-21, using the raw ORT decode path:

| Image | Result |
| --- | --- |
| Wikimedia `PET_Bottle_Water.jpg` | `bottle` at 0.36 and 0.29 with the default 0.25 threshold |
| Wikimedia `Car_keys.jpg` | `keychain` at 0.166 with `--conf 0.15`; missed at the default 0.25 threshold |

The keys result is weak. It supports the synonym-table need for `keys` versus
`keychain`, but it is not a Sunday-ready threshold. Probe the actual demo
objects through the C270 before choosing a runtime confidence value.

Local SHA-256 values for the exported files:

| File | SHA-256 |
| --- | --- |
| `yoloe26n_320.onnx` | `f1cef138ab5d59a42b916079374fae27fd1fe426abb84d7c9598ca379a56523b` |
| `depth_anything_v2_metric_indoor_small.onnx` | `494113edc11df63ebfd420b9162bc1fc026ec7e72cee855e3d10122db671ced6` |
| `depth_anything_v2_metric_indoor_small.onnx.data` | `11a48f4d0c5413df3172ccd261481f7aff9e376811cbd6e35e7c52c87614205e` |
