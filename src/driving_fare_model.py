# -*- coding: utf-8 -*-
"""
Description:
    This module is used to calculate commuting costs in cities where commuting costs in driving mode are not available.
"""

import os

import pandas as pd
from statsmodels.formula.api import ols

import economic_indicators as ei

# Constants
REGRESSION_SUMMARY_COLUMNS = [
    "b",
    "k1",
    "k2",
    "R-squared",
    "Adj. R-squared",
    "F-statistic",
    "Prob (F-statistic)",
    "b-Std. Error",
    "b-t-statistic",
    "b-p-value",
    "b-95% CI Lower",
    "b-95% CI Upper",
    "k1-Std. Error",
    "k1-t-statistic",
    "k1-p-value",
    "k1-95% CI Lower",
    "k1-95% CI Upper",
    "k2-Std. Error",
    "k2-t-statistic",
    "k2-p-value",
    "k2-95% CI Lower",
    "k2-95% CI Upper",
]

# Minimum fare
MIN_FARE = 10


def save_regression_result_to_excel(result, filepath):
    """
    Save regression results to an Excel file.

    :param result: Regression result object

    :param filepath: Path to save the Excel file
    """
    regression_summary = {
        "b": result.params[0],
        "k1": result.params[1],
        "k2": result.params[2],
        "R-squared": result.rsquared,
        "Adj. R-squared": result.rsquared_adj,
        "F-statistic": result.fvalue,
        "Prob (F-statistic)": result.f_pvalue,
        "b-Std. Error": result.bse[0],
        "b-t-statistic": result.tvalues[0],
        "b-p-value": result.pvalues[0],
        "b-95% CI Lower": result.conf_int().iloc[0, 0],
        "b-95% CI Upper": result.conf_int().iloc[1, 0],
        "k1-Std. Error": result.bse[1],
        "k1-t-statistic": result.tvalues[1],
        "k1-p-value": result.pvalues[1],
        "k1-95% CI Lower": result.conf_int().iloc[0, 1],
        "k1-95% CI Upper": result.conf_int().iloc[1, 1],
        "k2-Std. Error": result.bse[2],
        "k2-t-statistic": result.tvalues[2],
        "k2-p-value": result.pvalues[2],
        "k2-95% CI Lower": result.conf_int().iloc[0, 2],
        "k2-95% CI Upper": result.conf_int().iloc[1, 2],
    }

    summary_df = pd.DataFrame(regression_summary, index=[0])
    summary_df = summary_df.round(3)

    with pd.ExcelWriter(filepath, engine="openpyxl", mode="w") as writer:
        summary_df.to_excel(writer, sheet_name="Regression Summary", index=False)

    print(f"Regression results saved to {filepath}")


def main():
    city_list = ei.get_city()

    have_fare_city = []
    no_fare_city = []

    for city in city_list:
        city_dir = f"./data/driving/{city}"
        if not os.path.exists(city_dir):
            os.makedirs(city_dir)

        workplace_data = pd.read_excel(f"../data/workplace/{city}.xlsx")
        all_data = []

        for w in range(4):
            point_work = workplace_data.loc[w, "lat":"lng"]
            code = workplace_data.loc[w, "code"]
            api_data = pd.read_excel(
                f"./data/api/api_driving/{city}/{city}_driving_{code}.xlsx"
            )

            if "commuting distance/min" in api_data.columns:
                api_data["commuting distance/min"] = (
                    api_data["commuting distance/min"] / 1000
                )
                api_data = api_data.rename(
                    columns={
                        "commuting distance/min": "driving_distance/km",
                        "commuting time/m": "driving_time/min",
                        "fare": "driving_fare",
                    }
                )
                api_data.to_excel(
                    f"./data/driving/{city}/{city}_{code}.xlsx", index=False
                )

            fare = api_data["driving_fare"].tolist()
            if fare[0] == 0:
                break
            else:
                if not all_data:
                    all_data = api_data
                else:
                    all_data = pd.concat([all_data, api_data], axis=0)

        if fare[0] == 0:
            no_fare_city.append(city)
            print(f"{city} cannot get taxi fare")
        else:
            have_fare_city.append(city)
            new_df = all_data[
                ["driving_distance/km", "driving_time/min", "driving_fare"]
            ]
            new_df.columns = ["a", "b", "c"]

            model_formula = "c ~ a + b"
            model = ols(model_formula, data=new_df)
            result = model.fit()
            save_regression_result_to_excel(
                result, f"./data/faremodel/{city}-regression_summary.xlsx"
            )
            print(f"Finished {city}")

    results = pd.DataFrame()

    for city in have_fare_city:
        city_df = pd.read_excel(f"./data/faremodel/{city}-regression_summary.xlsx")
        city_df = city_df.assign(city=city).reindex(
            columns=["city"] + REGRESSION_SUMMARY_COLUMNS
        )
        results = pd.concat([results, city_df], axis=0)

    results.to_excel(f"./data/faremodel/all-regression_summary.xlsx", index=False)

    b = results["b"].mean()
    k1 = results["k1"].mean()
    k2 = results["k2"].mean()

    for city in no_fare_city:
        workplace_data = pd.read_excel(f"../data/workplace/{city}.xlsx")

        for w in range(4):
            code = workplace_data.loc[w, "code"]
            api_data = pd.read_excel(f"./data/driving/{city}/{city}_{code}.xlsx")
            api_data["driving_distance/km"] = api_data["driving_distance/km"] / 1000
            api_data["driving_fare"] = api_data.apply(
                lambda row: k1 * row["driving_distance/km"]
                + k2 * row["driving_time/min"]
                + b,
                axis=1,
            )
            api_data["driving_fare"] = (
                api_data["driving_fare"].clip(lower=MIN_FARE).astype(int)
            )
            api_data.to_excel(f"./data/driving/{city}/{city}_{code}.xlsx", index=False)

        print(f"Finished {city} fare calculation")


if __name__ == "__main__":
    main()
