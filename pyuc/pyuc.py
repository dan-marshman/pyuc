from pyuc import setup_problem as sp


def run_opt_problem(name, input_data_path, output_data_path):
    problem = sp.setup_problem(name, input_data_path, output_data_path)
