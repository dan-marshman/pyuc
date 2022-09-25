import os

import pandas as pd

from pyuc import pyuc, utils


def load_data(paths):
    """
    Builds the data dictionary, calling necessary functions to read files.

    :param paths dict: paths dictionary
    """

    return {
        'demand': load_demand_data(paths['demand']),
        'unit_data': load_unit_data(paths['unit_data']),
    }


def load_unit_data(unit_data_path):
    """
    Read the unit data csv to a dataframe, with Unit as the index.

    :param unit_data_path str: path to the unit data file.
    """

    utils.check_path_exists(unit_data_path, 'Unit Data File')

    return pd.read_csv(unit_data_path, index_col='Unit')


def load_demand_data(demand_data_path):
    """
    Read the demand csv to a dataframe, with Unit as the index.

    :param demand_data_path str: path to the deamnd file.
    """

    utils.check_path_exists(demand_data_path, 'Demand File')

    return pd.read_csv(demand_data_path, index_col='Interval')


def create_sets(data):
    """
    Load single sets (intervals and units) and combinations.

    :param data dict: Optimisation data
    """

    sets = create_single_sets(data)
    sets = create_combination_sets(data)

    return sets


def create_single_sets(data):
    """
    Load sets for intervals and units.

    :param data dict: Optimisation data
    """

    sets = {
        'intervals': pyuc.Set('intervals', data['demand'].index.to_list()),
        'units': pyuc.Set('units', data['units'].index.to_list()),
    }

    return sets


def create_combination_sets(sets):
    """
    Combine existing sets for convience.

    :param sets dict: problem sets
    """
