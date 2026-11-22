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
import statistics
import sys
import time
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LABELS = REPO_ROOT / "models" / "labels.txt"
DEPTH_SAMPLER_BOX = "box_median"
DEPTH_SAMPLER_PATCH = "patch_median"
DEFAULT_PREVIEW_WIDTH = 320
DEFAULT_PREVIEW_QUALITY = 60
DEFAULT_DEPTH_WINDOW = 5
DEFAULT_DEPTH_JUMP = 0.6
DEFAULT_DEPTH_EVICT = 10
DEFAULT_DEPTH_RECOVER = 3
DEFAULT_SLOT_IOU = 0.30
SLOT_SCORE_TOLERANCE = 1e-6
MIN_SLOT_BOX_AREA = 1.0


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


def encode_preview(frame: Any, width: int, quality: int) -> Optional[bytes]:
    """Encode one downscaled BGR JPEG for the bridge; None if encoding fails."""
    import cv2

    frame_h, frame_w = frame.shape[:2]
    scale = min(1.0, float(width) / frame_w)
    small = cv2.resize(
        frame,
        (max(1, round(frame_w * scale)), max(1, round(frame_h * scale))),
        interpolation=cv2.INTER_AREA,
    )
    ok, encoded = cv2.imencode(
        ".jpg", small, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    )
    return encoded.tobytes() if ok else None


def _draw_boxes(panel: Any, detections: Sequence[dict], frame_w: int,
                frame_h: int, target_name: Optional[str]) -> None:
    """Draw scaled boxes, name + range labels; the homing target stands out."""
    import cv2

    panel_h, panel_w = panel.shape[:2]
    sx = panel_w / float(frame_w)
    sy = panel_h / float(frame_h)
    for det in detections:
        box = det.get("bbox_px")
        if not isinstance(box, (list, tuple)) or len(box) < 4:
            continue
        x1 = int(round(float(box[0]) * sx))
        y1 = int(round(float(box[1]) * sy))
        x2 = int(round(float(box[2]) * sx))
        y2 = int(round(float(box[3]) * sy))
        is_target = target_name is not None and det.get("name") == target_name
        colour = (0, 255, 255) if is_target else (60, 220, 60)
        cv2.rectangle(panel, (x1, y1), (x2, y2), colour,
                      2 if is_target else 1)
        label = str(det.get("name", "?"))
        z = det.get("Z_m")
        if isinstance(z, (int, float)) and z == z and z > 0.0:
            label = f"{label} {float(z):.2f}m"
        cv2.putText(panel, label, (x1, max(8, y1 - 3)),
                    getattr(cv2, "FONT_HERSHEY_SIMPLEX", 0), 0.35, colour,
                    1, getattr(cv2, "LINE_AA", 16))


def crop_depth_padding(grid: Any, depth_affine: Any) -> Any:
    """Drop the letterbox padding from a square depth canvas.

    The depth net takes a padded square, so for a 16:9 frame the real depth is
    only the middle band; displaying the whole canvas squashes it vertically.
    """
    if depth_affine is None:
        return grid
    if isinstance(depth_affine, dict):
        pad_x = depth_affine.get("pad_x")
        pad_y = depth_affine.get("pad_y")
        scale = depth_affine.get("scale")
        full_w = depth_affine.get("full_w")
        full_h = depth_affine.get("full_h")
    else:
        pad_x = getattr(depth_affine, "pad_x", None)
        pad_y = getattr(depth_affine, "pad_y", None)
        scale = getattr(depth_affine, "scale", None)
        full_w = getattr(depth_affine, "full_w", None)
        full_h = getattr(depth_affine, "full_h", None)
    try:
        x0 = int(round(float(pad_x)))
        y0 = int(round(float(pad_y)))
        w = int(round(float(full_w) * float(scale)))
        h = int(round(float(full_h) * float(scale)))
    except (TypeError, ValueError):
        return grid
    if w <= 0 or h <= 0:
        return grid
    grid_h, grid_w = grid.shape[:2]
    x1 = min(grid_w, x0 + w)
    y1 = min(grid_h, y0 + h)
    x0 = max(0, min(x0, x1 - 1))
    y0 = max(0, min(y0, y1 - 1))
    crop = grid[y0:y1, x0:x1]
    return crop if crop.size else grid


