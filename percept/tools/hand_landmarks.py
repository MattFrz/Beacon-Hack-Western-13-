#!/usr/bin/env python3
"""MediaPipe hand landmarks straight from TFLite, with no MediaPipe bindings.

QNX packages both `tflite-runtime` and `mediapipe`, but the Task API cannot build
a HandLandmarker there: the QNX build's pybind11 proto caster is missing, so
`HandLandmarker.create_from_options()` raises `TypeError: create(): incompatible
function arguments` (docs/pi-bringup.md). The two models inside
`hand_landmarker.task` are ordinary TFLite graphs, so this module runs them
directly and does the decoding MediaPipe's calculators would otherwise do:

    hand_landmarker.task
      └─ hand_detector.tflite           192x192 -> 2016 boxes + 7 keypoints each
      └─ hand_landmarks_detector.tflite 224x224 -> 21 landmarks + presence score

Why this instead of the YOLO `hand` class it replaces: YOLOE-26n is zero-shot
over LVIS, whose 1,203 categories contain no bare `hand` (they contain handbag,
handle, handcuff, hand towel, handsaw, and `watch/wristwatch`). A text prompt for
a category the detector was never grounded on scored 0.05-0.25 against a
first-person hand on the Pi and 0.65 on a clean photo, which no threshold fixes.
`hand` here is a trained class with a real score, and landmarks give the wrist
and the fingertips instead of one box centre.

Everything is plain numpy plus two cv2 calls (`resize`, `warpAffine`). The
detector's 2016 anchors come from MediaPipe's SSD anchor configuration:
four stride layers (8, 16, 16, 16) over a 192 px input, two anchors per cell,
fixed anchor size, so 24² + 12² + 12² + 12² cells x 2 = 2016.
"""

from __future__ import annotations

import io
import math
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASK = REPO_ROOT / "models" / "hand_landmarker.task"

DETECTOR_MEMBER = "hand_detector.tflite"
LANDMARKS_MEMBER = "hand_landmarks_detector.tflite"

DETECTOR_SIZE = 192
DETECTOR_STRIDES: Tuple[int, ...] = (8, 16, 16, 16)
ANCHORS_PER_CELL = 2
LANDMARK_SIZE = 224

# MediaPipe's own palm-to-hand rectangle: 2.6x the detected box, shifted up by
# half a box height, squared on the longer side (modules/hand_landmark/
# palm_detection_detection_to_roi.pbtxt, RectTransformationCalculator
# scale_x/scale_y 2.6, shift_y -0.5, square_long true). A tighter crop loses the
# fingertips, and the landmark model was trained on this framing.
ROI_SCALE = 2.6
ROI_SHIFT_Y = -0.5

KEYPOINTS_PER_HAND = 7
# Detector keypoints worth knowing by name; the rest refine the rotation only.
KP_WRIST, KP_MIDDLE_MCP = 0, 2

# Landmark indices in MediaPipe's 21-point hand: wrist, index fingertip.
WRIST, INDEX_TIP = 0, 8
LANDMARK_COUNT = 21
LANDMARK_MAX = 100.0  # MediaPipe's score clipping before the sigmoid


def ssd_anchors(
    size: int = DETECTOR_SIZE,
    strides: Sequence[int] = DETECTOR_STRIDES,
    per_cell: int = ANCHORS_PER_CELL,
):
    """Normalised anchor centres, in the order the detector's output rows use."""
    import numpy as np

    centers: List[Tuple[float, float]] = []
    for stride in strides:
        grid = size // stride
        for row in range(grid):
            for column in range(grid):
                for _ in range(per_cell):
                    centers.append(((column + 0.5) / grid, (row + 0.5) / grid))
    return np.asarray(centers, dtype=np.float32)


