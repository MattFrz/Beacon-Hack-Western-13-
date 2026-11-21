# models

Large files are not committed (see `.gitignore`). Owner: Nathan. Bake list and export rules: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §9. Expected here:

- `yoloe26n_320.onnx` (baked prompts, detect-only) and `labels.txt`. The labels file is the runtime vocabulary and is committed.
- Depth Anything V2 Metric Indoor Small ONNX
- MediaPipe hand models (`hand_landmarker.task` for the Tasks API, or the legacy palm/landmark TFLite pair)
- whisper.cpp `ggml-tiny.en.bin`, optional llama.cpp GGUF

Note where each file came from here so anyone can rebuild the folder.

Laptop geometry probe: `percept/tools/probe_frame.py`. It reads one frame and prints full-frame boxes, metric depth, and landmark 8. Run `python3 percept/tools/probe_frame.py --help` for the model paths and calibration options.

Export the baked detector with:

```sh
python3 percept/tools/export_yoloe.py --out models/yoloe26n_320.onnx
```

Verified export on 2026-11-21 with Ultralytics 8.4.216 and checkpoint
`yoloe-26n-seg.pt` from the 8.4.0 assets. The first `set_classes()` call
downloads `mobileclip2_b.ts` (242 MB); that encoder is export-only. The result
was a detect-only static ONNX, 9.3 MB, output shape `(1, 21, 2100)` for 17
baked labels plus 4 box coordinates across 2100 raw proposals. The ONNX has no
NMS; QNX must letterbox, decode, and NMS the raw output. `probe_frame.py` uses
its own ONNX Runtime path for that by default and detected people in `bus.jpg`.
`--yolo-runtime ultralytics` remains available as a comparison path where the
Ultralytics package is installed.

Export depth with:

```sh
python3 percept/tools/export_depth.py --out models/depth_anything_v2_metric_indoor_small.onnx
```

Verified with Transformers 5.24.0 and ONNX Runtime 1.32.0 on the laptop. The
static input is `(1, 3, 210, 210)` and the output is metric depth `(1, 210, 210)`.
`probe_frame.py` combined it with the raw-decoded baked YOLOE ONNX on `bus.jpg`
and sampled 6.1 to 10.3 m at the detected person centres. Those are model outputs
that still need a tape check before spoken metres are allowed.

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

Local SHA-256 values for the exported files:

| File | SHA-256 |
| --- | --- |
| `yoloe26n_320.onnx` | `1a1f94415be20a123d0db389583bbb41bc3d7efe6ccd5f16af52bf467318dea7` |
| `depth_anything_v2_metric_indoor_small.onnx` | `494113edc11df63ebfd420b9162bc1fc026ec7e72cee855e3d10122db671ced6` |
| `depth_anything_v2_metric_indoor_small.onnx.data` | `11a48f4d0c5413df3172ccd261481f7aff9e376811cbd6e35e7c52c87614205e` |
