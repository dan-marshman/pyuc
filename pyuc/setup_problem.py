import csv
import os
import shutil

import pulp as pp

from pyuc import utils


def load_settings(settings_path):
    """
    Load settings function.

    :param settings_path str: path to the settings file.
    """

    utils.check_path_exists(settings_path, "Settings File")
    settings = import_settings_file(settings_path)
    settings = validate_settings(settings)

    return settings


def validate_settings(settings):
    if "reserves" not in settings.keys():
        settings["reserves"] = None

    return settings


def import_settings_file(settings_path):
    """
    Read the settings file and convert each parameter to the appropriate type.

    :param settings_path str: path to the settings file.
    """

    settings = dict()

    with open(settings_path) as f:
        settings_data = csv.DictReader(f)

        for row in settings_data:
            key = row["Parameter"]
            key_type = row["Type"]
            value = row["Value"]

            if key_type == "int":
                settings[key] = collect_setting_type_integer(value)

            elif key_type == "bool":
                settings[key] = collect_setting_type_boolean(value)

            elif key_type == "str":
                settings[key] = collect_setting_type_string(value)

            elif key_type == "float":
                settings[key] = collect_setting_type_float(value)

    return settings


def collect_setting_type_integer(value):
    """
    Change the setting value to an integer.

    :param value float or int: value to be converted.
    """

    return int(value)


def collect_setting_type_float(value):
    """
    Change the setting value to an float.

    :param value float or int: value to be converted.
    """

    return float(value)


def collect_setting_type_string(value):
    """
    Change the setting value to an string.

    :param value string, float or int: value to be converted.
    """

    return str(value)


def collect_setting_type_boolean(value):
    """
    Change the setting value to an integer.

    :param value str: value to be converted.
    """

    if value.lower() == "false":
        return False

    elif value.lower() == "true":
        return True


def initialise_uc_problem(name):
    """
    Create the problem dictionary, and add its name.

    :param name str: name of the problem
    """

    return {"name": name}


def initialise_paths(input_data_path, output_data_path, name):
    """
    Make the path dictionary and add paths to the inputs, settings and outputs, etc.

    :param input_data_path str: path to the directory with the input data.
    :param output_data_path str : path to the directory to write the output data.
    :param name str : name of the problem.
    """

    paths = {
        "input_data": input_data_path,
        "settings": os.path.join(input_data_path, "settings.csv"),
        "unit_data": os.path.join(input_data_path, "unit_data.csv"),
        "variable_traces": os.path.join(input_data_path, "variable_traces.csv"),
        "initial_state": os.path.join(input_data_path, "initial_state.csv"),
        "demand": os.path.join(input_data_path, "demand.csv"),
        "reserve_requirement": os.path.join(input_data_path, "reserve_requirement.csv"),
        "constraint_list": os.path.join(input_data_path, "constraint_list.csv"),
        "outputs": os.path.join(output_data_path, name),
        "results": os.path.join(output_data_path, name, "results"),
    }

    return paths


def make_pulp_problem(name):
    """
    Initiate the pulp problem

    :param name str: Name of problem for pulp
    """
    return pp.LpProblem(name=name, sense=pp.LpMinimize)


def make_results_folders(paths):
    """
    Make results folders, removing existing ones if relevant

    :param paths dict: dict of paths
    """
    for dir in [paths["outputs"], paths["results"]]:
        if os.path.exists(dir):
            shutil.rmtree(dir)
        os.makedirs(dir)


def setup_problem(name, input_data_path, output_data_path):
    """
    Take the steps to set up the problem.

    :param name str: problem name
    :param input_data_path str: path to data inputs
    :param output_data_path str: path to save outputs
    """

    problem = initialise_uc_problem(name)
    problem["paths"] = initialise_paths(input_data_path, output_data_path, name)
    problem["settings"] = load_settings(problem["paths"]["settings"])
    problem["problem"] = make_pulp_problem(name)
    make_results_folders(problem["paths"])

    return problem
