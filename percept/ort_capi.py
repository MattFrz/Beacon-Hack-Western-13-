"""Minimal ONNX Runtime binding over the C API, using ctypes.

Why: QNX's python3-onnxruntime package (repo.oss.qnx.com 8.0.5/extra) ships
`libonnxruntime.so` but omits the `onnxruntime_pybind11_state` extension, so
`import onnxruntime` fails on the loaner Pi with ModuleNotFoundError.  The C
API is stable and complete, so we bind it directly: no pybind, no rebuild, and
the same code runs on the laptop and on QNX.

Scope is deliberately small -- session creation, tensor I/O, Run.  This is not
a general ORT binding; it covers what percept needs.

    sess = Session("models/yoloe26n_320.onnx", threads=3)
    print(sess.inputs, sess.outputs)
    out = sess.run({"images": np.zeros((1, 3, 320, 320), np.float32)})
"""

import ctypes
import os
import sys

import numpy as np

from .ort_capi_table import ORT_API_TABLE

# OrtLoggingLevel
_LOGGING_WARNING = 2
# ONNXTensorElementDataType
_TYPE_FLOAT = 1
_TYPE_MAP = {
    _TYPE_FLOAT: np.float32,
    2: np.uint8,   # UINT8
    3: np.int8,
    6: np.int32,
    7: np.int64,
    10: np.float16,
    11: np.float64,
}
# OrtAllocatorType / OrtMemType
_ARENA_ALLOCATOR = 1
_MEMTYPE_DEFAULT = 0

API_VERSION_FALLBACKS = (23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13)


class OrtError(RuntimeError):
    pass


class _OrtApiBase(ctypes.Structure):
    _fields_ = [
        ("GetApi", ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_uint32)),
        ("GetVersionString", ctypes.CFUNCTYPE(ctypes.c_char_p)),
    ]


_api = None
_lib = None


def _find_library():
    """Locate libonnxruntime, tolerating the repo layout and PYTHONPATH."""
    env = os.environ.get("ORT_LIB")
    if env:
        return env
    names = ("libonnxruntime.so.1", "libonnxruntime.so")
    roots = [
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.environ.get("AIROOT", "/data/home/qnxuser/airoot"),
        "/usr",
    ]
    subdirs = ("", "usr/lib", "lib", "usr/lib/python3.14/site-packages/onnxruntime/capi")
    for root in roots:
        for sub in subdirs:
            for name in names:
                cand = os.path.join(root, sub, name) if sub else os.path.join(root, name)
                if os.path.exists(cand):
                    return cand
    return names[0]  # let the dynamic linker try


def api():
    """Return the OrtApi function table bound as callable ctypes objects."""
    global _api, _lib
    if _api is not None:
        return _api

    path = _find_library()
    try:
        _lib = ctypes.CDLL(path)
    except OSError as e:
        raise OrtError(f"cannot load onnxruntime from {path!r}: {e}") from e

    _lib.OrtGetApiBase.restype = ctypes.POINTER(_OrtApiBase)
    base = _lib.OrtGetApiBase()
    if not base:
        raise OrtError("OrtGetApiBase() returned NULL")

    table = None
    for ver in API_VERSION_FALLBACKS:
        ptr = base.contents.GetApi(ver)
        if ptr:
            table = ptr
            break
    if not table:
        raise OrtError("no supported OrtApi version (tried %s)" % (API_VERSION_FALLBACKS,))

    # Bind every function pointer in declared order.
    fns = {}
    for idx, (name, restype, argtypes) in enumerate(ORT_API_TABLE):
        proto = ctypes.CFUNCTYPE(restype, *argtypes)
        fns[name] = proto(_read_ptr(table, idx * ctypes.sizeof(ctypes.c_void_p)))
    fns["__version_string__"] = lambda: base.contents.GetVersionString().decode()
    _api = fns
    return _api


def _read_ptr(table, offset):
    """Read the function pointer at table+offset (table is an OrtApi* int)."""
    slot = ctypes.cast(table + offset, ctypes.POINTER(ctypes.c_void_p))
    return slot.contents.value


