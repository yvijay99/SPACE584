import time
import board
import busio
import numpy as np
import adafruit_mlx90640
from PIL import Image


def main():
    
    i2c = busio.I2C(board.SCL, board.SDA)
    
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    
    frame = [0] * 768
    
    try:
    	mlx.getFrame(frame)
    except ValueError:
    	time.sleep(0.1)
    	mlx.getFrame(frame)
    	
    data_array = np.array(frame).reshape((24,32))
    
    normalized = (data_array - np.min(data_array)) / (np.max(data_array) - np.min(data_array))
    image_8 = np.uint8(normalized * 255)
    image = Image.fromarray(image_8)
    
    image.save("/home/space584a/MATLAB_ws/R2025b/ADCS_python/ir_picture.jpg")

if __name__ == "__main__":
    
    main()