import cv2
import json

# Global variables to store coordinates
lane_y_coords = []
target_x_coord = None
image = None

def click_event(event, x, y, flags, params):
    global lane_y_coords, target_x_coord, image

    if event == cv2.EVENT_LBUTTONDOWN:
        # We need 4 Lane Y coordinates and 1 Target X coordinate
        if len(lane_y_coords) < 4:
            lane_y_coords.append(y)
            print(f"Lane {len(lane_y_coords)} Y-coordinate: {y}")
            # Visual feedback: Draw a horizontal line for the lane
            cv2.line(image, (0, y), (image.shape[1], y), (0, 255, 0), 2)
            cv2.putText(image, f"Lane {len(lane_y_coords)}", (10, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.imshow('Calibrate Lanes', image)
        
        elif target_x_coord is None:
            target_x_coord = x
            print(f"Target X-coordinate: {x}")
            # Visual feedback: Draw a vertical line for the target
            cv2.line(image, (x, 0), (x, image.shape[0]), (0, 0, 255), 2)
            cv2.putText(image, "Target X", (x + 10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.imshow('Calibrate Lanes', image)
            
            print("\nCalibration Complete!")
            print("Press any key to close and save...")

def main():
    global image
    
    # Try to load the calibration image, fallback to video frame if needed
    img_path = 'callibrate.png'
    image = cv2.imread(img_path)
    
    if image is None:
        print(f"Could not load {img_path}. Trying video...")
        cap = cv2.VideoCapture('sample-game-recording.mp4')
        ret, frame = cap.read()
        if ret:
            image = frame
        cap.release()

    if image is None:
        print("Error: Could not load image or video frame.")
        return

    print("--- Calibration Instructions ---")
    print("1. Click the center of the 4 lanes to set their Y (height) positions.")
    print("2. Click once to set the Target X (horizontal) position.")
    print("--------------------------------")

    cv2.imshow('Calibrate Lanes', image)
    cv2.setMouseCallback('Calibrate Lanes', click_event)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if len(lane_y_coords) == 4 and target_x_coord is not None:
        config = {
            "lane_y": lane_y_coords,
            "target_x": target_x_coord
        }
        
        with open('lane_config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"\nSaved configuration to lane_config.json:")
        print(config)
    else:
        print("\nCalibration incomplete. Config not saved.")

if __name__ == "__main__":
    main()