def render_preview(
    frame: Any,
    detections: Sequence[dict],
    depth: Any,
    *,
    width: int,
    quality: int,
    target_name: Optional[str] = None,
    depth_scale: float = 0.0,
    depth_affine: Any = None,
) -> Optional[bytes]:
    """Stacked preview JPEG: RGB with YOLO boxes, then depth with the same boxes.

    Panel one is what detection sees (boxes, labels, ranges, target
    highlighted); panel two is the metric depth map colourised, carrying the
    same boxes so an object's depth footprint is readable. None if encoding
    fails.
    """
    import cv2

    import numpy as np

    frame_h, frame_w = frame.shape[:2]
    panel_w = max(1, min(int(width), int(frame_w)))
    panel_h = max(1, round(frame_h * panel_w / float(frame_w)))

    boxed = cv2.resize(frame, (panel_w, panel_h),
                       interpolation=cv2.INTER_AREA).copy()
    _draw_boxes(boxed, detections, frame_w, frame_h, target_name)
    panels = [boxed]

    if depth is not None:
        grid = np.asarray(depth, dtype=np.float32)
        grid = np.nan_to_num(grid, nan=0.0, posinf=0.0, neginf=0.0)
        if depth_scale:
            grid = grid * float(depth_scale)
        grid = crop_depth_padding(grid, depth_affine)
        if grid.size:
            norm = cv2.normalize(grid, None, 0, 255,
                                 getattr(cv2, "NORM_MINMAX", 32))
            colour_map = cv2.applyColorMap(
                cv2.convertScaleAbs(norm),
                getattr(cv2, "COLORMAP_INFERNO", 2),
            )
            depth_panel = cv2.resize(colour_map, (panel_w, panel_h),
                                     interpolation=cv2.INTER_AREA)
            _draw_boxes(depth_panel, detections, frame_w, frame_h, target_name)
            panels.append(depth_panel)

    separator = np.full((2, panel_w, 3), 24, dtype=np.uint8)
    stacked = panels[0]
    for panel in panels[1:]:
        stacked = np.vstack([stacked, separator, panel])

    ok, encoded = cv2.imencode(
        ".jpg", stacked, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    )
    return encoded.tobytes() if ok else None


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


def _stable_detection_id(name: str) -> int:
    """Match probe_to_world's name id so the filter key is the world object id."""
    return 1 + (zlib.crc32(name.encode("utf-8")) & 0x7FFFFFFF)


@dataclass
class _DepthState:
    history: List[float]
    last_seen: int
    candidates: List[float]


@dataclass
class _SlotState:
    bbox_px: Tuple[float, float, float, float]
    last_seen: int


def _box_bounds(box: Sequence[float]) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = (float(value) for value in box)
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def _box_iou(
    left: Sequence[float], right: Sequence[float]
) -> Optional[float]:
    ax0, ay0, ax1, ay1 = _box_bounds(left)
    bx0, by0, bx1, by1 = _box_bounds(right)
    area_a = (ax1 - ax0) * (ay1 - ay0)
    area_b = (bx1 - bx0) * (by1 - by0)
    if area_a < MIN_SLOT_BOX_AREA or area_b < MIN_SLOT_BOX_AREA:
        return None  # a degenerate box has no meaningful overlap
    overlap_x = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    overlap_y = max(0.0, min(ay1, by1) - max(ay0, by0))
    overlap = overlap_x * overlap_y
    union = area_a + area_b - overlap
    return overlap / union if union > 0.0 else None


