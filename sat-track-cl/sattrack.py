"""
Satellite Tracker

"""

__author__ = "James Cole <james@jamescole.info"


import time
import pandas as pd
from skyfield.api import load
from datetime import timezone
from pathlib import Path
from sattrack_functions import *
from pick import pick
# from multiprocessing import Process
# from pynput import keyboard


# Intro message
print(" ")
print("* ------------------------------------- *")
print("    S A T E L L I T E   T R A C K E R    ")
print("* ------------------------------------- *")
print(" ")


# Load CSV
sats_df = pd.read_csv('satellites.csv')

# Your current location (lat/lon)
ground_station = (33.253408, -97.134179)

setup_step = 1
title = f'[ Setup {setup_step}/2 ]\n\nConfirm your location (lat/lon):\n'

location_options = [f'Use existing: {ground_station}', 
                    'Get location from IP address', 
                    'Enter manually']
location_selection, location_index = pick(location_options, title)

if location_index == 0:
    pass
elif location_index == 1:
    ground_station = getMyLocation()
elif location_index == 2:
    print('Enter latitude:')
    lat = input()
    print('Enter longitude:')
    lon = input()
    
    ground_station = (float(lat), float(lon))

ts = load.timescale()

above_horizon = []
count = 1
delay = 1

run = True
enable_checks = True
locked_on = False
was_locked_on = False

setup_step += 1
title = f'[ Setup {setup_step}/2 ]\n\nSelect a satellite:\n'
print(" ")
print(title)

sats = sats_df['sat_name']
sat, index = pick(sats, title)

sat_name = sats[index]
sat_data = sats_df.iloc[index]
line1 = sat_data['tle_line1']
line2 = sat_data['tle_line2']

alt_angle = 0
az_angle= 0

while run:
    positions = skyfieldTracker(line1, line2, sat_name, ground_station, alt_angle, az_angle)
    
    # stepper_alt = positions[8]
    # stepper_az = positions[9]
    
    # alt_angle = alt_angle + 10
    # az_angle = az_angle + 10
    
    if alt_angle >= 360: 
        alt_angle = 0
        
    if az_angle >= 360: 
        az_angle = 0
    
    time.sleep(1)