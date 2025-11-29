#!/usr/bin/env python3
"""
Simple ADCS Telemetry Viewer
Just displays raw values as they come in over UDP
"""

import struct
import socket
import threading
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc

# Configuration
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
PACKET_SIZE = 280  # 35 doubles * 8 bytes

latest_data = None
packet_count = 0
lock = threading.Lock()

# State names
STATE_NAMES = {0: "STARTUP", 1: "DETUMBLE", 2: "STAR_ACQ", 3: "FINE_POINT", 4: "DESAT", 5: "SCIENCE"}


def unpack_telemetry(data: bytes) -> dict:
    """Unpack 280 bytes into telemetry dict (35 doubles)"""
    if len(data) != PACKET_SIZE:
        return None
    values = struct.unpack('<35d', data)  # little-endian
    validity = int(values[29])
    return {
        "timestamp": values[0],
        "state": int(values[1]),
        "phi_ekf": values[2],
        "omega_ekf": values[3],
        "P11": values[4],
        "P22": values[5],
        "gyro1": [values[6], values[7], values[8]],
        "gyro2": [values[9], values[10], values[11]],
        "accel1": [values[12], values[13], values[14]],
        "accel2": [values[15], values[16], values[17]],
        "mag1": [values[18], values[19], values[20]],
        "mag2": [values[21], values[22], values[23]],
        "phi_st": values[24],
        "phi_ss": values[25],
        "delta_omega": values[26],
        "delay_st": values[27],
        "delay_ss": values[28],
        "validity_flags": validity,
        "gyro1_valid": bool(validity & 1),
        "gyro2_valid": bool(validity & 2),
        "accel1_valid": bool(validity & 4),
        "accel2_valid": bool(validity & 8),
        "mag1_valid": bool(validity & 16),
        "mag2_valid": bool(validity & 32),
        "ss_cam_valid": bool(validity & 64),
        "st_cam_valid": bool(validity & 128),
        "magnetorquer1": bool(values[30]),
        "magnetorquer2": bool(values[31]),
        "RWDuty": values[32],
    }


def udp_receiver():
    """Background thread to receive UDP telemetry"""
    global latest_data, packet_count
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((UDP_IP, UDP_PORT))
    
    print(f"Listening on {UDP_IP}:{UDP_PORT}")
    
    while True:
        try:
            data, addr = sock.recvfrom(PACKET_SIZE)
            if len(data) == PACKET_SIZE:
                packet = unpack_telemetry(data)
                with lock:
                    latest_data = packet
                    packet_count += 1
        except Exception as e:
            print(f"Error: {e}")


# Start UDP receiver thread
thread = threading.Thread(target=udp_receiver, daemon=True)
thread.start()

# Create Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "ADCS Telemetry"

app.layout = dbc.Container([
    html.H2("🛰️ ADCS Telemetry Stream", className="text-center my-3"),
    html.Div(id="packet-info", className="text-center mb-3"),
    html.Hr(),
    html.Pre(id="telemetry-display", 
             style={"backgroundColor": "#1a1a2e", "color": "#00ff00", 
                    "padding": "20px", "fontSize": "14px", "fontFamily": "monospace"}),
    dcc.Interval(id="interval", interval=100, n_intervals=0),
], fluid=True)


@callback(
    Output("packet-info", "children"),
    Output("telemetry-display", "children"),
    Input("interval", "n_intervals"),
)
def update_display(n):
    global latest_data, packet_count
    
    with lock:
        count = packet_count
        data = latest_data
    
    if data is None:
        return f"Waiting for packets on port {UDP_PORT}...", "No data received yet"
    
    state_name = STATE_NAMES.get(data["state"], f"UNKNOWN({data['state']})")
    
    # Format the display
    text = f"""
=== PACKET #{count} ===
Timestamp:    {data['timestamp']:.3f}
State:        {data['state']} ({state_name})

=== EKF ESTIMATES ===
phi_ekf:      {data['phi_ekf']:12.4f} deg
omega_ekf:    {data['omega_ekf']:12.4f} deg/s
P11:          {data['P11']:12.6f}
P22:          {data['P22']:12.6f}

=== GYROSCOPE 1 === (valid: {data['gyro1_valid']})
X: {data['gyro1'][0]:12.4f}   Y: {data['gyro1'][1]:12.4f}   Z: {data['gyro1'][2]:12.4f}

=== GYROSCOPE 2 === (valid: {data['gyro2_valid']})
X: {data['gyro2'][0]:12.4f}   Y: {data['gyro2'][1]:12.4f}   Z: {data['gyro2'][2]:12.4f}

=== ACCELEROMETER 1 === (valid: {data['accel1_valid']})
X: {data['accel1'][0]:12.4f}   Y: {data['accel1'][1]:12.4f}   Z: {data['accel1'][2]:12.4f}

=== ACCELEROMETER 2 === (valid: {data['accel2_valid']})
X: {data['accel2'][0]:12.4f}   Y: {data['accel2'][1]:12.4f}   Z: {data['accel2'][2]:12.4f}

=== MAGNETOMETER 1 === (valid: {data['mag1_valid']})
X: {data['mag1'][0]:12.4f}   Y: {data['mag1'][1]:12.4f}   Z: {data['mag1'][2]:12.4f}

=== MAGNETOMETER 2 === (valid: {data['mag2_valid']})
X: {data['mag2'][0]:12.4f}   Y: {data['mag2'][1]:12.4f}   Z: {data['mag2'][2]:12.4f}

=== CAMERAS ===
phi_st:       {data['phi_st']:12.4f} (valid: {data['st_cam_valid']}, delay: {data['delay_st']:.3f}s)
phi_ss:       {data['phi_ss']:12.4f} (valid: {data['ss_cam_valid']}, delay: {data['delay_ss']:.3f}s)
delta_omega:  {data['delta_omega']:12.6f}

=== ACTUATORS ===
Magnetorquer 1: {"ON" if data['magnetorquer1'] else "OFF":>12}
Magnetorquer 2: {"ON" if data['magnetorquer2'] else "OFF":>12}
Reaction Wheel Duty Cycle: {data['RWDuty']:12.4f}
"""

    info = dbc.Badge(f"Packets: {count} | State: {state_name}", color="success", className="fs-5")
    
    return info, text


if __name__ == "__main__":
    print("=" * 40)
    print("  Simple ADCS Telemetry Viewer")
    print(f"  Listening on UDP port {UDP_PORT}")
    print("=" * 40)
    app.run(host="0.0.0.0", port=8050, debug=False)