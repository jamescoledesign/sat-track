#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Functions used in satellite-tracking program


"""

__author__ = "James Cole <james@jamescole.info"


# import time
# import requests
# import numpy as np
# import pandas as pd
from sgp4.api import jday
from sgp4.api import Satrec
from datetime import datetime, timezone
# import matplotlib.pyplot as plt
from skyfield.api import EarthSatellite, load, wgs84
import geocoder
# from pathlib import Path
import datetime as dt
# from pynput import keyboard
import math


def makeJulianDateNow():
    t = datetime.now()
    jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)

    return jd, fr


def getMyLocation():
    g = geocoder.ip('me')
    g = g.latlng

    lat = g[0]
    lon = g[1]

    return lat, lon


def trackOverhead(line1, line2, print_data=False):
    # Get sat position and velocity
    date = makeJulianDateNow()

    s = line1
    t = line2
    tracked_sat = Satrec.twoline2rv(s, t)

    jd, fr = date[0], date[1]
    
    e, r, v = tracked_sat.sgp4(jd, fr)
    
    if print_data:
        # True Equator Mean Equinox position (km)
        print("Position: ", r)
        # True Equator Mean Equinox velocity (km/s)
        print("Velocity: ", v)

    return [e, r, v]


def make_timestamp():
    date_time_format = '%Y-%m-%d-%H-%M-%S'
    current_date_time_dt = dt.datetime.now()
    current_date_time_string = dt.datetime.strftime(current_date_time_dt, date_time_format)
    
    return current_date_time_string


def save_csv(data_frame, file_name):
    # Save CSV
    current_date_time_string = make_timestamp()

    file_name = f'./{current_date_time_string}-{file_name}.csv'
    data_frame.to_csv(file_name, index=False)

    print(f"Saved {file_name}")
    

def convert_to_cartesian(altitude_deg, azimuth_deg):
    """
    Credit: ChatGPT
    Convert spherical coordinates (altitude, azimuth) to Cartesian coordinates.
    
    Parameters:
    - altitude_deg: Altitude angle in degrees (above the horizon)
    - azimuth_deg: Azimuth angle in degrees (clockwise from true north)
    
    Returns:
    - A tuple (x, y, z) representing the Cartesian coordinates.
    """
    # Convert degrees to radians
    altitude_rad = math.radians(altitude_deg)
    azimuth_rad = math.radians(azimuth_deg)

    # Compute Cartesian coordinates
    x = math.cos(altitude_rad) * math.sin(azimuth_rad)
    y = math.cos(altitude_rad) * math.cos(azimuth_rad)
    z = math.sin(altitude_rad)
    
    return x, y, z


def skyfieldTracker(line1, line2, sat_name, ground_station, rounding=4, print_data=False):
    positions = []
    
    # Coordinates
    lat = ground_station[0]
    lon = ground_station[1]
    location = wgs84.latlon(lat, lon)

    # Timestamp
    ts = load.timescale()
    t = ts.now()
    timestamp = make_timestamp()
    
    satellite = EarthSatellite(line1, line2, sat_name, ts)
    difference = satellite - location

    # Position of the satellite relative to observer
    topocentric = difference.at(t)

    # altitude, azimuth, distance
    alt, az, distance = topocentric.altaz()
    
    # Spherical coordinates for MCU
    x, y, z = convert_to_cartesian(alt.degrees, az.degrees)
    serial_data = f"{x:.6f},{y:.6f},{z:.6f}\n"
    
    if alt.degrees > 0:
        visibility = 'Above'
    else: 
        visibility = 'Below'
    
    if print_data:
        # Telemetry
        # print(f"{sat_name}\t\tTime tracked: {timer}s")
        print("------------------------------------------------------------------")
        print(f'Timestamp:\t{timestamp}')
        
        print(f'Visibility:\t{visibility} horizon')
        print('Distance:\t{:.1f} km'.format(distance))
        print(f'Altitude:\t{alt.degrees}\t({alt})')
        print(f'Azimuth:\t{az.degrees}\t({az})')
        print(f'X, Y, Z:\t{serial_data}')
        
    if rounding > 0:
        distance_r = round(distance.km, rounding)
        alt_r = round(alt.degrees, rounding)
        az_r = round(az.degrees, rounding)
        x_r = round(x, rounding)
        y_r = round(y, rounding)
        z_r = round(z, rounding)

        positions = [timestamp, f'{visibility} horizon', distance_r, alt_r, az_r, x_r, y_r, z_r]
    
    else: 
        positions = [timestamp, f'{visibility} horizon', distance.km, alt.degrees, az.degrees, x, y, z]

    return positions


if __name__ == "__main__":
    makeJulianDateNow()
    getMyLocation()
    trackOverhead()
    skyfieldTracker()
    convert_to_cartesian()
