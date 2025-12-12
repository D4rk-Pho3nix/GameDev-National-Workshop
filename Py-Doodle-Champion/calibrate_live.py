from pynput import mouse
import json
import sys

# Storage for coordinates
lane_y_coords = []
target_x_coords = []

print("--- Live Calibration Started ---")
print("Please switch to your game window.")
print("1. Click 4 times: Once on each lane (Top to Bottom) to capture Y-coordinates.")
print("2. Click 2 times: To define the vertical Target Line (Top and Bottom of the line).")
print("--------------------------------")

def on_click(x, y, button, pressed):
    global lane_y_coords, target_x_coords
    
    if not pressed:
        return

    # Phase 1: Capture 4 Lanes
    if len(lane_y_coords) < 4:
        lane_y_coords.append(int(y))
        print(f"Captured Lane {len(lane_y_coords)} Y: {int(y)} (at x={int(x)})")
        
    # Phase 2: Capture 2 X-coordinates for the line
    elif len(target_x_coords) < 2:
        target_x_coords.append(int(x))
        print(f"Captured Target Point {len(target_x_coords)} X: {int(x)} (at y={int(y)})")

    # Check completion
    if len(lane_y_coords) == 4 and len(target_x_coords) == 2:
        # Save configuration
        # We store the 2 X values so we can draw a line or average them later
        config = {
            "lane_y": lane_y_coords,
            "target_x": target_x_coords 
        }
        
        with open('lane_config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
        print("\nCalibration Complete!")
        print(f"Saved: {config}")
        print("Exiting...")
        return False # Stop listener

# Collect events until released
with mouse.Listener(on_click=on_click) as listener:
    listener.join()
