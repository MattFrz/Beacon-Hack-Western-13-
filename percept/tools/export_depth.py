#!/usr/bin/env python3
"""Export Depth Anything V2 Metric Indoor Small to a static metric ONNX.

The runtime supplies a letterboxed, ImageNet-normalized RGB tensor of shape
(1, 3, N, N). The ONNX returns predicted depth in metres with shape (1, N, N).

    python3 percept/tools/export_depth.py --out models/depth_anything_v2_metric_indoor_small.onnx
"""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_MODEL = "depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf"
REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--size", type=int, default=210)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "models" / "depth_anything_v2_metric_indoor_small.onnx",
    )
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()

    if args.size <= 0 or args.size % 14 != 0:
        raise SystemExit("--size must be positive and a multiple of 14")

    import torch
    from transformers import AutoModelForDepthEstimation

    class DepthWrapper(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, pixel_values):
            return self.inner(pixel_values=pixel_values).predicted_depth

    model = AutoModelForDepthEstimation.from_pretrained(args.model).eval()
    wrapped = DepthWrapper(model).eval()
    dummy = torch.randn(1, 3, args.size, args.size, dtype=torch.float32)

    with torch.no_grad():
        sample = wrapped(dummy)
    print(f"sample output shape: {tuple(sample.shape)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        torch.onnx.export(
            wrapped,
            dummy,
            str(args.out),
            input_names=["pixel_values"],
            output_names=["depth"],
            opset_version=args.opset,
            do_constant_folding=True,
        )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
