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
        'output_data': output_data_path
    }

    paths['settings'] = os.path.join(paths['input_data'], 'settings.csv')

    return paths


def load_settings(settings_path):
    settings_data = read_settings_file(settings_path)

    settings = dict()

    for row in settings_data:
        if row['Type'] == 'int':
            settings.setdefault(row['Parameter'], int(row['Value']))

        if row['Type'] == 'bool':
            val = row['Value'].lower()

            if val == 'false':
                settings.setdefault(row['Parameter'], False)
            elif val == 'true':
                settings.setdefault(row['Parameter'], True)

        if row['Type'] == 'str':
            settings.setdefault(row['Parameter'], str(row['Value']))

        if row['Type'] == 'float':
            settings.setdefault(row['Parameter'], float(row['Value']))

    if 'OUTPUTS_PATH' not in settings.keys():
        settings['OUTPUTS_PATH'] = os.path.join(os.getcwd(), 'denki-outputs')

    return settings


def read_settings_file(settings_path):
    """
    Read the data rom the settings CSV file

    :param settings_path path: path to the problem's settings file
    """
    settings_data = pd.read_csv(settings_path)

    return settings_data
