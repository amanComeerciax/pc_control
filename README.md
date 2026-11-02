# Gesture PC Control

A touchless computer control application that uses a webcam and hand gestures to control the mouse, scrolling, volume, window switching, and app launching. Designed to run smoothly without a dedicated GPU.

## Features
* **Mouse Control**: Point to move, Pinch to click/drag.
* **Scrolling & Volume**: Use two fingers to scroll and three fingers to change volume.
* **Biomechanics / ROM Tracking**: Real-time 3D joint angle calculation (flexion/extension in degrees) with on-screen HUD for physical therapy and ergonomic analysis (Press `r` to toggle).
* **Low Latency**: Threaded camera capturing and optimized MediaPipe tracking.
* **Smooth Movements**: Implements a One Euro Filter to reduce cursor jitter.
* **Safety First**: Starts in OFF state. Requires holding OPEN hand for 2s to toggle ON/OFF. PyAutoGUI Failsafe enabled.

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *The MediaPipe hand tracking model will be downloaded automatically on the first run.*

## Running the App

```bash
python main.py
```
* **Toggle Control**: Hold an **OPEN** hand to the camera for 2 seconds. The Tkinter UI and OpenCV preview will show `Status: ON`.
* **Quit**: Press `q` while the preview window is focused, or press `Ctrl+C` in the terminal.

## Gesture Cheat Sheet

| Gesture | Action |
| --- | --- |
| **OPEN** (hold 2s) | Toggle Control ON/OFF |
| **POINT** (Index up) | Move cursor |
| **PINCH** (Thumb + Index) | Click (Tap) / Drag & Drop (Hold) |
| **FIST** | Right click |
| **TWO_FINGERS** (Index+Middle) | Scroll Up/Down (move hand vertically) |
| **THREE_FINGERS** | Volume Up/Down (move hand vertically) |
| **L_SHAPE** (Thumb+Index) | Launch App (default Notepad) |

## Configuration
Edit `config.json` to change thresholds, camera index, active zone margins, and custom apps.
* `active_zone_margin`: Defines the margin from the screen edges (e.g. 0.15 means the central 70% of the camera maps to 100% of your screen).

## Testing
Run unit tests with pytest:
```bash
pytest tests/
```

## Building with PyInstaller
To build an executable (`.exe`) for Windows:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --add-data "config.json:." --add-data "hand_landmarker.task:." "main.py"
```
*(On Windows, use `;` instead of `:` for `--add-data` separator: `--add-data "config.json;."`)*
The output will be in the `dist` folder.

## Troubleshooting
* **Camera not found**: Change the `index` in `config.json` from `0` to `1`.
* **Accidental clicks**: Increase `pinch_threshold_press` in `config.json`.
* **Cursor jitter**: Lower `min_cutoff` or `beta` under `smoothing` in `config.json`.
