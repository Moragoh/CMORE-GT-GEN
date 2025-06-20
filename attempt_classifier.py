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
    
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        sys.exit(1)
    
    # Create output CSV filename
    csv_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_csv = f"{csv_name}_ground_truth.csv"
    output_csv = f"{csv_name}_ground_truth.csv"
    
    # Read the input CSV
    try:
        df = pd.read_csv(csv_file)
        # Convert frame columns to integers
        df['Start Frame index'] = df['Start Frame index'].astype(int)
        df['End Frame index'] = df['End Frame index'].astype(int)
        # Convert frame columns to integers
        df['Start Frame index'] = df['Start Frame index'].astype(int)
        df['End Frame index'] = df['End Frame index'].astype(int)
        print(f"Loaded {len(df)} attempts from {csv_file}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_columns = ['Start Frame index', 'End Frame index']
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
    print("- Press '1' to classify as ground_truth_block_drop = 1 (block fell)")
    print("- Press '0' to classify as ground_truth_block_drop = 0 (block did not fall)") 
    print("- Press '2' to flag this attempt") 
    print("- Press 'q' to quit (progress will be saved)")
    print("\nStarting classification...")
    
    # Create output CSV with headers if it doesn't exist
    output_columns = list(df.columns)
    # Update the ground_truth_block_drop column or add it if it doesn't exist
    if 'ground_truth_block_drop' not in output_columns:
        output_columns.append('ground_truth_block_drop')
    
    output_columns = list(df.columns)
    # Update the ground_truth_block_drop column or add it if it doesn't exist
    if 'ground_truth_block_drop' not in output_columns:
        output_columns.append('ground_truth_block_drop')
    
    if not os.path.exists(output_csv):
        with open(output_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(output_columns)
    
    # Process each attempt
    for index, row in df.iterrows():
        attempt_num = index + 1  # Use row index + 1 as attempt number
        start_frame = int(row['Start Frame index'])
        end_frame = int(row['End Frame index'])
        start_time = start_frame / fps
        end_time = end_frame / fps
        attempt_num = index + 1  # Use row index + 1 as attempt number
        start_frame = int(row['Start Frame index'])
        end_frame = int(row['End Frame index'])
        start_time = start_frame / fps
        end_time = end_frame / fps
        
        print(f"\n--- Classifying Attempt {attempt_num} ---")
        print(f"Frames {start_frame} to {end_frame} ({start_time:.2f}s to {end_time:.2f}s)")
        print("Looping until user input...")
        
        classified = False
        falling_block_value = None
        falling_block_value = None
        
        while not classified:
            # Loop through the attempt frames
            current_frame = start_frame
            
            while current_frame <= end_frame and not classified:
                # Set video position to current frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                ret, frame = cap.read()
                
                if not ret:
                    print(f"Warning: Could not read frame {current_frame}")
                    current_frame += 1
                    continue
                
                # Calculate current time
                current_time = current_frame / fps
                
                # Display info on frame
                info_text = f"Attempt {attempt_num} | Frame: {current_frame} | Time: {current_time:.2f}s"
                cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Show frame range info
                range_text = f"Range: {start_frame}-{end_frame} | Press 0 (no drop) or 1 (drop) or 2 (flag attempt) "
                cv2.putText(frame, range_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Display the frame
                cv2.imshow('Attempt Classifier', frame)
                
                # Check for key press (small delay to make video playable)
                key = cv2.waitKey(50) & 0xFF
                
                if key == ord('q'):
                    print("Quitting...")
                    cap.release()
                    cv2.destroyAllWindows()
                    sys.exit(0)
                elif key == ord('1'):
                    falling_block_value = 1
                    falling_block_value = 1
                    classified = True
                    print(f"Attempt {attempt_num} classified as ground_truth_block_drop = 1 (block fell)")
                    print(f"Attempt {attempt_num} classified as ground_truth_block_drop = 1 (block fell)")
                    break
                elif key == ord('0'):
                    falling_block_value = 0
                    classified = True
                    print(f"Attempt {attempt_num} classified as ground_truth_block_drop = 0 (block did not fall)")
                elif key == ord('2'):
                    falling_block_value = 2
                    classified = True
                    print(f"Attempt {attempt_num} flagged for review")
                    break
                current_frame += 1
            
            # If we've reached the end of the segment without classification, loop back
            if not classified:
                print("Looping back to start of attempt...")
        
        # Prepare output row - update existing ground_truth_block_drop value or add new one
        output_row = row.copy()
        output_row['ground_truth_block_drop'] = falling_block_value
        
        # Prepare output row - update existing ground_truth_block_drop value or add new one
        output_row = row.copy()
        output_row['ground_truth_block_drop'] = falling_block_value
        
        # Write the classified attempt to output CSV
        with open(output_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(output_row.values)
            writer.writerow(output_row.values)
        
        print(f"✓ Attempt {attempt_num} saved with ground_truth_block_drop = {falling_block_value}")
        print(f"✓ Attempt {attempt_num} saved with ground_truth_block_drop = {falling_block_value}")
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"Classification complete!")
    print(f"Classified {len(df)} attempts")
    print(f"Results saved to: {output_csv}")

if __name__ == "__main__":
    main()