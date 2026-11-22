#!/usr/bin/env python3
"""Generate a ctypes view of OrtApi from onnxruntime_c_api.h.

Why this exists: QNX's python3-onnxruntime package ships the ORT shared
libraries but *not* the `onnxruntime_pybind11_state` extension, so plain
`import onnxruntime` fails on the loaner Pi.  The C API is a flat table of
function pointers, so ctypes can call it directly -- but only if the struct
layout is byte-exact, because one wrong offset silently calls a different
function.  Rather than hand-copy 383 signatures, this parses the header the
target actually ships and emits the table in declaration order.

Members are declared three ways in the header, all handled here:

    OrtStatus*(ORT_API_CALL* Name)(args)      direct
    ORT_API2_STATUS(Name, args)               macro -> OrtStatus* Name(args)
    ORT_CLASS_RELEASE(X)                      macro -> void ReleaseX(OrtX*)
    ORT_API_T(RET, Name, args)                macro -> RET Name(args)

Output: percept/ort_capi_table.py (generated; do not edit by hand).
Usage:  python3 percept/tools/gen_ort_capi_table.py <onnxruntime_c_api.h>
"""

import re
import sys

# Ort opaque handles are all pointers; these scalars get real ctypes types.
SCALARS = {
    "char": "c_char",
    "int": "c_int",
    "size_t": "c_size_t",
    "int64_t": "c_int64",
    "uint64_t": "c_uint64",
    "uint32_t": "c_uint32",
    "int32_t": "c_int32",
    "uint8_t": "c_uint8",
    "float": "c_float",
    "bool": "c_bool",
    "double": "c_double",
}
# Enums are ints on the wire.
ENUMS = {
    "OrtErrorCode", "ONNXTensorElementDataType", "OrtLoggingLevel",
    "OrtAllocatorType", "OrtMemType", "OrtFormat", "OrtCudnnConvAlgoSearch",
}
SAL = re.compile(r"_(In|Out|Inout|Frees_ptr_opt|Ret_maybenull|Check_return|Success|Frees_ptr)_?")


def clean(t):
    t = SAL.sub("", t)
    for tok in ("const", "struct", "enum", "_Success_", "_Check_return_",
                "_Ret_maybenull_", "_Must_inspect_result_", "ONNX_STATIC_"):
        t = re.sub(rf"\b{re.escape(tok)}\b", "", t)
    return " ".join(t.split())


def ctype_of(tok):
    t = clean(tok).strip()
    if not t or t == "void":
        return "None"
    if "*" in t:
        base = clean(t.split("*")[0]).strip()
        if base in SCALARS:
            star = t.count("*")
            inner = SCALARS[base]
            # char* is a string-ish pointer; keep it a raw pointer for args.
            return "POINTER(" * star + inner + ")" * star
        return "c_void_p"
    if t in SCALARS:
        return SCALARS[t]
    if t in ENUMS:
        return "c_int"
    # every remaining Ort* / OrtSomethingT is an opaque handle
    return "c_void_p"


def expand(body):
    """Rewrite the three declaration macros into real declarations."""
    # ORT_API2_STATUS(Name, args) -> OrtStatus*(ORT_API_CALL* Name)(args)
    def api2(m):
        return f"OrtStatus* (ORT_API_CALL* {m.group(1)})({m.group(2)})"

    body = re.sub(r"ORT_API2_STATUS\(\s*(\w+)\s*,(.*?)\)\s*;", lambda m: api2(m) + ";",
                  body, flags=re.S)
    # ORT_CLASS_RELEASE(X) -> void(ORT_API_CALL* ReleaseX)(OrtX* input)
    body = re.sub(r"ORT_CLASS_RELEASE\(\s*(\w+)\s*\)\s*;",
                  lambda m: f"void(ORT_API_CALL* Release{m.group(1)})(Ort{m.group(1)}* input);",
                  body)
    # ORT_API_T(RET, Name, args) -> RET(ORT_API_CALL* Name)(args)
    def apit(m):
        return f"{m.group(1)}(ORT_API_CALL* {m.group(2)})({m.group(3)})"

    body = re.sub(r"ORT_API_T\(\s*([\w\s\*]+?)\s*,\s*(\w+)\s*,(.*?)\)\s*;",
                  lambda m: apit(m) + ";", body, flags=re.S)
    return body


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    src = open(sys.argv[1], encoding="utf-8", errors="replace").read()

    # Isolate the struct body.
    body = src.split("struct OrtApi {", 1)[1]
    body = body.split("\n};", 1)[0]

    # Strip comments, then expand macros.
    body = re.sub(r"/\*.*?\*/", " ", body, flags=re.S)
    body = re.sub(r"//[^\n]*", " ", body)
    body = expand(body)
    # Trailing annotation macros sit between the closing paren and the ';'.
    body = re.sub(r"\b(NO_EXCEPTION|ORT_ALL_ARGS_NONNULL|ORT_MUST_USE_RESULT|"
                  r"ORT_WARN_UNUSED_RESULT)\b", " ", body)

    members = []
    for decl in body.split(";"):
        d = " ".join(decl.split())
        if not d:
            continue
        m = re.search(r"([\w\s\*]+?)\(\s*(?:ORT_API_CALL\s*)?\*\s*(\w+)\s*\)\s*\((.*)\)[^;]*$", d, re.S)
        if not m:
            continue
        ret, name, args = m.group(1).strip(), m.group(2), m.group(3)
        members.append((name, ctype_of(ret), [ctype_of(a) for a in split_args(args)]))

    if len(members) < 300:
        print(f"ERROR: only parsed {len(members)} members; the header layout "
              f"changed -- refusing to emit a wrong table", file=sys.stderr)
        return 1

    out = [
        '"""Generated from onnxruntime_c_api.h -- do not edit by hand.',
        "",
        "OrtApi is a flat table of function pointers. Getting one offset wrong",
        "calls a different function with no error, so the order below is the",
        "declaration order in the header the target ships. Regenerate with",
        "percept/tools/gen_ort_capi_table.py against that header.",
        '"""',
        "",
        "from ctypes import (POINTER, c_bool, c_char, c_double, c_float, c_int,",
        "                    c_int32, c_int64, c_size_t, c_uint32, c_uint64,",
        "                    c_uint8, c_void_p)",
        "",
        "# (name, restype, [argtypes]), in header order.",
        "ORT_API_TABLE = [",
    ]
    for name, rt, args in members:
        out.append(f"    ({name!r}, {rt}, [{', '.join(args)}]),")
    out += ["]", "", f"ORT_API_COUNT = {len(members)}", ""]

    with open("percept/ort_capi_table.py", "w") as fh:
        fh.write("\n".join(out))
    print(f"wrote percept/ort_capi_table.py: {len(members)} functions")
    return 0


def split_args(args):
    out, buf, depth = [], "", 0
    for ch in args:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        out.append(buf)
    return [a for a in out if clean(a).strip() and clean(a).strip() != "void"]


if __name__ == "__main__":
    sys.exit(main())
