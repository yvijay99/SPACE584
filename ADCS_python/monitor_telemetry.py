#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 14:35:21 2025

@author: atcushen

This script is to be run locally, and it will pull files from the rpi continuously to monitor its progress.


"""

import matplotlib
matplotlib.use('QtAgg') 
import numpy as np
import sys
import paramiko
from scp import SCPClient
import os
import time
from PIL import Image
import scipy.io
import matplotlib.pyplot as plt

def wait_for_file_stability(ssh_client, remote_path, timeout=30, interval=0.1):
    """
    Polls the remote file size until it remains unchanged for 'interval' seconds.
    Returns True if stable, False if timeout reached.
    """
    start_time = time.time()
    last_size = -1
    
    print(f"Polling remote file size for stability (max {timeout}s)...")

    while time.time() - start_time < timeout:
        # Use SSH command to get file size (Linux/macOS command: stat -c%s or ls -l)
        # We need a robust way to get file size via SSH
        stdin, stdout, stderr = ssh_client.exec_command(f'stat -c%s "{remote_path}" 2>/dev/null || stat -f%z "{remote_path}"')
        
        try:
            current_size_str = stdout.read().decode('utf-8').strip()
            if not current_size_str:
                # File likely doesn't exist yet, wait and retry
                time.sleep(interval)
                continue

            current_size = int(current_size_str)

            if current_size == last_size:
                print(f"File size stabilized at {current_size} bytes.")
                return True
            else:
                last_size = current_size
                print(f"File size changed to {current_size} bytes. Waiting {interval}s...")
        
        except ValueError:
            print(f"Could not read file size. Error: {stderr.read().decode('utf-8').strip()}")

        time.sleep(interval)

    print("Timeout reached. File size never stabilized.")
    return False

def scp_get_file_with_password(hostname, username, password, remote_path, local_destination_path, debug = False):
    """
    SCP a file from a remote_path to a local_destination_path using a password.
    
    :param hostname: The IP address or hostname of the remote server.
    :param username: The username for authentication.
    :param password: The password for authentication.
    :param remote_path: The full path to the file on the remote server.
    :param local_destination_path: The local directory or full path where the file will be saved.
    """
    ssh_client = paramiko.SSHClient()
    # Automatically add the server's host key (use with caution in production)
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if debug:
            print(f"Connecting to {hostname} as {username}...")
        # Connect to the remote server using password authentication
        ssh_client.connect(
            hostname=hostname,
            username=username,
            password=password,
            look_for_keys=False # Explicitly ignore SSH keys to force password use
        )
        if not wait_for_file_stability(ssh_client, remote_path, interval=0.1):
            print("Could not verify file integrity. Aborting SCP transfer.")
            return False
        
        if debug:
            print("Connected successfully!")
        else:
            print("Got file:", remote_path)

        # SCPCLient takes a paramiko transport as its only argument
        with SCPClient(ssh_client.get_transport()) as scp:
            print(f"Retrieving {remote_path} to {local_destination_path}...")
            # Use scp.get() to retrieve the file/directory
            scp.get(remote_path, local_destination_path)
            print("File retrieval complete.")

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check username and password.")
    except paramiko.SSHException as e:
        print(f"SSH error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if ssh_client:
            ssh_client.close()


def main():
    
    start_time = time.time()
    
    # Set up memory of test results
    t_st_ls = []
    t_ss_ls = []
    phi_st_ls = []
    phi_ss_ls = []
    delta_omega_RW_ls = []
    
    while monitor:
        
        elapsed_time =  time.time() - start_time
        
        print("###############")
        print(f"Looking for data at t = {elapsed_time:.0f}s ...")
        
        # Get star tracker and sun_sensor plots
        scp_get_file_with_password(HOST, USER, PASS, ROOT+"ADCS_python/star_tracker_analysis.jpg", LOCAL_DEST)
        scp_get_file_with_password(HOST, USER, PASS, ROOT+"ADCS_python/sun_sensor_analysis.jpg", LOCAL_DEST)
        
        # Get star tracjer and sun_sensor output results
        scp_get_file_with_password(HOST, USER, PASS, ROOT+"ADCS_python/phi_st.mat", LOCAL_DEST)
        scp_get_file_with_password(HOST, USER, PASS, ROOT+"ADCS_python/phi_ss.mat", LOCAL_DEST)
        
        # Get state controller output
        scp_get_file_with_password(HOST, USER, PASS, ROOT+"ADCS_python/RW_throttle.npy", LOCAL_DEST)
        
        # Load images
        st_analysis_img = Image.open("star_tracker_analysis.jpg")
        ss_analysis_img = Image.open("sun_sensor_analysis.jpg")
        
        # Load .mat files
        st_data = scipy.io.loadmat('phi_st.mat')
        ss_data = scipy.io.loadmat('phi_ss.mat')
        #controller_out = scipy.io.loadmat('controller_out.mat')
        delta_omega = np.load("RW_throttle.npy")
    
        # Append to list, if the data is new:
        if len(t_st_ls) == 0 or t_st_ls[-1] != st_data['t'].item():
            t_st_ls.append(st_data['t'].item())
            phi_st_ls.append(st_data['phi_st'].item())
        
        if len(t_ss_ls) == 0 or t_ss_ls[-1] != ss_data['t'].item():
            t_ss_ls.append(ss_data['t'].item())
            phi_ss_ls.append(ss_data['phi_ss'].item())
            
        if len(delta_omega_RW_ls) == 0 or delta_omega_RW_ls[-1] != delta_omega:
            delta_omega_RW_ls.append(delta_omega)
            
        time.sleep(wait_time/2)
        
        # Set up plot
        plt.close()
        plt.ion() 
        fig = plt.figure(constrained_layout=True, figsize=(50,30))
        axs = fig.subplot_mosaic([['Top', 'Top'],['BottomLeft', 'BottomRight']],
                          gridspec_kw={'width_ratios':[1, 1], 'height_ratios':[2,3]})
        
        RW_axs = axs['Top'].twinx()
        
        # Get the earliest time saved by either sensor, to set the epoch time of the rpi
        rpi_epoch_t0 = np.min([t_st_ls[0],t_ss_ls[0]])
        
        # Create fake time data for RW output, which has no time stamp
        RW_time = np.linspace(0,np.max([t_st_ls[-1],t_ss_ls[-1]]), len(delta_omega_RW_ls)) - rpi_epoch_t0
        
        # Show timeseries
        axs['Top'].plot(np.array(t_st_ls)-rpi_epoch_t0, np.array(phi_st_ls)*(180/np.pi),label='s.t.',marker = "x")
        axs['Top'].plot(np.array(t_ss_ls)-rpi_epoch_t0, np.array(phi_ss_ls)*(180/np.pi),label='s.s.',marker = "x")
        RW_axs.plot(RW_time,np.array(delta_omega_RW_ls)*(180/np.pi),label=r'RW $\delta \omega$',marker = "x", color = 'black')
        axs['Top'].legend()
        axs['Top'].set_xlabel("rpi. epoch time [s]")
        axs['Top'].set_ylabel(r"$\phi$ [deg.]")
        RW_axs.set_ylabel(r"Commanded acceleration [deg/s$^2$]")
        axs['Top'].set_title("Attitude timeseries")
        
        # Show analysis figures
        axs['BottomLeft'].imshow(st_analysis_img)
        axs['BottomLeft'].axis('off')
        axs['BottomRight'].imshow(ss_analysis_img)
        axs['BottomRight'].axis('off')
        
        # Show plot
        plt.draw()
        plt.pause(0.001)
        
        plt.savefig("telemetry.png", dpi=150)

        time.sleep(wait_time/2)

if __name__ == "__main__":
    
    monitor = True
    wait_time = 1 #[s]
    
    # For scp-ing files from the rpi
    HOST = "192.168.0.141"
    USER = "space584a"
    PASS = "raspberry"
    ROOT = "/home/"+USER+"/MATLAB_ws/R2025b/"
    LOCAL_DEST = "."
    
    main()
