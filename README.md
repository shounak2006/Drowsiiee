# 🚗 Drowsiiee — Real-Time Driver Drowsiness Detection

A real-time driver monitoring system using **MediaPipe Face Mesh**, **Eye Aspect Ratio (EAR)**, and a continuous **fatigue scoring model**.

Supports:
- Local OpenCV execution
- Streamlit Cloud deployment (WebRTC-based)

---

## 🔧 Architecture
Webcam Input
↓
OpenCV Frame Capture
↓
MediaPipe Face Mesh (468 landmarks)
↓
Eye Landmark Extraction
↓
EAR Calculation
↓
Fatigue Score Engine
↓
Alert System (SAFE / WARNING / CRITICAL)
↓
HUD / Dashboard Output

---

## 🧠 Core Features

- Real-time drowsiness detection  
- Fatigue score (0–100 scale)  
- Blink rate tracking  
- Eye closure duration  
- Visual HUD (dashboard + overlays)  
- Streamlit WebRTC support (cloud deployment)

---

## ⚙️ Installation (Local)

```bash
cd drowsiness_detection

python -m venv .venv
.venv\Scripts\activate   # Windows

pip install -r requirements.txt