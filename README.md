# 🚗 Real-Time Driver Drowsiness Detection

A modular, CPU-friendly drowsiness detection system using **MediaPipe Face Mesh**, **Eye Aspect Ratio (EAR)**, and a rolling **fatigue score** — no GPU required.

---

## Architecture

```
drowsiness_detection/
├── main.py            # Entry point, camera loop, HUD rendering
├── detection.py       # MediaPipe face mesh wrapper → landmarks + annotated frame
├── ear_calculation.py # EAR formula, landmark indices, pixel extraction
├── alert.py           # Fatigue scoring, state machine (SAFE/WARNING/CRITICAL), alarm
└── requirements.txt
```

---

## Installation

```bash
# 1. Clone / unzip the project
cd drowsiness_detection

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

> **Python 3.9 – 3.12** recommended.  
> MediaPipe does not yet support Python 3.13.

---

## Running

```bash
python main.py
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--camera 0` | 0 | Camera index (try `1` for external webcam) |
| `--width 1280` | 1280 | Capture width in pixels |
| `--height 720` | 720 | Capture height in pixels |
| `--fps-target 30` | 30 | FPS cap |
| `--ear-thresh 0.25` | 0.25 | Override EAR closure threshold |

### Controls (in the OpenCV window)

| Key | Action |
|-----|--------|
| **Q / ESC** | Quit |
| **R** | Reset fatigue score |
| **S** | Save snapshot PNG |

---

## How It Works

### 1. Eye Aspect Ratio (EAR)

Based on the paper *Real-Time Eye Blink Detection using Facial Landmarks* (Soukupová & Čech, 2016):

```
EAR = (‖p2−p6‖ + ‖p3−p5‖) / (2 × ‖p1−p4‖)
```

- **p1, p4** — horizontal eye corners  
- **p2, p3** — upper eyelid points  
- **p5, p6** — lower eyelid points  

Typical values: **≈ 0.28–0.38** (open), **< 0.20** (closed).

### 2. State Machine

```
EAR < 0.25  for  0.8 s → WARNING
EAR < 0.25  for  2.0 s → CRITICAL  +  alarm
```

### 3. Fatigue Score (0–100)

| Condition | Effect |
|-----------|--------|
| Eyes closed | +12 pts / sec |
| High blink rate | +3 pts / excess blink |
| Eyes open | −4 pts / sec (decay) |

- **Score ≥ 35** → WARNING  
- **Score ≥ 65** → CRITICAL

### 4. Alarm

- **Windows** → `winsound.Beep`  
- **macOS** → `afplay Sosumi.aiff`  
- **Linux** → `beep` command, or terminal bell `\a`

---

## HUD Description

| Element | Location | Description |
|---------|----------|-------------|
| Status banner | Top | SAFE / WARNING / CRITICAL |
| Info panel | Top-right | EAR values, fatigue gauge, blink rate, closure duration |
| EAR bar | Inside panel | Vertical bar vs. threshold line |
| Fatigue gauge | Inside panel | Circular arc 0–100 |
| Face box | Around face | Color-coded by state |
| Eye contours | On eyes | Green hull overlay |
| Warning text | Centre | Large overlay when CRITICAL |
| FPS / frame | Bottom | Performance info |

---

## Performance Tips

- Run at **720p** rather than 1080p for best FPS on CPU.
- Use `--fps-target 20` on older hardware.
- Close other GPU-intensive apps; MediaPipe runs on CPU.
- Ensure **good lighting** — EAR accuracy degrades in poor light.

---

## Optional: CNN Eye Classifier

For improved robustness (e.g., glasses, partial occlusion), you can train a lightweight CNN on the **MRL Eye Dataset** or **CEW Dataset**:

1. Crop eye ROI from each frame using the detected landmarks.
2. Resize to 24×24 grayscale.
3. Train a small CNN (Conv→Pool→Conv→Pool→FC) to classify Open / Closed.
4. Replace the EAR threshold check in `alert.py` with the CNN's prediction.

Uncomment the PyTorch lines in `requirements.txt` to get started.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Camera not opening | Try `--camera 1`; check OS permissions |
| Low FPS | Lower `--width` / `--height`; upgrade mediapipe |
| EAR always low | Adjust `--ear-thresh`; improve lighting |
| No alarm on Linux | Install `beep` package: `sudo apt install beep` |
| mediapipe install fails | Use Python 3.9–3.12; upgrade pip: `pip install -U pip` |
