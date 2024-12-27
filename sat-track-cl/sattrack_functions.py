"""
Functions used in satellite-tracking program

"""

__author__ = "James Cole <james@jamescole.info"

from sgp4.api import jday
from sgp4.api import Satrec
from datetime import datetime, timezone
from skyfield.api import EarthSatellite, load, wgs84
import geocoder
import datetime as dt
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

 
def calculate_steps(angle_degrees, starting_angle, steps_per_revolution=200, microstepping=32):
    """
    Credit: ChatGPT
    Calculate the number of steps needed for a stepper motor to reach a given angle from a starting position.
    
    Args:
        angle_degrees (float): The target angle in degrees.
        starting_angle (float): The current position of the motor (default: 0).
        steps_per_revolution (int): Steps per revolution of the motor (default: 200).
        microstepping (int): Microstepping value (default: 32).
    
    Returns:
        int: Number of steps to move.
    """
    angle_to_move = angle_degrees - starting_angle  # Account for the current position (starting_angle)
    steps_per_degree = (steps_per_revolution * microstepping) / 360
    steps = round(angle_to_move * steps_per_degree)
    
    return steps


def skyfieldTracker(line1, line2, sat_name, ground_station, starting_alt, starting_az, rounding=0, stepper=True, print_data=True):
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
        
    if stepper:
        altitude_steps = calculate_steps(alt.degrees, starting_alt)
        azimuth_steps = calculate_steps(az.degrees, starting_az)  
    
    if print_data:
        # Telemetry
        print("------------------------------------------------------------------")
        print(f'Timestamp:\t{timestamp}')
        print(f'Visibility:\t{visibility} horizon')
        print(f'Distance:\t{distance} km')
        print(f'Altitude:\t{alt.degrees}\t({alt})')
        print(f'Azimuth:\t{az.degrees}\t({az})')
        print(f'X, Y, Z:\t{serial_data}')
        print(f'Stepper altitude steps: {altitude_steps}')
        print(f'Stepper azimuth steps: {azimuth_steps}')
               
    if rounding > 0:
        distance_r = round(distance.km, rounding)
        alt_r = round(alt.degrees, rounding)
        az_r = round(az.degrees, rounding)
        x_r = round(x, rounding)
        y_r = round(y, rounding)
        z_r = round(z, rounding)

        positions = [timestamp, f'{visibility} horizon', alt_r, distance_r, az_r, x_r, y_r, z_r]
        
        if stepper:
            positions.append(altitude_steps)
            positions.append(azimuth_steps)
        
            return positions

    else: 
        positions = [timestamp, f'{visibility} horizon', alt.degrees, distance.km, az.degrees, x, y, z]
        if stepper:
            positions.append(altitude_steps)
            positions.append(azimuth_steps)
    
            return positions

if __name__ == "__main__":
    makeJulianDateNow()
    getMyLocation()
    trackOverhead()
    skyfieldTracker()
    convert_to_cartesian()
