"""
ear_calculation.py
------------------
Eye Aspect Ratio (EAR) computation utilities.

EAR formula (Soukupová & Čech, 2016):
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

where p1..p6 are the six eye landmark points ordered as:
    p1 = left corner, p4 = right corner,
    p2, p3 = upper lid,  p5, p6 = lower lid.
"""

import math
from typing import Tuple, List


# ---------------------------------------------------------------------------
# MediaPipe Face Mesh landmark indices for each eye
# ---------------------------------------------------------------------------
# Left eye  (from the subject's perspective)
LEFT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]
# Right eye (from the subject's perspective)
RIGHT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]

# Six-point EAR order: [left_corner, upper1, upper2, right_corner, lower2, lower1]
# Already encoded in the lists above.


def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Return the Euclidean distance between two 2-D points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def compute_ear(landmarks: List[Tuple[float, float]]) -> float:
    """
    Compute Eye Aspect Ratio for a single eye.

    Parameters
    ----------
    landmarks : list of (x, y) tuples, length == 6
        Eye landmark coordinates in the order:
        [left_corner, upper1, upper2, right_corner, lower2, lower1]

    Returns
    -------
    float : EAR value (0.0 … ~0.4 for open eyes)
    """
    if len(landmarks) != 6:
        raise ValueError(f"Expected 6 landmarks, got {len(landmarks)}.")

    p1, p2, p3, p4, p5, p6 = landmarks

    vertical_a = euclidean_distance(p2, p6)
    vertical_b = euclidean_distance(p3, p5)
    horizontal  = euclidean_distance(p1, p4)

    if horizontal < 1e-6:
        return 0.0

    ear = (vertical_a + vertical_b) / (2.0 * horizontal)
    return ear


def average_ear(left_ear: float, right_ear: float) -> float:
    """Return the mean EAR across both eyes."""
    return (left_ear + right_ear) / 2.0


def extract_eye_landmarks(face_landmarks, image_width: int, image_height: int,
                           indices: List[int]) -> List[Tuple[float, float]]:
    """
    Pull pixel coordinates for a given set of landmark indices from a
    MediaPipe NormalizedLandmarkList.

    Parameters
    ----------
    face_landmarks : mediapipe NormalizedLandmarkList
    image_width, image_height : frame dimensions (pixels)
    indices : landmark index list (e.g. LEFT_EYE_LANDMARKS)

    Returns
    -------
    list of (x_px, y_px) tuples
    """
    coords = []
    for idx in indices:
        lm = face_landmarks.landmark[idx]
        coords.append((lm.x * image_width, lm.y * image_height))
    return coords
