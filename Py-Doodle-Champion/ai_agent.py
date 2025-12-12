import time
import cv2
import numpy as np
import mss
from pynput import keyboard

# --- Configuration ---
TARGET_Y = 947

LANES = [
    {'x': 736,  'key': 'a', 'last_press': 0, 'was_triggered': False},
    {'x': 905,  'key': 'w', 'last_press': 0, 'was_triggered': False},
    {'x': 1067, 'key': 's', 'last_press': 0, 'was_triggered': False},
    {'x': 1231, 'key': 'd', 'last_press': 0, 'was_triggered': False}
]

# Detection Settings
ROI_WIDTH = 50
ROI_HEIGHT = 25
COLOR_THRESHOLD = 40
PIXEL_PERCENT = 0.15
COOLDOWN = 0.08
MONITOR_ID = 1

# --- AI Agent Class ---
class GameAgent:
    def __init__(self):
        self.sct = mss.mss()
        self.running = True
        self.background_colors = []
        self.last_key_pressed = None  # Track user's key press
        
        min_x = min(l['x'] for l in LANES) - ROI_WIDTH
        max_x = max(l['x'] for l in LANES) + ROI_WIDTH
        
        self.monitor_area = {
            "top": TARGET_Y - ROI_HEIGHT, 
            "left": min_x, 
            "width": max_x - min_x, 
            "height": ROI_HEIGHT * 2,
            "mon": MONITOR_ID
        }
        
        self.lane_rois = []
        for i, lane in enumerate(LANES):
            rel_x = lane['x'] - self.monitor_area["left"]
            rel_y = ROI_HEIGHT
            
            self.lane_rois.append({
                'x': rel_x, 
                'y': rel_y,
                'key': lane['key'],
                'lane_idx': i
            })

        print(f"Agent Initialized (DETECTION ONLY - NO AUTO KEYS)")
        print(f"Monitoring Region: {self.monitor_area}")
        print(f"Press 'q' in the debug window to stop.")
        print(f"Listening for your key presses: a, w, s, d\n")
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()

    def _on_key_press(self, key):
        """Callback when user presses a key"""
        try:
            if key.char in ['a', 'w', 's', 'd']:
                self.last_key_pressed = key.char
        except AttributeError:
            pass  # Special key, ignore

    def capture_background(self, frame):
        """Capture the average background color for each lane ROI"""
        self.background_colors = []
        
        for lane_config in self.lane_rois:
            x1, y1, x2, y2 = self._get_roi_bounds(lane_config)
            roi = frame[y1:y2, x1:x2]
            
            mean_color = np.mean(roi, axis=(0, 1))
            self.background_colors.append(mean_color)
            print(f"Lane {lane_config['lane_idx']+1} ({lane_config['key']}): Background color = {mean_color[:3].astype(int)}")

    def _get_roi_bounds(self, lane_config):
        """Get ROI bounds for a lane"""
        r_x = lane_config['x']
        r_y = lane_config['y']
        
        y1 = r_y - ROI_HEIGHT // 2
        y2 = r_y + ROI_HEIGHT // 2
        x1 = r_x - ROI_WIDTH // 2
        x2 = r_x + ROI_WIDTH // 2
        
        return x1, y1, x2, y2

    def detect_color_change(self, roi, bg_color):
        """Detect if a different colored object has entered the ROI."""
        diff = np.sqrt(np.sum((roi.astype(np.float32) - bg_color[:3]) ** 2, axis=2))
        changed_pixels = np.sum(diff > COLOR_THRESHOLD)
        total_pixels = roi.shape[0] * roi.shape[1]
        
        return changed_pixels / total_pixels if total_pixels > 0 else 0

    def run(self):
        print("\n=== STARTING IN 5 SECONDS ===")
        print("Please switch to your game window NOW!")
        print("Make sure the lanes are EMPTY when capture starts!")
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        print("=== CAPTURING BACKGROUND ===")

        initial_frame = np.array(self.sct.grab(self.monitor_area))
        self.capture_background(initial_frame)
        
        print("=== AGENT ACTIVE ===")
        print(f"Color threshold: {COLOR_THRESHOLD}, Pixel %: {PIXEL_PERCENT*100}%")

        while self.running:
            frame_raw = np.array(self.sct.grab(self.monitor_area))
            debug_frame = frame_raw.copy()
            current_time = time.time()
            
            for i, lane_config in enumerate(self.lane_rois):
                x1, y1, x2, y2 = self._get_roi_bounds(lane_config)
                
                y1, y2 = max(0, y1), min(frame_raw.shape[0], y2)
                x1, x2 = max(0, x1), min(frame_raw.shape[1], x2)
                
                roi = frame_raw[y1:y2, x1:x2, :3]
                change_percent = self.detect_color_change(roi, self.background_colors[i])
                is_triggered = change_percent >= PIXEL_PERCENT
                
                color = (0, 255, 0)
                status = "IDLE"
                
                lane_idx = lane_config['lane_idx']
                last_press = LANES[lane_idx]['last_press']
                was_triggered = LANES[lane_idx]['was_triggered']
                
                if is_triggered:
                    if not was_triggered:
                        LANES[lane_idx]['last_press'] = current_time
                        LANES[lane_idx]['was_triggered'] = True
                        color = (0, 0, 255)
                        status = "PRESS"
                        
                        key = lane_config['key']
                        print(f"AI Pressed '{key}' | Confidence: {change_percent*100:.1f}%")
                        self.last_key_pressed = None
                    else:
                        color = (0, 165, 255)
                        status = "HOLD"
                    
                    LANES[lane_idx]['was_triggered'] = True
                else:
                    LANES[lane_idx]['was_triggered'] = False
                    status = "IDLE"

                cv2.rectangle(debug_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(debug_frame, f"{change_percent*100:.0f}% {status}", (x1, y1-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

            cv2.imshow("Guitar Hero AI (Press 'q' to quit)", debug_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                break

        cv2.destroyAllWindows()
        self.keyboard_listener.stop()
        print("Agent stopped.")


if __name__ == "__main__":
    agent = GameAgent()
    agent.run()
