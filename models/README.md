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
baked labels plus 4 box coordinates. `probe_frame.py` loaded it and detected
people in `bus.jpg`.
