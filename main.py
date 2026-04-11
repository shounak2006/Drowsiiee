"""
main.py
-------
Real-time Driver Drowsiness Detection System
============================================

Entry point: reads from webcam, runs detection, renders HUD, triggers alerts.

Usage
-----
    python main.py [--camera 0] [--width 1280] [--height 720] [--fps-target 30]

Controls
--------
    Q / ESC  – quit
    R        – reset fatigue score
    S        – save current frame as PNG
"""

from __future__ import annotations

import argparse
import time
import sys
import cv2
import numpy as np

from detection import FaceDetector, DetectionResult
from alert import AlertManager, DrowsinessState
from ear_calculation import EAR_THRESHOLD   # re-exported for HUD label


# ---------------------------------------------------------------------------
# HUD rendering constants
# ---------------------------------------------------------------------------
FONT       = cv2.FONT_HERSHEY_DUPLEX
FONT_SMALL = cv2.FONT_HERSHEY_SIMPLEX
GREEN  = (0, 220, 60)
ORANGE = (0, 165, 255)
RED    = (0, 0, 230)
WHITE  = (240, 240, 240)
BLACK  = (10, 10, 10)
CYAN   = (0, 220, 200)
PANEL_ALPHA = 0.55          # transparency of the info panel


# ---------------------------------------------------------------------------
# Overlay helpers
# ---------------------------------------------------------------------------

def _alpha_rect(frame: np.ndarray, x: int, y: int, w: int, h: int,
                color_bgr, alpha: float) -> None:
    """Draw a semi-transparent filled rectangle."""
    roi = frame[y:y+h, x:x+w]
    overlay = roi.copy()
    overlay[:] = color_bgr
    cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)
    frame[y:y+h, x:x+w] = roi


def _draw_gauge(frame: np.ndarray, cx: int, cy: int, radius: int,
                value: float, color_bgr) -> None:
    """Draw a circular arc gauge (0–100) for the fatigue score."""
    # Background arc
    cv2.ellipse(frame, (cx, cy), (radius, radius), -90, 0, 360,
                (60, 60, 60), 6, cv2.LINE_AA)
    # Filled arc proportional to value
    sweep = int(value / 100 * 360)
    if sweep > 0:
        cv2.ellipse(frame, (cx, cy), (radius, radius), -90, 0, sweep,
                    color_bgr, 6, cv2.LINE_AA)
    # Centre text
    label = f"{int(value)}"
    (tw, th), _ = cv2.getTextSize(label, FONT_SMALL, 0.7, 2)
    cv2.putText(frame, label, (cx - tw // 2, cy + th // 2),
                FONT_SMALL, 0.7, WHITE, 2, cv2.LINE_AA)


def _draw_ear_bar(frame: np.ndarray, x: int, y: int, w: int, h: int,
                  ear: float) -> None:
    """Vertical bar showing EAR relative to threshold."""
    max_ear = 0.45
    filled = int(h * min(ear, max_ear) / max_ear)
    # Background
    cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 50), -1)
    # Bar
    color = GREEN if ear >= EAR_THRESHOLD else RED
    cv2.rectangle(frame, (x, y + h - filled), (x + w, y + h), color, -1)
    # Threshold line
    thresh_y = y + h - int(h * EAR_THRESHOLD / max_ear)
    cv2.line(frame, (x - 4, thresh_y), (x + w + 4, thresh_y), ORANGE, 1, cv2.LINE_AA)


