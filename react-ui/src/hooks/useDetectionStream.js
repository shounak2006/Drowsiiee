import { useState, useEffect, useRef, useCallback } from 'react';

// In production (GitHub Pages), set VITE_BACKEND_URL to your Render URL.
// In dev (npm run dev), falls back to localhost automatically.
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
const FRAME_INTERVAL_MS = 150; // ~6-7 fps to backend \u2014 enough for drowsiness detection

const INITIAL_STATE = {
  ear: 0.0,
  avg_ear: 0.0,
  fatigue_score: 0.0,
  status: 'IDLE',
  status_state: 'idle',
  closure_duration: 0.0,
  blink_rate: 0.0,
  camera_active: false,
  monitoring: false,
  trend: 'STABLE',
  fps: 0.0,
  face_detected: false,
};

export function useDetectionStream() {
  const [data, setData]           = useState(INITIAL_STATE);
  const [history, setHistory]     = useState([]);
  const [connected, setConnected] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [monitoring, setMonitoring]   = useState(false);

  // Refs \u2014 these are safe to read inside setInterval without stale closures
  const videoRef      = useRef(null);   // bound <video> DOM element
  const canvasRef     = useRef(null);   // offscreen canvas for frame extraction
  const streamRef     = useRef(null);   // MediaStream
  const intervalRef   = useRef(null);   // setInterval handle
  const sendingRef    = useRef(false);  // guard: don't stack overlapping requests

  // \u2500\u2500 Core: capture one frame and POST to backend \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  // Uses only refs so it is safe to call from setInterval without re-creating
  const sendFrameLoop = useRef(async () => {
    if (sendingRef.current) return; // previous request still in flight \u2192 skip

    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    // Mirror the frame (selfie orientation)
    const w = video.videoWidth  || 640;
    const h = video.videoHeight || 480;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width  = w;
      canvas.height = h;
    }
    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.translate(w, 0);
    ctx.scale(-1, 1);           // horizontal flip \u2192 same coordinate space as native selfie cam
    ctx.drawImage(video, 0, 0, w, h);
    ctx.restore();

    const b64 = canvas.toDataURL('image/jpeg', 0.75);

    sendingRef.current = true;
    try {
      const res = await fetch(`${BACKEND_URL}/api/process_frame`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ frame: b64 }),
        signal : AbortSignal.timeout(4000), // drop if backend takes > 4 s
      });

      if (!res.ok) {
        setConnected(false);
        return;
      }

      const result = await res.json();
      setConnected(true);

      setData(prev => ({ ...prev, ...result }));

      setHistory(prev => {
        const tick = {
          time: new Date().toLocaleTimeString('en-US', {
            hour12: false, hour: 'numeric', minute: 'numeric', second: 'numeric',
          }),
          fatigue: result.fatigue_score,
        };
        const next = [...prev, tick];
        return next.length > 60 ? next.slice(next.length - 60) : next;
      });
    } catch {
      // Network error or timeout \u2014 backend probably not running
      setConnected(false);
    } finally {
      sendingRef.current = false;
    }
  });

  // \u2500\u2500 Start camera + begin frame loop \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  const startCamera = useCallback(async () => {
    if (intervalRef.current) return; // already running
    setCameraError(null);

    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width:      { ideal: 640 },
          height:     { ideal: 480 },
          facingMode: 'user',
        },
        audio: false,
      });
    } catch (err) {
      setCameraError(err.message || 'Camera permission denied');
      return;
    }

    streamRef.current = stream;

    // Create offscreen canvas once
    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }

    // Attach stream to <video> element if already mounted
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play().catch(() => {});
    }

    // Notify backend
    try {
      await fetch(`${BACKEND_URL}/api/start`, { method: 'POST' });
    } catch { /* backend may not be up yet \u2014 that's fine, frames will still be sent */ }

    setMonitoring(true);
    setData(prev => ({ ...prev, monitoring: true, camera_active: true }));

    // Start frame-sending loop using the stable ref
    intervalRef.current = setInterval(() => {
      sendFrameLoop.current();
    }, FRAME_INTERVAL_MS);

  }, []);

  // \u2500\u2500 Stop camera + frame loop \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  const stopCamera = useCallback(async () => {
    clearInterval(intervalRef.current);
    intervalRef.current = null;

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    try {
      await fetch(`${BACKEND_URL}/api/stop`, { method: 'POST' });
    } catch { /* ignore */ }

    setConnected(false);
    setMonitoring(false);
    setData(INITIAL_STATE);
    setHistory([]);
  }, []);

  // \u2500\u2500 Bind <video> ref \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  // Called by React when the <video> element mounts or unmounts
  const attachVideoRef = useCallback((el) => {
    videoRef.current = el;
    if (el && streamRef.current) {
      el.srcObject = streamRef.current;
      el.play().catch(() => {});
    }
  }, []);

  // \u2500\u2500 Auto-start on mount \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  useEffect(() => {
    startCamera();
    return () => {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
      streamRef.current?.getTracks().forEach(t => t.stop());
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    data,
    history,
    connected,
    cameraError,
    monitoring,
    startCamera,
    stopCamera,
    attachVideoRef,
  };
}
