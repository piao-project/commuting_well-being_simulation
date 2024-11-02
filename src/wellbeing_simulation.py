# -*- coding: utf-8 -*-
"""
Description:
    This module constructed commuting well-being loss model to simulate residents' commuting well-being loss.
"""

import os
import random

import pandas as pd
from tqdm import tqdm

import economic_indicators as ei


def probability_normalize(
    distance_list, time_list, rent_list, weight1, weight2, weight3
):
    """
    The selection probability (linear) is determined according to the distance between each residential area and the work place,
    where the closer the distance is, the greater the probability of being selected, and the lower the rent is, the greater the probability of being selected,
    with weights of 0.8 and 0.2 respectively.

    :param distance_list: List of all rental property and work place linear distances
    :param time_list: List of all rental property and work place travel times
    :param rent_list: List of all rental properties for rent
    :param weight1: The weight of the distance factor
    :param weight2: The weight of the time factor
    :param weight3: The weight of the rent factor

    :return: The probability of selecting each rental property
    """
    distance_total = sum([1 / x for x in distance_list])
    distance_chance = [(1 / x) / distance_total for x in distance_list]

    time_total = sum([1 / x for x in time_list])
    time_chance = [(1 / x) / time_total for x in time_list]

    rent_total = sum([1 / x for x in rent_list])
    rent_chance = [(1 / x) / rent_total for x in rent_list]

    final_chance = [
        distance_chance[i] * weight1
        + time_chance[i] * weight2
        + rent_chance[i] * weight3
        for i in range(len(distance_chance))
    ]
    return final_chance


def get_city_data(city):
    """
    Get various data for a given city.

    :param city: The name of the city
    :return: Various city-related data
    """
    min_consumption = ei.city_min_consumption(city) / 30
    rent_income_ratio = ei.city_rent_income_ratio(city)
    income_list = ei.city_income(city)
    average_income = income_list[0]
    income_range = income_list[1]
    monthly_disposable_income = income_list[2]

    rainfall_df = pd.read_excel(f"./data/rainfall/{city}.xlsx")
    velocity_attenuation_percentage_list = rainfall_df["velocity_change"].tolist()

    residential_consumption_proportion = 0.24  # country average
    transportation_consumption_proportion = 0.13
    average_saving_ratio = 0.335

    workplace_data = pd.read_excel(f"../data/workplace/{city}.xlsx")
    workplace_name = workplace_data["code"].tolist()

    return (
        min_consumption,
        rent_income_ratio,
        average_income,
        income_range,
        monthly_disposable_income,
        velocity_attenuation_percentage_list,
        residential_consumption_proportion,
        transportation_consumption_proportion,
        average_saving_ratio,
        workplace_name,
    )