def decode_hands(regressors: Any, scores: Any, anchors: Any, size: int,
                 min_score: float):
    """Turn the detector's raw rows into normalised boxes, scores and keypoints.

    MediaPipe's TensorsToDetectionsCalculator with reverse_output_order and a
    fixed 1x1 anchor: each box is (x_center, y_center, w, h) relative to its
    anchor and divided by the input size, and each of the 7 keypoints is an
    (x, y) offset in the same units.
    """
    import numpy as np

    raw = np.asarray(regressors, dtype=np.float32).reshape(-1, 4 + KEYPOINTS_PER_HAND * 2)
    logits = np.asarray(scores, dtype=np.float32).reshape(-1)
    anchor = np.asarray(anchors, dtype=np.float32)

    confidence = 1.0 / (1.0 + np.exp(-np.clip(logits, -LANDMARK_MAX, LANDMARK_MAX)))
    keep = np.where(confidence >= float(min_score))[0]
    if keep.size == 0:
        return [], np.zeros((0, 7, 2), dtype=np.float32), np.zeros(0, dtype=np.float32)

    row = raw[keep]
    base = anchor[keep]
    x_center = row[:, 0] / size + base[:, 0]
    y_center = row[:, 1] / size + base[:, 1]
    half_w = row[:, 2] / size / 2.0
    half_h = row[:, 3] / size / 2.0
    boxes = np.stack(
        [x_center - half_w, y_center - half_h, x_center + half_w, y_center + half_h],
        axis=1,
    )
    offsets = row[:, 4:].reshape(-1, KEYPOINTS_PER_HAND, 2)
    keypoints = offsets / float(size) + base[:, None, :]
    return boxes, keypoints, confidence[keep]


def nms(boxes: Any, scores: Any, iou_threshold: float = 0.3) -> List[int]:
    """Greedy NMS over normalised xyxy boxes; returns indices, best first."""
    import numpy as np

    order = np.argsort(-np.asarray(scores, dtype=np.float32))
    boxes = np.asarray(boxes, dtype=np.float32)
    kept: List[int] = []
    while order.size:
        best = int(order[0])
        kept.append(best)
        rest = order[1:]
        if rest.size == 0:
            break
        x1 = np.maximum(boxes[best, 0], boxes[rest, 0])
        y1 = np.maximum(boxes[best, 1], boxes[rest, 1])
        x2 = np.minimum(boxes[best, 2], boxes[rest, 2])
        y2 = np.minimum(boxes[best, 3], boxes[rest, 3])
        inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
        area_best = (boxes[best, 2] - boxes[best, 0]) * (boxes[best, 3] - boxes[best, 1])
        area_rest = (boxes[rest, 2] - boxes[rest, 0]) * (boxes[rest, 3] - boxes[rest, 1])
        union = area_best + area_rest - inter
        iou = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
        order = rest[iou <= iou_threshold]
    return kept


def crop_transform(box: Sequence[float], keypoints: Any, frame_w: int, frame_h: int,
                   scale: float = ROI_SCALE, shift_y: float = ROI_SHIFT_Y):
    """2x3 affine mapping the landmark model's square crop back into the frame.

    The crop is `scale` times the detected box's longer side, centred on the box
    and shifted up by `shift_y` box heights, then rotated so the vector from the
    wrist to the middle knuckle points up the image -- that is the orientation
    the landmark model saw during training.
    """
    import cv2
    import numpy as np

    x1, y1, x2, y2 = (float(v) for v in box[:4])
    center_x = (x1 + x2) / 2.0 * frame_w
    center_y = (y1 + y2) / 2.0 * frame_h
    side = max((x2 - x1) * frame_w, (y2 - y1) * frame_h) * float(scale)
    center_y += float(shift_y) * (y2 - y1) * frame_h
    side = max(side, 1.0)

    wrist = np.asarray(keypoints[int(KP_WRIST)], dtype=np.float64)
    knuckle = np.asarray(keypoints[int(KP_MIDDLE_MCP)], dtype=np.float64)
    delta = (knuckle - wrist) * np.array([frame_w, frame_h], dtype=np.float64)
    # Fingers pointing up is -90 degrees in image coordinates (y grows down).
    angle = math.degrees(math.atan2(delta[1], delta[0])) + 90.0 if np.any(delta) else 0.0

    matrix = cv2.getRotationMatrix2D((center_x, center_y), angle, float(LANDMARK_SIZE) / side)
    matrix[0, 2] += LANDMARK_SIZE / 2.0 - (
        matrix[0, 0] * center_x + matrix[0, 1] * center_y + matrix[0, 2]
    )
    matrix[1, 2] += LANDMARK_SIZE / 2.0 - (
        matrix[1, 0] * center_x + matrix[1, 1] * center_y + matrix[1, 2]
    )
    return matrix


