#!/usr/bin/env python3

import cv2
import csv
import sys
import os
from pathlib import Path
from keypoint_detector import BoxDetector

def get_box(frame, box_detector: BoxDetector, width, height):
    box_detection = None

    # Continue to play the video until keypoints for the box are found
    # mimic the behavior of guiding user to aligh the box right
    ok, box_detection = box_detector.detect(frame)
    if ok:
        above_threshold = box_detection['Front divider top'][1]
        below_threshold =  min(box_detection['Back top left'][1], box_detection['Back top right'][1])
        return above_threshold, below_threshold
    elif box_detection is not None and not ok:
        # Guess the missing keypoints
        box_detection = box_detector.guess_missing_keypoints(
            box_detection,
            width,
            height
        )

        if box_detection is not None:
            # From guessed points
            above_threshold = box_detection['Front divider top'][1]
            below_threshold =  min(box_detection['Back top left'][1], box_detection['Back top right'][1])
            return above_threshold, below_threshold
        else:
            return 0,0
def draw_thresholds(frame, above_threshold_y, below_threshold_y):
    """
    Draws a red horizontal line with "ABOVE THRESHOLD" text and a blue horizontal line
    with "BELOW THRESHOLD" text on the given frame. Text color matches line color.
    Text placement adjusts to avoid going out of frame.

    Args:
        frame (np.array): The OpenCV image (frame) to draw on.
        above_threshold_y (int): The Y-coordinate for the red line.
        below_threshold_y (int): The Y-coordinate for the blue line.

    Returns:
        np.array: The frame with the lines and text drawn.
    """
    # Get the dimensions of the frame
    height, width, _ = frame.shape

    # Define colors in BGR format
    RED = (0, 0, 255)   # (Blue, Green, Red)
    BLUE = (255, 0, 0)  # (Blue, Green, Red)
    
    # Line thickness
    line_thickness = 2

    # Font properties for text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    font_thickness = 2
    text_x_start = 10 # X-coordinate for the start of the text (left side)
    text_vertical_buffer = 10 # Vertical buffer pixels between line and text/frame edge

    # --- Draw the red line for above_threshold ---
    cv2.line(frame, (0, above_threshold_y), (width - 1, above_threshold_y), RED, line_thickness)

    above_text = "ABOVE THRESHOLD"
    (above_text_width, above_text_height), above_baseline = cv2.getTextSize(above_text, font, font_scale, font_thickness)
    
    # Determine Y-position for ABOVE THRESHOLD text (baseline)
    # Option 1: Try to place text *above* the line
    # Baseline will be at above_threshold_y - text_vertical_buffer
    # Top of text will be at (above_threshold_y - text_vertical_buffer - above_text_height)
    above_text_y_baseline_option1 = above_threshold_y - text_vertical_buffer

    # Option 2: Try to place text *below* the line
    # Baseline will be at (above_threshold_y + text_vertical_buffer + above_text_height)
    above_text_y_baseline_option2 = above_threshold_y + text_vertical_buffer + above_text_height

    # Choose placement: Prioritize placing above unless it goes off screen
    if (above_text_y_baseline_option1 - above_text_height) < 0: # If text top is above frame top
        # Option 1 is invalid, use Option 2
        above_text_y_pos = above_text_y_baseline_option2
        # If Option 2 also goes off screen (bottom of frame), fallback to minimal offset below line
        if above_text_y_pos > height:
            above_text_y_pos = above_threshold_y + 5 + above_text_height # 5 pixels below line
    else:
        # Option 1 is valid, use it
        above_text_y_pos = above_text_y_baseline_option1

    cv2.putText(frame, above_text, (text_x_start, above_text_y_pos), font, font_scale, RED, font_thickness, cv2.LINE_AA)

    # --- Draw the blue line for below_threshold ---
    cv2.line(frame, (0, below_threshold_y), (width - 1, below_threshold_y), BLUE, line_thickness)

    below_text = "BELOW THRESHOLD"
    (below_text_width, below_text_height), below_baseline = cv2.getTextSize(below_text, font, font_scale, font_thickness)

    # Determine Y-position for BELOW THRESHOLD text (baseline)
    # Option 1: Try to place text *below* the line
    # Baseline will be at (below_threshold_y + text_vertical_buffer + below_text_height)
    below_text_y_baseline_option1 = below_threshold_y + text_vertical_buffer + below_text_height

    # Option 2: Try to place text *above* the line
    # Baseline will be at (below_threshold_y - text_vertical_buffer)
    # Top of text will be at (below_threshold_y - text_vertical_buffer - below_text_height)
    below_text_y_baseline_option2 = below_threshold_y - text_vertical_buffer

    # Choose placement: Prioritize placing below unless it goes off screen
    if below_text_y_baseline_option1 > height: # If text baseline is below frame bottom
        # Option 1 is invalid, use Option 2
        below_text_y_pos = below_text_y_baseline_option2
        # If Option 2 also goes off screen (top of frame), fallback to minimal offset above line
        if (below_text_y_pos - below_text_height) < 0:
            below_text_y_pos = below_threshold_y - 5 # 5 pixels above line
    else:
        # Option 1 is valid, use it
        below_text_y_pos = below_text_y_baseline_option1

    cv2.putText(frame, below_text, (text_x_start, below_text_y_pos), font, font_scale, BLUE, font_thickness, cv2.LINE_AA)

    return frame

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 attempt_labeler.py <video_file>")
        sys.exit(1)
    
    video_path = sys.argv[1]

    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        sys.exit(1)
    
    video_name = video_path.split('/')[-1].split('.')[0] # Extract filename only without path or extensions
    print(video_name)

    box_detector = BoxDetector("keypoint_detector.pt")

    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file '{video_path}'")
        sys.exit(1)
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    
    print(f"Video loaded: {video_path}")
    print(f"FPS: {fps}, Total frames: {total_frames}")
    print("\nControls:")
    print("- Press any key to advance frame")
    print("- Press r to rewind frame")
    print("- Press '1' to mark attempt start")
    print("- Press '2' to mark attempt end (and save to CSV)")
    print("- Press 'q' to quit")
    print("\nStarting playback...")
    
    # Initialize variables
    attempt_number = 1
    attempt_start_frame = None
    attempt_start_time = None
    current_frame = 0
    csv_file = f"{video_name}_attempt_ground_truths.csv"
    recorded_message = None
    recorded_message_timer = 0
    recorded_attempts = []  # Store completed attempts to track for deletion
    
    # Create CSV file with headers if it doesn't exist
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['attempt_number', 'attempt_start_time', 'attempt_end_time', 
                           'attempt_start_frame', 'attempt_end_frame'])
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("End of video reached.")
            break
        
        # Update box keypoints 
        if current_frame % 300 == 0:
            above_line_y, below_line_y = get_box(frame, box_detector, frame_width, frame_height)
            above_line_y = int(above_line_y)
            below_line_y = int(below_line_y)
            
        frame = draw_thresholds(frame, above_line_y, below_line_y)
      
        # Calculate current time in seconds
        current_time = current_frame / fps
        
        # Default control messages
        control_text = "Any key to advance / r to rewind / 1 to mark start / 2 to mark end / q to quit" 
        cv2.putText(frame, control_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Display frame info on the frame
        info_text = f"Frame: {current_frame} | Time: {current_time:.2f}s"
        cv2.putText(frame, info_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Show current attempt status
        if attempt_start_frame is not None:
            status_text = f"Attempt {attempt_number} - Start marked at frame {attempt_start_frame}"
            cv2.putText(frame, status_text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Show recorded message if active
        if recorded_message and recorded_message_timer > 0:
            cv2.putText(frame, recorded_message, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 50 , 255), 2)
            recorded_message_timer -= 1
        
        # Display the frame
        cv2.imshow('Attempt Labeler', frame)
        
        # Wait for key press
        key = cv2.waitKey(0) & 0xFF
        
        if key == ord('q'):
            print("Quitting...")
            break
        elif key == ord('1'):
            # Mark attempt start
            attempt_start_frame = current_frame
            attempt_start_time = current_time
            print(f"Attempt {attempt_number} start marked - Frame: {current_frame}, Time: {current_time:.2f}s")
        elif key == ord('2'):
            # Mark attempt end and save to CSV
            if attempt_start_frame is not None:
                attempt_end_frame = current_frame
                attempt_end_time = current_time
                # Write to CSV
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([attempt_number, attempt_start_time, attempt_end_time,
                                   attempt_start_frame, attempt_end_frame])
                
                # Store attempt info for tracking deletions
                recorded_attempts.append({
                    'number': attempt_number,
                    'start_time': attempt_start_time,
                    'end_time': attempt_end_time,
                    'start_frame': attempt_start_frame,
                    'end_frame': attempt_end_frame
                })
                
                print(f"✓ Attempt {attempt_number} has been recorded!")
                print(f"  Start - Frame: {attempt_start_frame}, Time: {attempt_start_time:.2f}s")
                print(f"  End   - Frame: {attempt_end_frame}, Time: {attempt_end_time:.2f}s")
                
                # Set message to display on video
                recorded_message = f"Attempt {attempt_number} recorded!"
                recorded_message_timer = 60  # Display for 60 frames
                
                # Reset for next attempt
                attempt_number += 1
                attempt_start_frame = None
                attempt_start_time = None
            else:
                print("Warning: Press '1' first to mark attempt start before pressing '2'")
        elif key == ord('r'):
            # Rewind frame
            if current_frame > 0:
                new_frame = current_frame - 1
                
                # Check if we're rewinding past any recorded attempts
                attempts_to_remove = []
                for attempt in recorded_attempts:
                    if new_frame < attempt['end_frame']:
                        attempts_to_remove.append(attempt)
                
                # Remove attempts and update CSV if necessary
                if attempts_to_remove:
                    for attempt in attempts_to_remove:
                        recorded_attempts.remove(attempt)
                        # Set message to display on video
                        recorded_message = f"Attempt {attempt['number']} erased!"
                        recorded_message_timer = 60
                        print(f"Attempt {attempt['number']} erased - rewound past end frame {attempt['end_frame']}")
                    
                    # Rewrite entire CSV file without the removed attempts
                    with open(csv_file, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['attempt_number', 'attempt_start_time', 'attempt_end_time', 
                                       'attempt_start_frame', 'attempt_end_frame'])
                        for attempt in recorded_attempts:
                            writer.writerow([attempt['number'], attempt['start_time'], attempt['end_time'],
                                           attempt['start_frame'], attempt['end_frame']])
                    
                    # Update attempt_number to be one more than the highest remaining attempt
                    if recorded_attempts:
                        attempt_number = max(attempt['number'] for attempt in recorded_attempts) + 1
                    else:
                        attempt_number = 1
                
                current_frame = new_frame - 1  # Subtract 1 because we'll add 1 at the end of loop
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                print(f"Rewound to frame {current_frame}")
            else:
                print("Already at the beginning of the video")
                current_frame -= 1  # Compensate for the +1 at end of loop
        
        # Advance to next frame (will be modified by key handlers above)
        current_frame += 1
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nData saved to: {csv_file}")

if __name__ == "__main__":
    main()