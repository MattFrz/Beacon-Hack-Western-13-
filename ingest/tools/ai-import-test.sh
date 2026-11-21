#!/bin/sh
# ai-import-test.sh: verify the QNX apk-repo AI stack on the Pi, no camera.
# Staged tree: /data/home/qnxuser/airoot (see docs/qnx-integration-plan.md).
# Run as qnxuser on the loaner: sh ai-import-test.sh
set -e
AIROOT=/data/home/qnxuser/airoot
export LD_LIBRARY_PATH=$AIROOT/usr/lib
export PYTHONPATH=$AIROOT/usr/lib/python3.14/site-packages

echo "== libs present =="
for l in libregex.so.1 libonnxruntime.so.1 libwhisper.so.1 libc++.so.1 libicuuc.so.76; do
  if ls /usr/lib/$l >/dev/null 2>&1 || ls $AIROOT/usr/lib/$l >/dev/null 2>&1 || \
     ls $AIROOT/usr/lib/python3.14/site-packages/onnxruntime/capi/$l >/dev/null 2>&1; then
    echo "  ok   $l"
  else
    echo "  MISS $l"
  fi
done

echo "== whisper.cpp =="
$AIROOT/usr/bin/whisper-cli --version 2>&1 | head -2 || true

echo "== python imports =="
python3 - <<'EOF'
import onnxruntime, numpy, cv2, mediapipe
print("onnxruntime", onnxruntime.__version__)
print("numpy", numpy.__version__)
print("cv2", cv2.__version__)
print("mediapipe", mediapipe.__version__)
EOF

echo "== one real inference (16-class YOLOE bake) =="
python3 - "$@" <<'EOF'
import sys, onnxruntime, numpy
model = "/data/home/qnxuser/beacon-test/models/yoloe26n_320.onnx"
try:
    import hashlib
    h = hashlib.sha256(open(model, "rb").read()).hexdigest()
    print("model sha256", h[:16])
except OSError as e:
    print("model missing:", e); sys.exit(1)
so = onnxruntime.SessionOptions()
so.intra_op_num_threads = 3
sess = onnxruntime.InferenceSession(model, so, providers=["CPUExecutionProvider"])
print("input", [i.name for i in sess.get_inputs()], [i.shape for i in sess.get_inputs()])
print("output", [o.name for o in sess.get_outputs()], [o.shape for o in sess.get_outputs()])
x = numpy.zeros(tuple(sess.get_inputs()[0].shape), dtype=numpy.float32)
out = sess.run(None, {sess.get_inputs()[0].name: x})[0]
print("ran one frame, output shape", out.shape)
EOF
echo "PASS"
