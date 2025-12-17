# CubeSat Attitude Determination and Control System 

**SPACE584 - Spacecraft Engineering Project**

An integrated attitude determination and control system for our CubeSat, integrating dual IMU sensors, reaction wheels, magnetorquers, star tracker, and sun sensor algorithms. The system uses an Arduino for sensor data collection and a Raspberry Pi running Simulink-generated Extended Kalman Filter algorithms for real-time attitude estimation and control.

---

## Repository Structure

```
├── ADCS_python/                    # Python scripts for Raspberry Pi
├── resources/project/              # Project resources and documentation
├── yukti_arduino_comms_ert_rtw/    # Simulink-generated C code for embedded deployment
├── arduinoICM20948.ino             # Arduino firmware for dual ICM-20948 IMU data collection
├── magcalibration.ino              # Arduino sketch for magnetometer calibration
├── yukti_arduino_comms.slx         # Main Simulink model (EKF, control logic, state machine)
├── yukti_arduino_comms.elf         # Compiled executable for Raspberry Pi
└── SPACE584.prj                    # MATLAB project file
```

---

## Hardware Architecture

| Component | Description |
|-----------|-------------|
| **Arduino** | Sensor interfacing and binary packet assembly |
| **Raspberry Pi** | Kalman filter processing and actuator control |
| **ICM-20948 IMU (x2)** | 9-DoF IMU with gyroscope, accelerometer, and magnetometer |
| **Reaction Wheels** | Fine attitude control via ESC-driven motors |
| **Magnetorquers** | Coarse detumbling using magnetic torque rods |
| **Star Tracker Camera** | Precision attitude determination |
| **Sun Sensor Camera** | Coarse sun vector determination |
| **Science Camera** | Payload imaging |

---

## File Descriptions

### Arduino Firmware

| File | Description |
|------|-------------|
| `arduinoICM20948.ino` | Main Arduino firmware that reads dual ICM-20948 IMUs via I2C, assembles 86-byte binary packets, and transmits to Raspberry Pi at 115200 baud. Implements time-multiplexed magnetometer readings to avoid I2C address conflicts. |
| `magcalibration.ino` | Calibration routine for magnetometer hard-iron and soft-iron compensation. Used inside Helmholtz coil for controlled calibration environment. |

### Simulink Model & Generated Code

| File | Description |
|------|-------------|
| `yukti_arduino_comms.slx` | Main Simulink model containing Extended Kalman Filter, state machine (Detumble → Coarse → Fine → Science), actuator control logic, and serial packet parsing. |
| `yukti_arduino_comms.slx.original` | Backup of original integrated ADCS model. |
| `yukti_arduino_comms.elf` | Compiled executable generated from Simulink for Raspberry Pi deployment. |
| `yukti_arduino_comms_ert_rtw/` | Auto-generated C code from Simulink Embedded Coder for real-time target. |

### MATLAB/Simulink Support Files

| File | Description |
|------|-------------|
| `SPACE584.prj` | MATLAB project file for managing paths and dependencies. |
| `get_unix_time.m` | MATLAB function to retrieve Unix timestamp for data logging. |
| `get_unix_time_wrapper.c/.h` | C wrapper for Unix time function (Simulink code generation). |
| `write_state.m` | MATLAB function to write current spacecraft state to file for inter-process communication. |
| `write_state.c/.h` | C implementation for state file writing (Simulink code generation). |
| `load_camera_bin.m` | MATLAB function to load camera binary data into Simulink. |
| `load_camera_bin.c/.h` | C implementation for camera data loading (Simulink code generation). |

---

## ADCS_python Directory

Python scripts running on the Raspberry Pi for actuator control, camera management, and telemetry.

### Actuator Control

| File | Description |
|------|-------------|
| `rw_duty_control.py` | Reaction wheel controller. Receives duty cycle commands via UDP from Simulink and drives ESCs via PWM (1040–2000 μs pulse width). |

### Camera Systems

