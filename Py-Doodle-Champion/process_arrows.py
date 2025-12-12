import cv2
import numpy as np

def main():
    video_path = 'sample-game-recording.mp4'
    output_path = 'output_game_processing.mp4'

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open {video_path}")
        return

    # Video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Video Writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Background Subtractor for motion detection
    # history=500, varThreshold=16, detectShadows=False (faster, less noise)
    back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    # For Lane Isolation (Accumulate motion mask)
    lane_accumulator = np.zeros((height, width), dtype=np.float32)

    print("Processing video... This might take a moment.")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # 1. Motion Detection
        fg_mask = back_sub.apply(frame)

        # Clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Accumulate for lane visualization (simple weighting)
        # We add a small amount of the current mask to the accumulator
        cv2.accumulateWeighted(fg_mask, lane_accumulator, 0.01)

        # 2. Find Contours (Arrows)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw Bounding Boxes
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter by area to avoid noise (adjust 500 based on arrow size)
            if area > 500: 
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Aspect ratio filter (arrows are somewhat square or rectangular)
                aspect_ratio = float(w)/h
                if 0.2 < aspect_ratio < 5: 
                    # Draw green bounding box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, "Arrow", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 3. Visualize Isolated Lanes (Optional overlay)
        # Convert accumulator to a visible map
        # lane_map = cv2.convertScaleAbs(lane_accumulator)
        # lane_map_color = cv2.applyColorMap(lane_map, cv2.COLORMAP_JET)
        # Overlay lanes faintly? 
        # For now, we stick to the requested "bounding boxes" as the primary visual.
        
        out.write(frame)
        
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")

    cap.release()
    out.release()
    print(f"Done! Saved to {output_path}")

    # Optional: If the user strictly wanted 'isolated lanes' as a separate image
    # We can save the accumulator
    lane_map = cv2.convertScaleAbs(lane_accumulator)
    cv2.imwrite('isolated_lanes_heatmap.png', lane_map)
    print("Saved accumulated lane motion heatmap to isolated_lanes_heatmap.png")

if __name__ == "__main__":
    main()
