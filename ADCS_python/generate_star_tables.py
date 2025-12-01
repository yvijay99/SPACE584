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
import matplotlib.pyplot as plt
from PIL import Image

def main():
    
    start_time = time.perf_counter()
    
    # Get input file name
    input_file = sys.argv[1]
    
    # Read in .csv
    pixel_table = np.loadtxt(input_file, delimiter=',', skiprows=1)
    
    # Index the first column of the pixel_table to get the phi positions
    phi_positions = (pixel_table[:, 0]-x0) * img_wFOV/nwpx;
    
    # Index the second column of the pixel_table to get the theta positions
    theta_positions = (pixel_table[:, 1]-y0) * img_hFOV/nhpx;

    # Combine the phi, theta, and brightness into the star_table
    star_table = np.array([phi_positions, theta_positions]).T
    
    # STARS TO REMOVE
    remove_ls = [13,17,24,25,43,45]
        
    star_table = np.delete(star_table, remove_ls, axis=0)
    
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
    
    '''
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
    '''
    # Update: the sign of the distance value indicates whether star is above or below istar
    for istar in range(len(star_table)):
        # Get the current star's coordinates [phi, theta]
        current_star_coords = star_table[istar, :]
        
        # Compute the angular distances from the current star to all other stars
        phi_diff =  star_table[:, 0] - current_star_coords[0]
        theta_diff = star_table[:, 1] - current_star_coords[1]
        angle_diff = np.sqrt(phi_diff**2 + theta_diff**2)
        
        # Assign the sign to each star
        for i in range(len(theta_diff)):
            if theta_diff[i] > 0:
                angle_diff[i] = angle_diff[i] * (-1)
    
        # Sort the computed angular distances from smallest to largest
        sorted_indices_angle = np.argsort(np.abs(angle_diff))
        sorted_angles = angle_diff[sorted_indices_angle]
        
        star_lookup[istar, :] = sorted_angles[1:nangle+1]
        
    
    # Save as .npy 
    # Save image as pkl and jpg (for testing)
    output_file = "star_distances.npy"
    np.save(output_file, star_lookup) 
    
    # Save reference pic
    # Load using pillow
    img = Image.open("star_field_reference.jpg")
    img_array = np.array(img)

    # Flatten to greyscale, by summing
    img_array_bw = np.sum(img_array,axis=2)/3
    
    fig,ax = plt.subplots(figsize=(40,20))
    dphi = (x0-nwpx//2) * (img_wFOV/nwpx)
    dtheta = (y0-nhpx//2) * (img_hFOV/nhpx)
    ax.imshow(img_array_bw,cmap = 'Greys_r',vmin=0,vmax=255, extent = [-img_wFOV/2-dphi,img_wFOV/2-dphi,-img_hFOV/2-dtheta,img_hFOV/2-dtheta])
    ax.scatter(star_table[:,0],star_table[:,1], s = 50, linewidths=0.5, marker='o', facecolors='none', edgecolors='yellow',label = 'identified stars')
    ax.grid()
    ax.set_aspect(1)
    ax.locator_params(axis='x', nbins=25)
    for istar,star in enumerate(star_table):
        ax.text(star[0]+0.001,star[1]+0.001,str(f"#{istar:.0f}"), color='white', fontsize=4)
        
    # Show distances to star# itarget
    itarget = 22
    for istar,star in enumerate(star_table):
        if istar!=44:
            ax.plot([star[0],star_table[itarget,0]], [star[1],star_table[itarget,1]], color='darkgoldenrod',lw=0.1)
            # Compute distances to other stars
            phi_diff = star[0] - star_table[itarget,0]
            theta_diff = star[1] - star_table[itarget,1]
            angle_diff = np.sqrt(phi_diff**2 + theta_diff**2)
            if theta_diff>0:
                angle_diff = angle_diff*(-1)
            ax.text(np.mean([star[0],star_table[itarget,0]]),np.mean([star[1],star_table[itarget,1]]), f"{angle_diff:.3f}", color='white',fontsize=4)
    
        
    plt.savefig("star_field_labelled_reference.png", bbox_inches = 'tight', dpi = 200)
        
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
    x0 = 3333 # phi-pixel coord of reference to use at theta=0
    y0 = 1651 # theta-pixel coord of rerence to use at theta = 0
    nangle = 10 # How many distances to neighbouring stars to compute per star
    
    # Run script
    main()

