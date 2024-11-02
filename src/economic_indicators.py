# -*- coding: utf-8 -*-
"""
Description:
    This module is used to obtain and process economic indicators related to cities.
"""

import os
import random
import math

import numpy as np
import pandas as pd

# Constants
COUNTRY_INCOME = 36883  # National average income (CNY)
INCOME_GROUP = [8601, 19303, 30598, 47397, 90116]  # Income groups
URBAN_PEOPLE = 897.578  # Urban population (million)
RURAL_PEOPLE = 514.597  # Rural population (million)
INCOME_MULTIPLE = 2.45  # Urban-rural income difference multiple (2022)


def city_income(city):
    """
    Get the average income level of the city and the average income level of the population at each income level.

    :param city: City name

    :return: The average income level of the city and the average income level of the population at all income levels
    """
    urban_income = ((URBAN_PEOPLE + RURAL_PEOPLE) * COUNTRY_INCOME) / (
        URBAN_PEOPLE + RURAL_PEOPLE * (1 / INCOME_MULTIPLE)
    )
    adjusted_income_group = [(urban_income / COUNTRY_INCOME) * i for i in INCOME_GROUP]

    df = get_data()
    income_list = df["average_income"].tolist()
    income_city = income_list[city_index(city)]

    average_income_perincomegroup = [
        int(income_city / COUNTRY_INCOME * i) for i in adjusted_income_group
    ]
    tran = [int(income_city / COUNTRY_INCOME * i) for i in adjusted_income_group]
    tran.insert(0, city_min_consumption(city))
    tran.append(2 * tran[-1])

    income_range_perincomegroup = []
    for i in range(len(tran) - 2):
        if i == 0:
            lower_limit = min(
                city_min_consumption(city) * 12, average_income_perincomegroup[i] / 1.2
            )
        else:
            lower_limit = (tran[i] + tran[i + 1]) / 2
        upper_limit = (tran[i + 1] + tran[i + 2]) / 2
        income_range_perincomegroup.append([lower_limit, upper_limit])

    disposable_income_permonth = [
        int((1 / 12) * p) for p in average_income_perincomegroup
    ]

    return (
        income_city,
        average_income_perincomegroup,
        urban_income,
        income_range_perincomegroup,
        disposable_income_permonth,
    )


def city_index(city):
    """
    Get the index of the city in the list of cities.

    :param city: City name

    :return: Index of the city in the list of cities
    """
    df = get_data()
    city_list = df["city"].tolist()
    index = city_list.index(city)
    return index


def city_min_consumption(city):
    """
    Get the minimum consumption for residents of a specific city.

    :param city: City name

    :return: The minimum consumption for residents of the city
    """
    df = get_data()
    min_c_list = df["min_c/month"].tolist()
    min_c_city = min_c_list[city_index(city)]
    return min_c_city


def city_rent_income_ratio(city):
    """
    Get the rent income ratio for a specific city.

    :param city: City name

    :return: The rent income ratio of the city
    """
    df = get_data()
    rent_income_ratio_list = df["rent_income_ratio"].tolist()
    rent_income_ratio_city = rent_income_ratio_list[city_index(city)]
    # Set increment by income group
    increment = -0.01
    each_income_group_rent_income_ratio = np.arange(
        rent_income_ratio_city - (increment * 2),
        rent_income_ratio_city + (increment * 3),
        increment,
    )
    return each_income_group_rent_income_ratio


def get_city():
    """
    Get a list of all city names.

    :return: A list of all city names
    """
    a = os.listdir("../data/rainfall")
    city = []
    for i in a:
        city1 = os.path.splitext(i)[0]
        city.append(city1)
    return city


def get_consumption(
    initial_disposable_consumption,
    rent_perday,
    income_perday,
    extra_consumption_perday,
    average_saving_ratio,
    commuting_consumption,
    income_loss,
):
    """
    Calculate individual daily consumption indicators.

    :param initial_disposable_consumption: Disposable consumption based on income
    :param rent_perday: Daily rent of the residents
    :param income_perday: Daily income of the residents
    :param extra_consumption_perday: Additional consumption of residents, including food, clothing, housing, and transportation, etc
    :param average_saving_ratio: Average savings to income ratio
    :param commuting_consumption: Consumption during commuting under rainfall
    :param income_loss: Income loss due to increased commuting time

    :return: The disposable consumption and asset loss of residents
    """
    disposable_consumption_today = (
        max(
            initial_disposable_consumption - rent_perday - extra_consumption_perday,
            income_perday * average_saving_ratio,
        )
        - commuting_consumption
        - income_loss
    )
    asset_loss_today = commuting_consumption + income_loss
    return disposable_consumption_today, asset_loss_today


def get_data():
    """
    Get the dataframe that holds the city information.

    :return: The dataframe that holds the city information
    """
    df = pd.read_excel("../data/city.xlsx")
    return df


def get_housing_group(df, rent_range_peryear):
    """
    Obtain the corresponding road network simulation information according to the working place name, and determine the housing that residents can live in.

    :param df: Rental listing dataframe
    :param rent_range_peryear: Rental property annual rent range

    :return: The housing available to the resident
    """
    group = df[
        (df["individual_rent_price"] < rent_range_peryear[1] / 12)
        & (df["individual_rent_price"] > rent_range_peryear[0] / 12)
    ]
    return group


def get_individual_income(income):
    """
    Calculate individual income indicators.

    :param income: Annual income

    :return: Hourly income, daily income, and monthly income
    """
    income_permonth = income / 12
    income_perday = income_permonth / 21.75
    income_perhour = income_perday / 8
    return income_permonth, income_perday, income_perhour


def get_people_income_list(income_range, average_income, people_number):
    """
    According to the average income and the number of people in this income class, output the simulated income distribution list.

    :param income_range: The income range of residents in this income bracket
    :param average_income: The average income of residents in that income bracket
    :param people_number: The number of people doing the simulation

    :return: The specific value of income per resident obtained by simulation
    """
    people_average_income = 0
    people_income_list = []
    for _ in range(people_number):
        if people_average_income > average_income:
            people_income_list.append(
                random.randint(int(income_range[0]), int(average_income))
            )
        else:
            people_income_list.append(
                random.randint(int(average_income), int(income_range[1]))
            )
        people_average_income = sum(people_income_list) / len(people_income_list)
    return people_income_list


def get_wellbeing(disposable_asset_today, disposable_asset_today_ideally, theta):
    """
    Calculate wellbeing.

    :param disposable_asset_today: The remaining disposable property of residents today
    :param disposable_asset_today_ideally: The remaining disposable property of residents today without rain
    :param theta: Model coefficient

    :return: Well-being value and well-being loss value
    """
    utility = (disposable_asset_today ** (1 - theta)) / (1 - theta)
    well_being_increment = utility * math.exp(-0.1)
    utility_ideally = (disposable_asset_today_ideally ** (1 - theta)) / (1 - theta)
    well_being_increment_ideally = utility_ideally * math.exp(-0.1)
    wellbeing_loss = well_being_increment_ideally - well_being_increment
    return well_being_increment, wellbeing_loss
