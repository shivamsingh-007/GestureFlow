<div align="center">

# 🖐️ GestureFlow

### *Control presentations with your hands. No clicker needed.*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-FF6F00?style=for-the-badge&logo=google&logoColor=white)](https://google.github.io/mediapipe/)
[![License: MIT](https://img.shields.io/badge/License-MIT-00C853?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-44%20passing-4CAF50?style=for-the-badge)](#testing)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#installation)

<br>

**GestureFlow** transforms your webcam into a gesture-powered remote control.
Swipe to change slides. Pinch to zoom. Peace sign to exit.
**100% offline. Zero lag. Zero tracking.**

<br>

```
  ✋ Swipe Right  →  Next Slide        ✌️ Peace Sign  →  Exit
  ✋ Swipe Left   →  Previous Slide    🤏 Pinch       →  Zoom In
  ✋ Swipe Up     →  Page Up           🤟 Spread      →  Zoom Out
  ✋ Swipe Down   →  Page Down
```

</div>

---

## ⚡ Why GestureFlow?

| | |
|---|---|
| 🚀 **~5μs** per gesture detection | Faster than human perception — zero perceived lag |
| 🎯 **21 hand landmarks** tracked | MediaPipe's precision hand model at 30 FPS |
| 🔒 **100% private** | No data leaves your machine. No cloud. No accounts. |
| 🖥️ **System tray app** | Runs quietly in background — toggle with one click |
| 🔌 **Dual control engine** | Keyboard simulation + PowerPoint COM API |
| 🧩 **Zero training** | No ML model training — pure geometric gesture logic |
| 📦 **7 files, ~800 lines** | Lightweight, auditable, easy to extend |

---

## 🎮 Gesture Controls

<div align="center">

| Gesture | How to Perform | Action |
|:---:|---|:---:|
| ✋ **Swipe Right** | Open palm, move hand right | ▶ Next slide |
| ✋ **Swipe Left** | Open palm, move hand left | ◀ Previous slide |
| ✋ **Swipe Up** | Open palm, move hand up | 🔼 Page up |
| ✋ **Swipe Down** | Open palm, move hand down | 🔽 Page down |
| 🤏 **Pinch** | Touch thumb tip to index tip | 🔍+ Zoom in |
| 🤟 **Two-Finger Spread** | Extend index + middle, spread apart | 🔍− Zoom out |
| ✌️ **Peace Sign** | V sign with index + middle fingers | ❌ Exit presentation |

</div>

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/shivamsingh-007/GestureFlow.git
cd GestureFlow
pip install -r requirements.txt
```

### 2. Run

```bash
python main.py
```

A **tray icon** appears in your system tray (bottom-right corner).

### 3. Control

Right-click the tray icon → **Start** → show your hand to the camera → start presenting!

> **Tip:** Sit 0.5–1.5m from the camera with good lighting for best detection.

---

## 🏗️ Architecture

```
                    ┌─────────────────────┐
                    │    System Tray      │
                    │  Start│Stop│Settings│
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │   Gesture Engine     │
                    │  ┌────────────────┐  │
                    │  │  OpenCV Camera  │  │
                    │  │  MediaPipe Hands│  │
                    │  │  Landmark Math  │  │
                    │  └───────┬────────┘  │
                    └──────────┼───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Action Dispatcher   │
                    │  (cooldown + route)  │
                    └──┬──────────────┬────┘
                       │              │
              ┌────────▼──┐    ┌──────▼───────┐
              │ pyautogui  │    │ PowerPoint   │
              │ (keyboard) │    │  COM API     │
              └────────┬──┘    └──────┬───────┘
                       │              │
              ┌────────▼──────────────▼───────┐
              │     Presentation App          │
              │  PPT│Google Slides│Keynote    │
              └───────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Hand Detection** | MediaPipe HandLandmarker | 21 keypoints, ~17ms CPU latency |
| **Webcam** | OpenCV | Frame capture at 640×480 |
| **Gesture Logic** | Pure Python geometry | Zero ML training required |
| **Slide Control** | pyautogui + pywin32 | Universal + native PowerPoint |
| **UI** | pystray + Pillow | System tray with start/stop |
| **Config** | JSON + dataclass | Runtime-adjustable settings |

---

## 🧪 Testing

```bash
python test_gestureflow.py
```

<div align="center">

| Category | Tests | Coverage |
|---|:---:|---|
| Gesture Detection | 15 | Peace, pinch, spread, all 4 swipe directions |
| Cooldown System | 5 | Blocking, expiry, per-gesture independence |
| Action Dispatcher | 7 | Keyboard shortcuts for all 7 actions |
| PPT Controller | 5 | COM init/disconnect, keyboard fallback |
| Edge Cases | 3 | Empty landmarks, insufficient frames, thresholds |
| Thread Safety | 2 | Concurrent detector usage, engine lifecycle |
| Performance | 1 | Detection speed benchmark |
| **Total** | **44** | **All passing** |

</div>

**Benchmark:** ~5μs per gesture detection frame — **200× faster** than the 1ms real-time threshold.

---

## ⚙️ Configuration

Adjust via the **Settings** window in the tray, or edit `config.json`:

| Setting | Default | Description |
|---|---|---|
| Camera Index | `0` | Webcam device number |
| Frame Skip | `2` | Process every Nth frame (lower = smoother) |
| Swipe Threshold | `0.12` | Hand movement needed (lower = easier) |
| Swipe Cooldown | `600ms` | Delay between swipe triggers |
| Pinch Threshold | `0.06` | Thumb-index distance for pinch |
| Show Camera Preview | Off | Show webcam feed with landmarks |
| Use COM API | On | Direct PowerPoint control (Windows) |

---

## 🔧 Keyboard Shortcuts

When COM API is unavailable, GestureFlow simulates these keys:

| Action | Key | Works With |
|---|---|---|
| Next slide | `→` | Any presentation app |
| Previous slide | `←` | Any presentation app |
| Page up | `Page Up` | Any presentation app |
| Page down | `Page Down` | Any presentation app |
| Zoom in | `Ctrl + +` | PowerPoint, Google Slides |
| Zoom out | `Ctrl + -` | PowerPoint, Google Slides |
| Exit slideshow | `Esc` | Any presentation app |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| Camera not found | Try `camera_index` = `1` or `2` in settings |
| Gestures not detected | Improve lighting, sit 0.5–1.5m from camera |
| Swipes too sensitive | Increase `swipe_threshold` (try `0.15`) |
| Swipes not responding | Decrease threshold, make bigger/faster swipes |
| High CPU usage | Set `skip_frames` to `3` or `4` |
| PowerPoint COM error | Ensure PPT is open with a presentation loaded |
| Tray icon hidden | Check the `^` overflow area in your taskbar |

---

## 📁 Project Structure

```
GestureFlow/
├── main.py                  # Entry point + system tray + settings
├── gesture_engine.py        # Camera + MediaPipe hand detection
├── gesture_detector.py      # Landmark math → gesture classification
├── action_dispatcher.py     # Gesture → action routing with cooldown
├── ppt_controller.py        # PowerPoint COM automation
├── config.py                # Settings dataclass + JSON persistence
├── assets/
│   └── hand_landmarker.task # MediaPipe hand model (7.8MB)
├── requirements.txt         # Python dependencies
├── test_gestureflow.py      # Test suite (44 tests)
└── README.md
```

---

## 📊 Stats

| Metric | Value |
|---|---|
| **Lines of Code** | ~800 |
| **Files** | 7 modules |
| **Dependencies** | 6 packages |
| **Model Size** | 7.8 MB (float16) |
| **Detection Latency** | ~5μs/frame |
| **Camera FPS** | 30 (configurable) |
| **Hand Landmarks** | 21 keypoints |
| **Supported Gestures** | 7 |
| **Test Coverage** | 44 tests, 100% pass |
| **Privacy** | 100% offline |

---

## 📄 License

MIT License — use it however you want.

---

## 🙏 Built With

- [**MediaPipe**](https://google.github.io/mediapipe/) — Hand landmark detection
- [**OpenCV**](https://opencv.org/) — Webcam capture
- [**pyautogui**](https://pyautogui.readthedocs.io/) — Keyboard simulation
- [**pystray**](https://github.com/moses-palmer/pystray) — System tray icons
- [**pywin32**](https://github.com/mhammond/pywin32) — PowerPoint COM API

---

<div align="center">

**Made with 🖐️ by [Shivam Singh](https://github.com/shivamsingh-007)**

*Star this repo if GestureFlow saved your presentation!*

</div>
