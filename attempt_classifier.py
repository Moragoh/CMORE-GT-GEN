#!/usr/bin/env python3

import cv2
import csv
import sys
import os
import pandas as pd
from pathlib import Path

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 attempt_classifier.py <csv_file> <source_video>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    video_path = sys.argv[2]
    
    # Check if files exist
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found.")
        sys.exit(1)
    
    
    # Create output CSV filename
    csv_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_csv = f"{csv_name}_ground_truth.csv"
    
    # Read the input CSV
    try:
        df = pd.read_csv(csv_file)
        # Convert frame columns to integers
        df['Start Frame index'] = df['Start Frame index'].astype(int)
        df['End Frame index'] = df['End Frame index'].astype(int)
        print(f"Loaded {len(df)} attempts from {csv_file}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_columns = ['Start Frame index', 'End Frame index']
    for col in required_columns:
        if col not in df.columns:
            print(f"Error: Required column '{col}' not found in CSV")
            sys.exit(1)
    
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
    print(f"Output will be saved to: {output_csv}")
    print("\nControls:")
    print("- Press 'j' to go back 1 frame")
    print("- Press 'k' to advance 1 frame")
    print("- Press 'h' to go back 10 frames")
    print("- Press 'l' to advance 10 frames")
    print("- Press 'u' to go to previous attempt")
    print("- Press 'i' to go to next attempt")
    print("- Press '1' to classify as ground_truth_block_drop = 1 (block fell)")
    print("- Press '0' to classify as ground_truth_block_drop = 0 (block did not fall)") 
    print("- Press '2' to open flag options") 
    print("- Press 'q' to quit (progress will be saved)")
    print("\nStarting classification...")
    
    # Create output CSV with headers if it doesn't exist
    output_columns = list(df.columns)
    # Update the ground_truth_block_drop column or add it if it doesn't exist
    if 'ground_truth_block_drop' not in output_columns:
        output_columns.append('ground_truth_block_drop')
    # Add flag columns if they don't exist
    if 'is_flagged' not in output_columns:
        output_columns.append('is_flagged')
    if 'reason_for_flag' not in output_columns:
        output_columns.append('reason_for_flag')
    
    if not os.path.exists(output_csv):
        with open(output_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(output_columns)
    
    # Process each attempt
    current_attempt_index = 0
    
    while current_attempt_index < len(df):
        index = current_attempt_index
        row = df.iloc[index]
        
        attempt_num = index + 1  # Use row index + 1 as attempt number
        start_frame = int(row['Start Frame index'])
        end_frame = int(row['End Frame index'])
        start_time = start_frame / fps
        end_time = end_frame / fps
        
        print(f"\n--- Classifying Attempt {attempt_num} ---")
        print(f"Frames {start_frame} to {end_frame} ({start_time:.2f}s to {end_time:.2f}s)")
        print("Use j/k to navigate, then 0/1/2 to classify...")
        
        classified = False
        falling_block_value = None
        is_flagged = 0
        reason_for_flag = ""
        current_frame = start_frame  # Start at the beginning of the attempt
        flag_menu_active = False
        custom_input_mode = False
        custom_text = ""
        
        while not classified:
            # Ensure current_frame stays within video bounds (but allow going beyond attempt bounds)
            current_frame = max(0, min(current_frame, total_frames - 1))
            
            # Set video position to current frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            
            if not ret:
                print(f"Warning: Could not read frame {current_frame}")
                current_frame += 1
                continue
            
            # Calculate current time
            current_time = current_frame / fps
            
            # Display info on frame with white background
            info_text = f"Attempt {attempt_num} | Frame: {current_frame} | Time: {current_time:.2f}s"
            # Get text size to create background rectangle
            (text_width, text_height), baseline = cv2.getTextSize(info_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            # Draw green background rectangle
            cv2.rectangle(frame, (10, 30 - text_height - 5), (10 + text_width + 5, 30 + baseline + 5), (0, 255, 0), -1)
            # Draw text on top of green background
            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # Show frame range info and controls
            range_text = f"Range: {start_frame}-{end_frame} | j/k: -/+1 | h/l: -/+10 | u/i: prev/next attempt"
            # Get text size to create background rectangle
            (text_width, text_height), baseline = cv2.getTextSize(range_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            # Draw white background rectangle
            cv2.rectangle(frame, (10, 60 - text_height - 5), (10 + text_width + 5, 60 + baseline + 5), (255, 255, 255), -1)
            # Draw text on top of white background
            cv2.putText(frame, range_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            classify_text = f"Press 0 (no drop) | 1 (drop) | 2 (flag options) | q (quit)"
            # Get text size to create background rectangle
            (text_width, text_height), baseline = cv2.getTextSize(classify_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            # Draw white background rectangle
            cv2.rectangle(frame, (10, 90 - text_height - 5), (10 + text_width + 5, 90 + baseline + 5), (255, 255, 255), -1)
            # Draw text on top of white background
            cv2.putText(frame, classify_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Show flag menu if active
            if flag_menu_active and not custom_input_mode:
                flag_options = [
                    "Flag Options:",
                    "w: Block transferred, fingers did not cross",
                    "e: Block transferred, fingers might not have crossed", 
                    "r: Needs manual review",
                    "t: Custom reason (type your own)",
                    "2: Back to main menu"
                ]
                
                y_start = 120
                for i, option in enumerate(flag_options):
                    y_pos = y_start + (i * 25)
                    # Get text size for background
                    (text_width, text_height), baseline = cv2.getTextSize(option, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    # Draw yellow background for flag menu
                    cv2.rectangle(frame, (10, y_pos - text_height - 3), (10 + text_width + 5, y_pos + baseline + 3), (0, 255, 255), -1)
                    # Draw text
                    cv2.putText(frame, option, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Show custom input interface if in custom input mode
            if custom_input_mode:
                # Title prompt
                prompt_text = "Type custom reason for flagging:"
                y_pos = 130
                (text_width, text_height), baseline = cv2.getTextSize(prompt_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (10, y_pos - text_height - 5), (10 + text_width + 5, y_pos + baseline + 5), (0, 0, 255), -1)
                cv2.putText(frame, prompt_text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Text input box showing what user has typed
                input_display = f"Input: {custom_text}|"  # | acts as cursor
                y_pos2 = y_pos + 35
                (text_width2, text_height2), baseline2 = cv2.getTextSize(input_display, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(frame, (10, y_pos2 - text_height2 - 3), (10 + text_width2 + 5, y_pos2 + baseline2 + 3), (255, 255, 255), -1)
                cv2.putText(frame, input_display, (10, y_pos2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                
                # Instructions
                instruction_text = "Press Enter to submit | Press Esc to cancel"
                y_pos3 = y_pos2 + 30
                (text_width3, text_height3), baseline3 = cv2.getTextSize(instruction_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(frame, (10, y_pos3 - text_height3 - 3), (10 + text_width3 + 5, y_pos3 + baseline3 + 3), (0, 0, 255), -1)
                cv2.putText(frame, instruction_text, (10, y_pos3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Display the frame
            cv2.imshow('Attempt Classifier', frame)
            
            # Wait for key press
            key = cv2.waitKey(0) & 0xFF  # Wait indefinitely for key press
            
            if key == ord('q') and not flag_menu_active:
                print("Quitting...")
                cap.release()
                cv2.destroyAllWindows()
                sys.exit(0)
            elif key == ord('j') and not custom_input_mode:  # Go back 1 frame
                current_frame -= 1
                current_frame = max(0, current_frame)
            elif key == ord('k') and not custom_input_mode:  # Advance 1 frame
                current_frame += 1
                current_frame = min(total_frames - 1, current_frame)
            elif key == ord('h') and not custom_input_mode:  # Go back 10 frames
                current_frame -= 10
                current_frame = max(0, current_frame)
            elif key == ord('l') and not custom_input_mode:  # Advance 10 frames
                current_frame += 10
                current_frame = min(total_frames - 1, current_frame)
            elif key == ord('u') and not custom_input_mode and not flag_menu_active:  # Go to previous attempt
                if current_attempt_index > 0:
                    current_attempt_index -= 1
                    prev_row = df.iloc[current_attempt_index]
                    current_frame = int(prev_row['Start Frame index'])
                    print(f"Jumped to attempt {current_attempt_index + 1}")
                    break  # Exit the inner loop to restart with new attempt
                else:
                    print("Already at first attempt")
            elif key == ord('i') and not custom_input_mode and not flag_menu_active:  # Go to next attempt
                if current_attempt_index < len(df) - 1:
                    current_attempt_index += 1
                    next_row = df.iloc[current_attempt_index]
                    current_frame = int(next_row['Start Frame index'])
                    print(f"Jumped to attempt {current_attempt_index + 1}")
                    break  # Exit the inner loop to restart with new attempt
                else:
                    print("Already at last attempt")
            elif key == ord('0') and not flag_menu_active:
                falling_block_value = 0
                classified = True
                print(f"Attempt {attempt_num} classified as ground_truth_block_drop = 0 (block did not fall)")
            elif key == ord('1') and not flag_menu_active:
                falling_block_value = 1
                classified = True
                print(f"Attempt {attempt_num} classified as ground_truth_block_drop = 1 (block fell)")
            elif key == ord('2'):
                if flag_menu_active:
                    # Go back to main menu
                    flag_menu_active = False
                    custom_input_mode = False
                    custom_text = ""
                    print("Returned to main menu")
                else:
                    # Open flag menu
                    flag_menu_active = True
                    custom_input_mode = False
                    custom_text = ""
                    print("Flag menu opened")
            elif flag_menu_active and not custom_input_mode:
                # Handle flag menu options
                if key == ord('w'):
                    falling_block_value = 2
                    is_flagged = 1
                    reason_for_flag = "Block transferred, but failure because the fingers did not cross"
                    classified = True
                    print(f"Attempt {attempt_num} flagged: {reason_for_flag}")
                elif key == ord('e'):
                    falling_block_value = 3
                    is_flagged = 1
                    reason_for_flag = "Block transferred, but fingers might not have crossed"
                    classified = True
                    print(f"Attempt {attempt_num} flagged: {reason_for_flag}")
                elif key == ord('r'):
                    falling_block_value = 4
                    is_flagged = 1
                    reason_for_flag = "Needs manual review"
                    classified = True
                    print(f"Attempt {attempt_num} flagged: {reason_for_flag}")
                elif key == ord('t'):
                    # Enter custom input mode
                    custom_input_mode = True
                    custom_text = ""
                    print("Custom input mode activated")
            elif custom_input_mode:
                # Handle custom input mode
                if key == 27:  # Escape key
                    # Go back to flag menu
                    custom_input_mode = False
                    custom_text = ""
                    print("Returned to flag menu")
                elif key == 13:  # Enter key
                    if custom_text.strip():
                        falling_block_value = 5
                        is_flagged = 1
                        reason_for_flag = custom_text.strip()
                        classified = True
                        print(f"Attempt {attempt_num} flagged with custom reason: {reason_for_flag}")
                    else:
                        print("No text entered, staying in custom input mode")
                elif key == 8 or key == 127:  # Backspace (different systems use different codes)
                    if custom_text:
                        custom_text = custom_text[:-1]
                elif key >= 32 and key <= 126:  # Printable ASCII characters
                    custom_text += chr(key)
        
        # Only save and advance if we actually classified (not if we jumped to another attempt)
        if classified:
            # Prepare output row - update existing values or add new ones
            output_row = row.copy()
            output_row['ground_truth_block_drop'] = falling_block_value
            output_row['is_flagged'] = is_flagged
            output_row['reason_for_flag'] = reason_for_flag
            
            # Write the classified attempt to output CSV
            with open(output_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(output_row.values)
            
            print(f"✓ Attempt {attempt_num} saved with ground_truth_block_drop = {falling_block_value}, is_flagged = {is_flagged}")
            
            # Move to next attempt
            current_attempt_index += 1
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"Classification complete!")
    print(f"Classified {len(df)} attempts")
    print(f"Results saved to: {output_csv}")

if __name__ == "__main__":
    main()