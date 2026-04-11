"""
alert.py
--------
Drowsiness logic, fatigue scoring, and alert management.

States
------
  SAFE     – EAR is normal; driver is alert.
  WARNING  – EAR below threshold for a short duration, or elevated fatigue score.
  CRITICAL – Eyes closed for > CLOSURE_SECONDS; immediate alarm.

Fatigue score (0–100)
---------------------
  Increases when:
    - Instantaneous EAR < EAR_THRESHOLD   (+SCORE_CLOSURE_RATE per second)
    - Blink rate is unusually high         (+SCORE_BLINK_RATE_PENALTY per excess blink)
  Decays slowly when the driver is alert   (-SCORE_DECAY_RATE per second)
"""

from __future__ import annotations

import time
import threading
import math
from collections import deque
from enum import Enum, auto
from typing import Deque


# ---------------------------------------------------------------------------
# Tunable constants
# ---------------------------------------------------------------------------
EAR_THRESHOLD       = 0.25   # below → eyes considered closed
CLOSURE_SECONDS     = 2.0    # closed for this long → CRITICAL
WARNING_SECONDS     = 0.8    # closed for this long → WARNING

SCORE_CLOSURE_RATE  = 12.0   # fatigue pts / sec while eyes closed
SCORE_BLINK_PENALTY = 3.0    # fatigue pts per excessive blink
SCORE_DECAY_RATE    = 4.0    # fatigue pts / sec while eyes open
BLINK_WINDOW_SEC    = 60.0   # window for blink-rate calculation
NORMAL_BLINK_RATE   = 15     # blinks/min considered normal

WARNING_THRESHOLD   = 35     # fatigue score → WARNING
CRITICAL_THRESHOLD  = 65     # fatigue score → CRITICAL

# Alarm sound (frequency Hz, duration ms) – played via winsound or beep
ALARM_FREQ  = 1000
ALARM_MS    = 500


class DrowsinessState(Enum):
    SAFE     = auto()
    WARNING  = auto()
    CRITICAL = auto()


class AlertManager:
    """
    Tracks eye-closure duration, blink events, fatigue score, and state.

    Call update(avg_ear, dt) once per frame with the current EAR value
    and the elapsed time since the previous call.
    """

    def __init__(self) -> None:
        self._closure_start: float | None = None   # timestamp when eyes closed
        self._closure_duration: float = 0.0

        self._blink_times: Deque[float] = deque()  # timestamps of recent blinks
        self._last_ear_open: bool = True            # previous frame eye state

        self._fatigue: float = 0.0
        self._state: DrowsinessState = DrowsinessState.SAFE

        self._alarm_active: bool = False
        self._alarm_thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, avg_ear: float, dt: float) -> None:
        """
        Update internal state given the current average EAR.

        Parameters
        ----------
        avg_ear : float  – mean EAR across both eyes this frame
        dt      : float  – seconds elapsed since previous call
        """
        eyes_closed = avg_ear < EAR_THRESHOLD
        now = time.monotonic()

        # ---- Blink detection -----------------------------------------
        if self._last_ear_open and eyes_closed:
            # Transition open → closed: potential blink start
            self._closure_start = now
        elif not self._last_ear_open and not eyes_closed:
            # Transition closed → open: blink completed
            if self._closure_start is not None:
                blink_dur = now - self._closure_start
                if blink_dur < WARNING_SECONDS:          # quick blink, not closure
                    self._blink_times.append(now)
                self._closure_start = None

        # Prune old blinks outside the rolling window
        cutoff = now - BLINK_WINDOW_SEC
        while self._blink_times and self._blink_times[0] < cutoff:
            self._blink_times.popleft()

        # ---- Closure duration ----------------------------------------
        if eyes_closed:
            self._closure_duration = (now - self._closure_start) if self._closure_start else 0.0
        else:
            self._closure_duration = 0.0

        # ---- Fatigue score -------------------------------------------
        if eyes_closed:
            self._fatigue += SCORE_CLOSURE_RATE * dt
        else:
            self._fatigue -= SCORE_DECAY_RATE * dt

        # Blink-rate penalty
        blinks_per_min = len(self._blink_times) * (60.0 / BLINK_WINDOW_SEC)
        excess = max(0, blinks_per_min - NORMAL_BLINK_RATE)
        self._fatigue += SCORE_BLINK_PENALTY * excess * dt / 60.0

        self._fatigue = max(0.0, min(100.0, self._fatigue))

        # ---- State machine -------------------------------------------
        if self._closure_duration >= CLOSURE_SECONDS or self._fatigue >= CRITICAL_THRESHOLD:
            self._state = DrowsinessState.CRITICAL
        elif self._closure_duration >= WARNING_SECONDS or self._fatigue >= WARNING_THRESHOLD:
            self._state = DrowsinessState.WARNING
        else:
            self._state = DrowsinessState.SAFE

        # ---- Alarm ---------------------------------------------------
        if self._state == DrowsinessState.CRITICAL:
            self._trigger_alarm()
        else:
            self._alarm_active = False

        self._last_ear_open = not eyes_closed

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> DrowsinessState:
        return self._state

    @property
    def fatigue_score(self) -> float:
        """Fatigue score in the range [0, 100]."""
        return self._fatigue

    @property
    def closure_duration(self) -> float:
        """Seconds eyes have been continuously closed (0 if open)."""
        return self._closure_duration

    @property
    def blink_rate(self) -> float:
        """Estimated blinks per minute over the rolling window."""
        return len(self._blink_times) * (60.0 / BLINK_WINDOW_SEC)

    @property
    def status_label(self) -> str:
        return {
            DrowsinessState.SAFE:     "SAFE",
            DrowsinessState.WARNING:  "WARNING",
            DrowsinessState.CRITICAL: "CRITICAL – PULL OVER!",
        }[self._state]

    @property
    def status_color_bgr(self):
        """BGR color tuple for the current state."""
        return {
            DrowsinessState.SAFE:     (0, 220, 60),
            DrowsinessState.WARNING:  (0, 165, 255),
            DrowsinessState.CRITICAL: (0, 0, 230),
        }[self._state]

    # ------------------------------------------------------------------
    # Alarm
    # ------------------------------------------------------------------

    def _trigger_alarm(self) -> None:
        if self._alarm_active:
            return
        self._alarm_active = True
        t = threading.Thread(target=self._play_alarm, daemon=True)
        t.start()
        self._alarm_thread = t

    @staticmethod
    def _play_alarm() -> None:
        """
        Cross-platform beep:
          - Windows  → winsound.Beep
          - Linux/Mac → system bell via print or os.system
        """
        try:
            import winsound
            for _ in range(3):
                winsound.Beep(ALARM_FREQ, ALARM_MS)
        except ImportError:
            try:
                import subprocess, sys
                if sys.platform == "darwin":
                    subprocess.call(["afplay", "/System/Library/Sounds/Sosumi.aiff"])
                else:
                    # Linux: use 'beep' if installed, else bell character
                    result = subprocess.call(
                        ["beep", f"-f {ALARM_FREQ}", f"-l {ALARM_MS}"],
                        stderr=subprocess.DEVNULL
                    )
                    if result != 0:
                        print("\a\a\a", end="", flush=True)
            except Exception:
                print("\a\a\a", end="", flush=True)
