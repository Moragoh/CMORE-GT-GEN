#!/usr/bin/env python3

import cv2
import csv
import sys
import os
from pathlib import Path
# Assuming keypoint_detector.py exists in the same directory or is importable
from keypoint_detector import BoxDetector 

"""
DEFINITIONS FOR WHEN TO START MARKING
Start: When the whole hand leaves the red line.
Crossing: When any one knuckle or fingertip crosses the divider line.
End: When all the topmost knuckles goe below the blue line. 
"""

def get_box(frame, box_detector: BoxDetector, width, height):
    """
    Detects keypoints for a box on the frame and returns y-coordinates for two thresholds.
    Handles guessing missing keypoints if initial detection is not fully successful.
    """
    box_detection = None

    # Attempt to detect box keypoints
    ok, box_detection = box_detector.detect(frame)
    if ok:
        above_threshold_y = box_detection['Front divider top'][1]
        below_threshold_y = min(box_detection['Back top left'][1], box_detection['Back top right'][1])
        divider_line_x = (box_detection['Front divider top'][0] + box_detection['Back divider top'][0]) / 2

        return above_threshold_y, below_threshold_y, divider_line_x
    elif box_detection is not None and not ok:
        # If detection was partial, try to guess missing keypoints
        box_detection = box_detector.guess_missing_keypoints(
            box_detection,
            width,
            height
        )

        if box_detection is not None:
            # From guessed points
            above_threshold_y = box_detection['Front divider top'][1]
            below_threshold_y = min(box_detection['Back top left'][1], box_detection['Back top right'][1])
            divider_line_x = (box_detection['Front divider top'][0] + box_detection['Back divider top'][0]) / 2
            
            return above_threshold_y, below_threshold_y,divider_line_x
        else:
            # If guessing also fails
            return 0, 0, 0 # Return default values
    else:
        # If no box_detection at all
        return 0, 0, 0 # Return default values


