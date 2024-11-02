# -*- coding: utf-8 -*-
"""
Description:
    This module is used to process rainfall data during the weekday commuting period in 2022 and construct a vehicle speed attenuation model under rainfall conditions. It includes functions for reading and processing rainfall data, as well as calculating the impact of rainfall on vehicle speeds.
"""

import math

import pandas as pd

import economic_indicators as ei

# Constants
RAINFALL_CONVERSION_FACTOR = 2  # Conversion factor from original units to mm/h
MAX_VEHICLE_SPEED = 1  # Maximum vehicle speed
RAIN_THRESHOLD = 250  # Heavy rain threshold in mm/24h
WATER_DEPTH_COEFFICIENT = 2.4  # Coefficient for water depth calculation


def get_city_rainfall_24hour(city):
    """
    Process rainfall data for specified cities.

    :param city: City name

    :return: Rainfall data for selected cities after processing
    """
    df = get_original_rainfall(city)
    rainfall = df["rain_final"].tolist()
    rainfall_process = [
        round(2 * x, 3) for x in rainfall
    ]  # Rainfall is converted to mm/h
    return rainfall_process


def get_original_rainfall(city):
    """
    Reads rainfall data for the given city.

    :param city: City name

    :return: Rainfall dataframe of the city
    """
    df = pd.read_excel(f"../data/rainfall/{city}.xlsx")
    return df


def rainfall_model(rainfall_list):
    """
    Calculate the velocity attenuation under rainfall.

    :param rainfall_list: List of rainfall data

    :return: List of percentage of speed decay per day
    """
    velocity_attenuation_percentage = []
    for rainfall in rainfall_list:
        if rainfall == 0:
            velocity_attenuation_percentage.append(1)
        else:
            depth = WATER_DEPTH_COEFFICIENT * 0.75 * rainfall / 1000
            v = MAX_VEHICLE_SPEED * math.exp((-9) * depth)
            velocity_attenuation_percentage.append(v)
    return velocity_attenuation_percentage


if __name__ == "__main__":
    city_list = ei.get_city()
    for city in city_list:
        rainfall_list = get_city_rainfall_24hour(city)
        velocity_attenuation = rainfall_model(rainfall_list)
        df = get_original_rainfall(city)
        df["velocity_change"] = velocity_attenuation
        df.to_excel(f"./data/rainfall/{city}.xlsx")
