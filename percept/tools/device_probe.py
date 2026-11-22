#!/usr/bin/env python3
"""Run percept/tools/probe_frame.py on QNX, with ORT backed by the C API.

QNX's python3-onnxruntime package ships the ORT libraries without the pybind
extension, so `import onnxruntime` fails there.  percept.ort_shim supplies the
handful of ORT entry points probe_frame uses, over the C API, and this launcher
installs the shim before handing over to the unmodified probe.

Arguments after `--tool NAME --` are that tool's own; everything following is
passed straight through.  Name any percept tool, not just probe_frame:

    python3 percept/tools/device_probe.py -- --image frame.jpg --labels models/labels.txt
    python3 percept/tools/device_probe.py --tool probe_to_world.py -- --udp 127.0.0.1:5006
"""

import runpy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PERCEPT = REPO / "percept" / "tools"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from percept import ort_shim  # noqa: E402

took = ort_shim.install()
print(f"[device_probe] onnxruntime: "
      f"{'C-API shim' if took else 'real package'} "
      f"(ORT {__import__('onnxruntime').__version__})", file=sys.stderr)

argv = sys.argv[1:]
tool = "probe_frame.py"
if len(argv) >= 2 and argv[0] == "--tool":
    tool = argv[1]
    argv = argv[2:]
if argv and argv[0] == "--":
    argv = argv[1:]
script = PERCEPT / tool
if not script.exists():
    raise SystemExit(f"no such percept tool: {script}")

sys.argv = [str(script)] + argv
runpy.run_path(str(script), run_name="__main__")
