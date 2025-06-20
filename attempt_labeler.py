#!/usr/bin/env python3

import cv2
import csv
import sys
import os
from pathlib import Path

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

    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file '{video_path}'")
        sys.exit(1)
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
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
        cv2.imshow('Video Frame Analyzer', frame)
        
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