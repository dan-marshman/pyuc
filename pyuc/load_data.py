import os

import pandas as pd

from pyuc import pyuc, utils


def load_data(problem):
    """
    Builds the data dictionary, calling necessary functions to read files.

    :param paths dict: paths dictionary
    """

    return {
        "demand": load_demand_data(problem["paths"]["demand"]),
        "units": load_unit_data(problem["paths"]["unit_data"]),
        "variable_traces": load_variable_data(problem["paths"]["variable_traces"]),
        "ValueOfLostLoad$/MWh": load_voll(problem["settings"]),
        "IntervalDurationHrs": load_interval_duration(problem["settings"])
    }


def load_unit_data(unit_data_path):
    """
    Read the unit data csv to a dataframe, with Unit as the index.

    :param unit_data_path str: path to the unit data file.
    """

    utils.check_path_exists(unit_data_path, "Unit Data File")

    return pd.read_csv(unit_data_path, index_col="Unit")


def load_demand_data(demand_data_path):
    """
    Read the demand csv to a dataframe, with Interval as the index.

    :param demand_data_path str: path to the deamnd file.
    """

    utils.check_path_exists(demand_data_path, "Demand File")

    return pd.read_csv(demand_data_path, index_col="Interval")


def load_variable_data(variable_data_path):
    """
    Read the variable generation csv to a dataframe, with Interval as the index.

    :param demand_data_path str: path to the deamnd file.
    """

    if not utils.check_path_exists(variable_data_path, "Variable Trace File"):
        return None
    else:
        return pd.read_csv(variable_data_path, index_col="Interval")


def load_voll(settings):
    """
    Return the value of lost load from the settings file

    :param settings dict: settings dictionary
    """

    return settings["ValueOfLostLoad$/MWh"]


def load_interval_duration(settings):
    """
    Return the interval duration from the settings file

    :param settings dict: settings dictionary
    """

    return settings["IntervalDurationHrs"]


def create_sets(data):
    """
    Load single sets (intervals and units) and combinations.

    :param data dict: Optimisation data
    """

    sets = create_single_sets(data)
    sets = create_subsets(sets, data)
    sets = create_combination_sets(sets)

    return sets


def create_single_sets(data):
    """
    Load sets for intervals and units.

    :param data dict: Optimisation data
    """

    sets = {
        "intervals": pyuc.Set("intervals", data["demand"].index.to_list()),
        "units": pyuc.Set("units", data["units"].index.to_list()),
    }

    return sets


def create_subsets(sets, data):
    def filter_technology(unit_df, selected_techs):
        return unit_df[unit_df.Technology.isin(selected_techs)].index.to_list()

    tech_commit = ["Coal", "CCGT", "OCGT", "Nuclear"]
    tech_variable = ["Wind", "Solar"]
    tech_storage = ["Storage"]

    sets["units_commit"] = \
        pyuc.Set("units_commit",
                 filter_technology(data["units"], tech_commit),
                 sets["units"])

    sets["units_variable"] = \
        pyuc.Set("units_variable",
                 filter_technology(data["units"], tech_variable),
                 sets["units"])

    sets["units_storage"] = \
        pyuc.Set("units_storage",
                 filter_technology(data["units"], tech_storage),
                 sets["units"])

    return sets


def create_combination_sets(sets):
    """
    Combine existing sets for convience.

    :param sets dict: problem sets
    """

    return sets