def simulate(
    city,
    people,
    theta,
    min_consumption,
    rent_income_ratio,
    average_income,
    income_range,
    velocity_attenuation_percentage_list,
    residential_consumption_proportion,
    transportation_consumption_proportion,
    average_saving_ratio,
    workplace_name,
):
    """
    Simulate the wellbeing loss for the redidents from a given city.

    :param city: The name of the city
    :param people: The number of simulation people for one income group in one work area
    :param theta: Well-being model coefficient
    :param min_consumption: Minimum consumption
    :param rent_income_ratio: Rent-income ratio
    :param average_income: Average income
    :param income_range: Income range
    :param monthly_disposable_income: Monthly disposable income
    :param velocity_attenuation_percentage_list: Velocity attenuation percentage list
    :param residential_consumption_proportion: Residential consumption proportion
    :param transportation_consumption_proportion: Transportation consumption proportion
    :param average_saving_ratio: Average saving ratio
    :param workplace_name: List of workplace names
    """
    result_save_df = pd.DataFrame()

    for w in range(4):
        workplace = workplace_name[w]
        df = pd.read_excel(f"./data/driving+transit/{city}/{city}_{workplace}.xlsx")
        each_group_people_num = [people] * 5

        for i in range(len(average_income)):
            if income_range[i][0] > average_income[i]:
                people_income_list = ei.get_people_income_list(
                    [average_income[i] - 100, income_range[i][1]],
                    average_income[i],
                    people,
                )
            else:
                people_income_list = ei.get_people_income_list(
                    income_range[i], average_income[i], people
                )

            average_rent_income_ratio = rent_income_ratio[i]
            actual_average_rent_income_ratio = 0  # Start

            for p in tqdm(range(len(people_income_list))):
                individual_income = people_income_list[p]
                income_per_month, income_per_day, income_per_hour = (
                    ei.get_individual_income(individual_income)
                )
                if actual_average_rent_income_ratio < average_rent_income_ratio:
                    rent_income_ratio_range = [average_rent_income_ratio, 1]
                else:
                    rent_income_ratio_range = [0, average_rent_income_ratio]
                rent_range = [individual_income * i for i in rent_income_ratio_range]
                rent_option = ei.get_housing_group(df, rent_range)

                while len(rent_option) == 0:
                    rent_income_ratio_range[0] -= 0.05
                    rent_income_ratio_range[1] += 0.05
                    rent_range = [
                        individual_income * i for i in rent_income_ratio_range
                    ]
                    rent_option = ei.get_housing_group(df, rent_range)

                distance = rent_option["driving_distance"]
                time = rent_option["driving_time"]
                rent = rent_option["individual_rent_price"]
                prob = probability_normalize(distance, time, rent, 0.4, 0.4, 0.2)

                rent_index = random.choices(range(len(prob)), weights=prob)

                rent = rent_option.iloc[rent_index[0]]

                # Initial deposit is the deposit of two years of work
                savings = 2 * people_income_list[p] * average_saving_ratio
                rent_per_month = rent["individual_rent_price"]
                rent_per_day = rent_per_month / 30
                actual_average_rent_income_ratio = (
                    actual_average_rent_income_ratio * p
                    + (rent_per_month / income_per_month)
                ) / (p + 1)

                extra_consumption_per_day = (
                    rent_per_day / residential_consumption_proportion
                ) * (
                    1
                    - residential_consumption_proportion
                    - transportation_consumption_proportion
                )

                transit_distance = rent["commuting_distance"]
                transit_time = rent["commuting_time"]
                transit_price = rent["transit_price"]
                driving_distance = rent["driving_distance"]
                driving_time = rent["driving_time"]
                driving_fare = rent["driving_fare"]

                initial_disposable_consumption = max(
                    income_per_day, min_consumption
                )  # Max(daily income, min_consumption)

                consumption = []
                asset = [savings]  # Set initial asset

                well_being_loss = []
                consumption_no_rainfall = []

                asset_lost_per_day = []
                time_add_per_day = []
                distance_add_per_day = []

                for r in range(len(velocity_attenuation_percentage_list)):
                    velocity_attenuation_percentage = (
                        velocity_attenuation_percentage_list[r]
                    )
                    if r % 7 == 0 or r % 7 == 1:  # Determine whether it is a work day
                        commuting_consumption = 0
                        income_lost = 0
                        time_add = 0
                        distance_add = 0
                    else:
                        if (
                            int(velocity_attenuation_percentage) == 1
                        ):  # If it's a weekday, determine if it rains during your commute
                            commuting_consumption = 0
                            income_lost = 0
                            time_add = 0
                            distance_add = 0
                        else:
                            fare_add = (
                                driving_fare - transit_price
                            ) / velocity_attenuation_percentage  # Driving costs more than transit
                            income_loss = (
                                (1 / velocity_attenuation_percentage)
                                * max(income_per_hour, 10)
                                * (transit_time - driving_time)
                                / 60
                            )  # Transit loses more revenue than driving
                            if fare_add <= income_loss:
                                commuting_consumption = fare_add
                                income_lost = (
                                    max(
                                        driving_time / velocity_attenuation_percentage
                                        - transit_time,
                                        0,
                                    )
                                    / 60
                                    * max(income_per_hour, 10)
                                )
                                time_add = (
                                    driving_time * (1 / velocity_attenuation_percentage)
                                    - transit_time
                                )
                                distance_add = driving_distance - transit_distance
                            else:  # Best to choose the original commuting mode under rainfall
                                commuting_consumption = 0
                                income_lost = (
                                    transit_time
                                    / (60 * velocity_attenuation_percentage)
                                    * max(income_per_hour, 10)
                                )
                                time_add = transit_time * (
                                    1 / velocity_attenuation_percentage - 1
                                )
                                distance_add = 0

                    consumption_today, asset_lost_today = ei.get_consumption(
                        initial_disposable_consumption,
                        rent_per_day,
                        income_per_day,
                        extra_consumption_per_day,
                        average_saving_ratio,
                        commuting_consumption,
                        income_lost,
                    )
                    consumption_today_no_rainfall = ei.get_consumption(
                        initial_disposable_consumption,
                        rent_per_day,
                        income_per_day,
                        extra_consumption_per_day,
                        average_saving_ratio,
                        0,
                        0,
                    )

                    consumption.append(consumption_today)
                    consumption_no_rainfall.append(consumption_today_no_rainfall)
                    disposable_asset_today = savings + sum(consumption)
                    disposable_asset_today_no_rainfall = savings + sum(
                        consumption_no_rainfall
                    )
                    asset.append(disposable_asset_today)
                    well_being_today, well_being_loss_today = ei.get_wellbeing(
                        disposable_asset_today,
                        disposable_asset_today_no_rainfall,
                        theta,
                    )
                    asset_lost_per_day.append(asset_lost_today)
                    time_add_per_day.append(time_add)
                    distance_add_per_day.append(distance_add)
                    well_being_loss.append(well_being_loss_today)

                rent_df = rent.to_frame().T
                result_df_1 = rent_df.assign(
                    people_income=individual_income,
                    workplace=w + 1,
                    initial_savings=savings,
                    income_group=i + 1,
                    people=p + 1,
                    well_being_loss=max(sum(well_being_loss), 0),
                    asset_loss=sum(asset_lost_per_day),
                    time_add=sum(time_add_per_day),
                    distance_add=sum(distance_add_per_day),
                )
                result_dave_df = pd.concat([result_save_df, result_df_1], axis=0)

            print(f"{city} + income group {i + 1} + {actual_average_rent_income_ratio}")

    result_dave_df.to_excel(f"./data/result/{city}/{city}{w + 1}.xlsx", index=False)


