#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 14:46:16 2025

@author: atcushen

Read in star_field.npy image, and reference data in star_table.npy and star_distances.npy, to determine the attitude of the star camera field of view

Requires the directory where the file is running, so it knows where to look for the files to load
e.g.
For local *run in current directory):
>> python3 star_tracker.py ./
For rpi deployment:
>> python3 /home/space584a/MATLAB_ws/R2025b/ADCS_python/star_tracker.py /home/space584a/MATLAB_ws/R2025b/ADCS_python/

"""

import numpy as np
import sys
import os
import time
from skimage.measure import label, regionprops
import matplotlib.pyplot as plt
from scipy.io import savemat
from datetime import datetime

def main():
    
    # List files
    '''
    entries = os.listdir('.')

    print(f"Contents of the current directory ({os.getcwd()}):")
    for entry in entries:
        full_path = os.path.join('.', entry)
        if os.path.isdir(full_path):
            print(f"📁 Directory: {entry}")
        elif os.path.isfile(full_path):
            print(f"📄 File:      {entry}")
        else:
            # Handles symlinks or other file types
            print(f"❓ Other:     {entry}")
    '''
    
    print('###### RUNNING STAR TRACKER ANALYSIS ######')
    
    input_directory = sys.argv[1]
    
    start_time = time.perf_counter()
    
    # Load in data
    st_im = np.load(str(input_directory+'star_field.npy'))
    star_table = np.load(str(input_directory+'star_table.npy'))
    star_distances = np.load(str(input_directory+'star_distances.npy'))
    
    # Print status
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Loaded the star_field image, star_table, and star_distances in : {elapsed_time:.4f} seconds")
    
    
    
    start_time = time.perf_counter()
    
    # Find stars
    star_ls, phi_positions, theta_positions = identify_stars(st_im, FOV)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Found {len(star_ls):.0f} stars in: {elapsed_time:.4f} seconds")
    
    
    
    start_time = time.perf_counter()
    
    # Begin plotting
    fig,ax = plt.subplots(figsize=(10,10))
    
    ax.imshow(st_im, origin='lower', cmap='Greys_r',extent = [phi_positions[0],phi_positions[-1],theta_positions[0],theta_positions[-1]])
    ax.scatter(star_ls[:,0],star_ls[:,1], s = 50, linewidths=0.5, marker='o', facecolors='none', edgecolors='yellow',label = 'identified stars')
    for istar,star in enumerate(star_ls):
        ax.text(star[0],star[1]+0.005,istar,color='white',fontsize=8)
    
    # Match to table
    star_num, deltaphi, deltatheta, ax = match_to_lookup(star_ls, star_pos_error, star_distances, ax)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Identified star num. {star_num:.0f} to be offset by {deltaphi:.3f},{deltatheta:.3f} from camera boresight in: {elapsed_time:.4f} seconds")
    
    
    
    # Determine phi_st
    phi_st = star_table[star_num,0] - deltaphi;


    # Finish plot
    ax.set_xlabel(r"$\delta \phi$ [rad]")
    ax.set_ylabel(r"$\delta \theta$ [rad]")
    
    ax.legend(loc='lower right')
    ax.set_title(str("Star tracker analysis, $\phi_{ss}$ = "+f"{phi_st:.4f}"))
    
    if savePlot:
        plt.savefig(str(input_directory+"star_tracker_analysis.jpg"), dpi=200)
        
    plt.close()
        
    
    # Save attitude for matlab to read
    phi_st = np.array([phi_st], dtype=np.float64) # Use float64 for standard MATLAB 'double' precision

    data_dict = {"phi_st": phi_st,"t": time.time()} # Save Unix Epoch Time (seconds since 1970)

    output_file = "phi_st.mat"
    savemat(str(input_directory+output_file), data_dict)
    
    print("Attitude is determined to be: phi_st =", round(phi_st.item(),5),", and is saved to:", output_file)
    
    
    return phi_st
    
def identify_stars(st_im, FOV):
    """
    Identifies stars in a star tracker image and returns their phi/theta positions.

    Args:
        st_im (np.ndarray): nxn array, representing image from star tracker.
        FOV (float): field of view along each edge of image.

    Returns:
        np.ndarray: nx2 array, the phi and theta positions (relative to the
                    center of the image) for each star identified.
    """
    
    # Get image dimensions (equivalent to [theta_nres, phi_nres] = size(st_im))
    theta_nres, phi_nres = st_im.shape
    if theta_nres != phi_nres:
        print("WARNING: IMAGE IS NOT SQAURE")
    
    # Convert coordinates to phi and theta positions
    phi_positions = np.linspace(-FOV / 2, FOV / 2, phi_nres)
    theta_positions = np.linspace(-FOV / 2, FOV / 2, theta_nres)
    
    # Identify bright points in the star tracker image
    # Note: Using 0.4 * 255 assumes your input image is uint8 (0-255 range).
    threshold_value = 0.2 * 255 
    
    # Create filtered image (boolean mask)
    filtered_im = st_im > threshold_value

    # Find connected components and create label matrix
    label_matrix = label(filtered_im, connectivity=2)

    # Find regions and compute centroids
    regions = regionprops(label_matrix)

    # Create output array for star positions
    star_ls = np.zeros((len(regions), 2))
    
    # Iterate through each connected component
    for istar, region in enumerate(regions):
        # The centroid coordinates are (row_index, col_index) or (y_coord, x_coord)
        # These are *pixel indices*, which we need to map back to phi/theta space.
        y_centroid_index, x_centroid_index = region.centroid
        
        # Map indices to the actual phi and theta positions using our linspace arrays
        # We access the continuous position arrays using the rounded integer indices
        
        # Note: Centroid indices are floats, so we round them to find the closest pixel position index
        phi_coord = phi_positions[int(round(x_centroid_index))]
        theta_coord = theta_positions[int(round(y_centroid_index))]
        
        # Store the average position of the cluster
        # MATLAB indices are [row, col], which mapped to phi (x) and theta (y)
        star_ls[istar, 0] = phi_coord   # Average phi coordinate (x-axis)
        star_ls[istar, 1] = theta_coord # Average theta coordinate (y-axis)
        
    return star_ls, phi_positions, theta_positions 

def match_to_lookup(star_ls, star_pos_error, star_lookup, ax):
    """
    Input
    star_ls: nx2 array, the phi and theta positions (relative to the
    center of the image) for each star identified
    star_pos_error: float, angular uncertainty in position of stars
    star_lookup: nx_angle array, each row corresponds to given row in
    star_table, columns are angular distances to closest stars

    Output
    star_num: integer, index number of matched star
    deltaphi: float, offset in phi of matched star from image center, in
    radians
    deltatheta: float, offset in phi of matched star from image center,
    in radians
    """

    # Iterate through stars in image, starting closest to middle, until we
    # get a positive match
    star_match = False
    
    # Calculate the sum of squares for each star position
    star_ls_dist = np.sum(star_ls**2, axis=1)
    
    # Sort the star_ls based on the sum of squares
    sorted_indices = np.argsort(star_ls_dist)
    star_ls = star_ls[sorted_indices, :]

    istar = 0
    
    fail_label = 'Failed Matches'
    
    while not star_match and istar < len(star_ls):
        # Compute distances to other stars
        phi_diff = star_ls[istar, 0] - star_ls[:, 0]
        theta_diff = star_ls[istar, 1] - star_ls[:, 1]
        angle_diff = np.sqrt(phi_diff**2 + theta_diff**2)

        # Sort the computed angular distances from smallest to largest
        sorted_indices_angle = np.argsort(angle_diff)
        sorted_angles = angle_diff[sorted_indices_angle]
        
        # Drop the first element of sorted_angles (distance to itself = 0)
        sorted_angles = sorted_angles[1:]

        # Reduce sorted angles to only be as long as star_lookup is wide
        num_lookup_angles = star_lookup.shape[1]
        sorted_angles = sorted_angles[:min(len(sorted_angles), num_lookup_angles)]

        # Create an array of stars within the positional error range
        # Note: star_lookup[:, 0] is the first column of the lookup table
        match_indices = (star_lookup[:, 0] >= (sorted_angles[0] - star_pos_error)) & \
                        (star_lookup[:, 0] <= (sorted_angles[0] + star_pos_error))
        
        matched_stars = star_lookup[match_indices, :]

        # Check if that immediately identified the current state. 
        # If not, compare the angular distances one by one, bringing in more to
        # reduce the number of remaining options
        iangle = 1 # Python uses 0-based indexing, so iangle=1 corresponds to the 2nd angle

        while matched_stars.shape[0] > 1 and iangle < star_lookup.shape[1]:
            print('Found multiple matches, refining to next angle')
            
            # We loop through the remaining matches
            # Create a copy of match_indices as an editable list/array
            match_indices_list = match_indices.tolist()
            
            for j in range(len(match_indices_list)):
                if match_indices_list[j]: # Check only currently matched stars
                    # Check to see if the next closest star is within error of
                    # any of the neighbouring stars listed in the lookup table
                    # If none of the angles are close enough, then reject this
                    # match
                    
                    # MATLAB's star_lookup(j, iangle:end) is star_lookup[j, iangle:] in Python
                    # Python's iangle is 1 here (second angle)
                    lookup_angles_remaining = star_lookup[j, iangle:]
                    
                    # Ensure sorted_angles has the iangle element available
                    if iangle < len(sorted_angles):
                        current_sorted_angle = sorted_angles[iangle]
                        
                        # Check if ANY angle in the lookup range is close enough to the sorted angle
                        if not np.any(np.abs(lookup_angles_remaining - current_sorted_angle) <= star_pos_error):
                            match_indices_list[j] = False # Reject this match
            
            match_indices = np.array(match_indices_list)
            matched_stars = star_lookup[match_indices, :]
        
            iangle += 1
        
        # Check if we could use this star 
        if matched_stars.shape[0] != 1:
            print(f'Could not find lookup table match for istar {istar:.0f}, moving to the next one')
            ax.scatter(star_ls[istar,0],star_ls[istar,1], s = 50, linewidths=0.6, marker='o', facecolors='none', edgecolors='red',label = fail_label)
            istar += 1 # Move to the next star
            fail_label=''
        else:
            # Get the original row number of the matched star
            # np.where returns a tuple of arrays, the first element has the indices
            star_num = np.where(match_indices)[0][0] 
            deltaphi = star_ls[istar, 0] # Offset in phi
            deltatheta = star_ls[istar, 1] # Offset in theta
            star_match = True
            ax.scatter(star_ls[istar,0],star_ls[istar,1], s = 60, linewidths=1, marker='o', facecolors='none', edgecolors='green',label = 'successful match')
            ax.scatter(star_ls[istar,0],star_ls[istar,1], s = 200, linewidths=2, marker='o', facecolors='none', edgecolors='green')
            print(f'Matched with istar {istar} as star #{star_num}, and it is offset {deltaphi:.4f} radians in phi and {deltatheta:.4f} radians in theta from boresight')
    
    # Return error if star tracker failed 
    if not star_match:
        print('Star tracker failed, unable to get a lock on any star.')
        star_num = -1
        deltaphi = np.nan
        deltatheta = np.nan
    
    return star_num, deltaphi, deltatheta, ax

if __name__ == "__main__":
    
    FOV = np.pi/6
    img_wFOV = np.deg2rad(102) # Total field of view width of starfield reference image [rad]
    nwpx = 4608 # How many pixels wide the full starfield reference image is
    star_pos_error = 10*img_wFOV/nwpx;
    
    savePlot = True
    
    main()