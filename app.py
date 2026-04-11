"""
app.py — Driver Drowsiness Detection on Streamlit Cloud
========================================================
Uses streamlit-webrtc to capture browser webcam frames,
runs the full MediaPipe + EAR + AlertManager pipeline server-side,
and renders a live HUD with metrics dashboard.
"""

from __future__ import annotations

import threading
import time
import queue
from collections import deque
from typing import Deque

import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

import av  # PyAV – used by streamlit-webrtc

from detection import FaceDetector
from alert import AlertManager, DrowsinessState
from alert import EAR_THRESHOLD


# ─────────────────────────────────────────────────────────────────────────────
# Page config (MUST be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Drowsiiee – Driver Drowsiness Detection",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─────────────────────────────────────────────────────────────────────────────
# Global shared state (thread-safe between WebRTC callback & Streamlit thread)
# ─────────────────────────────────────────────────────────────────────────────
class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self.avg_ear: float = 0.0
        self.left_ear: float = 0.0
        self.right_ear: float = 0.0
        self.fatigue: float = 0.0
        self.blink_rate: float = 0.0
        self.closure_duration: float = 0.0
        self.state: DrowsinessState = DrowsinessState.SAFE
        self.face_detected: bool = False
        self.fps: float = 0.0
        self.frame_count: int = 0
        self.ear_history: Deque[float] = deque(maxlen=120)
        self.fatigue_history: Deque[float] = deque(maxlen=120)
        self.reset_requested: bool = False

    def update(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def snapshot(self):
        with self._lock:
            return {
                "avg_ear": self.avg_ear,
                "left_ear": self.left_ear,
                "right_ear": self.right_ear,
                "fatigue": self.fatigue,
                "blink_rate": self.blink_rate,
                "closure_duration": self.closure_duration,
                "state": self.state,
                "face_detected": self.face_detected,
                "fps": self.fps,
                "frame_count": self.frame_count,
                "ear_history": list(self.ear_history),
                "fatigue_history": list(self.fatigue_history),
            }

    def request_reset(self):
        with self._lock:
            self.reset_requested = True

    def check_and_clear_reset(self):
        with self._lock:
            val = self.reset_requested
            self.reset_requested = False
            return val


if "shared" not in st.session_state:
    st.session_state.shared = SharedState()

shared: SharedState = st.session_state.shared


# ─────────────────────────────────────────────────────────────────────────────
# VideoProcessor — runs inside WebRTC thread
# ─────────────────────────────────────────────────────────────────────────────
class DrowsinessProcessor:
    def __init__(self):
        self.detector = FaceDetector(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.alert = AlertManager()
        self._prev_time = time.perf_counter()
        self._fps_smooth = 30.0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Check for reset
        if shared.check_and_clear_reset():
            self.alert = AlertManager()

        img_bgr = frame.to_ndarray(format="bgr24")

        # Timing
        now = time.perf_counter()
        dt = max(now - self._prev_time, 1e-6)
        self._prev_time = now
        self._fps_smooth = 0.9 * self._fps_smooth + 0.1 * (1.0 / dt)

        # Detection
        result = self.detector.process(img_bgr)

        if result.face_detected:
            self.alert.update(result.avg_ear, dt)
        else:
            self.alert.update(1.0, dt)

        # Update shared state
        shared.update(
            avg_ear=result.avg_ear,
            left_ear=result.left_ear,
            right_ear=result.right_ear,
            fatigue=self.alert.fatigue_score,
            blink_rate=self.alert.blink_rate,
            closure_duration=self.alert.closure_duration,
            state=self.alert.state,
            face_detected=result.face_detected,
            fps=self._fps_smooth,
            frame_count=shared.frame_count + 1,
        )
        with shared._lock:
            shared.ear_history.append(result.avg_ear)
            shared.fatigue_history.append(self.alert.fatigue_score)

        # Draw HUD onto frame
        annotated = result.annotated_frame if result.annotated_frame is not None else img_bgr
        out = self._render_hud(annotated, result, self.alert)

        return av.VideoFrame.from_ndarray(out, format="bgr24")

    def _render_hud(self, frame, result, alert):
        h, w = frame.shape[:2]
        state = alert.state
        state_color = alert.status_color_bgr

        FONT = cv2.FONT_HERSHEY_DUPLEX
        FONT_SM = cv2.FONT_HERSHEY_SIMPLEX
        WHITE = (240, 240, 240)
        BLACK = (10, 10, 10)
        GREEN = (0, 220, 60)
        ORANGE = (0, 165, 255)
        RED = (0, 0, 230)
        CYAN = (0, 220, 200)

        def alpha_rect(x, y, rw, rh, color, alpha=0.5):
            roi = frame[y:y+rh, x:x+rw]
            if roi.size == 0:
                return
            overlay = roi.copy()
            overlay[:] = color
            cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)
            frame[y:y+rh, x:x+rw] = roi

        # Face bounding box
        if result.face_bbox:
            fx, fy, fw, fh = result.face_bbox
            cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), state_color, 2, cv2.LINE_AA)

        # Top status banner
        alpha_rect(0, 0, w, 36, state_color, 0.4)
        label = alert.status_label
        (tw, _), _ = cv2.getTextSize(label, FONT, 0.75, 2)
        cv2.putText(frame, label, (w//2 - tw//2, 26), FONT, 0.75, WHITE, 2, cv2.LINE_AA)

        # Right info panel
        pw, ph = 210, 220
        px, py = w - pw - 8, 44
        alpha_rect(px, py, pw, ph, BLACK, 0.6)
        cv2.rectangle(frame, (px, py), (px+pw, py+ph), state_color, 1, cv2.LINE_AA)

        cv2.putText(frame, "DRIVER MONITOR", (px+8, py+18), FONT_SM, 0.42, state_color, 1, cv2.LINE_AA)
        cv2.line(frame, (px+6, py+24), (px+pw-6, py+24), state_color, 1)

        ear_color = GREEN if result.avg_ear >= EAR_THRESHOLD else RED
        cv2.putText(frame, f"EAR L:{result.left_ear:.3f} R:{result.right_ear:.3f}", (px+6, py+42), FONT_SM, 0.36, WHITE, 1, cv2.LINE_AA)
        cv2.putText(frame, f"AVG: {result.avg_ear:.3f}", (px+6, py+60), FONT_SM, 0.48, ear_color, 1, cv2.LINE_AA)

        # EAR vertical bar
        bx, by, bw2, bh2 = px+178, py+34, 20, 65
        cv2.rectangle(frame, (bx, by), (bx+bw2, by+bh2), (50,50,50), -1)
        max_ear = 0.45
        filled = int(bh2 * min(result.avg_ear, max_ear) / max_ear)
        bar_color = GREEN if result.avg_ear >= EAR_THRESHOLD else RED
        cv2.rectangle(frame, (bx, by+bh2-filled), (bx+bw2, by+bh2), bar_color, -1)
        thresh_y = by + bh2 - int(bh2 * EAR_THRESHOLD / max_ear)
        cv2.line(frame, (bx-3, thresh_y), (bx+bw2+3, thresh_y), ORANGE, 1, cv2.LINE_AA)

        # Fatigue gauge (arc)
        gcx, gcy, gr = px+55, py+148, 38
        cv2.ellipse(frame, (gcx, gcy), (gr, gr), -90, 0, 360, (60,60,60), 5, cv2.LINE_AA)
        sweep = int(alert.fatigue_score / 100 * 360)
        if sweep > 0:
            cv2.ellipse(frame, (gcx, gcy), (gr, gr), -90, 0, sweep, state_color, 5, cv2.LINE_AA)
        fs_label = f"{int(alert.fatigue_score)}"
        (ftw, fth), _ = cv2.getTextSize(fs_label, FONT_SM, 0.65, 2)
        cv2.putText(frame, fs_label, (gcx - ftw//2, gcy + fth//2), FONT_SM, 0.65, WHITE, 2, cv2.LINE_AA)
        cv2.putText(frame, "FATIGUE", (gcx-22, gcy+52), FONT_SM, 0.35, WHITE, 1, cv2.LINE_AA)

        # Stats
        sx = px + 118
        cv2.putText(frame, "Blink/min", (sx, py+130), FONT_SM, 0.35, (180,180,180), 1, cv2.LINE_AA)
        cv2.putText(frame, f"{alert.blink_rate:.1f}", (sx, py+148), FONT_SM, 0.52, CYAN, 1, cv2.LINE_AA)
        cv2.putText(frame, "Closure", (sx, py+170), FONT_SM, 0.35, (180,180,180), 1, cv2.LINE_AA)
        cv2.putText(frame, f"{alert.closure_duration:.2f}s", (sx, py+188), FONT_SM, 0.52, CYAN, 1, cv2.LINE_AA)
        cv2.putText(frame, f"Thr<{EAR_THRESHOLD}", (px+6, py+212), FONT_SM, 0.32, (120,120,120), 1, cv2.LINE_AA)

        # Critical overlay
        if state == DrowsinessState.CRITICAL:
            lines = ["DROWSINESS DETECTED", "PULL OVER NOW"]
            for i, line in enumerate(lines):
                (lw, lh), _ = cv2.getTextSize(line, FONT, 0.85, 2)
                yp = h//2 + i*42 - 15
                cv2.putText(frame, line, (w//2 - lw//2 + 2, yp+2), FONT, 0.85, BLACK, 3, cv2.LINE_AA)
                cv2.putText(frame, line, (w//2 - lw//2, yp), FONT, 0.85,
                            (0,0,255) if i==0 else WHITE, 2, cv2.LINE_AA)

        # Bottom bar
        cv2.putText(frame, f"FPS:{self._fps_smooth:.1f}  Frame:{shared.frame_count}", (8, h-8),
                    FONT_SM, 0.4, (130,130,130), 1, cv2.LINE_AA)
        if not result.face_detected:
            cv2.putText(frame, "NO FACE DETECTED", (w//2-85, h-8), FONT_SM, 0.48, ORANGE, 1, cv2.LINE_AA)

        return frame


# ─────────────────────────────────────────────────────────────────────────────
# CSS — dark HUD aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

  html, body, [data-testid="stAppViewContainer"] {
    background: #060a0f !important;
    color: #e0e8f0;
  }
  [data-testid="stAppViewContainer"] { background: #060a0f !important; }
  [data-testid="block-container"] { padding: 1rem 2rem; }

  h1, h2, h3 { font-family: 'Orbitron', monospace !important; }
  p, span, div, label { font-family: 'Share Tech Mono', monospace !important; }

  /* Title */
  .hud-title {
    font-family: 'Orbitron', monospace;
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: 4px;
    text-align: center;
    background: linear-gradient(90deg, #00e5ff, #00ff88, #00e5ff);
    background-size: 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s linear infinite;
    margin-bottom: 0.2rem;
  }
  @keyframes shimmer { 0%{background-position:0%} 100%{background-position:200%} }

  .hud-sub {
    text-align: center;
    color: #4a6a7a;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 3px;
    margin-bottom: 1.5rem;
  }

  /* Metric cards */
  .metric-card {
    background: linear-gradient(135deg, #0d1a22 0%, #0a1520 100%);
    border: 1px solid #1a3a4a;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
  }
  .metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00e5ff, transparent);
  }
  .metric-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    color: #4a7a8a;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  .metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1;
  }

  /* State badge */
  .state-safe     { color: #00dc3c; text-shadow: 0 0 12px #00dc3c88; }
  .state-warning  { color: #ffa500; text-shadow: 0 0 12px #ffa50088; }
  .state-critical { color: #ff2222; text-shadow: 0 0 18px #ff222288;
                    animation: pulse-red 0.6s ease-in-out infinite alternate; }
  @keyframes pulse-red { from{opacity:1} to{opacity:0.6} }

  .state-badge {
    font-family: 'Orbitron', monospace;
    font-size: 1.1rem;
    font-weight: 900;
    letter-spacing: 3px;
    padding: 8px 16px;
    border-radius: 6px;
    text-align: center;
    margin-bottom: 12px;
  }
  .badge-safe     { background:#001a0a; border:1px solid #00dc3c; color:#00dc3c; }
  .badge-warning  { background:#1a0f00; border:1px solid #ffa500; color:#ffa500; }
  .badge-critical { background:#1a0000; border:2px solid #ff2222; color:#ff2222;
                    animation: pulse-border 0.8s ease infinite; }
  @keyframes pulse-border { 0%{box-shadow:0 0 0 0 #ff222266} 70%{box-shadow:0 0 0 8px transparent} 100%{box-shadow:0 0 0 0 transparent} }

  /* Progress bar override */
  .stProgress > div > div > div { border-radius: 4px; }

  /* Buttons */
  .stButton > button {
    background: linear-gradient(135deg, #0d2030, #0a1520);
    border: 1px solid #1a5a7a;
    color: #00e5ff;
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    letter-spacing: 2px;
    border-radius: 6px;
    padding: 8px 16px;
    width: 100%;
    transition: all 0.2s;
  }
  .stButton > button:hover {
    border-color: #00e5ff;
    box-shadow: 0 0 12px #00e5ff44;
    color: #ffffff;
  }

  /* Chart area */
  .chart-container {
    background: #0a1520;
    border: 1px solid #1a3a4a;
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
  }

  /* Section headers */
  .section-header {
    font-family: 'Orbitron', monospace;
    font-size: 0.7rem;
    letter-spacing: 3px;
    color: #2a6a8a;
    text-transform: uppercase;
    border-bottom: 1px solid #1a3a4a;
    padding-bottom: 6px;
    margin-bottom: 10px;
    margin-top: 14px;
  }

  /* Hide streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
  [data-testid="stToolbar"] { display: none; }

  /* WebRTC video */
  .stVideo video { border-radius: 8px; border: 1px solid #1a3a4a; }
  iframe { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Title
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hud-title">🚗 DROWSIIEE</div>', unsafe_allow_html=True)
st.markdown('<div class="hud-sub">REAL-TIME DRIVER DROWSINESS DETECTION SYSTEM</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Layout — Camera left (wider), Metrics right
# ─────────────────────────────────────────────────────────────────────────────
col_cam, col_metrics = st.columns([3, 2], gap="medium")

with col_cam:
    st.markdown('<div class="section-header">▶ LIVE FEED</div>', unsafe_allow_html=True)

    RTC_CONFIG = RTCConfiguration({
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
        ]
    })

    ctx = webrtc_streamer(
        key="drowsiness-detector",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIG,
        video_processor_factory=DrowsinessProcessor,
        media_stream_constraints={
            "video": {"width": {"ideal": 1280}, "height": {"ideal": 720}, "frameRate": {"ideal": 30}},
            "audio": False,
        },
        async_processing=True,
    )

    # Camera status
    if ctx.state.playing:
        st.success("🟢 Camera active — drowsiness detection running", icon=None)
    else:
        st.info("👆 Click **START** above to activate your camera and begin detection.", icon=None)

    # Reset button
    if st.button("⟳  RESET FATIGUE SCORE", key="reset_btn"):
        shared.request_reset()
        st.toast("Fatigue score reset!", icon="✅")

with col_metrics:
    st.markdown('<div class="section-header">◈ SYSTEM METRICS</div>', unsafe_allow_html=True)

    # Metric placeholders
    badge_ph      = st.empty()
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        ear_ph    = st.empty()
        blink_ph  = st.empty()
    with col_e2:
        fatigue_ph  = st.empty()
        closure_ph  = st.empty()

    st.markdown('<div class="section-header">◈ FATIGUE SCORE</div>', unsafe_allow_html=True)
    fatigue_bar_ph  = st.empty()
    fatigue_text_ph = st.empty()

    st.markdown('<div class="section-header">◈ EAR TREND (last 120 frames)</div>', unsafe_allow_html=True)
    ear_chart_ph    = st.empty()

    st.markdown('<div class="section-header">◈ FATIGUE HISTORY</div>', unsafe_allow_html=True)
    fat_chart_ph    = st.empty()

    st.markdown('<div class="section-header">◈ SESSION INFO</div>', unsafe_allow_html=True)
    fps_ph    = st.empty()
    frame_ph  = st.empty()


# ─────────────────────────────────────────────────────────────────────────────
# Live dashboard update loop
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd

def state_to_badge(state: DrowsinessState) -> str:
    if state == DrowsinessState.SAFE:
        return '<div class="state-badge badge-safe">✔ SAFE</div>'
    elif state == DrowsinessState.WARNING:
        return '<div class="state-badge badge-warning">⚠ WARNING</div>'
    else:
        return '<div class="state-badge badge-critical">🚨 CRITICAL — PULL OVER!</div>'

def metric_card(label: str, value: str, color: str = "#00e5ff") -> str:
    return f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value" style="color:{color}">{value}</div>
    </div>"""

# Only run the update loop when camera is active
if ctx.state.playing:
    while True:
        snap = shared.snapshot()
        state = snap["state"]

        # State badge
        badge_ph.markdown(state_to_badge(state), unsafe_allow_html=True)

        # EAR color
        ear_col = "#00dc3c" if snap["avg_ear"] >= EAR_THRESHOLD else "#ff4444"
        ear_ph.markdown(metric_card("EAR (AVG)", f"{snap['avg_ear']:.3f}", ear_col), unsafe_allow_html=True)

        # Fatigue color
        f = snap["fatigue"]
        fat_col = "#00dc3c" if f < 35 else ("#ffa500" if f < 65 else "#ff2222")
        fatigue_ph.markdown(metric_card("FATIGUE", f"{f:.1f}", fat_col), unsafe_allow_html=True)

        blink_ph.markdown(metric_card("BLINK/MIN", f"{snap['blink_rate']:.1f}", "#00e5ff"), unsafe_allow_html=True)
        closure_ph.markdown(metric_card("CLOSURE", f"{snap['closure_duration']:.2f}s", "#00e5ff"), unsafe_allow_html=True)

        # Fatigue progress bar
        fatigue_bar_ph.progress(int(snap["fatigue"]))
        fatigue_text_ph.markdown(
            f'<p style="font-family:Share Tech Mono;font-size:0.75rem;color:#4a7a8a;margin-top:-8px">'
            f'WARN@35 &nbsp;|&nbsp; CRIT@65 &nbsp;|&nbsp; NOW:{f:.1f}</p>',
            unsafe_allow_html=True
        )

        # EAR chart
        ear_hist = snap["ear_history"]
        if len(ear_hist) > 2:
            df_ear = pd.DataFrame({"EAR": ear_hist, "Threshold": [EAR_THRESHOLD]*len(ear_hist)})
            ear_chart_ph.line_chart(df_ear, height=140, use_container_width=True)

        # Fatigue chart
        fat_hist = snap["fatigue_history"]
        if len(fat_hist) > 2:
            df_fat = pd.DataFrame({"Fatigue": fat_hist})
            fat_chart_ph.line_chart(df_fat, height=120, use_container_width=True)

        # FPS / frames
        fps_ph.markdown(metric_card("FPS", f"{snap['fps']:.1f}", "#00e5ff"), unsafe_allow_html=True)
        frame_ph.markdown(metric_card("FRAMES", str(snap["frame_count"]), "#00e5ff"), unsafe_allow_html=True)

        time.sleep(0.15)   # ~6-7 UI updates/sec
else:
    # Show placeholder metrics when camera is off
    badge_ph.markdown('<div class="state-badge badge-safe">— STANDBY —</div>', unsafe_allow_html=True)
    with col_e1:
        ear_ph.markdown(metric_card("EAR (AVG)", "—", "#2a5a6a"), unsafe_allow_html=True)
        blink_ph.markdown(metric_card("BLINK/MIN", "—", "#2a5a6a"), unsafe_allow_html=True)
    with col_e2:
        fatigue_ph.markdown(metric_card("FATIGUE", "—", "#2a5a6a"), unsafe_allow_html=True)
        closure_ph.markdown(metric_card("CLOSURE", "—", "#2a5a6a"), unsafe_allow_html=True)
    fatigue_bar_ph.progress(0)
    fatigue_text_ph.markdown(
        '<p style="font-family:Share Tech Mono;font-size:0.75rem;color:#2a4a5a">Start camera to begin.</p>',
        unsafe_allow_html=True
    )
    ear_chart_ph.markdown('<div class="chart-container" style="height:80px;display:flex;align-items:center;justify-content:center;color:#1a4a5a">No data yet</div>', unsafe_allow_html=True)
    fat_chart_ph.markdown('<div class="chart-container" style="height:80px;display:flex;align-items:center;justify-content:center;color:#1a4a5a">No data yet</div>', unsafe_allow_html=True)
    fps_ph.markdown(metric_card("FPS", "—", "#2a5a6a"), unsafe_allow_html=True)
    frame_ph.markdown(metric_card("FRAMES", "—", "#2a5a6a"), unsafe_allow_html=True)
