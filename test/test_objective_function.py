import unittest

import pandas as pd
import pulp as pp
from pyuc import objective_function as of
from pyuc import pyuc


class testObjectiveFunctionTerms(unittest.TestCase):
    def setUp(self):
        unit_data = pd.DataFrame(data={
            "Unit": ["U1", "U2"],
            "FuelCost$/GJ": [10/3.6, 20/3.6],
            "VOM$/MWh": [2.5, 6],
            "ThermalEfficiencyFrac": [1, 0.5],
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", list(unit_data.index), master_set=units)
        units_storage = pyuc.Set("units_storage", [], master_set=units)
        units_reserve = pyuc.Set("units_reserve", [], master_set=units)
        units_variable = pyuc.Set("units_variable", [], master_set=units)
        intervals = pyuc.Set("intervals", range(2))
        reserves = pyuc.Set("reserves", [])

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_storage": units_storage,
            "units_reserve": units_reserve,
            "units_variable": units_variable,
            "intervals": intervals,
            "reserves": reserves
        }

        data = {
                "units": unit_data,
                "ValueOfLostLoad$/MWh": 1000,
                "IntervalDurationHrs": 1
            }

        self.problem = {
            "data": data,
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(20)
        self.problem["var"]["power_generated"].var[(0, "U2")].setInitialValue(45)
        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(200)
        self.problem["var"]["power_generated"].var[(1, "U2")].setInitialValue(45)

        self.problem["var"]["unserved_power"].var[(0)].setInitialValue(5)
        self.problem["var"]["unserved_power"].var[(1)].setInitialValue(55)

        self.expected_fuel_cost = (20 + 200) * 10 + (45 + 45) * 20 / 0.5
        self.expected_vom_cost = (20 + 200) * 2.5 + (45 + 45) * 6
        self.expected_unserved_cost = (5 + 55) * 1000

    def test_fuel_cost_term(self):
        result = of.fuel_cost_term(self.problem)
        self.assertEqual(result.value(), self.expected_fuel_cost)

    def test_vom_cost_term(self):
        result = of.vom_cost_term(self.problem)
        self.assertEqual(result.value(), self.expected_vom_cost)

    def test_unserved_energy_cost_term(self):
        result = of.unserved_energy_cost_term(self.problem)
        self.assertEqual(result.value(), self.expected_unserved_cost)

    def test_vom_cost_term_interval_duration(self):
        self.problem["data"]["IntervalDurationHrs"] = 0.5
        result = of.vom_cost_term(self.problem)
        self.assertEqual(result.value(), self.expected_vom_cost*0.5)

    def test_fuel_cost_term_interval_duration(self):
        self.problem["data"]["IntervalDurationHrs"] = 0.5
        result = of.fuel_cost_term(self.problem)
        self.assertEqual(result.value(), self.expected_fuel_cost*0.5)

    def test_unserved_energy_cost_term_interval_duration(self):
        self.problem["data"]["IntervalDurationHrs"] = 0.5
        result = of.unserved_energy_cost_term(self.problem)
        self.assertEqual(result.value(), self.expected_unserved_cost*0.5)


class testObjectiveFunctionUtils(unittest.TestCase):
    def test_heat_rate_calculator(self):
        unit_data = pd.DataFrame(data={
            "Unit": ["U1", "U2"],
            "FuelCost$/GJ": [10, 20],
            "ThermalEfficiencyFrac": [0.5, 0.25]
        }).set_index("Unit")

        result = of.fuel_cost_per_mwh_calculator(unit_data, "U1")
        expected = 3.6*10/0.5

        self.assertEqual(result, expected)
