#!/usr/bin/env python3
"""VO probe: drive the vo_core step machine over a recorded or live walk.

Laptop bring-up tool only; it never writes shm and never runs on the Pi.
Depth comes from the metric depth ONNX (tape-gated --depth-scale) or, for
hermetic runs, --flat-depth Z which skips the model entirely. Keyframe
material is the frame being processed (spec F9): never re-read from a ring.

Modes (mutually exclusive):
  --record OUT_DIR [--seconds S]   capture the webcam to PNGs, then exit
  --video PATH                     a frame directory or one video file
  --camera N                        live webcam (default 0 when no source)

Examples:
  python3 vo_probe.py --record /tmp/beacon-l-walk --seconds 25
  python3 vo_probe.py --video /tmp/beacon-l-walk --depth models/depth.onnx \
      --depth-scale 0.25 --fov --h-chest 1.4
  python3 vo_probe.py --video /tmp/walk.avi --flat-depth 2.0 --h-chest 1.4 --fov
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from percept.tools import probe_frame, vo_core  # noqa: E402
from percept.tools.probe_frame import (  # noqa: E402
    make_affine,
    parse_csv3,
    predict_depth,
    resolve_calibration,
)

FLAT_GRID = 105          # --flat-depth metres grid size
RECORDED_DT_NS = 33_333_333  # recorded clips are assumed 30 fps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--record", type=Path, metavar="OUT_DIR",
                    help="capture the webcam to OUT_DIR PNGs, then exit")
    src.add_argument("--video", type=Path, metavar="PATH",
                    help="a frame directory (sorted PNGs) or one video file")
    src.add_argument("--camera", type=int, metavar="N",
                     help="live webcam index")
    parser.add_argument("--seconds", type=float, default=30.0,
                        help="capture length for --record (default 30)")
    parser.add_argument("--stride", type=int, default=3,
                        help="consume every Nth camera frame (default 3)")
    parser.add_argument("--depth", type=Path,
                        help="metric depth ONNX; omit with --flat-depth")
    parser.add_argument("--depth-size", type=int, default=210,
                        help="depth net input size (default 210)")
    parser.add_argument("--depth-scale", type=float, default=1.0,
                        help="tape-gated metres correction (laptop: 0.25)")
    parser.add_argument("--flat-depth", type=float, metavar="Z",
                        help="skip the model; metres grid constant Z (bring-up)")
    parser.add_argument("--depth-mean", default="0.485,0.456,0.406")
    parser.add_argument("--depth-std", default="0.229,0.224,0.225")
    parser.add_argument("--depth-pad", default="114,114,114")
    parser.add_argument("--fov", type=float, nargs="?", const=66.0,
                        help="bare = 66 deg pinhole guess; not a chessboard")
    parser.add_argument("--calib", type=Path, help="models/calib.json overrides --fov")
    parser.add_argument("--h-chest", type=float, required=True,
                        help="measured camera height above the floor (watchdog)")
    parser.add_argument("--vo-width", type=int, default=320,
                        help="VO gray working width (default 320)")
    parser.add_argument("--out", type=Path, help="append per-step JSONL here")
    return parser


def record_frames(out_dir: Path, camera: int, seconds: float) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise SystemExit(f"camera {camera} did not open")
    deadline = time.perf_counter() + seconds
    n = 0
    while time.perf_counter() < deadline:
        ok, frame = cap.read()
        if not ok:
            break
        n += 1
        cv2.imwrite(str(out_dir / f"frame_{n:05d}.png"), frame)
    cap.release()
    return n


def iter_frames(path: Path) -> Iterator[np.ndarray]:
    if path.is_dir():
        pngs = sorted(path.glob("*.png"))
        if not pngs:
            raise SystemExit(f"no PNG frames in {path}")
        for p in pngs:
            frame = cv2.imread(str(p))
            if frame is not None:
                yield frame
        return
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise SystemExit(f"cannot open video {path}")
    while True:
        ok, frame = cap.read()
        if not ok:
            cap.release()
            return
        yield frame


def main() -> int:
    args = build_parser().parse_args()
    if args.depth is None and args.flat_depth is None:
        raise SystemExit("need --depth ONNX or --flat-depth Z (bring-up)")
    if args.flat_depth is not None and args.flat_depth <= 0:
        raise SystemExit("--flat-depth must be positive metres")

    if args.record is not None:
        camera = 0 if args.camera is None else args.camera
        n = record_frames(args.record, camera, args.seconds)
        print(f"recorded {n} frames to {args.record}")
        return 0

    if args.camera is not None:
        cap = cv2.VideoCapture(args.camera)
        if not cap.isOpened():
            raise SystemExit(f"camera {args.camera} did not open")

        def frames() -> Iterator[np.ndarray]:
            while True:
                ok, frame = cap.read()
                if not ok:
                    raise SystemExit("camera read failed")
                yield frame
    elif args.video is not None:
        cap = None

        def frames() -> Iterator[np.ndarray]:
            yield from iter_frames(args.video)
    else:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise SystemExit("no source: pass --video, --camera, or --record")

        def frames() -> Iterator[np.ndarray]:
            while True:
                ok, frame = cap.read()
                if not ok:
                    raise SystemExit("camera read failed")
                yield frame

    source = frames()
    first = next(source, None)
    if first is None:
        raise SystemExit("no frames captured")
    frame_h, frame_w = first.shape[:2]
    vo_w = max(64, int(args.vo_width))
    vo_h = max(48, int(round(frame_h * vo_w / frame_w)))

    notes: List[str] = []
    calibration = resolve_calibration(args, frame_w, frame_h, notes)
    if calibration is None:
        raise SystemExit("VO needs intrinsics: pass --fov or --calib")

    if args.flat_depth is not None:
        session = None
        depth_affine = make_affine(frame_w, frame_h, FLAT_GRID, FLAT_GRID)
        scale = 1.0
    else:
        from percept.tools.probe_frame import load_depth_session

        session = load_depth_session(args.depth, None)
        depth_affine = make_affine(frame_w, frame_h, args.depth_size,
                                   args.depth_size)
        scale = float(args.depth_scale)
    mean = parse_csv3(args.depth_mean, "--depth-mean")
    std = parse_csv3(args.depth_std, "--depth-std")
    pad_color = tuple(int(round(v)) for v in
                      parse_csv3(args.depth_pad, "--depth-pad"))

    cfg = vo_core.VoConfig(h_chest_m=float(args.h_chest))
    # The guard is per camera frame (spec "~8 px/frame"); this probe consumes
    # every stride-th frame, so the measured prev->F displacement is stride
    # frames of motion. Scale the threshold to keep the semantics.
    cfg.max_disp_px *= max(1, int(args.stride))

    vo = vo_core.Vo(calibration, scale=scale, h_chest=float(args.h_chest),
                    cam_w=frame_w, cam_h=frame_h, vo_w=vo_w, vo_h=vo_h, cfg=cfg)

    out_handle = args.out.open("a", encoding="utf-8") if args.out else None
    steps = 0
    valid_steps = 0
    corrections = 0
    final_t_m = 0.0
    index = 0  # camera-frame index; frame_id = index + 1

    def process(frame: np.ndarray, live: bool) -> None:
        nonlocal steps, valid_steps, corrections, final_t_m
        frame_id = index + 1
        t_ns = (time.perf_counter_ns() if live
                else int(index * RECORDED_DT_NS))
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                          (vo_w, vo_h), interpolation=cv2.INTER_AREA)
        if session is None:
            metres = np.full((FLAT_GRID, FLAT_GRID), float(args.flat_depth),
                             dtype=np.float32)
        else:
            metres = predict_depth(frame, session, depth_affine, args,
                                   mean, std, pad_color)
        vo.on_depth_frame(gray, metres, depth_affine, frame_id, t_ns)
        step = vo.step(gray, frame_id, t_ns)
        steps += 1
        t = step.T_world_from_cam[:3, 3]
        if step.valid:
            valid_steps += 1
            final_t_m = float(np.linalg.norm(t))
            if step.scale_mult != 1.0:
                corrections += 1
        h = "None" if step.h_est is None else f"{step.h_est:.2f}"
        print(f"frame={frame_id} inliers={step.inliers} "
              f"disp_px={step.median_disp_px:.1f} h_est={h} "
              f"scale={step.scale_mult:.3f} valid={int(step.valid)} "
              f"t=[{t[0]:.3f},{t[1]:.3f},{t[2]:.3f}]", file=sys.stderr)
        if out_handle is not None:
            out_handle.write(json.dumps({
                "frame_id": frame_id, "valid": step.valid,
                "inliers": step.inliers,
                "median_disp_px": round(step.median_disp_px, 2),
                "h_est": step.h_est, "scale_mult": round(step.scale_mult, 4),
                "t": [round(float(v), 4) for v in t],
                "T_world_from_cam": [round(float(v), 5)
                                     for v in step.T_world_from_cam.reshape(-1)],
            }) + "\n")

    stride = max(1, int(args.stride))
    process(first, live=args.camera is not None or (args.video is None
                                                    and args.camera is None
                                                    and args.record is None))
    index = 1
    for frame in source:
        if index % stride != 0:
            index += 1
            continue
        process(frame, live=args.camera is not None)
        index += 1
    if cap is not None:
        cap.release()
    if out_handle is not None:
        out_handle.close()

    summary = {
        "frames": steps,
        "valid_fraction": (valid_steps / steps) if steps else 0.0,
        "correction_rate": (corrections / valid_steps) if valid_steps else 0.0,
        "final_t_m": final_t_m,
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
