# models

Large files are not committed (see `.gitignore`). Owner: Nathan. Bake list and export rules: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §9. Expected here:

- `yoloe26n_320.onnx` (baked prompts, detect-only) and `labels.txt`. The labels file is the runtime vocabulary and is committed.
- Depth Anything V2 Metric Indoor Small ONNX
- MediaPipe hand models (`hand_landmarker.task` for the Tasks API, or the legacy palm/landmark TFLite pair)
- whisper.cpp `ggml-tiny.en.bin`, optional llama.cpp GGUF

Note where each file came from here so anyone can rebuild the folder.

Laptop geometry probe: `percept/tools/probe_frame.py`. It reads one frame and prints full-frame boxes, metric depth, and landmark 8. Run `python3 percept/tools/probe_frame.py --help` for the model paths and calibration options.
