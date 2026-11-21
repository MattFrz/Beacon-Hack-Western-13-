#!/usr/bin/env python3
"""Single-frame Beacon geometry probe.

Reads one webcam frame or one image, runs the laptop-side models, and prints
full-frame pixels plus metric depth. It is a stand-in for percept on a laptop,
not a QNX process.

The models are optional so the affine math can be checked before export. Without
--depth there are no metres. Without --calib or --fov there is no xyz_cam.
--fov guesses a pinhole from horizontal field of view; it does not replace a
tape check on depth.

Example:

    python3 percept/tools/probe_frame.py \
      --image /tmp/keys.jpg \
      --yolo models/yoloe26n_320.onnx \
      --depth models/depth_anything_v2_metric_indoor_small.onnx \
      --hands --hand-model models/hand_landmarker.task \
      --fov

By default, ONNX Runtime decodes the raw YOLOE output: letterbox to 320 px, run
the static ONNX, decode centre/size boxes, NMS, then inverse-letterbox centres
back to full-frame pixels so the geometry matches docs/nathans-revision.md §7.
`--yolo-runtime ultralytics` keeps the packaged decode path as a comparison
where Ultralytics is installed. Depth and hands use the same captured frame_id.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LABELS = REPO_ROOT / "models" / "labels.txt"


@dataclass
class Affine:
    full_w: int
    full_h: int
    net_w: int
    net_h: int
    scale: float
    pad_x: float
    pad_y: float

    def full_to_net(self, u: float, v: float) -> Tuple[float, float]:
        return u * self.scale + self.pad_x, v * self.scale + self.pad_y

    def net_to_full(self, u: float, v: float) -> Tuple[float, float, bool]:
        u_full = (u - self.pad_x) / self.scale
        v_full = (v - self.pad_y) / self.scale
        in_pad = (
            self.pad_x <= u < self.net_w - self.pad_x
            and self.pad_y <= v < self.net_h - self.pad_y
        )
        in_image = 0 <= u_full < self.full_w and 0 <= v_full < self.full_h
        return u_full, v_full, bool(in_pad and in_image)


@dataclass
class Calibration:
    fx: float
    fy: float
    cx: float
    cy: float
    width: Optional[int] = None
    height: Optional[int] = None


def guess_calibration(frame_w: int, frame_h: int, hfov_deg: float) -> Calibration:
    """Pinhole from frame size and a guessed horizontal FOV. Not a chessboard."""
    if frame_w <= 0 or frame_h <= 0:
        raise ValueError("frame size must be positive")
    if not math.isfinite(hfov_deg) or hfov_deg <= 0.0 or hfov_deg >= 180.0:
        raise ValueError("fov must be between 0 and 180 degrees")
    fx = float(frame_w) / (2.0 * math.tan(math.radians(hfov_deg) / 2.0))
    return Calibration(
        fx=fx,
        fy=fx,
        cx=float(frame_w) / 2.0,
        cy=float(frame_h) / 2.0,
        width=int(frame_w),
        height=int(frame_h),
    )


def make_affine(full_w: int, full_h: int, net_w: int, net_h: int) -> Affine:
    if full_w <= 0 or full_h <= 0 or net_w <= 0 or net_h <= 0:
        raise ValueError("frame and net sizes must be positive")
    scale = min(net_w / full_w, net_h / full_h)
    pad_x = (net_w - full_w * scale) / 2.0
    pad_y = (net_h - full_h * scale) / 2.0
    return Affine(full_w, full_h, net_w, net_h, scale, pad_x, pad_y)


def letterbox(frame: Any, affine: Affine, pad_color: Tuple[int, int, int]):
    import cv2
    import numpy as np

    new_w = max(1, int(round(affine.full_w * affine.scale)))
    new_h = max(1, int(round(affine.full_h * affine.scale)))
    resized = cv2.resize(
        frame,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA if affine.scale < 1.0 else cv2.INTER_LINEAR,
    )
    canvas = np.full(
        (affine.net_h, affine.net_w, frame.shape[2]), pad_color, dtype=frame.dtype
    )
    x0 = int(round(affine.pad_x))
    y0 = int(round(affine.pad_y))
    canvas[y0 : y0 + new_h, x0 : x0 + new_w] = resized
    return canvas


def parse_csv3(text: str, name: str) -> Tuple[float, float, float]:
    parts = [float(p.strip()) for p in text.split(",")]
    if len(parts) != 3:
        raise SystemExit(f"{name} needs three comma-separated numbers")
    return parts[0], parts[1], parts[2]


def load_labels(path: Path) -> List[str]:
    labels = []
    for line in path.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if name and not name.startswith("#"):
            labels.append(name)
    if not labels:
        raise SystemExit(f"no labels in {path}")
    return labels


def load_frame(args: argparse.Namespace) -> Tuple[Any, int]:
    import cv2

    if args.image:
        frame = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
        if frame is None:
            raise SystemExit(f"could not read image: {args.image}")
        return frame, time.time_ns()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f"could not open camera {args.camera}")
    try:
        for _ in range(max(0, args.warmup)):
            ok, ignored = cap.read()
            if not ok:
                raise SystemExit("camera read failed during warmup")
        ok, frame = cap.read()
        if not ok or frame is None:
            raise SystemExit("camera read failed")
        return frame, time.time_ns()
    finally:
        cap.release()


def load_calibration(path: Optional[Path], frame_w: int, frame_h: int, notes: List[str]):
    if path is None:
        notes.append("no --calib or --fov: xyz_cam omitted")
        return None

    raw = json.loads(path.read_text(encoding="utf-8"))
    required = ("fx", "fy", "cx", "cy")
    missing = [key for key in required if key not in raw]
    if missing:
        raise SystemExit(f"calibration missing: {', '.join(missing)}")

    calibration = Calibration(
        fx=float(raw["fx"]),
        fy=float(raw["fy"]),
        cx=float(raw["cx"]),
        cy=float(raw["cy"]),
        width=int(raw["W"]) if "W" in raw else None,
        height=int(raw["H"]) if "H" in raw else None,
    )
    if calibration.fx <= 0 or calibration.fy <= 0:
        raise SystemExit("calibration fx/fy must be positive")
    if (
        calibration.width is not None
        and calibration.height is not None
        and (calibration.width != frame_w or calibration.height != frame_h)
    ):
        notes.append(
            "calibration W/H differs from captured frame; re-calibrate at this resolution"
        )
    return calibration


def resolve_calibration(
    args: argparse.Namespace, frame_w: int, frame_h: int, notes: List[str]
) -> Optional[Calibration]:
    """Prefer --calib JSON; otherwise a guessed --fov pinhole; else omit xyz_cam."""
    if getattr(args, "calib", None) is not None:
        return load_calibration(args.calib, frame_w, frame_h, notes)
    fov = getattr(args, "fov", None)
    if fov is not None:
        try:
            calibration = guess_calibration(frame_w, frame_h, float(fov))
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        notes.append(
            f"guessed --fov {float(fov):g}: xyz_cam from pinhole, not chessboard"
        )
        return calibration
    notes.append("no --calib or --fov: xyz_cam omitted")
    return None


def tensor_scalar(value: Any) -> float:
    if hasattr(value, "item"):
        return float(value.item())
    return float(value)


def load_yolo(path: Path):
    from ultralytics import YOLO

    try:
        return YOLO(str(path), task="detect")
    except TypeError:
        return YOLO(str(path))


def load_yolo_session(path: Path):
    import onnxruntime as ort

    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def detect_yolo_ort(
    frame: Any,
    args: argparse.Namespace,
    labels: Sequence[str],
    yolo_affine: Affine,
    notes: List[str],
):
    import cv2
    import numpy as np

    session = load_yolo_session(args.yolo)
    letterboxed = letterbox(frame, yolo_affine, (114, 114, 114))
    x = np.transpose(letterboxed, (2, 0, 1))[None, ...].astype(np.float32) / 255.0
    input_name = session.get_inputs()[0].name
    output = session.run(None, {input_name: x})[0]
    if output.ndim != 3 or output.shape[0] != 1:
        raise RuntimeError(f"unexpected YOLO output shape {output.shape}")
    if output.shape[1] != len(labels) + 4:
        raise RuntimeError(
            f"YOLO has {output.shape[1] - 4} class logits, labels has {len(labels)}"
        )

    preds = np.transpose(output[0], (1, 0))
    boxes = preds[:, :4]
    scores = preds[:, 4:]
    cls = np.argmax(scores, axis=1)
    conf = scores[np.arange(scores.shape[0]), cls]
    keep = np.where(conf >= args.conf)[0]
    if keep.size == 0:
        return []

    selected_boxes = boxes[keep]
    cx, cy, w, h = selected_boxes.T
    net_xyxy = np.column_stack(
        (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)
    ).astype(np.float32)
    nms = cv2.dnn.NMSBoxes(
        net_xyxy.tolist(),
        conf[keep].astype(np.float32).tolist(),
        float(args.conf),
        float(args.yolo_iou),
    )
    if len(nms) == 0:
        return []

    detections = []
    for index in np.asarray(nms).reshape(-1):
        selected = int(index)
        row = int(keep[selected])
        u_net = float(cx[selected])
        v_net = float(cy[selected])
        u_back, v_back, valid = yolo_affine.net_to_full(u_net, v_net)
        if not valid:
            continue
        x1, y1, x2, y2 = net_xyxy[selected]
        u1, v1, _ = yolo_affine.net_to_full(float(x1), float(y1))
        u2, v2, _ = yolo_affine.net_to_full(float(x2), float(y2))
        detections.append(
            {
                "name": labels[int(cls[row])],
                "conf": float(conf[row]),
                "bbox_px": [float(u1), float(v1), float(u2), float(v2)],
                "center_px": [float(u_back), float(v_back)],
                "center_net": [u_net, v_net],
            }
        )
    return detections


def detect(frame: Any, args: argparse.Namespace, labels: Sequence[str], yolo_affine: Affine, notes: List[str]):
    if args.yolo is None:
        notes.append("no --yolo: detections empty")
        return []
    if args.yolo_runtime == "ort":
        return detect_yolo_ort(frame, args, labels, yolo_affine, notes)

    model = load_yolo(args.yolo)
    result = model(frame, imgsz=args.yolo_size, conf=args.conf, verbose=False)[0]
    label_set = set(labels)
    names = getattr(model, "names", {}) or {}
    boxes = getattr(result, "boxes", None)
    detections = []

    for box in boxes if boxes is not None else []:
        cls = int(tensor_scalar(box.cls[0]))
        conf = float(tensor_scalar(box.conf[0]))
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
        if isinstance(names, dict):
            raw_name = names.get(cls)
        elif 0 <= cls < len(names):
            raw_name = names[cls]
        else:
            raw_name = None
        if raw_name is None:
            raw_name = labels[cls] if 0 <= cls < len(labels) else str(cls)
        name = str(raw_name)
        if name not in label_set:
            notes.append(f"discarded unbaked label {name!r}")
            continue

        u_full = (x1 + x2) / 2.0
        v_full = (y1 + y2) / 2.0
        u_net, v_net = yolo_affine.full_to_net(u_full, v_full)
        u_back, v_back, valid = yolo_affine.net_to_full(u_net, v_net)
        if not valid:
            notes.append(f"invalid letterbox inverse for {name!r}; detection skipped")
            continue

        detections.append(
            {
                "name": name,
                "conf": conf,
                "bbox_px": [x1, y1, x2, y2],
                "center_px": [u_back, v_back],
                "center_net": [u_net, v_net],
            }
        )
    return detections


def load_depth_session(path: Path):
    import onnxruntime as ort

    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def predict_depth(
    frame: Any,
    session: Any,
    affine: Affine,
    args: argparse.Namespace,
    mean: Tuple[float, float, float],
    std: Tuple[float, float, float],
    pad_color: Tuple[int, int, int],
):
    import cv2
    import numpy as np

    letterboxed = letterbox(frame, affine, pad_color)
    rgb = cv2.cvtColor(letterboxed, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    rgb = (rgb - np.asarray(mean, dtype=np.float32)) / np.asarray(std, dtype=np.float32)
    x = np.transpose(rgb, (2, 0, 1))[None, ...].astype(np.float32)

    input_name = session.get_inputs()[0].name
    output = session.run(None, {input_name: x})[0]
    metres = np.squeeze(output)
    if metres.ndim == 3:
        metres = metres[0]
    if metres.ndim != 2:
        raise RuntimeError(f"depth output shape {output.shape} is not a 2D grid")
    if metres.shape[1] != affine.net_w or metres.shape[0] != affine.net_h:
        raise RuntimeError(
            f"depth output {metres.shape[1]}x{metres.shape[0]} does not match "
            f"net {affine.net_w}x{affine.net_h}"
        )
    return metres.astype(np.float32)


def depth_at_full(metres: Any, affine: Affine, u: float, v: float, scale: float):
    if metres is None:
        return None
    import numpy as np

    u_net, v_net = affine.full_to_net(u, v)
    x = int(round(u_net))
    y = int(round(v_net))
    if not (0 <= x < affine.net_w and 0 <= y < affine.net_h):
        return None
    _, _, in_image = affine.net_to_full(x, y)
    if not in_image:
        return None
    z = float(metres[y, x]) * scale
    if not math.isfinite(z) or z <= 0:
        return None
    return z


def unproject(u: float, v: float, z: float, calibration: Calibration) -> List[float]:
    x = (u - calibration.cx) * z / calibration.fx
    y = (v - calibration.cy) * z / calibration.fy
    return [x, y, z]


def find_fingertip(frame: Any, frame_id: int, args: argparse.Namespace, depth: Any, depth_affine: Affine, calibration: Optional[Calibration], scale: float, notes: List[str]):
    if not args.hands:
        return None

    import cv2
    import mediapipe as mp

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    landmark = None

    if args.hand_model is not None:
        if not args.hand_model.exists():
            raise SystemExit(f"hand model not found: {args.hand_model}")
        from mediapipe.tasks import python as mp_tasks
        from mediapipe.tasks.python import vision

        options = vision.HandLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=str(args.hand_model)),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=args.hand_conf,
            min_hand_presence_confidence=args.hand_conf,
        )
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        with vision.HandLandmarker.create_from_options(options) as landmarker:
            result = landmarker.detect(image)
        if result.hand_landmarks:
            landmark = result.hand_landmarks[0][8]
    elif hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
        with mp.solutions.hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=args.hand_conf,
        ) as hands:
            result = hands.process(rgb)
        if result.multi_hand_landmarks:
            landmark = result.multi_hand_landmarks[0].landmark[8]
    else:
        notes.append("MediaPipe legacy Hands is unavailable; pass --hand-model for Tasks API")
        return None

    if landmark is None:
        return None

    u = float(landmark.x) * frame.shape[1]
    v = float(landmark.y) * frame.shape[0]
    z = depth_at_full(depth, depth_affine, u, v, scale)

    hand = {
        "frame_id": frame_id,
        "fingertip_px": [u, v],
        "hand_crop": {"origin_x": 0.0, "origin_y": 0.0, "scale": 1.0},
        "Z_m": z,
    }
    if z is not None and calibration is not None:
        hand["xyz_cam"] = unproject(u, v, z, calibration)
    return hand


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, help="read one image instead of the camera")
    parser.add_argument("--camera", type=int, default=0, help="webcam index, default 0")
    parser.add_argument("--warmup", type=int, default=3, help="frames to drop before capture")
    parser.add_argument(
        "--labels", type=Path, default=DEFAULT_LABELS, help="runtime vocabulary"
    )
    parser.add_argument("--yolo", type=Path, help="baked YOLOE model, .onnx or .pt")
    parser.add_argument("--yolo-size", type=int, default=320, help="YOLO net size")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence")
    parser.add_argument(
        "--yolo-runtime",
        choices=("ort", "ultralytics"),
        default="ort",
        help="ORT decodes raw ONNX output; ultralytics decodes and NMSes internally",
    )
    parser.add_argument(
        "--yolo-iou", type=float, default=0.5, help="YOLO NMS IoU for ORT decode"
    )
    parser.add_argument("--depth", type=Path, help="metric depth ONNX")
    parser.add_argument("--depth-size", type=int, default=210, help="depth net size")
    parser.add_argument(
        "--depth-scale",
        type=float,
        default=1.0,
        help="metres per model output unit; change only after tape check",
    )
    parser.add_argument(
        "--depth-mean", default="0.485,0.456,0.406", help="RGB mean for depth input"
    )
    parser.add_argument(
        "--depth-std", default="0.229,0.224,0.225", help="RGB std for depth input"
    )
    parser.add_argument(
        "--depth-pad", default="114,114,114", help="letterbox BGR pad colour"
    )
    parser.add_argument("--hands", action="store_true", help="run MediaPipe hands")
    parser.add_argument(
        "--hand-model",
        type=Path,
        help="MediaPipe Tasks .task model; needed when legacy solutions.Hands is absent",
    )
    parser.add_argument(
        "--hand-conf", type=float, default=0.5, help="MediaPipe detection confidence"
    )
    parser.add_argument(
        "--calib", type=Path, help="JSON with fx, fy, cx, cy, and optional W, H"
    )
    parser.add_argument(
        "--fov",
        type=float,
        nargs="?",
        const=66.0,
        default=None,
        help="horizontal FOV degrees for a guessed pinhole when --calib is omitted; bare --fov uses 66",
    )
    return parser


def prepare(
    args: argparse.Namespace,
) -> Tuple[List[str], Tuple[float, float, float], Tuple[float, float, float], Tuple[int, int, int]]:
    """Validate CLI paths and load static labels/preprocessing for repeated frames."""
    if not args.labels.exists():
        raise SystemExit(f"labels not found: {args.labels}")
    if args.yolo is not None and not args.yolo.exists():
        raise SystemExit(f"YOLO model not found: {args.yolo}")
    if args.depth is not None and not args.depth.exists():
        raise SystemExit(f"depth model not found: {args.depth}")
    if args.calib is not None and not args.calib.exists():
        raise SystemExit(f"calibration not found: {args.calib}")
    if args.hand_model is not None and not args.hand_model.exists():
        raise SystemExit(f"hand model not found: {args.hand_model}")

    mean = parse_csv3(args.depth_mean, "--depth-mean")
    std = parse_csv3(args.depth_std, "--depth-std")
    pad = parse_csv3(args.depth_pad, "--depth-pad")
    pad_color = tuple(int(round(v)) for v in pad)
    labels = load_labels(args.labels)
    return labels, mean, std, pad_color


def probe_once(
    args: argparse.Namespace,
    labels: Sequence[str],
    mean: Tuple[float, float, float],
    std: Tuple[float, float, float],
    pad_color: Tuple[int, int, int],
) -> Dict[str, Any]:
    """Capture and process one frame; timings_ms reports stage durations in ms."""
    frame, frame_id = load_frame(args)
    frame_h, frame_w = frame.shape[:2]

    notes: List[str] = []
    yolo_affine = make_affine(frame_w, frame_h, args.yolo_size, args.yolo_size)
    depth_affine = make_affine(frame_w, frame_h, args.depth_size, args.depth_size)
    calibration = resolve_calibration(args, frame_w, frame_h, notes)

    timings_ms: Dict[str, Optional[float]] = {"yolo": None, "depth": None}
    started_ns = time.perf_counter_ns()
    detections = detect(frame, args, labels, yolo_affine, notes)
    timings_ms["yolo"] = (time.perf_counter_ns() - started_ns) / 1e6
    for detection in detections:
        detection["frame_id"] = frame_id

    depth = None
    if args.depth is not None:
        started_ns = time.perf_counter_ns()
        session = load_depth_session(args.depth)
        depth = predict_depth(frame, session, depth_affine, args, mean, std, pad_color)
        for detection in detections:
            u, v = detection["center_px"]
            z = depth_at_full(depth, depth_affine, u, v, args.depth_scale)
            detection["Z_m"] = z
            if z is not None and calibration is not None:
                detection["xyz_cam"] = unproject(u, v, z, calibration)
        timings_ms["depth"] = (time.perf_counter_ns() - started_ns) / 1e6

    hand = find_fingertip(
        frame, frame_id, args, depth, depth_affine, calibration, args.depth_scale, notes
    )

    return {
        "frame_id": frame_id,
        "W": frame_w,
        "H": frame_h,
        "vocabulary": labels,
        "affines": {
            "yolo": asdict(yolo_affine),
            "depth": asdict(depth_affine),
            "hand": {"origin_x": 0.0, "origin_y": 0.0, "scale": 1.0},
        },
        "depth_grid": (
            {"W_d": depth.shape[1], "H_d": depth.shape[0], "scale": args.depth_scale}
            if depth is not None
            else None
        ),
        "detections": detections,
        "hand": hand,
        "notes": notes,
        "timings_ms": timings_ms,
    }


def main() -> int:
    args = build_parser().parse_args()
    labels, mean, std, pad_color = prepare(args)
    print(json.dumps(probe_once(args, labels, mean, std, pad_color), indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
