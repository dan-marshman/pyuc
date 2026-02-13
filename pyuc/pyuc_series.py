from pyuc import pyuc
from pyuc import setup_problem as sp
from pyuc import load_data as ld

import math
import sys


def run_series_problem(name, input_path, output_path):
    problem_details = \
        {
            "name": name,
            "input_path": input_path,
            "output_path": output_path,
            "paths": paths
        }

    paths = sp.initialise_paths(input_path, output_path, name)
    settings = sp.load_settings(paths["settings"])
    traces = read_traces(input_path)
    days = get_days(traces, settings["day_length"])

    for day in days:
        filter_traces(traces, settings["day_length"], settings["look_ahead_length"])
        write_current_day_to_folder()
        call_pyuc()
        update_initial_state()


def read_traces_series(paths):
    return {
        "demand": ld.load_demand_data(paths["demand"]),
        "variable_traces": ld.load_variable_data(paths["variable_traces"])
    }


def filter_traces(traces):
    days_traces = {}
    for key, value in traces.items():
        days_traces[key]

    return days_traces


def write_current_day_to_folder():
    pass


def update_initial_state():
    pass


def get_days(traces, day_length):
    def check_len_demand_equals_len_variable_traces():
        if len(traces["demand"]) != len(traces["variable_traces"]):
            print("Length of demand trace and variable traces are unequal")
            sys.exit(1)
        else:
            return

    def get_number_of_days(traces, settings):
        return math.ceil(len(traces["demand"]) / day_length)

    check_len_demand_equals_len_variable_traces()
    number_of_days = get_number_of_days(traces, day_length)

    return number_of_days

def call_pyuc():
    pass
