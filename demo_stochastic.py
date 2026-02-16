from pyuc import pyuc
from visual import plots

input_data_path = "demo_problem/stochastic"
output_data_path = "demo_problem/stochastic"
name = "PyUC Demo"

pyuc.run_opt_problem(input_data_path, output_data_path, name=name)
plots.plot_dispatch(output_data_path, name=name, plot_price=True, scenario=0)
plots.plot_dispatch(output_data_path, name=name, plot_price=True, scenario=1)
plots.plot_dispatch(output_data_path, name=name, plot_price=True, scenario=2)
