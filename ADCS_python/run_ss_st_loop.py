#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 14:10:31 2025

@author: alexandercushen
"""

#from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import os
import time
import numpy as np
import subprocess
import sun_sensor
import sys

def main():
    
    print("######## STARTING SUN SENSOR (SS) AND STAR TRACKER (ST) SENSOR LOOPS #########")
    
    start_time = time.time()
    
    ss_last_run = start_time
    st_last_run = start_time
    
    run = True
    
    while run:
        
        loop_start_time = time.time()
        
        # Attempt to run sun sensor
        if loop_start_time-ss_last_run > 1/ss_freq:
            
            print(round(loop_start_time-ss_last_run,2),"s elapsed since last sun sensor run, executing now...")
            
            ss_start_time = time.time()
            
            # TAKE PHOTO
            log = subprocess.run(
                [sys.executable, "ir_camera_take_picture.py"],
                capture_output=True,
                text=True,
                check=False)
            
            if printLog:
                print(log)
            
            
            # RUN ANALYSIS
            log = subprocess.run(
                [sys.executable, str(root+"sun_sensor.py"), root],
                capture_output=True,
                text=True,
                check=True)
            
            if printLog:
                print(log)
                
            ss_last_run = time.time()
            ss_run_time = ss_last_run-ss_start_time
            
            print(f"Sun sensor execution complete in {ss_run_time:.2f} s")
            
            if ss_run_time > 1/ss_freq:
                
                print("WARNING: SS CAN NOT KEEP UP WITH REQUIRED RUN FREQ.")
            
        
        # Attempt to run star tracker
        if loop_start_time-st_last_run > 1/st_freq:
            
            print(round(loop_start_time-st_last_run,2),"s elapsed since last star tracker run, executing now...")
            
            st_start_time = time.time()
            
            # TAKE PHOTO
            
            shutter_time = 0.1 # [s]
            shutter_str = str(int(shutter_time * 1000000))
            cmd = 'rpicam-still -o '+root+'star_field.jpg --shutter '+shutter_str+' --gain 1 --awbgains 1,1 --immediate --camera 1 --rotation 180'
            log = os.system(cmd)
            
            if printLog:
                print(log)
            
            
            # CROP IMAGE
            log = subprocess.run(
                [sys.executable, "crop_image.py", str(root+"star_field.jpg")],
                capture_output=True,
                text=True,
                check=True)
            
            if printLog:
                print(log)
                
            # RUN ANALYSIS
            log = subprocess.run(
                [sys.executable, "star_tracker.py", root],
                capture_output=True,
                text=True,
                check=True)
            
            if printLog:
                print(log)
            
                
            st_last_run = time.time()
            st_run_time = st_last_run-st_start_time
            
            print(f"Star tracker execution complete in {st_run_time:.2f} s")
            
            if st_run_time > 1/st_freq:
                
                print("WARNING: ST CAN NOT KEEP UP WITH REQUIRED RUN FREQ.")
        
        time.sleep(np.min([1/st_freq,1/ss_freq])/2)

        
if __name__ == "__main__":
    
    st_freq = 0.5 # How frequently to run star tracker [Hz]
    ss_freq = 1 # How frequently to run star tracker [Hz]
    
    printLog = True
    
    #root = "/home/space584a/MATLAB_ws/R2025b/ADCS_python/"
    root = "./"
    
    main()
    
    
    
    