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
        "initial_state": load_initial_state(problem["paths"]["initial_state"]),
        "ValueOfLostLoad$/MWh": load_voll(problem["settings"]),
        "IntervalDurationHrs": load_interval_duration(problem["settings"])
    }


def load_unit_data(unit_data_path):
    """
    Read the unit data csv to a dataframe, with Unit as the index.

    :param unit_data_path str: path to the unit data file.
    """

    utils.check_path_exists(unit_data_path, "Unit Data File")

    return pd.read_csv(unit_data_path, index_col="Unit").fillna(0)


def load_demand_data(demand_data_path):
    """
    Read the demand csv to a dataframe, with Interval as the index.

    :param demand_data_path str: path to the deamnd file.
    """

    utils.check_path_exists(demand_data_path, "Demand File")

    return pd.read_csv(demand_data_path, index_col="Interval")


def load_variable_data(variable_trace_path):
    """
    Read the variable generation csv to a dataframe, with Interval as the index.

    :param demand_data_path str: path to the deamnd file.
    """

    if not utils.check_path_exists(variable_trace_path, "Variable Trace File"):
        return None
    else:
        return pd.read_csv(variable_trace_path, index_col="Interval")


def load_initial_state(initial_state_path):
    """
    Read the initial state file to a dataframe, with Interval as the index.

    :param demand_data_path str: path to the deamnd file.
    """

    if not utils.check_path_exists(
        initial_state_path,
        "Initial State File",
        required_file=False
    ):

        return None
    else:
        df = pd.read_csv(initial_state_path, index_col=[0], header=[0, 1])
        df.columns = df.columns.set_levels(df.columns.levels[1].astype(int), level=1)

        return df


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


def create_sets(data, reserve_opt=None):
    """
    Load single sets (intervals and units) and combinations.

    :param data dict: Optimisation data
    """

    sets = create_single_sets(data, reserve_opt)
    sets = create_subsets(sets, data)
    sets = create_combination_sets(sets)

    return sets


def create_single_sets(data, reserve_opt=None):
    """
    Load sets for intervals and units.

    :param data dict: Optimisation data
    :param settings dict: Settings dict
    :param reserve_opt None, str or list: specifies which types of reserve to include
    """

    reserve_opts = {"None": [], None: [], "RaiseAndLower": ["raise", "lower"]}

    if reserve_opt in reserve_opts.keys():
        reserves = reserve_opts[reserve_opt]
    else:
        reserves = []

    sets = {
        "intervals": pyuc.Set("intervals", data["demand"].index.to_list()),
        "units": pyuc.Set("units", data["units"].index.to_list()),
        "reserves": pyuc.Set("reserves", reserves),
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

    sets["units_reserve"] = \
        pyuc.Set("units_reserve",
                 filter_technology(data["units"], tech_storage+tech_commit),
                 sets["units"])

    return sets


def create_combination_sets(sets):
    """
    Combine existing sets for convience.

    :param sets dict: problem sets
    """

    return sets
