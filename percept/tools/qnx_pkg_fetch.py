#!/usr/bin/env python3
"""Resolve and download the QNX apk-repo dependency closure for Beacon's AI stack.

Method 2B of the openqnx install guide, applied to QNX's own repo
(repo.oss.qnx.com): parse the v2 APKINDEX files, build the dependency closure
from seed packages, download every .apk (they are gzipped tars), for later
manual extraction on the target.

Skips packages the QSTI loaner image already ships (python3, libssl3,
libcrypto3, zlib-ng, zstd-libs, apk-tools, ca-certificates*): repo builds of
those pull QNX-software-center-only deps (qnx-crypto, qnx-io-sock) that are not
in the public repo, and the image copies have the same sonames.
"""

import gzip
import os
import re
import sys
import urllib.request

REPOS = [
    ("8.0.3/core", "https://repo.oss.qnx.com/8.0.3/core/aarch64"),
    ("8.0.3/extra", "https://repo.oss.qnx.com/8.0.3/extra/aarch64"),
    ("8.0.5/core", "https://repo.oss.qnx.com/8.0.5/core/aarch64"),
    ("8.0.5/extra", "https://repo.oss.qnx.com/8.0.5/extra/aarch64"),
]

SEEDS = [
    "python3-onnxruntime",
    "onnxruntime",
    "python3-numpy",
    "python3-opencv",
    "opencv",
    "python3-mediapipe",
    "whisper.cpp",
]

# Provided by the QSTI image already; do not pull their repo counterparts.
SKIP = {
    "python3", "python3-dev", "python3-tests",
    "libssl3", "libcrypto3", "libcrypto", "zlib-ng", "zlib-ng-dev",
    "zstd-libs", "apk-tools", "ca-certificates", "ca-certificates-bundle",
    "p11-kit", "qnx-crypto", "qnx-io-sock",
}

NAME_RE = re.compile(r"^[A-Za-z0-9._+-]+$")


def parse_index(path):
    """APKINDEX v2: blocks of KEY:VALUE lines; package blocks separated by blank lines."""
    import tarfile
    with tarfile.open(path) as tf:
        member = [m for m in tf.getmembers() if m.name.endswith("APKINDEX")][0]
        text = tf.extractfile(member).read().decode("utf-8", errors="replace")
    pkgs = {}
    for block in text.split("\n\n"):
        f = {}
        provides = []
        for line in block.splitlines():
            if len(line) > 2 and line[1] == ":":
                k, v = line[0], line[2:]
                if k == "p":
                    provides.append(v)
                else:
                    f.setdefault(k, v)
        if "P" in f:
            pkg = {
                "name": f["P"], "version": f.get("V", ""), "deps": f.get("D", ""),
                "size": int(f.get("S", "0") or 0), "provides": provides,
                "repo": None,
            }
            # latest version wins per name
            if pkg["name"] not in pkgs or version_gt(pkg["version"], pkgs[pkg["name"]]["version"]):
                pkgs[pkg["name"]] = pkg
    return pkgs


def version_gt(a, b):
    def key(v):
        return [(0, int(x)) if x.isdigit() else (1, x) for x in re.split(r"[._-]", v)]
    return key(a) > key(b)


def dep_names(dep_line):
    out = []
    for tok in re.split(r"[\s,]+", dep_line.strip()):
        if not tok or tok.startswith("!"):
            continue
        name = tok.split("=")[0]
        name = name.split("~")[0].split(">")[0].split("<")[0]
        if name and NAME_RE.match(name):
            out.append(name)
    return out


def dep_names_split(line):
    out, buf, depth = [], "", 0
    for ch in line:
        if ch in "(<":
            depth += 1
        elif ch in ")>":
            depth -= 1
        if ch == "," and depth == 0:
            if buf.strip():
                out.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        out.append(buf.strip())
    return out


def main():
    all_pkgs = {}
    for name, base in REPOS:
        idx_path = f"/tmp/apkin-{name.replace('/', '_')}.tgz"
        if not os.path.exists(idx_path):
            print(f"missing index {idx_path}; download it first", file=sys.stderr)
            return 1
        pkgs = parse_index(idx_path)
        for p in pkgs.values():
            p["repo"] = name
            cur = all_pkgs.get(p["name"])
            if cur is None or version_gt(p["version"], cur["version"]):
                all_pkgs[p["name"]] = p
    print(f"index: {len(all_pkgs)} packages")

    # provider map: provides names -> package name
    providers = {}
    for p in all_pkgs.values():
        for prov in p["provides"]:
            pname = prov.split("=")[0]
            providers.setdefault(pname, p["name"])

    todo = list(SEEDS)
    closure = {}
    while todo:
        name = todo.pop(0)
        if name in SKIP:
            continue
        pkg = all_pkgs.get(name)
        if pkg is None:
            pkg = all_pkgs.get(providers.get(name, ""))
        if pkg is None:
            print(f"  !! not in any repo (and not in SKIP): {name}")
            continue
        if pkg["name"] in closure:
            continue
        closure[pkg["name"]] = pkg
        for dep in dep_names(pkg["deps"]):
            if dep not in SKIP and dep not in closure:
                todo.append(dep)

    total = sum(p["size"] for p in closure.values())
    print(f"closure: {len(closure)} packages, {total/1e6:.1f} MB download")

    os.makedirs("/tmp/qnx-ai-pkgs", exist_ok=True)
    manifest = []
    for name in sorted(closure):
        pkg = closure[name]
        base = dict(REPOS)[pkg["repo"]]
        fname = f"{name}-{pkg['version']}.apk"
        url = f"{base}/{fname}"
        dest = f"/tmp/qnx-ai-pkgs/{fname}"
        manifest.append((fname, url, pkg))
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            print(f"  have   {fname}")
            continue
        try:
            urllib.request.urlretrieve(url, dest)
            ok = open(dest, "rb").read(2) == b"\x1f\x8b"
            print(f"  {'OK ' if ok else 'BAD'}    {fname} ({os.path.getsize(dest)//1024} KiB)")
            if not ok:
                os.unlink(dest)
                return 1
        except Exception as e:
            print(f"  FAIL   {fname}: {e}")
            return 1

    with open("/tmp/qnx-ai-pkgs/MANIFEST", "w") as fh:
        for fname, url, pkg in manifest:
            fh.write(f"{fname}\t{url}\t{pkg['deps']}\n")
    print(f"manifest: /tmp/qnx-ai-pkgs/MANIFEST ({len(manifest)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
