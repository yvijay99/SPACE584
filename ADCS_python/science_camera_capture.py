"""
Created on 11/07/2025

@author: Dane Goodman

Science camera image capture for Mars sphere observation.
Captures images using Raspberry Pi HQ Camera with 25mm lens.

Usage:
Single capture:
>> python3 science_camera_capture.py single /home/space584a/MATLAB_ws/R2025b/ADCS_python/
"""

import numpy as np
import sys
import os
import time
from picamera2 import Picamera2 # picamera2 package can only be run on Linux, may need to use secure shell (SSH) would need Pi's IP address
from libcamera import controls
import matplotlib.pyplot as plt
from scipy.io import savemat
from datetime import datetime


def initialize_camera(exposure_time=5000, analog_gain=2.0):
    """
    Initialize Raspberry Pi HQ Camera with optimal settings for object observation.

    Arguments:
        exposure_time (int): Exposure time in microseconds (default 5000 = 5ms)
        analog_gain (float): Analog gain multiplier (default 2.0)

    Returns:
        Picamera2: Configured camera object
    """
    start_time = time.perf_counter()

    picam2 = Picamera2()

    # Configure for high-quality still images
    config = picam2.create_still_configuration(
        main={"size": (4056, 3040)},  # Full 12.3MP resolution
        buffer_count = 2
    )
    picam2.configure(config)

    # Setting manual controls for consistent imaging
    picam2.set_controls({
        "ExposureTime": exposure_time,
        "AnalogueGain": analog_gain,
        "AeEnable": False,  # Disable auto-exposure
        "AwbEnable": False,  # Disable auto white balance
        "Sharpness": 1.5,  # Enhance sharpness for features
        "Contrast": 1.2,  # Improve contrast
        "Brightness": 0.0,  # Neutral brightness
        "Saturation": 1.0  # Normal saturation
    })

    # Starting camera
    picam2.start()

    # Allowing camera to stabilize
    time.sleep(2)

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Camera initialized in: {elapsed_time:.4f} seconds")
    print(f"Settings: Exposure={exposure_time}μs, Gain={analog_gain}")

    return picam2


def capture_single_image(picam2, output_directory, filename_prefix="mars_obs"):
    """
    Capture a single high-resolution image of the sphere.

    Arguments:
        picam2 (Picamera2): Initialized camera object
        output_directory (str): Directory to save images
        filename_prefix (str): Prefix for output files

    Returns:
        str: Path to captured image
        np.ndarray: Image array
    """
    start_time = time.perf_counter()

    # Generating timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    # Capturing image
    filename = f"{filename_prefix}_{timestamp}.jpg"
    filepath = os.path.join(output_directory, filename)

    # Uploading to file
    picam2.capture_file(filepath)

    # Also loading as numpy array for processing
    img_array = picam2.capture_array()

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"Captured image: {filename}")
    print(f"Size: {img_array.shape}, in {elapsed_time:.4f} seconds")

    return filepath, img_array

def process_image_to_npy(image_path, output_directory, target_fov=None):
    """
    Process captured image similar to crop_image.py workflow.
    Converts to grayscale and saves as .npy for analysis.

    Arguments:
        image_path (str): Path to input image
        output_directory (str): Directory for output
        target_fov (float): Target field of view in radians (optional)

    Returns:
        str: Path to .npy file
    """
    start_time = time.perf_counter()

    from PIL import Image

    # Load image
    img = Image.open(image_path)
    img_array = np.array(img)

    # Convert to grayscale (average of RGB channels)
    if len(img_array.shape) == 3:
        img_array_bw = np.sum(img_array, axis=2) / 3
    else:
        img_array_bw = img_array

    # Generating output filename
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_file = os.path.join(output_directory, f"{base_name}.npy")

    # Saving as numpy array
    np.save(output_file, img_array_bw)

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"Processed to .npy: {base_name}.npy in {elapsed_time:.4f}s")

    return output_file