def _slot_match_score(
    detection_box: Sequence[float],
    slot_box: Sequence[float],
    iou_threshold: float,
) -> Optional[float]:
    """IoU score, or a centre-distance score when a box is too small for IoU."""
    iou = _box_iou(detection_box, slot_box)
    if iou is not None:
        return iou if iou >= iou_threshold else None
    ax0, ay0, ax1, ay1 = _box_bounds(detection_box)
    bx0, by0, bx1, by1 = _box_bounds(slot_box)
    centre_a = ((ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0)
    centre_b = ((bx0 + bx1) / 2.0, (by0 + by1) / 2.0)
    radius = max(ax1 - ax0, ay1 - ay0, bx1 - bx0, by1 - by0, 1.0)
    distance = math.hypot(centre_a[0] - centre_b[0], centre_a[1] - centre_b[1])
    return 1.0 - distance / radius if distance <= radius else None


class SlotTracker:
    """Greedy per-name IoU association of detections to stable instance slots.

    Only slots from the current tracking window are candidates. Ambiguous
    claims are reported on the detection instead of updating slot geometry, so
    the depth stabiliser can leave those samples out of every involved history.
    """

    def __init__(self, iou: float = DEFAULT_SLOT_IOU, evict: int = DEFAULT_DEPTH_EVICT):
        if not math.isfinite(iou) or not 0.0 <= iou <= 1.0:
            raise ValueError("slot iou must be between 0 and 1")
        if evict < 1:
            raise ValueError("slot evict must be at least 1")
        self.iou = float(iou)
        self.evict = int(evict)
        self._slots: Dict[str, Dict[int, _SlotState]] = {}
        self._next_slot: Dict[str, int] = {}
        self._frame = 0

    def advance(self) -> None:
        self._frame += 1
        cutoff = self._frame - self.evict
        for slots in self._slots.values():
            stale = [slot for slot, state in slots.items() if state.last_seen < cutoff]
            for slot in stale:
                del slots[slot]

    def associate(self, detections: Sequence[Dict[str, Any]]) -> None:
        """Set ``slot`` and ``z_ambiguous`` on each detection with depth."""
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for detection in detections:
            name = str(detection.get("name", "unknown"))
            groups.setdefault(name, []).append(detection)

        for name, group in groups.items():
            slots = self._slots.setdefault(name, {})
            boxes = [_box_bounds(detection["bbox_px"]) for detection in group]
            candidates: Dict[Tuple[int, int], float] = {}
            for index, box in enumerate(boxes):
                for slot, state in slots.items():
                    score = _slot_match_score(box, state.bbox_px, self.iou)
                    if score is not None:
                        candidates[(index, slot)] = score

            ambiguous = set()
            for index in range(len(group)):
                scores = sorted(
                    (
                        score
                        for (candidate_index, _slot), score in candidates.items()
                        if candidate_index == index
                    ),
                    reverse=True,
                )
                if len(scores) > 1 and scores[0] - scores[1] <= SLOT_SCORE_TOLERANCE:
                    ambiguous.add(index)
            for slot in slots:
                claimants = [
                    index for (index, candidate_slot) in candidates if candidate_slot == slot
                ]
                if len(claimants) > 1:
                    ambiguous.update(claimants)

            ranked = sorted(
                candidates.items(), key=lambda item: (-item[1], item[0][0], item[0][1])
            )
            claims: Dict[int, int] = {}
            claimed_slots = set()
            for (index, slot), _score in ranked:
                if index in claims or slot in claimed_slots:
                    continue
                claims[index] = slot
                claimed_slots.add(slot)

            for index, detection in enumerate(group):
                slot = claims.get(index)
                if slot is None:
                    slot = self._next_slot.get(name, 0)
                    self._next_slot[name] = slot + 1
                detection["slot"] = slot
                detection["z_ambiguous"] = index in ambiguous
                if not detection["z_ambiguous"]:
                    slots[slot] = _SlotState(bbox_px=boxes[index], last_seen=self._frame)


class DepthStabiliser:
    """Per-id rolling median with jump rejection, recovery, and eviction.

    advance() marks one new probe frame; ids unseen for more than evict frames
    lose their history. A run of agreeing rejects can replace a stale median
    after recover samples, so a real fast approach is not held forever. A
    missing sample is never replaced with a stale median and does not count as
    a sighting; untracked_sample() emits one frame's own depth when a slot match
    is ambiguous. Callers key update() by (name, slot) from SlotTracker.
    """

    def __init__(
        self,
        window: int = DEFAULT_DEPTH_WINDOW,
        jump: float = DEFAULT_DEPTH_JUMP,
        evict: int = DEFAULT_DEPTH_EVICT,
        recover: int = DEFAULT_DEPTH_RECOVER,
    ):
        if window < 1:
            raise ValueError("depth window must be at least 1")
        if not math.isfinite(jump) or jump <= 0.0:
            raise ValueError("depth jump ratio must be greater than 0")
        if evict < 1:
            raise ValueError("depth evict must be at least 1")
        if recover < 1:
            raise ValueError("depth recover must be at least 1")
        self.window = int(window)
        self.jump = float(jump)
        self.evict = int(evict)
        self.recover = int(recover)
        self._states: Dict[Any, _DepthState] = {}
        self._frame = 0

    def settings(self) -> Dict[str, Any]:
        return {
            "window": self.window,
            "jump": self.jump,
            "evict": self.evict,
            "recover": self.recover,
        }

    def advance(self) -> None:
        self._frame += 1
        cutoff = self._frame - self.evict
        stale = [
            object_id
            for object_id, state in self._states.items()
            if state.last_seen < cutoff
        ]
        for object_id in stale:
            del self._states[object_id]

    def _within_jump(self, z: float, reference: float) -> bool:
        return abs(z - reference) / reference <= self.jump

    @staticmethod
    def _normalise(z: Optional[float]) -> Optional[float]:
        raw = None if z is None else float(z)
        return raw if raw is None or math.isfinite(raw) else None

    def untracked_sample(self, z: Optional[float]) -> Dict[str, Any]:
        """Emit this frame's own depth without reading or writing history."""
        raw = self._normalise(z)
        return {
            "Z_m": raw if raw is not None and raw > 0.0 else None,
            "z_raw": raw,
            "z_rejected": True,
        }

    def update(self, object_id: Any, z: Optional[float]) -> Dict[str, Any]:
        raw = self._normalise(z)
        valid = raw is not None and raw > 0.0

        state = self._states.get(object_id)
        if state is None:
            if not valid:
                return {"Z_m": None, "z_raw": raw, "z_rejected": True}
            state = _DepthState(history=[raw], last_seen=self._frame, candidates=[])
            self._states[object_id] = state
            return {"Z_m": raw, "z_raw": raw, "z_rejected": False}

        if not valid:
            state.candidates.clear()
            return {"Z_m": None, "z_raw": raw, "z_rejected": True}

        state.last_seen = self._frame
        median = statistics.median(state.history)
        if self._within_jump(raw, median):
            state.history.append(raw)
            if len(state.history) > self.window:
                state.history = state.history[-self.window :]
            state.candidates.clear()
            return {
                "Z_m": statistics.median(state.history),
                "z_raw": raw,
                "z_rejected": False,
            }

        if (
            not state.candidates
            or not self._within_jump(raw, statistics.median(state.candidates))
        ):
            state.candidates = [raw]
        else:
            state.candidates.append(raw)
        if len(state.candidates) >= self.recover:
            adopted = statistics.median(state.candidates)
            state.history = [adopted]
            state.candidates.clear()
            return {"Z_m": adopted, "z_raw": raw, "z_rejected": False}

        return {"Z_m": median, "z_raw": raw, "z_rejected": True}


class ProbeResources:
    """Process-lifetime camera, ORT sessions, and hand landmarker.

    Enter once around a probe loop; handles are reused across cycles and
    released on exit. Model handles are created lazily on first use.
    """

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.depth_stabiliser = DepthStabiliser(
            window=getattr(args, "depth_window", DEFAULT_DEPTH_WINDOW),
            jump=getattr(args, "depth_jump", DEFAULT_DEPTH_JUMP),
            evict=getattr(args, "depth_evict", DEFAULT_DEPTH_EVICT),
            recover=getattr(args, "depth_recover", DEFAULT_DEPTH_RECOVER),
        )
        self.slot_tracker = SlotTracker(
            iou=getattr(args, "slot_iou", DEFAULT_SLOT_IOU),
            evict=getattr(args, "depth_evict", DEFAULT_DEPTH_EVICT),
        )
        self.cap: Any = None
        self._options: Any = None
        self._yolo_session: Any = None
        self._depth_session: Any = None
        self._landmarker: Any = None
        self._hand_mode: Optional[str] = None
        self._mp: Any = None

    def __enter__(self) -> "ProbeResources":
        if self.args.image is None:
            import cv2

            from_video = self.args.video is not None
            source = str(self.args.video) if from_video else self.args.camera
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                cap.release()
                if from_video:
                    raise SystemExit(f"could not open video: {self.args.video}")
                raise SystemExit(f"could not open camera {self.args.camera}")
            self.cap = cap
            # A file needs no exposure settling; dropping warmup frames would eat content.
            warmup = 0 if from_video else self.args.warmup
            try:
                for _ in range(max(0, warmup)):
                    ok, _ignored = cap.read()
                    if not ok:
                        raise SystemExit("camera read failed during warmup")
            except BaseException:
                cap.release()
                self.cap = None
                raise
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self._landmarker is not None:
            close = getattr(self._landmarker, "close", None)
            if callable(close):
                close()
            self._landmarker = None
        for session in (self._yolo_session, self._depth_session):
            if session is not None:
                close = getattr(session, "close", None)
                if callable(close):
                    close()
        self._yolo_session = None
        self._depth_session = None

    def session_options(self):
        """CPU-only ORT options; --ort-intra/--ort-parallel are laptop knobs."""
        if self._options is None:
            import onnxruntime as ort

            options = ort.SessionOptions()
            options.intra_op_num_threads = int(self.args.ort_intra)
            if self.args.ort_parallel:
                options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
            self._options = options
        return self._options

    def yolo_session(self):
        if self.args.yolo is None:
            return None
        # Ultralytics decodes internally; only the ort runtime uses this session.
        if getattr(self.args, "yolo_runtime", "ort") != "ort":
            return None
        if self._yolo_session is None:
            self._yolo_session = load_yolo_session(
                self.args.yolo, self.session_options()
            )
        return self._yolo_session

    def depth_session(self):
        if self.args.depth is None:
            return None
        if self._depth_session is None:
            self._depth_session = load_depth_session(
                self.args.depth, self.session_options()
            )
        return self._depth_session

    def read_frame(self) -> Tuple[Optional[Any], int, int]:
        """Return (frame, frame_id, capture t_ns); frame is None at video EOF."""
        import cv2

        if self.args.image is not None:
            frame = cv2.imread(str(self.args.image), cv2.IMREAD_COLOR)
            if frame is None:
                raise SystemExit(f"could not read image: {self.args.image}")
            t_ns = time.monotonic_ns()
            return frame, t_ns, t_ns

        if self.cap is None:
            raise RuntimeError("camera resources are not open")
        ok, frame = self.cap.read()
        if not ok or frame is None:
            if self.args.video is not None:
                return None, 0, 0
            raise SystemExit("camera read failed")
        t_ns = time.monotonic_ns()
        return frame, t_ns, t_ns

    def hand_landmarks(self, rgb: Any, notes: List[str]):
        """Detect one hand; the landmarker is created only on first use."""
        if self._landmarker is None:
            import mediapipe as mp

            if self.args.hand_model is not None:
                from mediapipe.tasks import python as mp_tasks
                from mediapipe.tasks.python import vision

                options = vision.HandLandmarkerOptions(
                    base_options=mp_tasks.BaseOptions(
                        model_asset_path=str(self.args.hand_model)
                    ),
                    running_mode=vision.RunningMode.IMAGE,
                    num_hands=1,
                    min_hand_detection_confidence=self.args.hand_conf,
                    min_hand_presence_confidence=self.args.hand_conf,
                )
                self._mp = mp
                self._hand_mode = "tasks"
                self._landmarker = vision.HandLandmarker.create_from_options(options)
            elif hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                self._hand_mode = "legacy"
                self._landmarker = mp.solutions.hands.Hands(
                    static_image_mode=True,
                    max_num_hands=1,
                    model_complexity=0,
                    min_detection_confidence=self.args.hand_conf,
                )
            else:
                notes.append(
                    "MediaPipe legacy Hands is unavailable; pass --hand-model for Tasks API"
                )
                return None

        if self._hand_mode == "tasks":
            image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
            result = self._landmarker.detect(image)
            return result.hand_landmarks[0] if result.hand_landmarks else None
        result = self._landmarker.process(rgb)
        if result.multi_hand_landmarks:
            return result.multi_hand_landmarks[0].landmark
        return None


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


def load_yolo_session(path: Path, sess_options: Any):
    import onnxruntime as ort

    return ort.InferenceSession(
        str(path), providers=["CPUExecutionProvider"], sess_options=sess_options
    )


def detect_yolo_ort(
    frame: Any,
    args: argparse.Namespace,
    labels: Sequence[str],
    yolo_affine: Affine,
    notes: List[str],
    session: Any,
):
    import cv2
    import numpy as np

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


def detect(frame: Any, args: argparse.Namespace, labels: Sequence[str], yolo_affine: Affine, notes: List[str], session: Any):
    if args.yolo is None:
        notes.append("no --yolo: detections empty")
        return []
    if args.yolo_runtime == "ort":
        return detect_yolo_ort(frame, args, labels, yolo_affine, notes, session)

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


def load_depth_session(path: Path, sess_options: Any):
    import onnxruntime as ort

    return ort.InferenceSession(
        str(path), providers=["CPUExecutionProvider"], sess_options=sess_options
    )


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


def _median_depth(metres: Any, cells: Sequence[Tuple[int, int]], scale: float, min_cells: int = 1):
    """Median of finite positive depths over net cells (y, x); scale applied once."""
    import numpy as np

    values = []
    for y, x in cells:
        z = float(metres[y, x]) * scale
        if math.isfinite(z) and z > 0:
            values.append(z)
    if len(values) < min_cells:
        return None
    return float(np.median(values))


def _central_bounds(length: int, frac: float) -> Tuple[int, int]:
    margin = int(length * (1.0 - frac) / 2.0)
    start = min(margin, length - 1)
    end = max(start + 1, length - margin)
    return start, min(end, length)


def depth_at_box(
    metres: Any,
    affine: Affine,
    bbox_px: Sequence[float],
    scale: float,
    frac: float = 0.5,
    min_cells: int = 4,
):
    """Median depth over the central frac of valid net cells inside a full-frame box.

    Clipped boxes and letterbox pad are excluded before the central crop, so a
    cell outside the captured image cannot contribute to the sample.
    """
    if metres is None:
        return None

    frac = min(1.0, max(0.0, float(frac)))
    u1, v1, u2, v2 = bbox_px
    x1, y1 = affine.full_to_net(min(u1, u2), min(v1, v2))
    x2, y2 = affine.full_to_net(max(u1, u2), max(v1, v2))
    x_lo = max(0, int(math.floor(x1)))
    # A cell index n covers [n, n+1), so an edge exactly at n excludes cell n.
    x_hi = min(affine.net_w - 1, int(math.ceil(x2)) - 1)
    y_lo = max(0, int(math.floor(y1)))
    y_hi = min(affine.net_h - 1, int(math.ceil(y2)) - 1)
    if x_hi < x_lo or y_hi < y_lo:
        return None

    cells = [
        (y, x)
        for y in range(y_lo, y_hi + 1)
        for x in range(x_lo, x_hi + 1)
        if affine.net_to_full(x, y)[2]
    ]
    if len(cells) < min_cells:
        return None

    xs = sorted({x for _, x in cells})
    ys = sorted({y for y, _ in cells})
    x_start, x_end = _central_bounds(len(xs), frac)
    y_start, y_end = _central_bounds(len(ys), frac)
    keep_x, keep_y = set(xs[x_start:x_end]), set(ys[y_start:y_end])
    sampled = [(y, x) for y, x in cells if x in keep_x and y in keep_y]
    return _median_depth(metres, sampled, scale, min_cells)


def depth_at_patch(
    metres: Any,
    affine: Affine,
    u: float,
    v: float,
    scale: float,
    radius: int = 1,
):
    """Small square median around one point; a landmark is genuinely a point."""
    if metres is None:
        return None

    u_net, v_net = affine.full_to_net(u, v)
    cx, cy = int(round(u_net)), int(round(v_net))
    # The landmark itself must be in the captured image; neighbours cannot
    # substitute for a centre cell in the letterbox pad or off the grid.
    if not (
        0 <= cx < affine.net_w
        and 0 <= cy < affine.net_h
        and affine.net_to_full(cx, cy)[2]
    ):
        return None
    cells = [
        (y, x)
        for y in range(cy - radius, cy + radius + 1)
        for x in range(cx - radius, cx + radius + 1)
        if 0 <= x < affine.net_w
        and 0 <= y < affine.net_h
        and affine.net_to_full(x, y)[2]
    ]
    return _median_depth(metres, cells, scale)


def depth_at_full(metres: Any, affine: Affine, u: float, v: float, scale: float):
    """Single-cell sample; kept as a comparison against the box median."""
    return depth_at_patch(metres, affine, u, v, scale, radius=0)


def unproject(u: float, v: float, z: float, calibration: Calibration) -> List[float]:
    x = (u - calibration.cx) * z / calibration.fx
    y = (v - calibration.cy) * z / calibration.fy
    return [x, y, z]


def find_fingertip(frame: Any, frame_id: int, args: argparse.Namespace, depth: Any, depth_affine: Affine, calibration: Optional[Calibration], scale: float, notes: List[str], resources: ProbeResources):
    if not args.hands:
        return None

    import cv2

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    landmarks = resources.hand_landmarks(rgb, notes)
    if landmarks is None:
        return None
    landmark = landmarks[8]

    u = float(landmark.x) * frame.shape[1]
    v = float(landmark.y) * frame.shape[0]
    z = depth_at_patch(depth, depth_affine, u, v, scale)

    hand = {
        "frame_id": frame_id,
        "fingertip_px": [u, v],
        "hand_crop": {"origin_x": 0.0, "origin_y": 0.0, "scale": 1.0},
        "Z_m": z,
    }
    if z is not None and calibration is not None:
        hand["xyz_cam"] = unproject(u, v, z, calibration)
    return hand


def _positive_int_arg(name: str):
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{name} must be an integer") from exc
        if parsed < 1:
            raise argparse.ArgumentTypeError(f"{name} must be at least 1")
        return parsed

    return parse


def _positive_float_arg(name: str):
    def parse(value: str) -> float:
        try:
            parsed = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{name} must be a number") from exc
        if not math.isfinite(parsed) or parsed <= 0.0:
            raise argparse.ArgumentTypeError(f"{name} must be greater than 0")
        return parsed

    return parse


def _unit_float_arg(name: str):
    def parse(value: str) -> float:
        try:
            parsed = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{name} must be a number") from exc
        if not math.isfinite(parsed) or not 0.0 <= parsed <= 1.0:
            raise argparse.ArgumentTypeError(f"{name} must be between 0 and 1")
        return parsed

    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--image", type=Path, help="read one image instead of the camera")
    source.add_argument("--video", type=Path, help="read every frame of a video file, then stop at EOF")
    parser.add_argument("--camera", type=int, default=0, help="webcam index, default 0")
    parser.add_argument("--warmup", type=int, default=3, help="frames to drop before capture")
    parser.add_argument(
        "--ort-intra",
        type=int,
        default=4,
        help="ORT intra_op_num_threads per session (laptop only; QNX spec uses <=3)",
    )
    parser.add_argument(
        "--ort-parallel",
        action="store_true",
        help="use ORT parallel execution mode (laptop only; default sequential)",
    )
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
    parser.add_argument(
        "--depth-window",
        type=_positive_int_arg("--depth-window"),
        default=DEFAULT_DEPTH_WINDOW,
        help=f"accepted-Z median window per object id (default {DEFAULT_DEPTH_WINDOW})",
    )
    parser.add_argument(
        "--depth-jump",
        type=_positive_float_arg("--depth-jump"),
        default=DEFAULT_DEPTH_JUMP,
        help=f"max |z-median|/median before a sample is rejected (default {DEFAULT_DEPTH_JUMP})",
    )
    parser.add_argument(
        "--depth-evict",
        type=_positive_int_arg("--depth-evict"),
        default=DEFAULT_DEPTH_EVICT,
        help=f"frames unseen before an id's history is dropped (default {DEFAULT_DEPTH_EVICT})",
    )
    parser.add_argument(
        "--depth-recover",
        type=_positive_int_arg("--depth-recover"),
        default=DEFAULT_DEPTH_RECOVER,
        help=f"agreeing rejects before a stale median is replaced (default {DEFAULT_DEPTH_RECOVER})",
    )
    parser.add_argument(
        "--slot-iou",
        type=_unit_float_arg("--slot-iou"),
        default=DEFAULT_SLOT_IOU,
        help=f"minimum box IoU to reuse an instance slot (default {DEFAULT_SLOT_IOU:g})",
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
) -> Tuple[List[str], Tuple[float, float, float], Tuple[float, float, float], Tuple[int, int, int], ProbeResources]:
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
    return labels, mean, std, pad_color, ProbeResources(args)


def probe_once(
    args: argparse.Namespace,
    labels: Sequence[str],
    mean: Tuple[float, float, float],
    std: Tuple[float, float, float],
    pad_color: Tuple[int, int, int],
    resources: ProbeResources,
    *,
    want_jpeg: bool = False,
    want_preview: bool = False,
    want_vo: bool = False,
) -> Optional[Dict[str, Any]]:
    """Capture and process one frame; None when a video file reaches EOF."""
    cycle_started_ns = time.perf_counter_ns()
    frame, frame_id, t_ns = resources.read_frame()
    if frame is None:
        return None
    frame_h, frame_w = frame.shape[:2]

    notes: List[str] = []
    stabiliser = resources.depth_stabiliser
    stabiliser_settings = stabiliser.settings()
    if args.depth is not None:
        stabiliser.advance()
        resources.slot_tracker.advance()
        notes.append(
            "depth stabiliser window={window} jump={jump:g} "
            "evict={evict} recover={recover}".format(**stabiliser_settings)
        )
    yolo_affine = make_affine(frame_w, frame_h, args.yolo_size, args.yolo_size)
    depth_affine = make_affine(frame_w, frame_h, args.depth_size, args.depth_size)
    calibration = resolve_calibration(args, frame_w, frame_h, notes)

    timings_ms: Dict[str, Optional[float]] = {
        "yolo": None,
        "depth": None,
        "hands": None,
        "cycle": None,
    }
    yolo_session = resources.yolo_session()
    started_ns = time.perf_counter_ns()
    detections = detect(frame, args, labels, yolo_affine, notes, yolo_session)
    timings_ms["yolo"] = (time.perf_counter_ns() - started_ns) / 1e6
    for detection in detections:
        detection["frame_id"] = frame_id
        detection["id"] = detection.get(
            "id", _stable_detection_id(str(detection.get("name", "unknown")))
        )

    depth = None
    if args.depth is not None:
        started_ns = time.perf_counter_ns()
        session = resources.depth_session()
        depth = predict_depth(frame, session, depth_affine, args, mean, std, pad_color)
        resources.slot_tracker.associate(detections)
        for detection in detections:
            u, v = detection["center_px"]
            raw_z = depth_at_box(
                depth, depth_affine, detection["bbox_px"], args.depth_scale
            )
            if detection["z_ambiguous"]:
                sample = stabiliser.untracked_sample(raw_z)
            else:
                sample = stabiliser.update(
                    (str(detection.get("name", "unknown")), detection["slot"]), raw_z
                )
            detection["z_raw"] = sample["z_raw"]
            detection["Z_m"] = sample["Z_m"]
            detection["z_rejected"] = sample["z_rejected"]
            z = detection["Z_m"]
            if z is not None and calibration is not None:
                detection["xyz_cam"] = unproject(u, v, z, calibration)
        timings_ms["depth"] = (time.perf_counter_ns() - started_ns) / 1e6

    started_ns = time.perf_counter_ns()
    hand = find_fingertip(
        frame, frame_id, args, depth, depth_affine, calibration, args.depth_scale, notes,
        resources,
    )
    if args.hands:
        timings_ms["hands"] = (time.perf_counter_ns() - started_ns) / 1e6

    result: Dict[str, Any] = {
        "frame_id": frame_id,
        "t_ns": t_ns,
        "W": frame_w,
        "H": frame_h,
        "vocabulary": labels,
        "affines": {
            "yolo": asdict(yolo_affine),
            "depth": asdict(depth_affine),
            "hand": {"origin_x": 0.0, "origin_y": 0.0, "scale": 1.0},
        },
        "depth_grid": (
            {
                "W_d": depth.shape[1],
                "H_d": depth.shape[0],
                "scale": args.depth_scale,
                "depth_scale": args.depth_scale,
                "sampler": DEPTH_SAMPLER_BOX,
                "fingertip_sampler": DEPTH_SAMPLER_PATCH,
            }
            if depth is not None
            else None
        ),
        "detections": detections,
        "depth_stabiliser": stabiliser_settings,
        "hand": hand,
        "notes": notes,
        "timings_ms": timings_ms,
    }
    if want_vo:
        # Keep the in-memory frame/depth pair available to the live VO consumer;
        # these arrays are intentionally excluded from the JSON probe output.
        result["_vo_input"] = {
            "frame": frame,
            "depth": depth,
            "depth_affine": depth_affine,
            "calibration": calibration,
        }

    if want_jpeg:
        started_ns = time.perf_counter_ns()
        jpeg = encode_preview(
            frame,
            getattr(args, "jpeg_width", DEFAULT_PREVIEW_WIDTH),
            getattr(args, "jpeg_quality", DEFAULT_PREVIEW_QUALITY),
        )
        timings_ms["jpeg"] = (time.perf_counter_ns() - started_ns) / 1e6
        if jpeg is not None:
            result["jpeg"] = jpeg

    if want_preview:
        started_ns = time.perf_counter_ns()
        preview = render_preview(
            frame,
            detections,
            depth,
            width=getattr(args, "preview_width", DEFAULT_PREVIEW_WIDTH),
            quality=getattr(args, "preview_quality", DEFAULT_PREVIEW_QUALITY),
            target_name=getattr(args, "preview_target", None),
            depth_scale=float(getattr(args, "depth_scale", 0.0)),
            depth_affine=depth_affine if depth is not None else None,
        )
        timings_ms["preview"] = (time.perf_counter_ns() - started_ns) / 1e6
        if preview is not None:
            result["preview"] = preview

    timings_ms["cycle"] = (time.perf_counter_ns() - cycle_started_ns) / 1e6
    return result


def main() -> int:
    args = build_parser().parse_args()
    labels, mean, std, pad_color, resources = prepare(args)
    with resources:
        probe = probe_once(args, labels, mean, std, pad_color, resources)
        if probe is None:
            return 0
        print(
            json.dumps(
                probe,
                indent=2,
                sort_keys=False,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
