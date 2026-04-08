# Team Contributions

This document outlines the detailed contributions of all 5 team members for the **Driver Drowsiness Detection Project**. The project is built using a modern decoupled architecture, combining a Python-based computer vision backend with a dynamic React-based frontend.

---

### Member 1: Frontend Architecture & UI Design
**Name / Roll No:** [Insert Name Here]
**Role:** Frontend Developer
**Technical Contributions:** 
- **React Environment Setup:** Initialized and structured the React UI using Vite (`react-ui/`), organizing reusable components like `MetricsPanel.jsx`.
- **Modern HUD Aesthetics:** Styled the dashboard to resemble a futuristic "Heads-Up Display" exclusively using Tailwind CSS, focusing on dark modes, gradients, and dynamic visual states (e.g., pulsing red transitions for `CRITICAL` fatigue).
- **Asynchronous Data Handling:** Engineered a robust Server-Sent Events (SSE) listener within the frontend to continuously consume real-time JSON data streams representing fatigue metrics, preventing the overhead of standard HTTP polling.

### Member 2: Backend Web Server & M-JPEG Streaming 
**Name / Roll No:** [Insert Name Here]
**Role:** Backend Server Architect
**Technical Contributions:**
- **Flask Server Construction:** Developed the core Python web environment (`app.py`), defining the entire routing and RESTful API structures (`/api/start`, `/api/reset`, `/api/log`).
- **Live Video Piping:** Built the `_mjpeg_generator()` loop that takes raw BGR frames, encodes them into JPEG byte buffers via `cv2.imencode`, and securely pipes them over the HTTP network using `multipart/x-mixed-replace` boundaries.
- **Server Threading Strategy:** Delegated the heavy CV processing loop to a background daemon thread, decoupling it from the main Flask web thread to prevent server blocks and UI freezing.

### Member 3: Computer Vision & Facial Tracking Engine
**Name / Roll No:** [Insert Name Here]
**Role:** Computer Vision Specialist
**Technical Contributions:**
- **MediaPipe Integration:** Authored `detection.py`, directly executing Google's MediaPipe Face Mesh model configuration to process high-fidelity human facial topography (468 landmarks).
- **Region of Interest Extraction:** Precisely mapped and extracted 12 distinct topological integer coordinates representing the exact corners and vertical eyelids of the user's left and right eye.
- **Frame Annotation Pipeline:** Handled the NumPy array manipulation and drawing utilities `cv2.polylines` / `cv2.circle` to cast geometric overlays directly onto the user's live video stream frame by frame.

### Member 4: Fatigue Heuristics & Scoring Mechanics
**Name / Roll No:** [Insert Name Here]
**Role:** Algorithmic & Logic Engineer
**Technical Contributions:**
- **EAR Computations:** Implemented the Soukupová and Čech 6-point Euclidean distance equation inside `ear_calculation.py` to establish a quantitative ratio for eye openness.
- **State Machine Construction:** Designed the `AlertManager` class (`alert.py`) that observes temporal patterns to govern the transition between `SAFE`, `WARNING`, and `CRITICAL` statuses.
- **Micro-Sleep & Blink Penalty Dynamics:** Utilized rolling `collections.deque` buffers to track timestamps of blinks within a 60-second window, building a fatigue algorithm that continuously applies mathematical penalty points for prolonged closures (`SCORE_CLOSURE_RATE`) and excessive blink frequencies.

### Member 5: Multithreading Control, Optimization & Persistence
**Name / Roll No:** [Insert Name Here]
**Role:** Systems Integrator
**Technical Contributions:**
- **Thread-Safety & Synchronization:** Identified and neutralized data race conditions between the active Camera Loop and HTTP requests by engineering extensive `threading.Lock()` wrappers across the active session memory dictionaries (`_state`).
- **Hardware Optimization:** Resolved extreme low-FPS bottlenecks natively on Windows architecture by injecting the `cv2.CAP_DSHOW` MSMF fallback and actively downscaling capture hardware constraints to 640x480 resolution.
- **Time-Series Persistence:** Configured the continuous offline dumping logic (`fatigue_logs.json`) that saves up to 2000 historical logs of the session and mathematically deduces systemic rolling average fatigue trends ("RISING", "STABLE").
