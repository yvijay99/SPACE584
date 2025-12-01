#!/usr/bin/env python3
"""
Actuator Controller
Receives commands from Simulink via UDP, drives reaction wheel and magnetorquers.

Packet format (10 bytes, little-endian):
    - RW duty cycle: double (8 bytes), 0-100
    - MT1 enable: bool (1 byte)
    - MT2 enable: bool (1 byte)

GPIO assignments:
    - RW PWM:  GPIO 18 (pin 12)
    - MT1:     GPIO 17 (pin 11)
    - MT2:     GPIO 27 (pin 13)
"""

import RPi.GPIO as GPIO
import socket
import struct
import time

# ---------------------
# CONFIGURATION
# ---------------------
UDP_IP = "192.168.0.117"
UDP_PORT = 5006
PACKET_SIZE = 10

# GPIO pins
RW_PIN = 18
MT1_PIN = 17
MT2_PIN = 27

# ESC settings
PWM_FREQ = 50
MIN_US = 1000
MAX_US = 2000

# ---------------------
# SETUP
# ---------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(RW_PIN, GPIO.OUT)
GPIO.setup(MT1_PIN, GPIO.OUT)
GPIO.setup(MT2_PIN, GPIO.OUT)

# Initialize PWM for reaction wheel
pwm = GPIO.PWM(RW_PIN, PWM_FREQ)
pwm.start(0)

# Initialize magnetorquers OFF
GPIO.output(MT1_PIN, GPIO.LOW)
GPIO.output(MT2_PIN, GPIO.LOW)

def set_throttle(pct):
    """Set reaction wheel throttle (0-100%)"""
    pct = max(0, min(100, pct))
    pulse_us = MIN_US + (pct / 100) * (MAX_US - MIN_US)
    duty = (pulse_us / 20000.0) * 100.0
    pwm.ChangeDutyCycle(duty)
    return pulse_us

def set_magnetorquers(mt1, mt2):
    """Set magnetorquer relay states"""
    GPIO.output(MT1_PIN, GPIO.HIGH if mt1 else GPIO.LOW)
    GPIO.output(MT2_PIN, GPIO.HIGH if mt2 else GPIO.LOW)

# ---------------------
# MAIN LOOP
# ---------------------
def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(1.0)  # 1 second timeout for status prints
    
    print("=" * 45)
    print("  ADCS Actuator Controller")
    print(f"  Listening on {UDP_IP}:{UDP_PORT}")
    print(f"  RW: GPIO {RW_PIN}, MT1: GPIO {MT1_PIN}, MT2: GPIO {MT2_PIN}")
    print("=" * 45)
    
    # Arm ESC
    print("Arming ESC...")
    set_throttle(0)
    time.sleep(2)
    print("Ready.")
    
    packet_count = 0
    last_print = time.time()
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(PACKET_SIZE)
                
                if len(data) == PACKET_SIZE:
                    rw_duty, mt1, mt2 = struct.unpack('<d??', data)

                    pulse = set_throttle(rw_duty * 100)  # Scale 0-1 to 0-100
                
                    set_magnetorquers(mt1, mt2)
                    
                    packet_count += 1
                    
                    # Print status every second
                    if time.time() - last_print >= 1.0:
                        mt1_str = "ON" if mt1 else "OFF"
                        mt2_str = "ON" if mt2 else "OFF"
                        print(f"[{packet_count}] RW: {rw_duty:5.1f}% ({pulse:.0f}us) | MT1: {mt1_str} | MT2: {mt2_str}")
                        last_print = time.time()
                else:
                    print(f"[WARN] Bad packet size: {len(data)} bytes")
                    
            except socket.timeout:
                # No packet received, just continue
                pass
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        set_throttle(0)
        set_magnetorquers(False, False)
        pwm.stop()
        GPIO.cleanup()
        print("Cleanup complete.")

if __name__ == "__main__":
    main()