def load_interpreter(model_content: Optional[bytes] = None,
                     model_path: Optional[Path] = None, threads: int = 1):
    """Open a TFLite interpreter on whichever runtime this image ships.

    QNX packages `tflite-runtime`; a laptop usually has `ai_edge_litert` or full
    TensorFlow. Import order is deliberate: the QNX package first, so the device
    never pays for a fallback import chain.
    """
    errors: List[str] = []
    for module, attribute in (
        ("tflite_runtime.interpreter", "Interpreter"),
        ("ai_edge_litert.interpreter", "Interpreter"),
        ("tensorflow.lite.python.interpreter", "Interpreter"),
    ):
        try:
            namespace = __import__(module, fromlist=[attribute])
            interpreter_class = getattr(namespace, attribute)
        except Exception as exc:  # ImportError, or a broken packaged module
            errors.append(f"{module}: {exc}")
            continue
        if model_content is not None:
            interpreter = interpreter_class(model_content=model_content, num_threads=threads)
        else:
            interpreter = interpreter_class(model_path=str(model_path), num_threads=threads)
        return interpreter
    raise RuntimeError(
        "no TFLite runtime (tflite_runtime, ai_edge_litert or tensorflow); "
        + "; ".join(errors)
    )


def read_bundle(path: Path) -> Tuple[bytes, bytes]:
    """Pull the two .tflite graphs out of a MediaPipe .task bundle.

    The bundle is a zip of the same files a raw TFLite pipeline needs, and
    `models/hand_landmarker.task` is already staged on the device, so nothing
    has to be downloaded or unzipped there.
    """
    path = Path(path)
    if path.suffix != ".task":
        raise ValueError(f"expected a .task bundle, got {path}")
    with zipfile.ZipFile(io.BytesIO(path.read_bytes())) as bundle:
        names = set(bundle.namelist())
        missing = [name for name in (DETECTOR_MEMBER, LANDMARKS_MEMBER) if name not in names]
        if missing:
            raise ValueError(f"{path} has no {', '.join(missing)}; found {sorted(names)}")
        return bundle.read(DETECTOR_MEMBER), bundle.read(LANDMARKS_MEMBER)


