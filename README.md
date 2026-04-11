# 🚗 Drowsiiee — Real-Time Driver Drowsiness Detection on Streamlit Cloud

## How to Deploy (Get Your Hosted Link)

### Step 1 — Push to GitHub
1. Create a **new public GitHub repository** (e.g. `drowsiiee-streamlit`)
2. Push all files in this folder to it:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/drowsiiee-streamlit.git
   git push -u origin main
   ```

### Step 2 — Deploy on Streamlit Cloud
1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository → Branch: `main` → Main file: `app.py`
5. Click **"Deploy!"**
6. Wait ~3-5 minutes for build (MediaPipe installs take time)
7. Your app will be live at: `https://YOUR_USERNAME-drowsiiee-streamlit-app-XXXX.streamlit.app`

### Step 3 — Use the App
1. Open the link in **Chrome or Edge** (best WebRTC support)
2. Click **START** in the video panel
3. Allow camera access when prompted
4. The full CV pipeline runs in real-time!

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit app — WebRTC camera + HUD + dashboard |
| `alert.py` | Fatigue scoring state machine (SAFE/WARNING/CRITICAL) |
| `detection.py` | MediaPipe Face Mesh wrapper |
| `ear_calculation.py` | EAR formula (Soukupová & Čech 2016) |
| `requirements.txt` | Python dependencies for Streamlit Cloud |
| `.streamlit/config.toml` | Dark theme + server config |

## Architecture on Streamlit Cloud

```
Browser (Chrome)
  └── getUserMedia() → WebRTC stream
        └── streamlit-webrtc (SENDRECV)
              └── DrowsinessProcessor.recv() [server thread]
                    ├── MediaPipe Face Mesh → landmarks
                    ├── EAR calculation
                    ├── AlertManager (fatigue score + state)
                    └── HUD overlay → back to browser
SharedState (thread-safe) → Streamlit UI thread → metrics dashboard
```

## Notes
- **Browser**: Chrome/Edge recommended for best WebRTC support
- **Lighting**: Ensure good face lighting for reliable EAR detection
- **Latency**: Expect ~200-400ms round-trip on cloud vs local
- **Free tier**: Streamlit Cloud free tier is sufficient for this app
