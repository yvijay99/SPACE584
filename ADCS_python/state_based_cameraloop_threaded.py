#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 14:10:31 2025

Modified to be state-based: cameras only run in appropriate ADCS states.
State file written by Simulink at /tmp/adcs_state.bin.

Threaded architecture: each camera runs in its own thread to avoid blocking.

States:
    0 - Detumble: No cameras
    1 - Coarse pointing: Sun sensor (IR) only
    2 - Fine pointing: Star tracker + Sun sensor (IR)
    3 - Science: Science camera only
"""

import threading
import os
import time
import numpy as np
import subprocess
import struct
import sys

# Global flag for clean shutdown
running = True

def read_state(state_file):
    """
    Read current ADCS state from binary file written by Simulink.
    Returns state as int, or -1 if file doesn't exist / can't be read.
    """
    try:
        with open(state_file, 'rb') as f:
            data = f.read(4)
            if len(data) == 4:
                state = struct.unpack('<i', data)[0]
                return state
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error reading state file: {e}")
    return -1

def sun_sensor_loop(state_file, root, freq, printLog):
    """
    Sun sensor thread: runs in states 1 and 2
    """
    global running
    
    print("[SS] Sun sensor thread started")
    last_run = 0
    
    while running:
        
        current_state = read_state(state_file)
        
        if current_state in [1, 2]:
            
            now = time.time()
            
            if now - last_run > 1/freq:
                
                print(f"[SS] {now - last_run:.2f}s elapsed, executing...")
                
                start_time = time.time()
                
                # TAKE PHOTO
                log = subprocess.run(
                    [sys.executable, root + "ir_camera_take_picture.py"],
                    capture_output=True,
                    text=True,
                    check=False)
                
                if printLog:
                    print(log)
                
                # RUN ANALYSIS
                try:
                    log = subprocess.run(
                        [sys.executable, root + "sun_sensor.py", root],
                        capture_output=True,
                        text=True,
                        check=True)
                    if printLog:
                        print(log)
                except subprocess.CalledProcessError as e:
                    print(f"[SS] Analysis failed: {e}")
                
                last_run = time.time()
                run_time = last_run - start_time
                
                print(f"[SS] Complete in {run_time:.2f}s")
                
                if run_time > 1/freq:
                    print("[SS] WARNING: CAN NOT KEEP UP WITH REQUIRED FREQ")
        
        time.sleep(0.1)  # Small sleep to avoid busy-waiting
    
    print("[SS] Sun sensor thread stopped")

def star_tracker_loop(state_file, root, freq, printLog):
    """
    Star tracker thread: runs in state 2 only
    """
    global running
    
    print("[ST] Star tracker thread started")
    last_run = 0
    
    while running:
        
        current_state = read_state(state_file)
        
        if current_state == 2:
            
            now = time.time()
            
            if now - last_run > 1/freq:
                
                print(f"[ST] {now - last_run:.2f}s elapsed, executing...")
                
                start_time = time.time()
                
                # TAKE PHOTO
                shutter_time = 0.1  # [s]
                shutter_str = str(int(shutter_time * 1000000))
                cmd = [
                    "rpicam-still",
                    "-o", root + "star_field.jpg",
                    "--shutter", shutter_str,
                    "--gain", "1",
                    "--awbgains", "1,1",
                    "--immediate",
                    "--camera", "0",
                    "--rotation", "180"
                ]
                
                cam = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if printLog:
                    print(cam)
                
                # CROP IMAGE
                try:
                    log = subprocess.run(
                        [sys.executable, root + "crop_image.py", root + "star_field.jpg"],
                        capture_output=True,
                        text=True,
                        check=True)
                    if printLog:
                        print(log)
                except subprocess.CalledProcessError as e:
                    print(f"[ST] Crop failed: {e}")
                
                # RUN ANALYSIS
                try:
                    log = subprocess.run(
                        [sys.executable, root + "star_tracker.py", root],
                        capture_output=True,
                        text=True,
                        check=True)
                    if printLog:
                        print(log)
                except subprocess.CalledProcessError as e:
                    print(f"[ST] Analysis failed: {e}")
                
                last_run = time.time()
                run_time = last_run - start_time
                
                print(f"[ST] Complete in {run_time:.2f}s")
                
                if run_time > 1/freq:
                    print("[ST] WARNING: CAN NOT KEEP UP WITH REQUIRED FREQ")
        
        time.sleep(0.1)  # Small sleep to avoid busy-waiting
    
    print("[ST] Star tracker thread stopped")

def science_camera_loop(state_file, root, freq, printLog):
    """
    Science camera thread: runs in state 3 only
    """
    global running
    
    print("[SCI] Science camera thread started")
    last_run = 0
    
    while running:
        
        current_state = read_state(state_file)
        
        if current_state == 3:
            
            now = time.time()
            
            if now - last_run > 1/freq:
                
                print(f"[SCI] {now - last_run:.2f}s elapsed, executing...")
                
                start_time = time.time()
                
                # CAPTURE SCIENCE IMAGE
                try:
                    log = subprocess.run(
                        [sys.executable, root + "science_camera_capture.py", "single", root],
                        capture_output=True,
                        text=True,
                        check=True)
                    if printLog:
                        print(log)
                except subprocess.CalledProcessError as e:
                    print(f"[SCI] Capture failed: {e}")
                
                last_run = time.time()
                run_time = last_run - start_time
                
                print(f"[SCI] Complete in {run_time:.2f}s")
                
                if run_time > 1/freq:
                    print("[SCI] WARNING: CAN NOT KEEP UP WITH REQUIRED FREQ")
        
        time.sleep(0.1)  # Small sleep to avoid busy-waiting
    
    print("[SCI] Science camera thread stopped")

def main():
    global running
    
    print("######## STARTING STATE-BASED CAMERA LOOP (THREADED) #########")
    print(f"State file: {state_file}")
    print(f"ST freq: {st_freq} Hz, SS freq: {ss_freq} Hz, Science freq: {sci_freq} Hz")
    print(f"State 1 -> SS | State 2 -> ST+SS | State 3 -> Science | State 0 -> idle")
    print("###############################################################")
    
    # Start camera threads
    ss_thread = threading.Thread(
        target=sun_sensor_loop,
        args=(state_file, root, ss_freq, printLog),
        daemon=True
    )
    
    st_thread = threading.Thread(
        target=star_tracker_loop,
        args=(state_file, root, st_freq, printLog),
        daemon=True
    )
    
    sci_thread = threading.Thread(
        target=science_camera_loop,
        args=(state_file, root, sci_freq, printLog),
        daemon=True
    )
    
    ss_thread.start()
    st_thread.start()
    sci_thread.start()
    
    # Main thread: just monitor state and keep alive
    try:
        while running:
            current_state = read_state(state_file)
            
            if current_state == -1:
                print("[MAIN] Waiting for state file from Simulink...")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down...")
        running = False
    
    # Wait for threads to finish
    ss_thread.join(timeout=2)
    st_thread.join(timeout=2)
    sci_thread.join(timeout=2)
    
    print("[MAIN] All threads stopped")


if __name__ == "__main__":
    
    st_freq = 0.5   # How frequently to run star tracker [Hz]
    ss_freq = 1     # How frequently to run sun sensor [Hz]
    sci_freq = 0.33 # How frequently to run science camera [Hz]
    
    printLog = True
    
    state_file = "/tmp/adcs_state.bin"
    
    #root = "/home/space584a/MATLAB_ws/R2025b/ADCS_python/"
    root = "./"
    
    main()