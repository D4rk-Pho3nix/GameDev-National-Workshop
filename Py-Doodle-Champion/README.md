# Guitar Hero AI Agent
---
made with 🩷 by Dark_Pho3nix (Dark Phoenix#3055)
A computer vision-based AI that detects notes in rhythm games like Guitar Hero and logs key presses.

## Installation

1. **Install Python 3.8+**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python ai_agent.py
```

The agent will:
1. Wait 5 seconds for you to switch to your game
2. Capture the background (make sure lanes are empty!)
3. Start detecting notes and logging key presses

Press `q` in the debug window to stop.

## Calibration

Edit these values in `ai_agent.py` to match your game:

### Lane Positions

```python
TARGET_Y = 947  # Y-coordinate of the hit line

LANES = [
    {'x': 736,  'key': 'a', ...},  # Lane 1 X position
    {'x': 905,  'key': 'w', ...},  # Lane 2 X position
    {'x': 1067, 'key': 's', ...},  # Lane 3 X position
    {'x': 1231, 'key': 'd', ...}   # Lane 4 X position
]
```

**How to find coordinates:**
1. Take a screenshot of your game
2. Open in an image editor (Paint, Photoshop, etc.)
3. Hover over the center of each lane at the hit line
4. Note the X and Y pixel coordinates

### Detection Sensitivity

```python
ROI_WIDTH = 50        # Width of detection box (pixels)
ROI_HEIGHT = 25       # Height of detection box (pixels)
COLOR_THRESHOLD = 40  # Color difference threshold (0-255)
PIXEL_PERCENT = 0.15  # % of pixels that must differ (0.0-1.0)
COOLDOWN = 0.08       # Seconds between detections per lane
```

**Tuning tips:**
- Notes not detected? Lower `COLOR_THRESHOLD` or `PIXEL_PERCENT`
- False detections? Raise `COLOR_THRESHOLD` or `PIXEL_PERCENT`
- Missing rapid notes? Lower `COOLDOWN`
- Detecting same note twice? Raise `COOLDOWN`

### Monitor Selection

```python
MONITOR_ID = 1  # 1 = primary monitor, 2 = secondary, etc.
```

## Debug Window

The debug window shows:
- **Green box** = Idle (no note detected)
- **Red box** = Note detected (AI "pressed" key)
- **Orange box** = Note still in detection zone

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No detection | Check lane X/Y coordinates match your game |
| False positives | Increase `COLOR_THRESHOLD` to 50-60 |
| Missing notes | Decrease `COLOR_THRESHOLD` to 30-35 |
| Wrong monitor | Change `MONITOR_ID` |
| Laggy detection | Close other applications |

## File Structure

```
Doodle-Champion/
├── ai_agent.py       # Main AI script
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## License

MIT License - Use freely for educational purposes.
