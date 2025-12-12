import time
import cv2
import numpy as np
import mss
from pynput.keyboard import Controller, Listener
from threading import Thread

# --- Configuration ---
# Target Line Y-coordinate (where we check for hits)
TARGET_Y = 947

# Lane X-coordinates (centers)
LANES = [
    {'x': 736,  'key': 'a', 'last_press': 0},
    {'x': 905,  'key': 'w', 'last_press': 0},
    {'x': 1067, 'key': 's', 'last_press': 0},
    {'x': 1231, 'key': 'd', 'last_press': 0}
]

# Detection Settings
ROI_WIDTH = 60          # Width of the lane detection box
ROI_HEIGHT = 40         # Height of the lane detection box
# Note: Using the values that worked for you in the debug vision
THRESHOLD = 5000        # Pixel change threshold to trigger a press
COOLDOWN = 0.5          # Seconds between key presses for the same lane
MONITOR_ID = 1          # Monitor index

# Global Hotkey to stop the script
STOP_HOTKEY = 'esc' 

# --- AI Agent Class ---
class GameAgent:
    def __init__(self):
        self.keyboard = Controller()
        self.sct = mss.mss()
        self.running = True
        
        # Calculate capture area: A horizontal strip covering all lanes
        min_x = min(l['x'] for l in LANES) - ROI_WIDTH
        max_x = max(l['x'] for l in LANES) + ROI_WIDTH
        
        # Capture region: Centered vertically on TARGET_Y
        self.monitor_area = {
            "top": TARGET_Y - ROI_HEIGHT, 
            "left": min_x, 
            "width": max_x - min_x, 
            "height": ROI_HEIGHT * 2,
            "mon": MONITOR_ID
        }
        
        # Pre-calculate relative ROI coordinates for each lane within the captured image
        self.lane_rois = []
        for lane in LANES:
            # Relative X in the captured strip
            rel_x = lane['x'] - self.monitor_area["left"]
            # Relative Y is just centered in the strip (height is ROI_HEIGHT*2)
            rel_y = ROI_HEIGHT 
            
            self.lane_rois.append({
                'x': rel_x, 
                'y': rel_y,
                'key': lane['key'],
                'lane_idx': LANES.index(lane)
            })

        print(f"Agent Initialized.")
        print(f"Monitoring Region: {self.monitor_area}")
        print(f"Press '{STOP_HOTKEY}' globally to stop.")

        # Start global hotkey listener
        self.hotkey_listener_thread = Thread(target=self._start_hotkey_listener, daemon=True)
        self.hotkey_listener_thread.start()

    def _start_hotkey_listener(self):
        def on_press(key):
            try:
                if key.char == STOP_HOTKEY:
                    print(f"\n'{STOP_HOTKEY}' pressed. Stopping agent...")
                    self.running = False
                    return False 
            except AttributeError:
                if str(key) == f"Key.{STOP_HOTKEY}":
                    print(f"\n'{STOP_HOTKEY}' pressed. Stopping agent...")
                    self.running = False
                    return False
        
        with Listener(on_press=on_press) as listener:
            listener.join()

    def run(self):
        # --- 5 Second Delay ---
        print("\n=== STARTING IN 5 SECONDS ===")
        print("Please switch to your game window NOW!")
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        print("=== AGENT ACTIVE ===")

        # Initial capture for background reference
        initial_shot = np.array(self.sct.grab(self.monitor_area))
        gray_bg = cv2.cvtColor(initial_shot, cv2.COLOR_BGRA2GRAY)
        gray_bg = cv2.GaussianBlur(gray_bg, (21, 21), 0)

        # Pre-allocate reuse variables to avoid garbage collection overhead
        kernel = None # Not using morphology for speed, unless needed

        while self.running:
            # 1. Capture Frame (Fastest method)
            # mss is very fast, but capturing only the small strip is key
            frame_raw = np.array(self.sct.grab(self.monitor_area))
            frame_gray = cv2.cvtColor(frame_raw, cv2.COLOR_BGRA2GRAY)
            frame_gray = cv2.GaussianBlur(frame_gray, (21, 21), 0)
            
            # 2. Compute Difference
            delta_frame = cv2.absdiff(gray_bg, frame_gray)
            _, thresh = cv2.threshold(delta_frame, 25, 255, cv2.THRESH_BINARY)
            
            # 3. Check Each Lane
            current_time = time.time()
            
            for lane_config in self.lane_rois:
                # Slice the threshold image for this lane's ROI
                y1 = lane_config['y'] - int(ROI_HEIGHT/2)
                y2 = lane_config['y'] + int(ROI_HEIGHT/2)
                x1 = lane_config['x'] - int(ROI_WIDTH/2)
                x2 = lane_config['x'] + int(ROI_WIDTH/2)
                
                # Check bounds (fast clamp)
                y1, y2 = max(0, y1), min(thresh.shape[0], y2)
                x1, x2 = max(0, x1), min(thresh.shape[1], x2)
                
                # Count white pixels
                non_zero_count = cv2.countNonZero(thresh[y1:y2, x1:x2])

                # Trigger
                if non_zero_count > THRESHOLD:
                    lane_idx = lane_config['lane_idx']
                    if (current_time - LANES[lane_idx]['last_press']) > COOLDOWN:
                        key = lane_config['key']
                        self.keyboard.press(key)
                        self.keyboard.release(key)
                        LANES[lane_idx]['last_press'] = current_time
                        print(f"Hit '{key}'") # Minimal logging

            # 4. Background Update (Adaptive)
            # Adjust the background slowly to account for lighting/shifting
            # Using a very small alpha so moving objects don't become background too quickly
            cv2.accumulateWeighted(frame_gray, gray_bg.astype('float'), 0.05)
            gray_bg = gray_bg.astype('uint8')
            
            # No sleep here - run as fast as possible

        print("Agent stopped.")

if __name__ == "__main__":
    agent = GameAgent()
    agent.run()