def save_metadata(output_directory, capture_mode, image_paths, camera_settings):
    """
    Save capture metadata to .mat file for MATLAB integration.

    Arguments:
        output_directory (str): Output directory
        capture_mode (str): Mode used (single/timelapse/video)
        image_paths (list): List of captured image paths
        camera_settings (dict): Camera configuration used
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    metadata = {
        "capture_mode": capture_mode,
        "timestamp": timestamp,
        "unix_time": time.time(),
        "num_images": len(image_paths) if isinstance(image_paths, list) else 1,
        "image_files": image_paths,
        "exposure_time_us": camera_settings["exposure_time"],
        "analog_gain": camera_settings["analog_gain"],
        "focal_length_mm": FOCAL_LENGTH,
        "sensor_width_mm": SENSOR_WIDTH,
        "sensor_height_mm": SENSOR_HEIGHT,
        "image_width_px": IMAGE_WIDTH,
        "image_height_px": IMAGE_HEIGHT,
        "target_distance_m": TARGET_DISTANCE,
        "target_diameter_m": TARGET_DIAMETER
    }

    output_file = os.path.join(output_directory, f"mars_capture_metadata_{timestamp}.mat")
    savemat(output_file, metadata)

    print(f"\nMetadata saved: mars_capture_metadata_{timestamp}.mat")


def main():
    """
    Main execution function.
    """
    # Parsing command line arguments
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Single:    python3 science_camera_capture.py single <output_dir>")
        sys.exit(1)

    capture_mode = sys.argv[1].lower()
    output_directory = sys.argv[2]

    # Validating output directory
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created output directory: {output_directory}")

    print("\n###### SCIENCE CAMERA CAPTURE ######")
    print(f"Mode: {capture_mode.upper()}")
    print(f"Output: {output_directory}\n")

    # Initializing camera
    camera_settings = {
        "exposure_time": EXPOSURE_TIME,
        "analog_gain": ANALOG_GAIN
    }
    picam2 = initialize_camera(
        exposure_time=camera_settings["exposure_time"],
        analog_gain=camera_settings["analog_gain"]
    )

    try:
        # Executing based on mode
        if capture_mode == "single":
            filepath, img_array = capture_single_image(picam2, output_directory)
            image_paths = [filepath]

            # Processing to .npy
            if SAVE_NPY:
                process_image_to_npy(filepath, output_directory)

        else:
            print(f"Error: Unknown capture mode '{capture_mode}'")
            sys.exit(1)

        # Saving metadata
        save_metadata(output_directory, capture_mode, image_paths, camera_settings)

        print("\n###### CAPTURE COMPLETE ######\n")

    finally:
        # Cleaning up
        picam2.stop()
        picam2.close()
        print("Camera released.")


if __name__ == "__main__":
    # Camera specifications (Raspberry Pi HQ Camera + 25mm lens)
    FOCAL_LENGTH = 25.0  # mm
    SENSOR_WIDTH = 6.287  # mm (1/2.3" sensor)
    SENSOR_HEIGHT = 4.712  # mm
    IMAGE_WIDTH = 4056  # pixels
    IMAGE_HEIGHT = 3040  # pixels

    # Calculating FOV
    FOV_HORIZONTAL = 2 * np.arctan(SENSOR_WIDTH / (2 * FOCAL_LENGTH))  # radians
    FOV_VERTICAL = 2 * np.arctan(SENSOR_HEIGHT / (2 * FOCAL_LENGTH))  # radians

    # Target specifications
    TARGET_DISTANCE = 5.0  # meters
    TARGET_DIAMETER = 0.25  # meters

    # Camera settings
    EXPOSURE_TIME = 5000  # microseconds (5ms - prevents motion blur at 0.5 deg/s)
    ANALOG_GAIN = 2.0  # Adjust based on lighting

    # Processing options
    SAVE_NPY = True  # Save processed .npy files alongside JPG

    # Printing camera specs
    print(f"\nCamera Specifications:")
    print(f"  Focal Length: {FOCAL_LENGTH}mm")
    print(f"  Sensor: {SENSOR_WIDTH}mm × {SENSOR_HEIGHT}mm")
    print(f"  Resolution: {IMAGE_WIDTH} × {IMAGE_HEIGHT} px")
    print(f"  Horizontal FOV: {np.rad2deg(FOV_HORIZONTAL):.2f}°")
    print(f"  Vertical FOV: {np.rad2deg(FOV_VERTICAL):.2f}°")
    print(
        f"  GSD at {TARGET_DISTANCE}m: {(SENSOR_WIDTH / IMAGE_WIDTH * TARGET_DISTANCE / FOCAL_LENGTH) * 1000:.3f} mm/pixel")

    main()
