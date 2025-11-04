#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 14:16:22 2025

@author: atcushen

Reads in a .csv describing the pixel locations of all stars in the star_field_reference image,
outputs a table of their locations shifted to center x0,y0, in radians, saved as star_table.npy
Also produce the distance table of each star to its nangle nearest neighbours, saved as star_distances.npy

e.g.
<< python3 generate_star_tables.py star_table_pixel_loc.csv >>

"""

import numpy as np
import sys
import os
import time

def main():
    
    start_time = time.perf_counter()
    
    # Get input file name
    input_file = sys.argv[1]
    
    # Read in .csv
    pixel_table = np.loadtxt(input_file, delimiter=',', skiprows=1)
    
    # Index the first column of the pixel_table to get the phi positions
    phi_positions = (pixel_table[:, 0]-x0) * np.pi/180 * img_wFOV/nwpx;
    
    # Index the second column of the pixel_table to get the theta positions
    theta_positions = (pixel_table[:, 1]-y0) * np.pi/180 * img_hFOV/nhpx;

    # Combine the phi, theta, and brightness into the star_table
    star_table = np.array([phi_positions, theta_positions]).T
    
    # Save as .npy 
    # Save image as pkl and jpg (for testing)
    output_file = "star_table.npy"
    np.save(output_file, star_table) 
        
    # Print status
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print("Saved startable:",output_file,"with size:",np.shape(star_table), f"in : {elapsed_time:.4f} seconds")
    
    # Compute lookup table
    start_time = time.perf_counter()
    star_lookup = np.zeros((star_table.shape[0], nangle))
    
    # Iterate through each star in the table
    for istar in range(len(star_table)):
        # Get the current star's coordinates [phi, theta]
        current_star_coords = star_table[istar, :]
        
        # Compute the angular distances from the current star to all other stars
        phi_diff = current_star_coords[0] - star_table[:, 0]
        theta_diff = current_star_coords[1] - star_table[:, 1]
        
        angle_diff = np.sqrt(phi_diff**2 + theta_diff**2)
    
        # Sort the angular distances
        sorted_angles = np.sort(angle_diff)
    
        # Calculate the upper bound for the slice dynamically
        upper_bound = min(nangle + 1, len(sorted_angles))
        
        star_lookup[istar, :] = sorted_angles[1:upper_bound]
        
    # Save as .npy 
    # Save image as pkl and jpg (for testing)
    output_file = "star_distances.npy"
    np.save(output_file, star_lookup) 
        
    # Print status
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print("Saved startable:",output_file,"with size:",np.shape(star_lookup), f"in : {elapsed_time:.4f} seconds")
    

if __name__ == "__main__":
    
    # Define control parameters
    img_wFOV = np.deg2rad(102) # Total field of view width of starfield reference image [rad]
    img_hFOV = np.deg2rad(67) # Total field of view height of starfield reference image [rad]
    nwpx = 4608 # How many pixels wide the full starfield reference image is
    nhpx = 2592 # How many pixels wide the full starfield reference image is
    x0 = 3270 # phi-pixel coord of reference to use at theta=0
    y0 = 1608 # theta-pixel coord of rerence to use at theta = 0
    nangle = 10 # How many distances to neighbouring stars to compute per star
    
    # Run script
    main()

