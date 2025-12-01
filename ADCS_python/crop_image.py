#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 12:32:19 2025

@author: atcushen

input: directory of jpg or png to convert to a pkl file, trimmed down to the area of interest
e.g.
<< python3 crop_image.py star_field_reference.jpg >>

"""

from PIL import Image
#import cvs
import numpy as np
import sys
import os
import time
#import pickle

def main():
    # Start timer
    start_time = time.perf_counter()
    
    # Get input file name
    input_file = sys.argv[1]
    
    # Load using pillow
    img = Image.open(input_file)
    img_array = np.array(img)
    #img_array = cv2.imread(input_file)
    

    # Print status
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print("Read image:",input_file,"with size:",np.shape(img_array),f"in : {elapsed_time:.4f} seconds")
    
    
    # Start timer
    start_time = time.perf_counter()
    
    # Flatten to greyscale, by summing
    img_array_bw = np.sum(img_array,axis=2)/3
    
    # Get image size
    pixel_width = np.shape(img_array_bw)[1]
    pixel_height = np.shape(img_array_bw)[0]
    
    # Find the index of the edges of the area to crop, based on horizontal axis
    w0 = int((img_wFOV/2 - FOV/2) * pixel_width /  img_wFOV)
    w1 = int((img_wFOV/2 + FOV/2) * pixel_width /  img_wFOV)
    nres = w1-w0
    
    # Work out hpow many pixels to shift the view up, to ensure stars are visible
    img_h_adjust_pixels = int(pixel_height / img_hFOV * img_h_adjust)
    
    # Find vertical range indices, ensuring the image is square
    h0 = pixel_height//2 - nres//2 + img_h_adjust_pixels 
    h1 = h0 + nres
    
    # Crop image
    img_array_bw_crop = img_array_bw[h0:h1,w0:w1]
    
    # Save image as pkl and jpg (for testing)
    output_file = str(input_file[:-3]+"npy")
    np.save(output_file,img_array_bw_crop[::-1,:])
        
    # Print status
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print("Saved cropped image:",output_file,"with size:",np.shape(img_array_bw_crop),f"and FOV {np.rad2deg(FOV):.2f} deg", f"in : {elapsed_time:.4f} seconds")
    

if __name__ == "__main__":
    
    # Define control parameters
    img_wFOV = np.deg2rad(102) # Total field of view of full image width [rad]
    img_hFOV = np.deg2rad(67) # Total field of view of full image width [rad]
    img_h_adjust = np.deg2rad(-11) # adjust the vertical frame of the image [rad] 
    FOV = np.pi/6 # Cropped image field of view [rad]
    
    if FOV>img_hFOV:
        print("WARNING: FIELD OF VIEW EXCEEDS RAW IMAGE")
    
    # Run script
    main()
    
