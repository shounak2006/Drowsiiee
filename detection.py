"""
detection.py
------------
Face mesh detection wrapper — compatible with mediapipe 0.10+.
"""

from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

# ------------------------------------------------------------------
# Robust mediapipe import — handles both old and new package layouts
# ------------------------------------------------------------------
try:
    import mediapipe.python.solutions.face_mesh as _fm_mod
    import mediapipe.python.solutions.drawing_utils as _du_mod
    _FaceMesh    = _fm_mod.FaceMesh
    _draw_lm     = _du_mod.draw_landmarks
    _DrawSpec    = _du_mod.DrawingSpec
    _TESSELATION = _fm_mod.FACEMESH_TESSELATION
except Exception:
    import mediapipe as _mp  # type: ignore
    _sol         = _mp.solutions
    _FaceMesh    = _sol.face_mesh.FaceMesh
    _draw_lm     = _sol.drawing_utils.draw_landmarks
    _DrawSpec    = _sol.drawing_utils.DrawingSpec
    _TESSELATION = _sol.face_mesh.FACEMESH_TESSELATION

from ear_calculation import (
    LEFT_EYE_LANDMARKS,
    RIGHT_EYE_LANDMARKS,
    extract_eye_landmarks,
    compute_ear,
    average_ear,
)


@dataclass
class DetectionResult:
    face_detected: bool = False
    left_ear: float = 0.0
    right_ear: float = 0.0
    avg_ear: float = 0.0
    left_eye_pts: List[Tuple[float, float]] = field(default_factory=list)
    right_eye_pts: List[Tuple[float, float]] = field(default_factory=list)
    face_bbox: Optional[Tuple[int, int, int, int]] = None
    annotated_frame: Optional[np.ndarray] = None


class FaceDetector:
    def __init__(
        self,
        max_faces: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
    ) -> None:
        self._face_mesh = _FaceMesh(
            max_num_faces=max_faces,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process(self, frame_bgr: np.ndarray) -> DetectionResult:
        h, w = frame_bgr.shape[:2]
        result = DetectionResult(annotated_frame=frame_bgr.copy())

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        mp_result = self._face_mesh.process(frame_rgb)
        frame_rgb.flags.writeable = True

        if not mp_result.multi_face_landmarks:
            return result

        face_landmarks = mp_result.multi_face_landmarks[0]
        result.face_detected = True

        left_pts  = extract_eye_landmarks(face_landmarks, w, h, LEFT_EYE_LANDMARKS)
        right_pts = extract_eye_landmarks(face_landmarks, w, h, RIGHT_EYE_LANDMARKS)

        result.left_eye_pts  = left_pts
        result.right_eye_pts = right_pts
        result.left_ear  = compute_ear(left_pts)
        result.right_ear = compute_ear(right_pts)
        result.avg_ear   = average_ear(result.left_ear, result.right_ear)
        result.face_bbox = self._face_bbox(face_landmarks, w, h)
        result.annotated_frame = self._draw(
            result.annotated_frame, face_landmarks, left_pts, right_pts
        )
        return result

    def release(self) -> None:
        self._face_mesh.close()

    @staticmethod
    def _face_bbox(face_landmarks, w: int, h: int) -> Tuple[int, int, int, int]:
        xs = [lm.x * w for lm in face_landmarks.landmark]
        ys = [lm.y * h for lm in face_landmarks.landmark]
        x1, y1 = int(min(xs)), int(min(ys))
        x2, y2 = int(max(xs)), int(max(ys))
        pad = 15
        x1 = max(0, x1 - pad);  y1 = max(0, y1 - pad)
        x2 = min(w, x2 + pad);  y2 = min(h, y2 + pad)
        return (x1, y1, x2 - x1, y2 - y1)

    @staticmethod
    def _draw_eye_contour(frame, pts, color):
        int_pts = [(int(x), int(y)) for x, y in pts]
        for pt in int_pts:
            cv2.circle(frame, pt, 2, color, -1, cv2.LINE_AA)
        hull = cv2.convexHull(np.array(int_pts))
        cv2.polylines(frame, [hull], True, color, 1, cv2.LINE_AA)

    def _draw(self, frame, face_landmarks, left_pts, right_pts):
        _draw_lm(
            image=frame,
            landmark_list=face_landmarks,
            connections=_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=_DrawSpec(color=(80, 80, 80), thickness=1),
        )
        self._draw_eye_contour(frame, left_pts,  (0, 255, 180))
        self._draw_eye_contour(frame, right_pts, (0, 255, 180))
        return frame