def render_hud(
    frame: np.ndarray,
    result: DetectionResult,
    alert: AlertManager,
    fps: float,
    frame_count: int,
) -> np.ndarray:
    """
    Overlay the full HUD on the (already annotated) frame.

    Layout
    ------
    Top-left  : Status banner + warning text if critical
    Right     : Info panel (EAR, fatigue gauge, blink rate, closure duration)
    Bottom    : FPS, frame counter
    """
    h, w = frame.shape[:2]
    state = alert.state
    state_color = alert.status_color_bgr

    # ---- Face bounding box -------------------------------------------
    if result.face_bbox:
        fx, fy, fw, fh = result.face_bbox
        cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), state_color, 2, cv2.LINE_AA)
        cv2.putText(frame, "FACE", (fx, fy - 8), FONT_SMALL, 0.5, state_color, 1, cv2.LINE_AA)

    # ---- Right-side info panel ---------------------------------------
    panel_w = 220
    panel_h = 300
    panel_x = w - panel_w - 10
    panel_y = 10
    _alpha_rect(frame, panel_x, panel_y, panel_w, panel_h, BLACK, PANEL_ALPHA)
    cv2.rectangle(frame, (panel_x, panel_y),
                  (panel_x + panel_w, panel_y + panel_h), state_color, 1, cv2.LINE_AA)

    # Title
    cv2.putText(frame, "DRIVER MONITOR", (panel_x + 10, panel_y + 22),
                FONT_SMALL, 0.45, state_color, 1, cv2.LINE_AA)
    cv2.line(frame, (panel_x + 8, panel_y + 28),
             (panel_x + panel_w - 8, panel_y + 28), state_color, 1)

    # EAR values
    ear_label = f"EAR  L:{result.left_ear:.3f} R:{result.right_ear:.3f}"
    avg_label = f"AVG: {result.avg_ear:.3f}"
    ear_color = GREEN if result.avg_ear >= EAR_THRESHOLD else RED
    cv2.putText(frame, ear_label, (panel_x + 8, panel_y + 50),
                FONT_SMALL, 0.38, WHITE, 1, cv2.LINE_AA)
    cv2.putText(frame, avg_label, (panel_x + 8, panel_y + 68),
                FONT_SMALL, 0.5, ear_color, 1, cv2.LINE_AA)

    # EAR bar
    _draw_ear_bar(frame, panel_x + 175, panel_y + 38, 22, 70, result.avg_ear)
    cv2.putText(frame, "EAR", (panel_x + 172, panel_y + 120),
                FONT_SMALL, 0.32, WHITE, 1, cv2.LINE_AA)

    # Fatigue gauge
    gauge_cx = panel_x + 65
    gauge_cy = panel_y + 170
    _draw_gauge(frame, gauge_cx, gauge_cy, 42, alert.fatigue_score, state_color)
    cv2.putText(frame, "FATIGUE", (gauge_cx - 26, gauge_cy + 56),
                FONT_SMALL, 0.38, WHITE, 1, cv2.LINE_AA)

    # Stats column
    stats_x = panel_x + 128
    cv2.putText(frame, f"Blink/min", (stats_x, panel_y + 140),
                FONT_SMALL, 0.38, (180, 180, 180), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{alert.blink_rate:.1f}", (stats_x, panel_y + 158),
                FONT_SMALL, 0.55, CYAN, 1, cv2.LINE_AA)

    cv2.putText(frame, f"Closure", (stats_x, panel_y + 185),
                FONT_SMALL, 0.38, (180, 180, 180), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{alert.closure_duration:.2f}s", (stats_x, panel_y + 202),
                FONT_SMALL, 0.55, CYAN, 1, cv2.LINE_AA)

    # Threshold reminder
    cv2.putText(frame, f"Thresh EAR<{EAR_THRESHOLD}", (panel_x + 8, panel_y + 285),
                FONT_SMALL, 0.33, (140, 140, 140), 1, cv2.LINE_AA)

    # ---- Top status banner -------------------------------------------
    banner_h = 38
    _alpha_rect(frame, 0, 0, w, banner_h, state_color, 0.35)
    status_text = alert.status_label
    (tw, _), _ = cv2.getTextSize(status_text, FONT, 0.75, 2)
    cv2.putText(frame, status_text, (w // 2 - tw // 2, 27),
                FONT, 0.75, WHITE, 2, cv2.LINE_AA)

    # ---- CRITICAL overlay warning ------------------------------------
    if state == DrowsinessState.CRITICAL:
        warn_lines = ["⚠  DROWSINESS DETECTED  ⚠", "STOP DRIVING – PULL OVER NOW"]
        for i, line in enumerate(warn_lines):
            (tw, th), _ = cv2.getTextSize(line, FONT, 0.9, 2)
            ypos = h // 2 + i * 45 - 20
            # shadow
            cv2.putText(frame, line, (w // 2 - tw // 2 + 2, ypos + 2),
                        FONT, 0.9, BLACK, 3, cv2.LINE_AA)
            cv2.putText(frame, line, (w // 2 - tw // 2, ypos),
                        FONT, 0.9, (0, 0, 255) if i == 0 else WHITE, 2, cv2.LINE_AA)

    # ---- Bottom bar --------------------------------------------------
    bottom_y = h - 12
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, bottom_y),
                FONT_SMALL, 0.45, (150, 150, 150), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Frame: {frame_count}", (100, bottom_y),
                FONT_SMALL, 0.45, (150, 150, 150), 1, cv2.LINE_AA)
    if not result.face_detected:
        cv2.putText(frame, "NO FACE DETECTED", (w // 2 - 90, bottom_y),
                    FONT_SMALL, 0.5, ORANGE, 1, cv2.LINE_AA)

    return frame


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Driver Drowsiness Detection")
    p.add_argument("--camera",     type=int,   default=0,    help="Camera index (default 0)")
    p.add_argument("--width",      type=int,   default=1280, help="Capture width")
    p.add_argument("--height",     type=int,   default=720,  help="Capture height")
    p.add_argument("--fps-target", type=float, default=30.0, help="Target FPS cap")
    p.add_argument("--ear-thresh", type=float, default=None, help="Override EAR threshold")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Optionally override EAR threshold at runtime
    if args.ear_thresh is not None:
        import ear_calculation as _ec
        import alert as _al
        _ec.EAR_THRESHOLD = args.ear_thresh
        _al.EAR_THRESHOLD = args.ear_thresh

    # ---- Camera setup ------------------------------------------------
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera index {args.camera}. "
              "Try --camera 1 or check permissions.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS,          args.fps_target)
    # Minimal buffer to reduce latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] Camera opened: {actual_w}×{actual_h}")

    # ---- Modules -----------------------------------------------------
    detector = FaceDetector(min_detection_confidence=0.6, min_tracking_confidence=0.6)
    alert    = AlertManager()

    # ---- Timing ------------------------------------------------------
    prev_time   = time.perf_counter()
    fps_smooth  = args.fps_target
    frame_count = 0
    min_dt      = 1.0 / args.fps_target

    print("[INFO] Starting detection loop. Press Q or ESC to quit, R to reset, S to save.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Frame grab failed – retrying.")
            time.sleep(0.05)
            continue

        frame_count += 1

        # ---- Timing --------------------------------------------------
        now = time.perf_counter()
        dt  = now - prev_time
        if dt < min_dt:
            # Simple FPS cap (avoid busy-waiting hammering the CPU)
            time.sleep(min_dt - dt)
            now = time.perf_counter()
            dt  = now - prev_time
        prev_time = now
        fps_smooth = 0.9 * fps_smooth + 0.1 * (1.0 / dt if dt > 0 else fps_smooth)

        # ---- Detection -----------------------------------------------
        result = detector.process(frame)

        # ---- Alert logic ---------------------------------------------
        if result.face_detected:
            alert.update(result.avg_ear, dt)
        else:
            # No face → decay fatigue slowly; don't trigger closure timer
            alert.update(1.0, dt)   # EAR = 1.0 → eyes "open" from alert's perspective

        # ---- Render HUD ----------------------------------------------
        annotated = render_hud(
            result.annotated_frame if result.annotated_frame is not None else frame,
            result, alert, fps_smooth, frame_count,
        )

        cv2.imshow("Driver Drowsiness Detection", annotated)

        # ---- Key handling --------------------------------------------
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):        # Q or ESC
            break
        elif key == ord("r"):            # Reset fatigue
            alert.__init__()
            print("[INFO] Fatigue score reset.")
        elif key == ord("s"):            # Save snapshot
            fname = f"snapshot_{frame_count:06d}.png"
            cv2.imwrite(fname, annotated)
            print(f"[INFO] Snapshot saved → {fname}")

    # ---- Cleanup -----------------------------------------------------
    cap.release()
    detector.release()
    cv2.destroyAllWindows()
    print("[INFO] Session ended.")


if __name__ == "__main__":
    main()
