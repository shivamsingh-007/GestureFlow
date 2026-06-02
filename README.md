# 🖐️ GestureFlow — Gesture-Controlled Presentation Remote

Control your PowerPoint, Google Slides, or any presentation app with **hand gestures** via your webcam. No clicker, no keyboard, no phone — just your hands.

> **100% local** — no data leaves your machine. No internet required.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🖐️ Swipe gestures | Swipe left/right to change slides, up/down to scroll pages |
| 🤏 Pinch to zoom | Pinch thumb + index finger to zoom in |
| ✌️ Two-finger spread | Spread index + middle finger to zoom out |
| ✌️ Peace sign to exit | Show V sign to exit the presentation |
| 🔌 Dual control | Keyboard simulation (any app) + PowerPoint COM API |
| 🧊 System tray | Runs in background, toggle on/off from tray icon |
| ⚡ Low latency | ~5μs gesture detection, ~30 FPS camera processing |
| 🔒 Private | All processing happens locally on your device |

---

## 🎬 Demo

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│    🖐️ Open Palm Swipe Right    →   ▶ Next Slide        │
│    🖐️ Open Palm Swipe Left     →   ◀ Previous Slide    │
│    🖐️ Open Palm Swipe Up       →   🔼 Page Up          │
│    🖐️ Open Palm Swipe Down     →   🔽 Page Down        │
│    🤏 Pinch (thumb+index)      →   🔍+ Zoom In         │
│    ✌️ Two Finger Spread         →   🔍- Zoom Out        │
│    ✌️ Peace Sign (V)            →   ❌ Exit             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

- **Python 3.10+**
- **Webcam** (built-in or USB)
- **Windows 10/11** (for PowerPoint COM API; keyboard simulation works on all OS)

### Setup

```bash
# Clone the project
git clone https://github.com/shivamsingh-007/GestureFlow.git
cd GestureFlow

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Dependencies

| Package | Purpose |
|---|---|
| `mediapipe` | Hand landmark detection (21 keypoints) |
| `opencv-python` | Webcam capture |
| `pyautogui` | Keyboard simulation for slide control |
| `pywin32` | PowerPoint COM API (Windows) |
| `pystray` | System tray icon |
| `Pillow` | Tray icon image generation |

---

## 🚀 Usage

### Starting the App

```bash
python main.py
```

A **tray icon** (red circle) will appear in your system tray (bottom-right corner of Windows taskbar).

### Controlling the App

Right-click the tray icon to access:

| Menu Item | Action |
|---|---|
| **Start** | Activates camera + gesture detection |
| **Stop** | Deactivates camera, keeps tray icon |
| **Settings** | Opens configuration window |
| **Quit** | Exits the application |

### Gesture Controls

| Gesture | How to Perform | Action |
|---|---|---|
| **Swipe Right** | Open palm, swipe hand right | Next slide |
| **Swipe Left** | Open palm, swipe hand left | Previous slide |
| **Swipe Up** | Open palm, swipe hand up | Page up |
| **Swipe Down** | Open palm, swipe hand down | Page down |
| **Pinch** | Touch thumb tip to index tip | Zoom in |
| **Two-Finger Spread** | Extend index + middle, spread apart | Zoom out |
| **Peace Sign** | Index + middle up, ring + pinky curled, thumb tucked | Exit presentation |

### Tips for Best Results

- **Distance**: Sit 0.5–1.5 meters from the camera
- **Lighting**: Ensure your hand is well-lit
- **Background**: Contrasting background helps detection
- **Speed**: Swipe deliberately but don't rush — the cooldown prevents double-triggers
- **Full palm**: Keep all fingers extended for swipe gestures

---

## ⚙️ Configuration

Click **Settings** in the tray menu to configure:

| Setting | Default | Description |
|---|---|---|
| Camera Index | `0` | Webcam device number (0 = default camera) |
| Frame Skip | `2` | Process every Nth frame (lower = smoother, higher CPU) |
| Swipe Threshold | `0.12` | Hand movement needed to trigger swipe (lower = easier) |
| Swipe Cooldown | `600ms` | Delay between swipe triggers |
| Pinch Threshold | `0.06` | Distance between thumb+index to trigger pinch |
| Show Camera Preview | Off | Show webcam feed with hand landmarks |
| Use COM API | On | Use PowerPoint's API directly (Windows only) |

Or edit `config.json` directly:

```json
{
  "camera_index": 0,
  "frame_width": 640,
  "frame_height": 480,
  "swipe_threshold": 0.12,
  "swipe_frames": 5,
  "swipe_cooldown_ms": 600,
  "pinch_threshold": 0.06,
  "pinch_cooldown_ms": 400,
  "spread_threshold": 0.10,
  "spread_cooldown_ms": 400,
  "peace_cooldown_ms": 800,
  "min_detection_confidence": 0.7,
  "min_tracking_confidence": 0.6,
  "num_hands": 1,
  "zoom_step": 0.1,
  "use_com_api": true,
  "show_camera_preview": false,
  "skip_frames": 2
}
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│              System Tray (pystray)                │
│         Start / Stop / Settings / Quit            │
└──────────────┬───────────────────┬───────────────┘
               │ Toggle ON/OFF     │
     ┌─────────▼───────────┐       │
     │   Gesture Engine     │◄──────┘
     │  (Background Thread) │
     │  ┌─────────────────┐ │
     │  │ OpenCV Capture   │ │
     │  │ MediaPipe Hands  │ │
     │  │ GestureDetector  │ │
     │  └────────┬────────┘ │
     └───────────┼──────────┘
                 │ Gesture event
     ┌───────────▼──────────┐
     │  Action Dispatcher    │
     │  (Cooldown + Routing) │
     └───┬───────────────┬───┘
         │               │
   ┌─────▼─────┐   ┌─────▼──────┐
   │ pyautogui  │   │ PowerPoint │
   │ (Keyboard) │   │ COM API    │
   └─────┬─────┘   └─────┬──────┘
         │               │
   ┌─────▼───────────────▼─────┐
   │   Presentation App         │
   │   (PPT / Google Slides /   │
   │    Keynote / Any App)       │
   └────────────────────────────┘