def _check(status):
    """Raise OrtError if an OrtStatus* signals failure."""
    if not status:
        return
    api_ = api()
    msg = ctypes.cast(api_["GetErrorMessage"](status), ctypes.c_char_p).value
    code = api_["GetErrorCode"](status)
    api_["ReleaseStatus"](status)
    raise OrtError(f"ORT error {code}: {msg.decode() if msg else '?'}")


class TensorInfo:
    __slots__ = ("name", "shape", "elem_type", "dtype")

    def __init__(self, name, shape, elem_type):
        self.name = name
        self.shape = tuple(shape)
        self.elem_type = elem_type
        self.dtype = _TYPE_MAP.get(elem_type, np.float32)

    def __repr__(self):
        return f"TensorInfo({self.name!r}, shape={self.shape}, dtype={np.dtype(self.dtype).name})"


class Session:
    """An OrtSession. Call close() or use as a context manager."""

    def __init__(self, model_path, threads=0, graph_opt=0):
        a = api()
        self._env = ctypes.c_void_p()
        _check(a["CreateEnv"](_LOGGING_WARNING, b"beacon", ctypes.byref(self._env)))

        self._opts = ctypes.c_void_p()
        _check(a["CreateSessionOptions"](ctypes.byref(self._opts)))
        if threads:
            _check(a["SetIntraOpNumThreads"](self._opts, threads))
            _check(a["SetInterOpNumThreads"](self._opts, 1))

        # Prefer loading from the path: models with external weights (e.g.
        # Depth Anything's .onnx.data sibling) are resolved relative to the
        # model file, which in-memory loading cannot do.
        self._sess = ctypes.c_void_p()
        try:
            _check(a["CreateSession"](self._env, os.fsencode(model_path),
                                      self._opts, ctypes.byref(self._sess)))
        except OrtError:
            with open(model_path, "rb") as fh:
                blob = fh.read()
            buf = ctypes.create_string_buffer(blob, len(blob))
            self._model_buf = buf  # keep alive
            self._sess = ctypes.c_void_p()
            _check(a["CreateSessionFromArray"](self._env, buf, len(blob),
                                               self._opts, ctypes.byref(self._sess)))

        self._alloc = ctypes.c_void_p()
        _check(a["GetAllocatorWithDefaultOptions"](ctypes.byref(self._alloc)))
        self.inputs = self._describe(a["SessionGetInputCount"], a["SessionGetInputName"],
                                     a["SessionGetInputTypeInfo"])
        self.outputs = self._describe(a["SessionGetOutputCount"], a["SessionGetOutputName"],
                                      a["SessionGetOutputTypeInfo"])
        # One reusable CPU memory info.
        self._meminfo = ctypes.c_void_p()
        _check(a["CreateCpuMemoryInfo"](_ARENA_ALLOCATOR, _MEMTYPE_DEFAULT,
                                        ctypes.byref(self._meminfo)))

    # -- metadata ---------------------------------------------------------
    def _describe(self, get_count, get_name, get_type_info):
        a = api()
        count = ctypes.c_size_t()
        _check(get_count(self._sess, ctypes.byref(count)))
        infos = []
        for i in range(count.value):
            name_ptr = ctypes.c_char_p()
            _check(get_name(self._sess, i, self._alloc, ctypes.byref(name_ptr)))
            name = name_ptr.value.decode()
            a["AllocatorFree"](self._alloc, ctypes.cast(name_ptr, ctypes.c_void_p))

            ti = ctypes.c_void_p()
            _check(get_type_info(self._sess, i, ctypes.byref(ti)))
            try:
                tensor_info = ctypes.c_void_p()
                _check(a["CastTypeInfoToTensorInfo"](ti, ctypes.byref(tensor_info)))
                dims = ctypes.c_size_t()
                _check(a["GetDimensionsCount"](tensor_info, ctypes.byref(dims)))
                arr = (ctypes.c_int64 * dims.value)()
                _check(a["GetDimensions"](tensor_info, arr, dims.value))
                et = ctypes.c_int()
                _check(a["GetTensorElementType"](tensor_info, ctypes.byref(et)))
                infos.append(TensorInfo(name, list(arr), et.value))
            finally:
                a["ReleaseTypeInfo"](ti)
        return infos

    # -- run --------------------------------------------------------------
    def run(self, feed, output_names=None):
        """Run the graph. feed: {name: np.ndarray}. Returns {name: np.ndarray}."""
        a = api()
        names_in = [n.encode() for n in feed]
        n_in = len(names_in)
        values_in = (ctypes.c_void_p * n_in)()
        keep = []
        for i, (name, arr) in enumerate(feed.items()):
            arr = np.ascontiguousarray(arr)
            info = next((x for x in self.inputs if x.name == name), None)
            if info is None:
                raise OrtError(f"unknown input {name!r}; expected one of "
                               f"{[x.name for x in self.inputs]}")
            if arr.dtype != info.dtype:
                arr = arr.astype(info.dtype)
            shape = (ctypes.c_int64 * arr.ndim)(*arr.shape)
            val = ctypes.c_void_p()
            _check(a["CreateTensorWithDataAsOrtValue"](
                self._meminfo, arr.ctypes.data_as(ctypes.c_void_p), arr.nbytes,
                shape, arr.ndim, info.elem_type, ctypes.byref(val)))
            values_in[i] = val
            keep.append((arr, shape, val))

        names_out = [x.name for x in self.outputs] if output_names is None else output_names
        n_out = len(names_out)
        c_names_out = (ctypes.c_char_p * n_out)(*[x.encode() for x in names_out])
        values_out = (ctypes.c_void_p * n_out)()
        try:
            _check(a["Run"](self._sess, None,
                            (ctypes.c_char_p * n_in)(*names_in), values_in, n_in,
                            c_names_out, n_out, values_out))
            result = {}
            for i, name in enumerate(names_out):
                result[name] = self._to_numpy(values_out[i])
            return result
        finally:
            for _, _, val in keep:
                a["ReleaseValue"](val)
            for i in range(n_out):
                if values_out[i]:
                    a["ReleaseValue"](values_out[i])

    def _to_numpy(self, value):
        a = api()
        ti = ctypes.c_void_p()
        _check(a["GetTensorTypeAndShape"](value, ctypes.byref(ti)))
        try:
            dims = ctypes.c_size_t()
            _check(a["GetDimensionsCount"](ti, ctypes.byref(dims)))
            arr_shape = (ctypes.c_int64 * dims.value)()
            _check(a["GetDimensions"](ti, arr_shape, dims.value))
            et = ctypes.c_int()
            _check(a["GetTensorElementType"](ti, ctypes.byref(et)))
            shape = tuple(arr_shape)
            dtype = _TYPE_MAP.get(et.value, np.float32)
            ptr = ctypes.c_void_p()
            _check(a["GetTensorMutableData"](value, ctypes.byref(ptr)))
            size = int(np.prod(shape)) if shape else 1
            buf = (ctypes.c_char * (size * np.dtype(dtype).itemsize)).from_address(ptr.value)
            return np.frombuffer(buf, dtype=dtype).reshape(shape).copy()
        finally:
            a["ReleaseTensorTypeAndShapeInfo"](ti)

    # -- lifecycle --------------------------------------------------------
    def close(self):
        a = api()
        if getattr(self, "_sess", None):
            a["ReleaseSession"](self._sess)
            self._sess = None
        if getattr(self, "_meminfo", None):
            a["ReleaseMemoryInfo"](self._meminfo)
            self._meminfo = None
        if getattr(self, "_opts", None):
            a["ReleaseSessionOptions"](self._opts)
            self._opts = None
        if getattr(self, "_env", None):
            a["ReleaseEnv"](self._env)
            self._env = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def version():
    return api()["__version_string__"]()


if __name__ == "__main__":
    print("onnxruntime", version(), "from", _find_library())
    if len(sys.argv) > 1:
        with Session(sys.argv[1], threads=3) as s:
            print("inputs ", s.inputs)
            print("outputs", s.outputs)