def merge_city():
    """
    Merge all files in city's folder.
    """
    city_list = ei.get_city()
    for city in city_list:
        folder_path = f"./data/result/{city}"
        dfs = []
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".xlsx"):
                file_path = os.path.join(folder_path, file_name)
                df = pd.read_excel(file_path)
                dfs.append(df)
        merged_df = pd.concat(dfs, ignore_index=True)
        merged_df.to_excel(f"./data/result/{city}.xlsx", index=False)


if __name__ == "__main__":
    city_list = ei.get_city()
    # The number of simulation people for one income group in one work area
    people = 5000
    theta_select = 1.5

    for city in tqdm(city_list):
        theta = theta_select
        city_dir = f"./data/result/{city}"
        os.makedirs(city_dir, exist_ok=True)

        (
            min_consumption,
            rent_income_ratio,
            average_income,
            income_range,
            monthly_disposable_income,
            velocity_attenuation_percentage_list,
            residential_consumption_proportion,
            transportation_consumption_proportion,
            average_saving_ratio,
            workplace_name,
        ) = get_city_data(city)

        simulate(
            city,
            people,
            theta,
            min_consumption,
            rent_income_ratio,
            average_income,
            income_range,
            monthly_disposable_income,
            velocity_attenuation_percentage_list,
            residential_consumption_proportion,
            transportation_consumption_proportion,
            average_saving_ratio,
            workplace_name,
        )

    merge_city()