```

### Module Overview

| Module | Lines | Purpose |
|---|---|---|
| `main.py` | 200 | Entry point, system tray lifecycle, settings UI |
| `gesture_engine.py` | 114 | Camera capture + MediaPipe hand detection (background thread) |
| `gesture_detector.py` | 155 | Landmark math → gesture classification (pure geometry, no ML) |
| `action_dispatcher.py` | 104 | Maps gestures → keyboard/COM actions with cooldown |
| `ppt_controller.py` | 114 | PowerPoint COM automation for direct control |
| `config.py` | 47 | Configuration dataclass + JSON persistence |

---

## 🧪 Testing

Run the full test suite:

```bash
python test_gestureflow.py
```

**44 tests** covering:

- Gesture detection (peace, pinch, spread, all swipe directions)
- Cooldown system (blocking, expiry, per-gesture independence)
- Action dispatcher (keyboard simulation for all 7 actions)
- PPT controller (COM init/disconnect, keyboard fallback)
- Edge cases (empty landmarks, insufficient frames, threshold boundaries)
- Thread safety (concurrent detector usage)
- Performance (~5μs per frame — well under 1ms)

---

## 🔧 Keyboard Shortcuts Used

| Action | Shortcut | Works With |
|---|---|---|
| Next slide | `→ Right Arrow` | Any presentation app |
| Previous slide | `← Left Arrow` | Any presentation app |
| Page up | `Page Up` | Any presentation app |
| Page down | `Page Down` | Any presentation app |
| Zoom in | `Ctrl + +` | PowerPoint, Google Slides |
| Zoom out | `Ctrl + -` | PowerPoint, Google Slides |
| Exit slideshow | `Esc` | Any presentation app |

> When PowerPoint COM API is active, zoom is controlled directly via the API for smoother experience.

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| Camera not found | Check `camera_index` in settings. Try `0`, `1`, or `2` |
| Gestures not detected | Improve lighting, ensure hand is 0.5-1.5m from camera |
| Swipes trigger too easily | Increase `swipe_threshold` in settings |
| Swipes don't trigger | Decrease `swipe_threshold`, make larger/faster swipes |
| App crashes on start | Install all dependencies: `pip install -r requirements.txt` |
| PowerPoint COM fails | Ensure PowerPoint is open with a presentation loaded |
| High CPU usage | Increase `skip_frames` to 3 or 4 |
| Tray icon not visible | Check system tray overflow area (↑ arrow in taskbar) |

---

## 📁 Project Structure

```
GestureFlow/
├── main.py                  # Entry point + system tray
├── config.py                # Settings management
├── config.json              # User configuration (auto-generated)
├── gesture_detector.py      # Hand landmark → gesture logic
├── gesture_engine.py        # Camera + MediaPipe integration
├── action_dispatcher.py     # Gesture → action mapping
├── ppt_controller.py        # PowerPoint COM automation
├── requirements.txt         # Python dependencies
├── test_gestureflow.py      # Test suite (44 tests)
└── assets/                  # Icon assets
```

---

## 📄 License

MIT License

---

## 🙏 Credits

- [MediaPipe](https://google.github.io/mediapipe/) — Hand landmark detection
- [OpenCV](https://opencv.org/) — Camera capture
- [pyautogui](https://pyautogui.readthedocs.io/) — Keyboard simulation
- [pystray](https://github.com/moses-palmer/pystray) — System tray icons
