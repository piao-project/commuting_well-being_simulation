# -*- coding: utf-8 -*-
"""
Description:
    This module is used to parse and process all the commute data information that is received.
"""

import os

import numpy as np
import pandas as pd
from tqdm import tqdm
import ast

import economic_indicators as ei

city_list = ei.get_city()


def is_valid_for_literal_eval(route):
    """
    Check if the given route string can be safely evaluated using ast.literal_eval.

    :param route: A string that potentially represents a Python literal

    :return: True if the route can be safely evaluated, False otherwise
    """
    try:
        if not isinstance(route, str):
            return False
        ast.literal_eval(route)
        return True
    except (ValueError, SyntaxError, TypeError):
        return False


def merge_api_files():
    """
    Merge all API files for each city.
    """
    for c in range(len(city_list)):
        city = city_list[c]
        workplace_data = pd.read_excel(f"../data/workplace/{city}.xlsx")
        for path in ["driving", "transit"]:
            for w in range(4):
                code = workplace_data.loc[w, "code"]
                file_path = f"./data/api/api_{path}/{city}/{city}_{path}_{code}.xlsx"
                if not os.path.exists(file_path):
                    data1 = pd.read_excel(
                        f"./data/api/api_{path}/{city}/{city}_{path}_{code}_1.xlsx"
                    )
                    data2 = pd.read_excel(
                        f"./data/api/api_{path}/{city}/{city}_{path}_{code}_2.xlsx"
                    )
                    data = pd.concat([data1, data2], axis=0)
                    data.to_excel(file_path, index=False)
        print(f"Finish {city}")


def parse_transit_files():
    """
    Parse the transit API files and extract relevant information.
    """
    for c in range(len(city_list)):
        city = city_list[c]
        if os.path.exists(f"./data/transit/{city}"):
            print(f"Finish {city}")
        else:
            os.makedirs(f"./data/transit/{city}")
            workplace_data = pd.read_excel(f"../data/workplace/{city}.xlsx")
            for w in range(4):
                code = workplace_data.loc[w, "code"]
                api_data_original = pd.read_excel(
                    f"./data/api/api_transit/{city}/{city}_transit_{code}.xlsx"
                )
                api_data = api_data_original[api_data_original["commuting time/m"] != 0]

                route_info = api_data["route"].tolist()
                invalid_indices = []
                for index, route in enumerate(route_info):
                    if not is_valid_for_literal_eval(route):
                        invalid_indices.append(index)

                df_cleaned = api_data.drop(index=api_data.index[invalid_indices])
                api_data = df_cleaned
                route_info = api_data["route"].tolist()

                walking_time = []
                walking_distance = []
                transit_time = []
                transit_distance = []
                transit_price = []
                commuting_mode = []

                for route in tqdm(route_info):
                    list_route = ast.literal_eval(route)
                    walking_time_1 = []
                    walking_distance_1 = []
                    transit_time_1 = []
                    transit_distance_1 = []
                    transit_price_1 = []
                    commuting_mode_1 = []

                    for each_route in list_route:
                        mode = each_route.get("mode")
                        if mode == "WALKING":
                            commuting_mode_1.append(mode)
                            walking_time_1.append(each_route.get("duration"))
                            walking_distance_1.append(each_route.get("distance"))
                        else:
                            lines = each_route.get("lines")[0]
                            commuting_mode_1.append(lines.get("vehicle"))
                            transit_time_1.append(lines.get("duration"))
                            transit_distance_1.append(lines.get("distance"))
                            price = lines.get("price")
                            if price == -1:
                                transit_price_1.append(0)
                            elif lines.get("vehicle") == "RAIL":
                                transit_price_1.append(price * 100)
                            else:
                                transit_price_1.append(price)

                    walking_time.append(sum(walking_time_1))
                    walking_distance.append(sum(walking_distance_1) / 1000)
                    transit_time.append(sum(transit_time_1))
                    transit_distance.append(sum(transit_distance_1) / 1000)
                    transit_price.append(sum(transit_price_1) / 100)
                    commuting_mode.append(commuting_mode_1)

                new_df = pd.DataFrame(
                    {
                        "commuting_mode": commuting_mode,
                        "walking_time": walking_time,
                        "walking_distance": walking_distance,
                        "transit_price": transit_price,
                        "transit_time": transit_time,
                        "transit_distance": transit_distance,
                    }
                )

                del api_data[api_data.columns[-1]]
                api_data.to_excel(
                    f"./data/transit/{city}/{city}_{code}.xlsx", index=False
                )
                old_df = pd.read_excel(f"./data/transit/{city}/{city}_{code}.xlsx")
                final_df = pd.concat([old_df, new_df], axis=1)
                final_df.to_excel(
                    f"./data/transit/{city}/{city}_{code}.xlsx", index=False
                )
            print(f"Complete the parsing of {city} trainsit")


def merge_driving_and_transit_files():
    """
    Merge driving and transit API files for each city.
    """
    for c in range(len(city_list)):
        city = city_list[c]
        if not os.path.exists(f"./data/driving+transit/{city}"):
            os.makedirs(f"./data/driving+transit/{city}")
        workplace_data = pd.read_excel(f"../data/workplace/{city}.xlsx")
        for w in range(4):
            point_work = workplace_data.loc[w, "lat":"lng"]
            code = workplace_data.loc[w, "code"]

            api_transit_data = pd.read_excel(
                f"./data/transit/{city}/{city}_{code}.xlsx"
            )
            api_transit_data["individual_rent_price"] = (
                api_transit_data["价格(元/月）"] / api_transit_data["室/房间"]
            )
            api_transit_data["commuting_distance"] = (
                api_transit_data["commuting distance/min"] / 1000
            )
            api_transit_data = api_transit_data.rename(
                columns={
                    "commuting distance": "commuting_distance",
                    "commuting time": "commuting_time",
                }
            )

            api_driving_data = pd.read_excel(
                f"./data/driving/{city}/{city}_{code}.xlsx"
            )
            api_driving_data = api_driving_data.drop(
                columns=api_driving_data.columns[7:11], axis=1
            )
            api_driving_data = api_driving_data.drop(
                columns=api_driving_data.columns[3:6], axis=1
            )

            all_data = api_transit_data.merge(
                api_driving_data,
                on=["标题", "价格(元/月）", "总面积(m^2/平方米）", "详细地址"],
                how="left",
            )

            all_data.to_excel(
                f"./data/driving+transit/{city}/{city}_{code}.xlsx", index=False
            )
        print(f"Complete the analysis of {city} driving and transit data")


if __name__ == "__main__":
    merge_api_files()
    parse_transit_files()
    merge_driving_and_transit_files()
