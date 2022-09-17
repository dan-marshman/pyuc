import csv
import os

import pandas as pd


def run_opt_problem(name, input_data_path, outputs_path=False):
    initialise_problem(name)


def initialise_problem(name):
    """
    Create the problem dictionary, and add its name.

    :param name str: name of the problem
    """

    return {'name': name}


def initialise_paths(input_data_path, output_data_path):
    """
    Make the path dictionary and add paths to the inputs, settings and outputs.

    :param input_data_path str: path to the directory with the input data.
    :param output_data_path str : path to the directory to write the output data.
    """

    paths = {
        'input_data': input_data_path,
        'settings': os.path.join(input_data_path, 'settings.csv'),
        'output_data': output_data_path
    }

    return paths


def load_settings(settings_path):
    """
    Read the settings file and convert each parameter to the appropriate type.

    :param settings_path str: path to the settings file.
    """

    settings = dict()

    with open(settings_path) as f:
        settings_data = csv.DictReader(f)

        for row in settings_data:
            key = row['Parameter']
            key_type = row['Type']
            value = row['Value']

            if key_type == 'int':
                settings[key] = collect_setting_type_integer(value)

            elif key_type == 'bool':
                settings[key] = collect_setting_type_boolean(value)

            elif key_type == 'str':
                settings[key] = collect_setting_type_string(value)

            elif key_type == 'float':
                settings[key] = collect_setting_type_float(value)

    # if 'OUTPUTS_PATH' not in settings.keys():
        # settings['OUTPUTS_PATH'] = os.path.join(os.getcwd(), 'denki-outputs')

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

    if value.lower() == 'false':
        return False

    elif value.lower() == 'true':
        return True
