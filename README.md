# Ground Truth Attempt Generator for Box and Blocks

## Requirements
Python 3

## Installation
1) Download the repository as a .zip file and unzip it to a preferred destination.
2) In a terminal of your choice, travel to the inside of directory CMORE-GT-GEN-main.
3) Run the following commands in order:
```
python3 -m venv venv
source venv/bin/activate
pip3 install requirements.txt
```
4) The Ground Truth Generator is now ready for use.

## Usage
1) If you haven't already, run
```
source venv/bin/activate
```
2) Run
```
python3 label_generator.py [path to video file]
```
For instance, if I wanted to run the label generator on test.mp4 which is in the same directory is label_generator.py, I would run:
```
python3 label_generator.py test.mp4
```
3) A new window will pop up, allowing you to review the video frame-by-frame.
4) Press any key to advance a frame (you can also hold any key to rapidly advance through frames).
5) When you want to mark the start of an attempt, press '1'
6) When you want to mark the end of an attempt, press '2' 

   NOTE: A new row for the attempt will be appended to the resulting csv file after the script finishes.
8) Press 'r' ro rewind (holding r to rapidly move backward through frames also works).

   NOTE: While rewinding, if you rewind past where an attempt spans, that attempt will automatically be deleted off of the resulting csv file. For instance, if Attempt 4 lasted from frame 50 to 100, and you rewinded to before frame 100, Attempt 4 will be erased.
10) The script will automatically generate a csv file of all the attempts noted in each row when you get to the end of the video. It will have the name [video_name]_attempt_ground_truth.csv





