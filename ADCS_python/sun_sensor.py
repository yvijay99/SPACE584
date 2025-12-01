#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 11:01:47 2025

@author: atcushen

Load in "ir_picture.jpg" from the directory passed  after the function call, determine whether the sun is in view, and if so, determine the attitude of the IR camera.
The sun is assumed to be at phi=0

"""

from PIL import Image
import numpy as np
import sys
import os
import time
import matplotlib.pyplot as plt
from scipy.io import savemat
from datetime import datetime

def main():
    
    print('###### RUNNING SUN SENSOR ANALYSIS ######')
    
    # Load jpg from command argument
    
    start_time = time.perf_counter()
    
    input_directory = sys.argv[1]
    
    #img = Image.open(str(input_directory+'ir_picture.jpg'))
                     
    #img_array = np.asarray(img)
    
    img_array = np.load(str(input_directory+'ir_data_array.npy'))
    
    img_array_filtered = np.copy(img_array)
    
    # Print status
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    #print(f"Loaded",str(input_directory+'ir_picture.jpg'),f"in : {elapsed_time:.4f} seconds")
    print(f"Loaded",str(input_directory+'ir_data_array.npy'),f"in : {elapsed_time:.4f} seconds")
    
    
    # Process the image
    
    start_time = time.perf_counter()
    
    # Set threshold; cells dimmer than this will be assumed to not be the sun
    cutoff_brightness = 0.90 * sun_brightness
    img_array_filtered[img_array<cutoff_brightness] = 0
    
    # Get dimensions of the image
    [theta_res,phi_res] = img_array_filtered.shape;
    
    # Sum img_array along columns to get the total pixel brightness in each column
    col_brightness = np.sum(img_array_filtered, 0)
    
    # Print status
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    if np.max(col_brightness)>0:
        try_to_find_sun = True
        print(np.sum(img_array_filtered>0)," bright pixels detected in",theta_res,"x",phi_res,f"image, in : {elapsed_time:.4f} seconds")
    else:
        try_to_find_sun = False
        print("No bright pixels detected in",theta_res,"x",phi_res,f"image, in : {elapsed_time:.4f} seconds, aborting...")
        phi_ss = np.nan
    
    # Locate the sun
    
    if try_to_find_sun:
    
        start_time = time.perf_counter()

        # Initialize flags
        adjacent_found = False
        multiple_adjacents = False
        n = len(col_brightness)
        
        # Check for adjacent entries in col_brightness greater than zero
        for i in range(n - 1):
            if col_brightness[i] > 0 and col_brightness[i+1] > 0:
                if adjacent_found and col_brightness[i-1] == 0:
                    multiple_adjacents = True
                else:
                    adjacent_found = True
            # Optimization: if multiple adjacencies are already found, we can break early
            if multiple_adjacents:
                break
        
        # Display errors      
        if np.sum(col_brightness>0) > phi_res/2:
            print('ERROR: Sun too close, taking up too much of the frame')
            phi_ss = np.nan  # Return NaN if no adjacent entries are found
        
        elif multiple_adjacents:
            print('ERROR: Multiple sun-like clusters found, cannot identify the sun')
            phi_ss = np.nan  # Return NaN if multiple adjacent entries are found

        elif not adjacent_found:
            # print('ERROR: No sun found in frame')
            # phi_ss = np.nan  # Return NaN if no adjacent entries are found
            print('WARNING: No adjacent found, using 1 pixel sun')

            # Iterate over the indices of col_brightness that are greater than zero
            sun_indices = np.where(col_brightness > 0)[0]
            # Get the brightness-weighted pixel location of the sun
            weighted_sum = np.sum(col_brightness[sun_indices] * sun_indices)
            brightness_sum = np.sum(col_brightness[sun_indices])

            sun_pixel_loc = weighted_sum / brightness_sum
        
            # Determine phi_ss from this relative position
            phi_ss = sun_phi - ((sun_pixel_loc / phi_res) * ss_phi_FOV - ss_phi_FOV / 2)
            
        else:
            # Iterate over the indices of col_brightness that are greater than zero
            sun_indices = np.where(col_brightness > 0)[0]
        
            # Get the brightness-weighted pixel location of the sun
            weighted_sum = np.sum(col_brightness[sun_indices] * sun_indices)
            brightness_sum = np.sum(col_brightness[sun_indices])
            
            sun_pixel_loc = weighted_sum / brightness_sum
        
            # Determine phi_ss from this relative position
            phi_ss = sun_phi - ((sun_pixel_loc / phi_res) * ss_phi_FOV - ss_phi_FOV / 2)

        # Print status
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print(f"Sun search complete in : {elapsed_time:.4f} seconds, phi_ss = {phi_ss:.4f}")
    
    if savePlot:
        
        fig,axs = plt.subplots(ncols = 2, figsize = (20,10))
        
        axs1_1 = axs[1].twinx()
        
        axs[0].imshow(img_array, origin='lower', vmin = sun_brightness*0.8, vmax = sun_brightness*1.1, cmap='Greys_r')
        axs[0].set_title("Raw IR image")
        axs[0].set_aspect(1)
        
        axs[1].imshow(img_array_filtered, origin='lower', extent = [-ss_phi_FOV/2,ss_phi_FOV/2,-ss_theta_FOV/2,ss_theta_FOV/2], 
                      vmin = 0, vmax = sun_brightness)
        axs[1].axvline(x=(sun_phi-phi_ss), color='red')
        axs[1].set_xlabel(r"$\delta \phi$ [rad]")
        axs[1].set_ylabel(r"$\delta \theta$ [rad]")
        axs[1].grid()
        axs[1].set_aspect(1)
        axs[1].set_ylim(-ss_theta_FOV/2,ss_theta_FOV/2)
        
        axs1_1.plot(np.linspace(-ss_phi_FOV/2,ss_phi_FOV/2, phi_res), col_brightness/(theta_res*sun_brightness), color='white')
        axs1_1.set_ylim(-1,2)      
    
        axs[1].set_title(str(r"Sun sensor analysis, $\phi_{ss}$ = "+str(round(phi_ss,4))))
        
        if savePlot:
            plt.savefig(str(input_directory+"sun_sensor_analysis.jpg"), dpi=200)
            
        plt.close()
        
        # Save attitude for matlab to read
        phi_st = np.array([phi_ss], dtype=np.float64) # Use float64 for standard MATLAB 'double' precision

        data_dict = {"phi_ss": phi_ss,"t": time.time()} # Save Unix Epoch Time (seconds since 1970)

        output_file = "phi_ss.mat"
        savemat(str(input_directory+output_file), data_dict)
        
        print("Attitude is determined to be: phi_st =", round(phi_st.item(),5),", and is saved to:", output_file)
        
        return phi_ss

if __name__ == "__main__":
    
    ss_bit_depth = 255 # No longer used, as we stopped using normalized images
    sun_brightness = 30 # Pixel brightness of sun.
    sun_phi = -0.32
    ss_phi_FOV = np.deg2rad(55) 
    ss_theta_FOV = np.deg2rad(35) 
    
    savePlot = True
    
    phi_ss = main()