| File | Description |
|------|-------------|
| `star_tracker.py` | Star tracker algorithm. Captures images, detects stars, computes centroids, and matches against star catalog for attitude determination. |
| `sun_sensor.py` | Sun sensor algorithm. Processes camera images to determine sun vector for coarse attitude estimation. |
| `science_camera_capture.py` | Science payload camera capture script. |
| `ir_camera_take_picture.py` | Infrared camera capture for thermal imaging. |
| `state_based_cameraloop_threaded.py` | Main camera controller. Monitors spacecraft state file and activates appropriate camera (star tracker, sun sensor, or science) based on current operational mode. |
| `run_ss_st_loop.py` | Runs sun sensor and star tracker in a continuous loop. |
| `crop_image.py` | Image cropping utility for camera preprocessing. |

### Star Tracker Support Files

| File | Description |
|------|-------------|
| `generate_star_tables.py` | Generates reference star catalog tables from astronomical data. |
| `star_table.npy` | Precomputed star catalog for pattern matching. |
| `star_distances.npy` | Inter-star angular distances for triangle matching algorithm. |
| `star_table_pixel_loc.csv` | Star positions in pixel coordinates. |
| `star_field.npy` / `star_field.jpg` | Captured star field data and image. |
| `star_field_reference.npy` / `star_field_reference.jpg` | Reference star field for calibration. |
| `star_tracker_analysis.jpg` | Star tracker output visualization. |

### Sun Sensor Support Files

| File | Description |
|------|-------------|
| `phi_ss.bin` | Sun sensor calibration/output data. |
| `sun_sensor_analysis.jpg` | Sun sensor output visualization. |

### Telemetry & Ground Station

| File | Description |
|------|-------------|
| `monitor_telemetry.py` | Real-time telemetry monitoring script. Displays attitude estimates, sensor data, and system health. |
| `ground_station584.py` | Ground station interface for remote commanding and telemetry reception. |

### Other Files

| File | Description |
|------|-------------|
| `ir_data_array.npy` / `ir_picture.jpg` | IR camera captured data and image. |
| `test.jpg` / `testvid.mp4` | Test imagery and video. |
| `thermal_env/` | Python virtual environment for thermal camera dependencies. |

---

## Communication Protocol

### Binary Packet Structure (Arduino → Raspberry Pi)

The Arduino transmits 86-byte binary packets over USB serial at 115200 baud:

| Bytes | Contents |
|-------|----------|
| 0–1 | Header (`0x55`, `0xAA`) |
| 2 | Validity flags |
| 3 | Reserved |
| 4–7 | Sequence number (uint32) |
| 8–11 | Timestamp (uint32) |
| 12–23 | Gyroscope 1 XYZ (3 floats) |
| 24–35 | Accelerometer 1 XYZ (3 floats) |
| 36–47 | Magnetometer 1 XYZ (3 floats) |
| 48–59 | Gyroscope 2 XYZ (3 floats) |
| 60–71 | Accelerometer 2 XYZ (3 floats) |
| 72–83 | Magnetometer 2 XYZ (3 floats) |
| 84–85 | CRC16-CCITT checksum |

### UDP Commands (Simulink → Python Actuators)

- Reaction wheel duty cycles sent via UDP to `rw_duty_control.py`
- State information written to file for camera controller coordination

---

## Operational Modes

The spacecraft state machine progresses through the following modes:

1. **Detumble** - Reduces high rotation rates using magnetorquers (bang-bang control)
2. **Coarse Pointing** - Initial attitude acquisition using sun sensor and reaction wheels
3. **Fine Pointing** - Precision pointing using star tracker and reaction wheels
4. **Science** - Science camera operations while maintaining attitude

---

## Setup & Deployment

### Arduino Setup
1. Install ICM-20948 library in Arduino IDE
2. Connect IMU 1 with AD0 → GND (address `0x68`)
3. Connect IMU 2 with AD0 → VCC (address `0x69`)
4. Upload `arduinoICM20948.ino`

### Raspberry Pi Setup
1. Install MATLAB Runtime for Simulink executable
2. Install Python dependencies: `numpy`, `opencv-python`, `pigpio`
3. Deploy `yukti_arduino_comms.elf` and ADCS_python scripts
4. Configure serial port permissions for Arduino communication

### Running the System
```bash
# Start the Simulink executable
./yukti_arduino_comms.elf &

# Start actuator controller
python3 rw_duty_control.py &

# Start camera state machine
python3 state_based_cameraloop_threaded.py &

# Monitor telemetry
python3 monitor_telemetry.py
```

---

## Authors

SPACE584 CubeSat ADCS Team

---

## License

This project was developed for SPACE584 Spacecraft Engineering coursework.
