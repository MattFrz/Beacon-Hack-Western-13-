#!/usr/bin/env python3
"""Chessboard calibration for the laptop/C270 probe path only.

Detects inner corners in posed chessboard views and writes models/calib.json in
the shape probe_frame.load_calibration reads: fx, fy, cx, cy, W, H, plus
width/height duplicates for the world-frame plan. Never copy these numbers into
include/beacon.h; the QNX camera size stays unset. Intrinsics do not make depth
metric: the tape check is still a separate human step.

Example:

    python3 percept/tools/calibrate_camera.py --write-board /tmp/beacon-chessboard.png
    python3 percept/tools/calibrate_camera.py \
      --images '/tmp/beacon-chess/*.jpg' \
      --rows 6 --cols 9 --square-m 0.025 \
      --out models/calib.json
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MIN_BOARDS = 6
MAX_RMS_PX = 1.5
MIN_POSE_SPREAD_M = 0.02


def write_board(path: Path, rows: int = 6, cols: int = 9, square_px: int = 80) -> Path:
    """Write a printable/screen chessboard with the requested inner-corner counts."""
    import cv2
    import numpy as np

    if rows < 2 or cols < 2:
        raise ValueError("need at least 2x2 inner corners")
    if square_px <= 0:
        raise ValueError("square_px must be positive")
    squares_x = cols + 1
    squares_y = rows + 1
    margin = square_px
    board = np.full(
        (squares_y * square_px + 2 * margin, squares_x * square_px + 2 * margin),
        255,
        dtype=np.uint8,
    )
    for row in range(squares_y):
        for col in range(squares_x):
            if (col + row) % 2 == 0:
                y0 = margin + row * square_px
                x0 = margin + col * square_px
                board[y0 : y0 + square_px, x0 : x0 + square_px] = 0
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), board):
        raise SystemExit(f"could not write chessboard {path}")
    return path


def make_calibration(
    fx: float, fy: float, cx: float, cy: float, width: int, height: int
) -> Dict[str, Any]:
    """Build the JSON payload shared by probe_frame and the world-frame plan."""
    intrinsics = (float(fx), float(fy), float(cx), float(cy))
    if not all(math.isfinite(value) for value in intrinsics):
        raise ValueError("calibration intrinsics must be finite")
    w, h = int(width), int(height)
    if w <= 0 or h <= 0:
        raise ValueError("calibration frame size must be positive")
    return {
        "fx": intrinsics[0],
        "fy": intrinsics[1],
        "cx": intrinsics[2],
        "cy": intrinsics[3],
        "W": w,
        "H": h,
        "width": w,
        "height": h,
    }


def write_calibration(path: Path, calibration: Mapping[str, Any]) -> None:
    path = Path(path)
    path.write_text(json.dumps(calibration, indent=2) + "\n", encoding="utf-8")


def find_corners(image: Any, rows: int, cols: int):
    """Return refined inner corners, or None when the board is not found."""
    import cv2

    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(
        gray,
        (cols, rows),
        cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE,
    )
    if not found:
        return None
    criteria = (
        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.001,
    )
    return cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)


def calibrate_images(
    paths: Iterable[Path], rows: int = 6, cols: int = 9, square_m: float = 0.025
) -> Dict[str, Any]:
    """Recover camera intrinsics from chessboard views at one fixed frame size."""
    import cv2
    import numpy as np

    if square_m <= 0:
        raise ValueError("square_m must be positive")
    if rows < 2 or cols < 2:
        raise ValueError("need at least 2x2 inner corners")

    paths = list(paths)
    if len(paths) < MIN_BOARDS:
        raise ValueError(
            f"need at least {MIN_BOARDS} chessboard views; got {len(paths)}"
        )

    object_template = np.zeros((rows * cols, 3), dtype=np.float32)
    object_template[:, :2] = (
        np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * float(square_m)
    )
    object_points: List[Any] = []
    image_points: List[Any] = []
    size: Optional[Tuple[int, int]] = None
    for path in paths:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"could not read calibration image: {path}")
        frame_h, frame_w = image.shape[:2]
        if size is None:
            size = (frame_w, frame_h)
        elif (frame_w, frame_h) != size:
            raise ValueError(
                f"calibration image {path} is {frame_w}x{frame_h}, "
                f"expected {size[0]}x{size[1]}"
            )
        corners = find_corners(image, rows, cols)
        if corners is None:
            raise ValueError(
                f"no chessboard corners in {path}; "
                f"expected {cols}x{rows} inner corners"
            )
        object_points.append(object_template)
        image_points.append(corners)

    if size is None:
        raise ValueError("no calibration images")
    rms, k_matrix, _, rvecs, tvecs = cv2.calibrateCamera(
        object_points, image_points, size, None, None
    )
    if not math.isfinite(float(rms)) or float(rms) > MAX_RMS_PX:
        raise ValueError(
            f"reprojection error {float(rms):.2f} px is too high "
            f"(limit {MAX_RMS_PX} px); recapture with a flatter, sharper board"
        )
    translations = np.asarray([np.asarray(tvec).reshape(3) for tvec in tvecs])
    spread = float(np.linalg.norm(translations.max(axis=0) - translations.min(axis=0)))
    if spread < MIN_POSE_SPREAD_M:
        raise ValueError(
            "views are too similar; move or tilt the board between captures"
        )
    fx, fy = float(k_matrix[0, 0]), float(k_matrix[1, 1])
    cx, cy = float(k_matrix[0, 2]), float(k_matrix[1, 2])
    if not all(math.isfinite(v) for v in (fx, fy, cx, cy)) or fx <= 0 or fy <= 0:
        raise ValueError("calibration did not yield finite positive intrinsics")
    return make_calibration(fx, fy, cx, cy, size[0], size[1])


def capture_frames(
    camera: int,
    count: int,
    directory: Path,
    prompt=input,
) -> List[Path]:
    """Capture --count chessboard views, pausing so the board can move."""
    import cv2

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise SystemExit(f"could not open camera {camera}")
    paths: List[Path] = []
    try:
        for index in range(count):
            if index > 0:
                prompt(
                    f"captured {index}/{count}. Reposition the board, then press Enter"
                )
            ok, frame = cap.read()
            if not ok or frame is None:
                raise SystemExit(f"camera {camera} read failed at frame {index}")
            path = directory / f"chess_{index:03d}.png"
            if not cv2.imwrite(str(path), frame):
                raise SystemExit(f"could not write captured frame {path}")
            paths.append(path)
    finally:
        cap.release()
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--images", help="glob of chessboard views, e.g. '/tmp/beacon-chess/*.jpg'"
    )
    parser.add_argument(
        "--camera", type=int, help="optional webcam index; capture --frames instead"
    )
    parser.add_argument(
        "--frames", type=int, default=12, help="views to capture from --camera"
    )
    parser.add_argument(
        "--rows", type=int, default=6, help="inner corners vertically (default 6)"
    )
    parser.add_argument(
        "--cols", type=int, default=9, help="inner corners horizontally (default 9)"
    )
    parser.add_argument(
        "--square-m",
        type=float,
        default=0.025,
        help="measured square side in metres (default 0.025)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("models/calib.json"),
        help="output JSON path (default models/calib.json)",
    )
    parser.add_argument(
        "--write-board",
        type=Path,
        help="write a chessboard PNG for a screen or printer, then exit",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.write_board is not None:
        if args.images is not None or args.camera is not None:
            parser.error("--write-board cannot be combined with --images or --camera")
        write_board(args.write_board, rows=args.rows, cols=args.cols)
        print(
            f"wrote {args.write_board}. Open it fullscreen. Measure one square "
            "with a ruler and pass that as --square-m when you calibrate."
        )
        return 0
    if (args.images is None) == (args.camera is None):
        parser.error("pass exactly one of --images, --camera, or --write-board")
    if args.camera is not None and args.frames < MIN_BOARDS:
        parser.error(f"--frames must be at least {MIN_BOARDS}")

    temporary = None
    if args.camera is not None:
        temporary = tempfile.TemporaryDirectory(prefix="beacon-calib-")
        paths = capture_frames(args.camera, args.frames, Path(temporary.name))
    else:
        paths = [Path(match) for match in sorted(glob.glob(args.images))]
        if not paths:
            raise SystemExit(f"no images matched {args.images!r}")

    try:
        calibration = calibrate_images(
            paths, rows=args.rows, cols=args.cols, square_m=args.square_m
        )
        write_calibration(args.out, calibration)
    finally:
        if temporary is not None:
            temporary.cleanup()

    print(
        f"wrote {args.out} from {len(paths)} views: "
        f"fx={calibration['fx']:.2f} fy={calibration['fy']:.2f} "
        f"cx={calibration['cx']:.2f} cy={calibration['cy']:.2f} "
        f"W={calibration['W']} H={calibration['H']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
