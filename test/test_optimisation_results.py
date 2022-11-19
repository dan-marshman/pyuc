import unittest

import mock
import pandas as pd
import pulp as pp
from pyuc import constraint_adder as ca
from pyuc import objective_function, pyuc


class testThermal(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={"Demand": [200, 300, 400]})

        unit_data = pd.DataFrame(data={
            "Unit": ["U1", "U2"],
            "Technology": ["Coal", "Coal"],
            "CapacityMW": [100, 100],
            "NumUnits": [2, 1],
            "FuelCost$/GJ": [10/3.6, 20/3.6],
            "VOM$/MWh": [1, 1],
            "ThermalEfficiencyFrac": [1, 0.5],
            "MinimumGenerationFrac": [1, 1],
            "MinimumUpTimeHrs": [1, 1],
            "MinimumDownTimeHrs": [1, 1],
            "RampRate_pctCapphr": [1, 1],
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", list(unit_data.index), master_set=units)
        units_variable = pyuc.Set("units_variable", [], master_set=units)
        units_storage = pyuc.Set("units_storage", [], master_set=units)
        intervals = pyuc.Set("intervals", list(demand.index))

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_storage": units_storage,
            "units_variable": units_variable,
            "intervals": intervals
        }

        self.problem = {
            "data": {
                "demand": demand,
                "units": unit_data,
                "initial_state": None,
                "ValueOfLostLoad$/MWh": 1000,
                "IntervalDurationHrs": 0.5
            },
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])
        self.constraint_list = ca.make_constraint_index()
        self.constraint_list["ToInclude"] = True

    @mock.patch("pyuc.constraint_adder.constraint_selector")
    def test_thermal_problem1(self, constraint_selector_mock):
        constraint_selector_mock.return_value = self.constraint_list
        self.problem["problem"] = ca.add_constraints(self.problem)
        self.problem["problem"]  \
            = objective_function.make_objective_function(self.problem)
        self.problem["problem"].solve(solver=pp.apis.PULP_CBC_CMD(msg=False))

        # Unit 1: 3 hours producing 200 MW.
        # Unit 2: 2 hour producing 100 MW.
        # Unserved Energy: 1 hour producing 100 MW.
        expected = (200*(10+1)*3) + (100*(40+1)*2) + (100*1000*1)
        expected *= 0.5  # Interval Duration
        result = self.problem["problem"].objective.value()

        self.assertEqual(result, expected)


class testVariableAndStorage(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={"Demand": [200, 181, 100]})
        wind_trace = pd.DataFrame(data={"Wind": [1, 0, 0]})

        unit_data = pd.DataFrame(data={
            "Unit": ["U1", "W1", "B1"],
            "Technology": ["Coal", "Wind", "Battery"],
            "CapacityMW": [100, 300, 100],
            "NumUnits": [1, 1, 1],
            "FuelCost$/GJ": [5/3.6, 0, 0],
            "VOM$/MWh": [0, 1, 0],
            "ThermalEfficiencyFrac": [0.5, 0, 0],
            "MinimumGenerationFrac": [1, 0, 0],
            "MinimumUpTimeHrs": [1, 1, 0],
            "MinimumDownTimeHrs": [1, 1, 0],
            "RampRate_pctCapphr": [1, 1, 0],
            "RoundTripEfficiencyFrac": [1, 0, 0.8],
            "StorageHrs": [0, 0, 1],
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", ["U1"], master_set=units)
        units_variable = pyuc.Set("units_variable", ["W1"], master_set=units)
        units_storage = pyuc.Set("units_storage", ["B1"], master_set=units)
        intervals = pyuc.Set("intervals", list(demand.index))

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_storage": units_storage,
            "units_variable": units_variable,
            "intervals": intervals
        }

        data = {
                "demand": demand,
                "units": unit_data,
                "variable_traces": wind_trace,
                "initial_state": None,
                "ValueOfLostLoad$/MWh": 1000,
                "IntervalDurationHrs": 0.5
            }

        self.problem = {
            "data": data,
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])
        self.constraint_list = ca.make_constraint_index()
        self.constraint_list["ToInclude"] = True

    @mock.patch("pyuc.constraint_adder.constraint_selector")
    def test_variable_with_storage_problem1(self, constraint_selector_mock):
        constraint_selector_mock.return_value = self.constraint_list
        self.problem["problem"] = ca.add_constraints(self.problem)
        self.problem["problem"]  \
            = objective_function.make_objective_function(self.problem)
        self.problem["problem"].solve(solver=pp.apis.PULP_CBC_CMD(msg=False))

        # Unit U1: 0 in hour 1, 100 in hours 2 and 3
        # Unit W1: 300 in hour 1, 0 in hours 2 and 3
        # Unit B1: 80 in hour 2, 0 in hours 2 and 3
        # Unserved Energy: 1 MW in hour 2
        expected = 2 * 100 * 10 + 300 * 1 + 1000*1
        expected *= 0.5  # Interval Duration
        result = self.problem["problem"].objective.value()

        self.assertEqual(result, expected)