def draw_thresholds(frame, above_threshold_y, below_threshold_y, divider_threshold_x):
    """
    Draws a red horizontal line with "ABOVE THRESHOLD" text and a blue horizontal line
    with "BELOW THRESHOLD" text on the given frame. Text color matches line color.
    Text placement adjusts to avoid going out of frame.

    Args:
        frame (np.array): The OpenCV image (frame) to draw on.
        above_threshold_y (int): The Y-coordinate for the red line.
        below_threshold_y (int): The Y-coordinate for the blue line.
        divider_threshold_x (int): The X-coordinate for the green vertical divider line.

    Returns:
        np.array: The frame with the lines and text drawn.
    """
    # Get the dimensions of the frame
    height, width, _ = frame.shape

    # Define colors in BGR format
    RED = (0, 0, 255)   # (Blue, Green, Red)
    BLUE = (255, 0, 0)  # (Blue, Green, Red)
    GREEN = (0,255,0) 
    
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
    above_text_y_baseline_option1 = above_threshold_y - text_vertical_buffer
    above_text_y_baseline_option2 = above_threshold_y + text_vertical_buffer + above_text_height

    if (above_text_y_baseline_option1 - above_text_height) < 0:
        above_text_y_pos = above_text_y_baseline_option2
        if above_text_y_pos > height:
            above_text_y_pos = above_threshold_y + 5 + above_text_height
    else:
        above_text_y_pos = above_text_y_baseline_option1

    cv2.putText(frame, above_text, (text_x_start, above_text_y_pos), font, font_scale, RED, font_thickness, cv2.LINE_AA)

    # --- Draw the blue line for below_threshold ---
    cv2.line(frame, (0, below_threshold_y), (width - 1, below_threshold_y), BLUE, line_thickness)

    below_text = "BELOW THRESHOLD"
    (below_text_width, below_text_height), below_baseline = cv2.getTextSize(below_text, font, font_scale, font_thickness)

    # Determine Y-position for BELOW THRESHOLD text (baseline)
    below_text_y_baseline_option1 = below_threshold_y + text_vertical_buffer + below_text_height
    below_text_y_baseline_option2 = below_threshold_y - text_vertical_buffer

    if below_text_y_baseline_option1 > height:
        below_text_y_pos = below_text_y_baseline_option2
        if (below_text_y_pos - below_text_height) < 0:
            below_text_y_pos = below_threshold_y - 5
    else:
        below_text_y_pos = below_text_y_baseline_option1

    cv2.putText(frame, below_text, (text_x_start, below_text_y_pos), font, font_scale, BLUE, font_thickness, cv2.LINE_AA)

    # Draw green divider line
    cv2.line(frame, (divider_threshold_x,0), (divider_threshold_x, height-1), GREEN, line_thickness)

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
    
    video_name = Path(video_path).stem # Use pathlib for robust filename extraction
    print(f"Processing video: {video_name}")

    # Initialize BoxDetector
    # Make sure 'keypoint_detector.pt' is in the same directory or provide full path
    try:
        box_detector = BoxDetector("keypoint_detector.pt")
    except FileNotFoundError:
        print("Error: 'keypoint_detector.pt' not found. Please ensure the model file is in the correct directory.")
        sys.exit(1)


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
    
    # Handle empty video (0 frames)
    if total_frames == 0:
        print("Error: Video contains 0 frames. Exiting.")
        cap.release()
        sys.exit(1)

    print(f"Video loaded: {video_path}")
    print(f"FPS: {fps}, Total frames: {total_frames}")
    print("\nControls:")
    print("- Press 'k' to advance frame (+1)")
    print("- Press 'l' to advance frames (+10)")
    print("- Press 'j' to rewind frame (-1, with undo logic)")
    print("- Press 'h' to rewind frames (-10, with undo logic)") # Updated control description
    print("- Press '1' to mark attempt start")
    print("- Press '2' to mark cross frame (e.g., when fingers cross the plane)")
    print("- Press '3' to mark attempt end (and save current attempt to CSV)")
    print("- Press 'q' to quit (progress will be saved)")
    print("\nStarting playback...")
    
    # Initialize variables
    attempt_number = 1
    attempt_start_frame = None
    attempt_start_time = None
    cross_frame = None
    cross_time = None
    current_frame = 0
    
    csv_file = f"./outputs/attempt_labels/{video_name}_attempt_ground_truths.csv"
    recorded_message = None
    recorded_message_timer = 0
    recorded_attempts = []  # Store completed attempts to track for deletion and rewriting
    
    # Initialize default threshold lines (will be updated by get_box)
    above_line_y = 0
    below_line_y = frame_height # Set to bottom of frame initially
    divider_line_x = 0
    
    # Create CSV file with headers if it doesn't exist
    if not os.path.exists(csv_file):
        os.makedirs(os.path.dirname(csv_file), exist_ok=True) # Ensure output directory exists
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['attempt_number', 'attempt_start_time', 'attempt_end_time', 
                           'attempt_start_frame', 'attempt_end_frame',
                           'cross_time', 'cross_frame'])
    else:
        # If CSV exists, load existing data to continue labeling
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            # Check if headers match, if not, print warning (or handle migration)
            expected_headers = ['attempt_number', 'attempt_start_time', 'attempt_end_time', 
                                'attempt_start_frame', 'attempt_end_frame',
                                'cross_time', 'cross_frame']
            if reader.fieldnames != expected_headers:
                print(f"Warning: Existing CSV headers do not match expected headers. "
                      f"Expected: {expected_headers}, Found: {reader.fieldnames}")
                print("Appended data might not align correctly if you proceed.")
                # You might want to add a sys.exit(1) here or force a new file name.

            for row in reader:
                # Convert relevant fields back to their original types for in-memory tracking
                try:
                    recorded_attempts.append({
                        'number': int(row['attempt_number']),
                        'start_time': float(row['attempt_start_time']),
                        'end_time': float(row['attempt_end_time']),
                        'start_frame': int(row['attempt_start_frame']),
                        'end_frame': int(row['attempt_end_frame']),
                        'cross_time': float(row['cross_time']) if row['cross_time'] else None,
                        'cross_frame': int(row['cross_frame']) if row['cross_frame'] else None
                    })
                except (ValueError, KeyError) as e:
                    print(f"Error reading existing CSV row: {row}. Skipping. Error: {e}")
        
        if recorded_attempts:
            attempt_number = max(a['number'] for a in recorded_attempts) + 1
            print(f"Loaded {len(recorded_attempts)} existing attempts. Continuing from attempt {attempt_number}.")
            # Set current_frame to end of last recorded attempt to continue from there
            current_frame = recorded_attempts[-1]['end_frame']
            # Ensure current_frame doesn't exceed total_frames-1
            current_frame = min(current_frame, total_frames - 1) 
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)


    while True:
        # Ensure correct frame is read after 'j', 'h' or initialization
        # Also ensures we don't try to seek beyond the last frame for reading
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        
        if not ret:
            # We have reached or overshot the end of the video.
            # Set current_frame to the last valid frame and re-read it.
            print("End of video reached. Staying on the last frame. Press 'q' to quit or 'j'/'h' to rewind.")
            current_frame = total_frames - 1 # Go back to the last valid frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read() # Re-read the last frame to ensure 'frame' is valid
            
            if not ret: # If even re-reading the last frame fails, something is very wrong.
                print("Critical Error: Could not retrieve last frame. Exiting.")
                break # This is an unrecoverable error.

            # Do NOT break here. Continue to display and wait for input.
            # The user can still press 'q' or rewind.
        
        # Update box keypoints at specified interval (e.g., every 300 frames)
        if current_frame % 5000 == 0:
            above_line_y_float, below_line_y_float, divider_line_x = get_box(frame, box_detector, frame_width, frame_height)
            above_line_y = int(above_line_y_float)
            below_line_y = int(below_line_y_float)
            divider_line_x = int(divider_line_x)

        

        # Draw the threshold lines on the frame
        frame = draw_thresholds(frame, above_line_y, below_line_y, divider_line_x)
      
        # Calculate current time in seconds
        current_time = current_frame / fps
        
        # Display control messages
        control_text = "k: +1 | l: +10 | j: -1 | h: -10 | 1: start | 2: cross | 3: end | q: quit" 
        cv2.putText(frame, control_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Display frame info on the frame
        info_text = f"Frame: {current_frame} | Time: {current_time:.2f}s"
        cv2.putText(frame, info_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Show current attempt status
        status_lines = []
        if attempt_start_frame is not None:
            status_lines.append(f"Attempt {attempt_number} START: {attempt_start_frame} ({attempt_start_time:.2f}s)")
        if cross_frame is not None:
            status_lines.append(f"CROSS: {cross_frame} ({cross_time:.2f}s)")
        
        y_offset = 110
        for line in status_lines:
            cv2.putText(frame, line, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            y_offset += 30 # Move down for next line

        # Show recorded message if active
        if recorded_message and recorded_message_timer > 0:
            cv2.putText(frame, recorded_message, (10, y_offset + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 50 , 255), 2)
            recorded_message_timer -= 1
        
        # Display the frame
        cv2.imshow('Attempt Labeler', frame)
        
        # Wait for key press
        key = cv2.waitKey(0) & 0xFF
        
        if key == ord('q'):
            print("Quitting...")
            break
        elif key == ord('k'):
            # Advance one frame.
            new_frame = current_frame + 1
            if new_frame >= total_frames: # Ensure we don't go past the last frame
                current_frame = total_frames - 1
                print("Already at the end of the video. Cannot advance further.")
            else:
                current_frame = new_frame
                print(f"Advanced to frame {current_frame}")
        elif key == ord('l'):
            # Advance 10 frames
            new_frame = current_frame + 10
            # Ensure new_frame does not exceed total_frames - 1
            current_frame = min(total_frames - 1, new_frame) 
            print(f"Advanced to frame {current_frame}")
        elif key == ord('1'):
            # Mark attempt start
            attempt_start_frame = current_frame
            attempt_start_time = current_time
            cross_frame = None # Reset cross_frame for new attempt
            cross_time = None  # Reset cross_time for new attempt
            print(f"Attempt {attempt_number} start marked - Frame: {current_frame}, Time: {current_time:.2f}s")
        elif key == ord('2'):
            # Mark cross frame
            if attempt_start_frame is not None:
                cross_frame = current_frame
                cross_time = current_time
                print(f"Attempt {attempt_number} cross frame marked - Frame: {current_frame}, Time: {current_time:.2f}s")
            else:
                print("Warning: Mark attempt start ('1') first before marking cross frame.")
        elif key == ord('3'):
            # Mark attempt end and save to CSV
            if attempt_start_frame is not None:
                attempt_end_frame = current_frame
                attempt_end_time = current_time
                
                # Write to CSV
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([attempt_number, attempt_start_time, attempt_end_time,
                                   attempt_start_frame, attempt_end_frame,
                                   cross_time if cross_time is not None else '', # Write empty string if None
                                   cross_frame if cross_frame is not None else '']) # Write empty string if None
                
                # Store attempt info for tracking deletions
                recorded_attempts.append({
                    'number': attempt_number,
                    'start_time': attempt_start_time,
                    'end_time': attempt_end_time,
                    'start_frame': attempt_start_frame,
                    'end_frame': attempt_end_frame,
                    'cross_time': cross_time,
                    'cross_frame': cross_frame
                })
                
                print(f"✓ Attempt {attempt_number} has been recorded!")
                print(f"  Start - Frame: {attempt_start_frame}, Time: {attempt_start_time:.2f}s")
                if cross_frame is not None:
                    print(f"  Cross - Frame: {cross_frame}, Time: {cross_time:.2f}s")
                print(f"  End   - Frame: {attempt_end_frame}, Time: {attempt_end_time:.2f}s")
                
                # Set message to display on video
                recorded_message = f"Attempt {attempt_number} recorded!"
                recorded_message_timer = 60  # Display for 60 frames
                
                # Reset for next attempt
                attempt_number += 1
                attempt_start_frame = None
                attempt_start_time = None
                cross_frame = None
                cross_time = None
            else:
                print("Warning: Press '1' first to mark attempt start before pressing '3'")
        elif key == ord('j'):
            # Rewind one frame (with undo logic for recorded attempts)
            if current_frame > 0:
                new_frame = current_frame - 1
                
                # The shared logic for checking and removing attempts due to rewind
                current_frame, recorded_attempts, attempt_number, \
                attempt_start_frame, attempt_start_time, cross_frame, cross_time, \
                recorded_message, recorded_message_timer = \
                    handle_rewind_and_undo(new_frame, current_frame, recorded_attempts, 
                                           attempt_number, attempt_start_frame, 
                                           attempt_start_time, cross_frame, cross_time, 
                                           recorded_message, recorded_message_timer, csv_file)
                
                print(f"Rewound to frame {current_frame}")
            else:
                print("Already at the beginning of the video")
        elif key == ord('h'):
            # Rewind 10 frames (with undo logic for recorded attempts)
            if current_frame > 0:
                new_frame = current_frame - 10
                
                # The shared logic for checking and removing attempts due to rewind
                current_frame, recorded_attempts, attempt_number, \
                attempt_start_frame, attempt_start_time, cross_frame, cross_time, \
                recorded_message, recorded_message_timer = \
                    handle_rewind_and_undo(new_frame, current_frame, recorded_attempts, 
                                           attempt_number, attempt_start_frame, 
                                           attempt_start_time, cross_frame, cross_time, 
                                           recorded_message, recorded_message_timer, csv_file)
                
                print(f"Rewound to frame {current_frame}")
            else:
                print("Already at the beginning of the video")
        else:
            # For any other key, do nothing.
            pass
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nData saved to: {csv_file}")

# Helper function to encapsulate rewind and undo logic
def handle_rewind_and_undo(new_frame, current_frame, recorded_attempts, 
                           attempt_number, attempt_start_frame, 
                           attempt_start_time, cross_frame, cross_time, 
                           recorded_message, recorded_message_timer, csv_file):
    
    # Ensure new_frame does not go below 0
    new_frame = max(0, new_frame)

    attempts_to_remove = []
    for attempt in recorded_attempts:
        # An attempt is "erased" if its end frame is now beyond the new current frame
        if attempt['end_frame'] >= new_frame: 
            attempts_to_remove.append(attempt)
    
    # Remove attempts and update CSV if necessary
    if attempts_to_remove:
        # Sort in reverse order to avoid index issues if removing from original list
        attempts_to_remove.sort(key=lambda x: x['number'], reverse=True)
        for attempt in attempts_to_remove:
            recorded_attempts.remove(attempt)
            recorded_message = f"Attempt {attempt['number']} erased!"
            recorded_message_timer = 60
            print(f"Attempt {attempt['number']} erased - rewound past its end frame {attempt['end_frame']}")
        
        # Rewrite entire CSV file without the removed attempts
        # This will recreate the file if it was deleted due to all attempts being removed.
        # Make sure the directory exists before writing.
        os.makedirs(os.path.dirname(csv_file), exist_ok=True) 
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['attempt_number', 'attempt_start_time', 'attempt_end_time', 
                           'attempt_start_frame', 'attempt_end_frame',
                           'cross_time', 'cross_frame'])
            for attempt in recorded_attempts:
                writer.writerow([attempt['number'], attempt['start_time'], attempt['end_time'],
                               attempt['start_frame'], attempt['end_frame'],
                               attempt['cross_time'] if attempt['cross_time'] is not None else '',
                               attempt['cross_frame'] if attempt['cross_frame'] is not None else ''])
        
        # Update attempt_number to be one more than the highest remaining attempt
        if recorded_attempts:
            attempt_number = max(a['number'] for a in recorded_attempts) + 1
        else:
            attempt_number = 1
        
        # Reset current attempt's marking if it was part of the removed ones
        # This checks if the current START frame or CROSS frame would now be *after* the new_frame
        # If the start or cross point is still valid (i.e., less than new_frame), we keep it.
        # This assumes current_frame is updated after this function.
        if attempt_start_frame is not None and attempt_start_frame >= new_frame:
            attempt_start_frame = None
            attempt_start_time = None
        if cross_frame is not None and cross_frame >= new_frame:
            cross_frame = None
            cross_time = None
        
    return new_frame, recorded_attempts, attempt_number, \
           attempt_start_frame, attempt_start_time, cross_frame, cross_time, \
           recorded_message, recorded_message_timer


if __name__ == "__main__":
    main()