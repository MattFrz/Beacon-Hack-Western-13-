"""Make `import onnxruntime` work on QNX, where the pip/pybind wheel does not.

The loaner Pi installs QNX's python3-onnxruntime package, which carries the ORT
shared libraries but not the `onnxruntime_pybind11_state` extension, so the real
onnxruntime package raises ModuleNotFoundError.  percept/tools/probe_frame.py
only ever uses a handful of ORT entry points, so we provide those over the C API
(percept/ort_capi.py) and register the module before percept imports it:

    from percept import ort_shim; ort_shim.install()
    import onnxruntime as ort            # now resolves to the C-API shim

Nothing here is a general ORT reimplementation; it is the slice that percept
needs. If the real onnxruntime is importable, install() leaves it alone.
"""

from __future__ import annotations

import sys
import types

import numpy as np

from . import ort_capi

_installed = False


class SessionOptions:
    """The subset of ort.SessionOptions percept touches."""

    def __init__(self):
        self.intra_op_num_threads = 0
        self.inter_op_num_threads = 0
        self.graph_optimization_level = 0


class InferenceSession:
    """Drop-in for ort.InferenceSession over the C API."""

    def __init__(self, path, sess_options=None, providers=None, **kwargs):
        threads = 0
        if sess_options is not None:
            threads = int(getattr(sess_options, "intra_op_num_threads", 0) or 0)
        self._sess = ort_capi.Session(str(path), threads=threads)
        self._inputs = self._sess.inputs
        self._outputs = self._sess.outputs

    # -- metadata --------------------------------------------------------
    def get_inputs(self):
        return list(self._inputs)

    def get_outputs(self):
        return list(self._outputs)

    def get_providers(self):
        return ["CPUExecutionProvider"]

    # -- inference -------------------------------------------------------
    def run(self, output_names, input_feed, run_options=None):
        result = self._sess.run(input_feed)
        if output_names is None:
            return [result[o.name] for o in self._outputs]
        return [result[n] for n in output_names]

    def close(self):
        self._sess.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def install(force: bool = False) -> bool:
    """Register this shim as `onnxruntime`. Returns True if it took effect.

    If the real package imports cleanly we do nothing, so the shim never
    shadows a working install.
    """
    global _installed
    if _installed and not force:
        return True

    if not force:
        try:
            import onnxruntime  # noqa: F401

            return False
        except Exception:
            pass

    mod = types.ModuleType("onnxruntime")
    mod.InferenceSession = InferenceSession
    mod.SessionOptions = SessionOptions
    mod.get_available_providers = lambda: ["CPUExecutionProvider"]
    mod.__version__ = ort_capi.version()
    mod.__file__ = __file__
    mod.__beacon_shim__ = True

    # Some code paths import onnxruntime.capi.* for version checks.
    capi = types.ModuleType("onnxruntime.capi")
    capi.__beacon_shim__ = True
    mod.capi = capi

    sys.modules["onnxruntime"] = mod
    sys.modules["onnxruntime.capi"] = capi
    _installed = True
    return True


def is_shim(module) -> bool:
    return bool(getattr(module, "__beacon_shim__", False))
