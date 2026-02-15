from pyuc import pyuc
from visual import plots

input_data_path = "demo_problem"
output_data_path = "demo_problem"
name = "PYUC Demo"

pyuc.run_opt_problem(input_data_path, output_data_path, name=name)
plots.plot_dispatch(output_data_path, name=name, plot_price=True)
