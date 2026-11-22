#!/usr/bin/env python3
"""Export Beacon's detect-only YOLOE-26n ONNX with baked prompt labels.

Run on a laptop with network access. The first set_classes() call downloads the
MobileCLIP text encoder. The encoder is used only here; it does not ship in the
ONNX file.

    python3 percept/tools/export_yoloe.py --out models/yoloe26n_320.onnx
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LABELS = REPO_ROOT / "models" / "labels.txt"


def read_labels(path: Path) -> list[str]:
    names = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    names = [name for name in names if name and not name.startswith("#")]
    # The demo vocabulary is 6 nouns (bottle, can, keys, phone, box, mouse).
    # The ceiling stays at 64 because that is what the baked ONNX decoder is
    # sized for; the floor is only a guard against an empty or truncated file.
    if not (1 <= len(names) <= 64):
        raise SystemExit(f"expected 1-64 labels, got {len(names)} in {path}")
    if any(" " in name for name in names):
        raise SystemExit("YOLOE set_classes expects single-token labels")
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "models" / "yoloe26n_320.onnx")
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--checkpoint", default="yoloe-26n-seg.pt")
    args = parser.parse_args()

    from ultralytics import YOLOE

    labels = read_labels(args.labels)
    print(f"baking {len(labels)} labels: {', '.join(labels)}")

    model = YOLOE("yoloe-26n.yaml").load(args.checkpoint)
    model.set_classes(labels, model.get_text_pe(labels))

    exported = Path(
        model.export(format="onnx", imgsz=args.imgsz, dynamic=False, simplify=True)
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if exported.resolve() != args.out.resolve():
        shutil.copyfile(exported, args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
