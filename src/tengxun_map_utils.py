# -*- coding: utf-8 -*-
"""
Description:
    This module is used to invoke Tencent map api to obtain location coordinates and path information.
"""

import requests
from pprint import pprint


def get_coordinates(city, address):
    """
    Get the latitude and longitude coordinates of the specified location.

    :param city: Specify the target city
    :param address: Specify the location details

    :return: The latitude and longitude coordinates of the specified location
    """
    response = requests.get(
        url="https://apis.map.qq.com/ws/geocoder/v1/",
        params={
            "region": city,
            "address": address,
            "key": "YOUR_API_KEY",  # Replace with your actual API key
        },
    ).json()
    pprint(response)


def get_driving_directions(
    start_latitude, start_longitude, end_latitude, end_longitude, key_index
):
    """
    Get car travel mode traffic information from start to finish.

    :param start_latitude: Latitude of the starting point.
    :param start_longitude: Longitude of the starting point.
    :param end_latitude: Latitude of the ending point.
    :param end_longitude: Longitude of the ending point.
    :param key_index: Used to select a different API key.

    :return: Minimum path time, corresponding length, and related information.
    """
    start_point = f"{start_latitude},{start_longitude}"
    end_point = f"{end_latitude},{end_longitude}"
    keys = ["YOUR_API_KEY"]  # Replace with your actual API keys
    response = requests.get(
        url="https://apis.map.qq.com/ws/direction/v1/driving/",
        params={
            "key": keys[key_index],
            "from": start_point,
            "to": end_point,
            "policy": "LEAST_TIME",
        },
    ).json()

    route = response.get("result", {}).get("routes", [{}])[0]
    return (
        route.get("distance"),
        route.get("duration"),
        route.get("taxi_fare", {}).get("fare"),
    )


def get_transit_directions(
    start_latitude, start_longitude, end_latitude, end_longitude, key_index
):
    """
    Get public transport travel information from start to finish.

    :param start_latitude: Latitude of the starting point.
    :param start_longitude: Longitude of the starting point.
    :param end_latitude: Latitude of the ending point.
    :param end_longitude: Longitude of the ending point.
    :param key_index: Used to select a different API key.

    :return: Minimum path time, corresponding length, and related information.
    """
    start_point = f"{start_latitude},{start_longitude}"
    end_point = f"{end_latitude},{end_longitude}"
    keys = ["YOUR_API_KEY"]  # Replace with your actual API keys
    response = requests.get(
        url="https://apis.map.qq.com/ws/direction/v1/transit/",
        params={
            "key": keys[key_index],
            "from": start_point,
            "to": end_point,
            "policy": "LEAST_TIME",
        },
    ).json()

    if response.get("status") == 0:
        route = response.get("result", {}).get("routes", [{}])[0]
        return (route.get("distance"), route.get("duration"), route.get("steps"))
    else:
        return 0, 0, []