class HandLandmarks:
    """Palm detection plus 21 landmarks on a BGR frame, no MediaPipe bindings."""

    def __init__(self, task_path: Path = DEFAULT_TASK, min_score: float = 0.5,
                 nms_iou: float = 0.3, min_presence: float = 0.5, threads: int = 1):
        self.task_path = Path(task_path)
        detector_model, landmark_model = read_bundle(self.task_path)
        self.min_score = float(min_score)
        self.nms_iou = float(nms_iou)
        # MediaPipe gates landmarks on this score before they leave the graph
        # (GateCalculator on hand_presence); it is the cheapest way to reject a
        # palm-detector false positive, e.g. a bottle scoring 0.40 with presence 0.001.
        self.min_presence = float(min_presence)
        self._detector = load_interpreter(model_content=detector_model, threads=threads)
        self._landmarks = load_interpreter(model_content=landmark_model, threads=threads)
        self._anchors = ssd_anchors()
        self._detector_in = self._detector.get_input_details()[0]
        self._detector.allocate_tensors()
        outputs = self._detector.get_output_details()
        # Identity is the 18 regressors per anchor, Identity_1 the score.
        self._detector_out = (
            next(d for d in outputs if d["shape"][-1] == 4 + KEYPOINTS_PER_HAND * 2),
            next(d for d in outputs if d["shape"][-1] == 1),
        )
        self._landmarks_in = self._landmarks.get_input_details()[0]
        self._landmarks.allocate_tensors()
        landmark_outputs = self._landmarks.get_output_details()
        self._landmarks_out = next(d for d in landmark_outputs if d["shape"][-1] == LANDMARK_COUNT * 3)
        self._presence_out = next(
            d for d in landmark_outputs if d["shape"][-1] == 1
        )

    # ---- stages ---------------------------------------------------------
    def palms(self, frame: Any):
        """Detect palm boxes in normalised xyxy, with 7 keypoints each."""
        import cv2
        import numpy as np

        square = cv2.resize(frame, (DETECTOR_SIZE, DETECTOR_SIZE),
                            interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(square, cv2.COLOR_BGR2RGB)
        tensor = rgb.astype(np.float32)[None, ...] / 255.0
        self._detector.set_tensor(self._detector_in["index"], tensor)
        self._detector.invoke()
        regressors = self._detector.get_tensor(self._detector_out[0]["index"])
        scores = self._detector.get_tensor(self._detector_out[1]["index"])

        boxes, keypoints, confidence = decode_hands(
            regressors, scores, self._anchors, DETECTOR_SIZE, self.min_score
        )
        if not len(boxes):
            return []
        keep = nms(boxes, confidence, self.nms_iou)
        return [
            {
                "bbox_norm": [float(v) for v in boxes[index]],
                "keypoints_norm": [[float(u), float(v)] for u, v in keypoints[index]],
                "conf": float(confidence[index]),
            }
            for index in keep
        ]

    def landmarks_for(self, frame: Any, palm: Dict[str, Any]):
        """Run the 21-landmark model on one palm's crop; None when it declines."""
        import cv2
        import numpy as np

        height, width = frame.shape[:2]
        matrix = crop_transform(
            palm["bbox_norm"], palm["keypoints_norm"], width, height
        )
        crop = cv2.warpAffine(frame, matrix, (LANDMARK_SIZE, LANDMARK_SIZE),
                              flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        tensor = rgb.astype(np.float32)[None, ...] / 255.0
        self._landmarks.set_tensor(self._landmarks_in["index"], tensor)
        self._landmarks.invoke()
        raw = np.asarray(self._landmarks.get_tensor(self._landmarks_out["index"]),
                         dtype=np.float32).reshape(LANDMARK_COUNT, 3)
        presence = float(
            self._landmarks.get_tensor(self._presence_out["index"]).reshape(-1)[0]
        )
        if not np.all(np.isfinite(raw)):
            return None

        inverse = cv2.invertAffineTransform(matrix)
        # The landmark model reports crop pixels (0..224), not [0, 1] fractions.
        points = raw[:, :2]
        stacked = np.concatenate([points, np.ones((len(points), 1), dtype=np.float32)], axis=1)
        full = stacked @ inverse.T
        return {
            "landmarks_px": [[float(u), float(v)] for u, v in full],
            "presence": presence,
            "palm": palm,
        }

    def find(self, frame: Any) -> Optional[Dict[str, Any]]:
        """The best hand in one BGR frame, or None.

        Returns the field names live_probe puts on the wire plus the landmarks:
        `bbox_px`, `conf`, `landmarks_px`, `tip_px`, `wrist_px`, `presence`.
        """
        height, width = frame.shape[:2]
        best: Optional[Dict[str, Any]] = None
        for palm in self.palms(frame):
            found = self.landmarks_for(frame, palm)
            if found is None or found["presence"] < self.min_presence:
                continue
            if best is None or found["presence"] > best["presence"]:
                best = found
        if best is None:
            return None

        palm = best["palm"]
        x1, y1, x2, y2 = palm["bbox_norm"]
        points = best["landmarks_px"]
        # The landmark model's crop is wider than the palm box, so the box the
        # dashboard draws and the law measures from is the landmarks' own extent.
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        return {
            "bbox_px": [
                max(0.0, min(xs)),
                max(0.0, min(ys)),
                min(float(width), max(xs)),
                min(float(height), max(ys)),
            ],
            "conf": float(palm["conf"]),
            "presence": float(best["presence"]),
            "landmarks_px": points,
            "tip_px": points[int(INDEX_TIP)],
            "wrist_px": points[int(WRIST)],
            "palm_bbox_norm": [float(x1), float(y1), float(x2), float(y2)],
        }
