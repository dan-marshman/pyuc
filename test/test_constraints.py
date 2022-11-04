import unittest

import pandas as pd
import pulp as pp
from pyuc import constraints as ca
from pyuc import load_data, pyuc


class BasicConstraintEquations(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={"Demand": [200, 300, 400]})

        unit_data = pd.DataFrame(data={
            "Unit": ["U1", "U2"],
            "CapacityMW": [100, 100],
            "NumUnits": [2, 1],
            "FuelCost$/GJ": [10/3.6, 20/3.6],
            "VOM$/MWh": [1, 1],
            "ThermalEfficiencyFrac": [1, 0.5],
            "MinimumGenerationFrac": [0.5, 0.2],
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units", list(unit_data.index), master_set=units)
        intervals = pyuc.Set("intervals", list(demand.index))

        self.problem = {
            "data": {"demand": demand, "units": unit_data, "ValueOfLostLoad$/MWh": 1000},
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": {"units": units, "units_commit": units_commit, "intervals": intervals},
            "paths": None
        }
        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(20)
        self.problem["var"]["power_generated"].var[(0, "U2")].setInitialValue(45)
        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(200)
        self.problem["var"]["power_generated"].var[(1, "U2")].setInitialValue(45)

        self.problem["var"]["unserved_power"].var[(0)].setInitialValue(5)
        self.problem["var"]["unserved_power"].var[(1)].setInitialValue(55)

        self.problem["var"]["num_committed"].var[(0, "U1")].setInitialValue(1)
        self.problem["var"]["num_committed"].var[(1, "U1")].setInitialValue(2)
        self.problem["var"]["num_committed"].var[(0, "U2")].setInitialValue(1)
        self.problem["var"]["num_committed"].var[(1, "U2")].setInitialValue(0)

        self.problem["var"]["num_starting_up"].var[(0, "U1")].setInitialValue(1)
        self.problem["var"]["num_starting_up"].var[(1, "U1")].setInitialValue(1)
        self.problem["var"]["num_starting_up"].var[(0, "U2")].setInitialValue(1)
        self.problem["var"]["num_starting_up"].var[(1, "U2")].setInitialValue(0)

        self.problem["var"]["num_shutting_down"].var[(0, "U1")].setInitialValue(0)
        self.problem["var"]["num_shutting_down"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["num_shutting_down"].var[(0, "U2")].setInitialValue(0)
        self.problem["var"]["num_shutting_down"].var[(1, "U2")].setInitialValue(1)

    def test_cnt_supply_eq_demand(self):
        constraints = ca.cnt_supply_eq_demand(self.problem)
        self.assertEqual(constraints["supply_eq_demand_(i=0)"].value(), 20+45+5-200)
        self.assertEqual(constraints["supply_eq_demand_(i=1)"].value(), 200+45+55-300)

    def test_cnt_power_lt_capacity(self):
        constraints = ca.cnt_power_lt_capacity(self.problem)

        self.assertEqual(
            constraints["power_lt_capacity_(i=0, u=U1)"].value(),
            20-2*100
        )

        self.assertEqual(
            constraints["power_lt_capacity_(i=1, u=U1)"].value(),
            200-2*100
        )

        self.assertEqual(
            constraints["power_lt_capacity_(i=0, u=U2)"].value(),
            45-1*100
        )

        self.assertEqual(
            constraints["power_lt_capacity_(i=1, u=U2)"].value(),
            45-1*100
        )

    def test_cnt_power_lt_committed_capacity(self):
        constraints = ca.cnt_power_lt_committed_capacity(self.problem)

        self.assertEqual(
            constraints["power_lt_committed_capacity_(i=0, u=U1)"].value(),
            20-1*100
        )

        self.assertEqual(
            constraints["power_lt_committed_capacity_(i=0, u=U2)"].value(),
            45-1*100
        )

        self.assertEqual(
            constraints["power_lt_committed_capacity_(i=1, u=U1)"].value(),
            200-2*100
        )

        self.assertEqual(
            constraints["power_lt_committed_capacity_(i=1, u=U2)"].value(),
            45-0*100
        )

    def test_cnt_power_gt_minimum_generation(self):
        constraints = ca.cnt_power_gt_minimum_generation(self.problem)

        self.assertEqual(
            constraints["power_gt_minimum_generation_(i=0, u=U1)"].value(),
            20-0.5*1*100
        )

        self.assertEqual(
            constraints["power_gt_minimum_generation_(i=1, u=U1)"].value(),
            200-0.5*2*100
        )

        self.assertEqual(
            constraints["power_gt_minimum_generation_(i=0, u=U2)"].value(),
            45-0.2*1*100
        )

        self.assertEqual(
            constraints["power_gt_minimum_generation_(i=1, u=U2)"].value(),
            45-0.2*0*100
        )

    def test_cnt_num_committed_lt_num_units(self):
        constraints = ca.cnt_num_committed_lt_num_units(self.problem)

        self.assertEqual(
            constraints["num_committed_lt_num_units(i=0, u=U1)"].value(),
            1-2
        )

        self.assertEqual(
            constraints["num_committed_lt_num_units(i=1, u=U1)"].value(),
            2-2
        )

        self.assertEqual(
            constraints["num_committed_lt_num_units(i=0, u=U2)"].value(),
            1-1
        )

        self.assertEqual(
            constraints["num_committed_lt_num_units(i=1, u=U2)"].value(),
            0-1
        )

    def test_cnt_commitment_continuity(self):
        constraints = ca.cnt_commitment_continuity(self.problem)

        self.assertEqual(
            constraints["commitment_continuity(i=1, u=U1)"].value(),
            0
        )

        self.assertEqual(
            constraints["commitment_continuity(i=1, u=U2)"].value(),
            2-2
        )

    def test_cnt_commitment_continuity_initial_interval(self):
        constraints = ca.cnt_commitment_continuity_initial_interval(self.problem)

        self.assertEqual(
            constraints["commitment_continuity(i=0, u=U1)"].value(),
            0
        )

        self.assertEqual(
            constraints["commitment_continuity(i=0, u=U2)"].value(),
            2-2
        )


class MinUpAndDownTimes(unittest.TestCase):
    def setUp(self):
        unit_data = pd.DataFrame(data={
            "Unit": ["U1"],
            "NumUnits": [10],
            "MinimumUpTimeHrs": [3],
            "MinimumDownTimeHrs": [2],
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", list(unit_data.index), master_set=units)
        intervals = pyuc.Set("intervals", list(range(24)))
        sets = {"units": units, "units_commit": units_commit, "intervals": intervals}

        self.problem = {
            "data": {"units": unit_data},
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }
        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

        self.problem["var"]["num_starting_up"].var[(0, "U1")].setInitialValue(1)
        self.problem["var"]["num_starting_up"].var[(1, "U1")].setInitialValue(2)
        self.problem["var"]["num_starting_up"].var[(2, "U1")].setInitialValue(3)
        self.problem["var"]["num_starting_up"].var[(3, "U1")].setInitialValue(2)

        self.problem["var"]["num_shutting_down"].var[(0, "U1")].setInitialValue(1)
        self.problem["var"]["num_shutting_down"].var[(1, "U1")].setInitialValue(2)
        self.problem["var"]["num_shutting_down"].var[(2, "U1")].setInitialValue(3)
        self.problem["var"]["num_shutting_down"].var[(3, "U1")].setInitialValue(2)

    def test_minimum_up_time(self):
        constraints = ca.cnt_minimum_up_time(self.problem)

        self.problem["var"]["num_committed"].var[(3, "U1")].setInitialValue(3)
        self.assertEqual(
            constraints["minimum_up_time(i=3, u=U1)"].value(),
            3 - (2 + 3 + 2)
        )

        self.problem["var"]["num_committed"].var[(3, "U1")].setInitialValue(7)
        self.assertEqual(
            constraints["minimum_up_time(i=3, u=U1)"].value(),
            7 - (2 + 3 + 2)
        )

    def test_minimum_down_time(self):
        constraints = ca.cnt_minimum_down_time(self.problem)

        self.problem["var"]["num_committed"].var[(3, "U1")].setInitialValue(6)
        self.assertEqual(
            constraints["minimum_down_time(i=3, u=U1)"].value(),
            10 - 6 - (2 + 3)
        )

        self.problem["var"]["num_committed"].var[(3, "U1")].setInitialValue(5)
        self.assertEqual(
            constraints["minimum_down_time(i=3, u=U1)"].value(),
            10- 5 - (2 + 3)
        )


class RampRates(unittest.TestCase):
    def setUp(self):
        unit_data = pd.DataFrame(data={
            "Unit": ["U1"],
            "NumUnits": [10],
            "CapacityMW": [100],
            "RampRate_pctCapphr": [0.2],
            "MinimumGenerationFrac": [0.6],
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", list(unit_data.index), master_set=units)
        intervals = pyuc.Set("intervals", list(range(2)))
        sets = {"units": units, "units_commit": units_commit, "intervals": intervals}

        self.problem = {
            "data": {"units": unit_data},
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }
        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

    def test_ramp_rate_up_committed_only(self):
        self.problem["var"]["num_committed"].var[(1, "U1")].setInitialValue(2)
        self.problem["var"]["num_starting_up"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["num_shutting_down"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(140)
        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(180)

        constraints = ca.cnt_ramp_rate_up(self.problem)
        self.assertEqual(constraints["ramp_rate_up_(i=1, u=U1)"].value(), 0)

    def test_ramp_rate_up_starting_up(self):
        self.problem["var"]["num_committed"].var[(1, "U1")].setInitialValue(2)
        self.problem["var"]["num_starting_up"].var[(1, "U1")].setInitialValue(1)
        self.problem["var"]["num_shutting_down"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(60)
        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(140)

        constraints = ca.cnt_ramp_rate_up(self.problem)
        self.assertEqual(constraints["ramp_rate_up_(i=1, u=U1)"].value(), 0)

    def test_ramp_rate_up_shutting_down(self):
        self.problem["var"]["num_committed"].var[(1, "U1")].setInitialValue(1)
        self.problem["var"]["num_starting_up"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["num_shutting_down"].var[(1, "U1")].setInitialValue(1)
        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(120)
        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(80)

        constraints = ca.cnt_ramp_rate_up(self.problem)
        self.assertEqual(constraints["ramp_rate_up_(i=1, u=U1)"].value(), 0)

    def test_ramp_rate_down_committed_only(self):
        self.problem["var"]["num_committed"].var[(1, "U1")].setInitialValue(2)
        self.problem["var"]["num_starting_up"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["num_shutting_down"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(180)
        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(140)

        constraints = ca.cnt_ramp_rate_down(self.problem)
        self.assertEqual(constraints["ramp_rate_down_(i=1, u=U1)"].value(), 0)

    def test_ramp_rate_down_starting_up(self):
        self.problem["var"]["num_committed"].var[(1, "U1")].setInitialValue(2)
        self.problem["var"]["num_starting_up"].var[(1, "U1")].setInitialValue(1)
        self.problem["var"]["num_shutting_down"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(140)
        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(180)

        constraints = ca.cnt_ramp_rate_down(self.problem)
        self.assertEqual(constraints["ramp_rate_down_(i=1, u=U1)"].value(), 0)

    def test_ramp_rate_down_shutting_down(self):
        self.problem["var"]["num_committed"].var[(1, "U1")].setInitialValue(1)
        self.problem["var"]["num_starting_up"].var[(1, "U1")].setInitialValue(0)
        self.problem["var"]["num_shutting_down"].var[(1, "U1")].setInitialValue(1)
        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(120)
        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(40)

        constraints = ca.cnt_ramp_rate_down(self.problem)
        self.assertEqual(constraints["ramp_rate_down_(i=1, u=U1)"].value(), 0)


class VariableResourceConstraints(unittest.TestCase):
    def setUp(self):
        unit_data = pd.DataFrame(
            data={
                "Unit": ["W", "S"],
                "Technology": ["Wind", "Solar"],
                "NumUnits": [1, 2],
                "CapacityMW": [100, 200]
            }
        ).set_index("Unit")

        variable_traces = pd.DataFrame(
            data={
                "Wind": [0.2, 0.4],
                "Solar": [0.3, 0.5]
            }
        )

        units = pyuc.Set("units", list(unit_data.index))
        units_variable = pyuc.Set("units_variable", list(unit_data.index), master_set=units)
        intervals = pyuc.Set("intervals", list(range(2)))
        sets = {"units": units, "units_variable": units_variable, "intervals": intervals}

        self.problem = {
            "data": {"units": unit_data, "variable_traces": variable_traces},
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

    def test_variable_power_lt_resource_availability(self):
        self.problem["var"]["power_generated"].var[(0, "W")].setInitialValue(0.2*1*100)
        self.problem["var"]["power_generated"].var[(1, "W")].setInitialValue(0.4*1*100)
        self.problem["var"]["power_generated"].var[(0, "S")].setInitialValue(0.3*2*200)
        self.problem["var"]["power_generated"].var[(1, "S")].setInitialValue(0.5*2*200)

        constraints = ca.cnt_variable_resource_availability(self.problem)
        self.assertEqual(constraints["variable_resource_availability(i=0, u=W)"].value(), 0)
        self.assertEqual(constraints["variable_resource_availability(i=1, u=W)"].value(), 0)
        self.assertEqual(constraints["variable_resource_availability(i=0, u=S)"].value(), 0)
        self.assertEqual(constraints["variable_resource_availability(i=1, u=S)"].value(), 0)


class UnitTypeConstraintSets(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={"Demand": [200]})

        self.units = ["Coal", "CCGT", "OCGT", "Nuclear", "Wind", "Solar", "Storage"]

        self.unit_data = pd.DataFrame(
            data={
                "Unit": self.units,
                "Technology": self.units,
                "CapacityMW": [100] * len(self.units),
                "NumUnits": [1] * len(self.units),
                "FuelCost$/GJ": [1] * len(self.units),
                "MinimumGenerationFrac": [1] * len(self.units),
                "MinimumUpTimeHrs": [1] * len(self.units),
                "MinimumDownTimeHrs": [1] * len(self.units),
                "RampRate_pctCapphr": [1] * len(self.units)
            }
        ).set_index("Unit")

        variable_traces = pd.DataFrame(data={"Wind": [1], "Solar": [1]})

        data = {"demand": demand,
                "units": self.unit_data,
                "variable_traces": variable_traces,
                "ValueOfLostLoad$/MWh": 1000}
        sets = load_data.create_sets(data)

        self.problem = {
            "data": data,
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

    def test_sets_cnt_power_lt_capacity(self):
        constraints = ca.cnt_power_lt_capacity(self.problem)
        expected = [f"power_lt_capacity_(i=0, u={u})" for u in self.units]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_power_lt_committed_capacity(self):
        constraints = ca.cnt_power_lt_committed_capacity(self.problem)
        expected = [f"power_lt_committed_capacity_(i=0, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_power_gt_minimum_generation(self):
        constraints = ca.cnt_power_gt_minimum_generation(self.problem)
        expected = [f"power_gt_minimum_generation_(i=0, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_num_committed_lt_num_units(self):
        constraints = ca.cnt_num_committed_lt_num_units(self.problem)
        expected = [f"num_committed_lt_num_units(i=0, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_commitment_continuity(self):
        demand = pd.DataFrame(data={"Demand": [200, 200]})
        data = {"demand": demand, "units": self.unit_data, "ValueOfLostLoad$/MWh": 1000}
        sets = load_data.create_sets(data)

        self.problem = {
            "data": data,
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }
        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

        constraints = ca.cnt_commitment_continuity(self.problem)
        expected = [f"commitment_continuity(i=1, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_commitment_continuity_initial_interval(self):
        constraints = ca.cnt_commitment_continuity_initial_interval(self.problem)
        expected = [f"commitment_continuity(i=0, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_minimum_up_time(self):
        constraints = ca.cnt_minimum_up_time(self.problem)
        expected = [f"minimum_up_time(i=0, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_minimum_down_time(self):
        constraints = ca.cnt_minimum_down_time(self.problem)
        expected = [f"minimum_down_time(i=0, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_ramp_rate_up(self):
        constraints = ca.cnt_ramp_rate_up(self.problem)
        expected = [f"ramp_rate_up_(i=0, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_ramp_rate_down(self):
        constraints = ca.cnt_ramp_rate_down(self.problem)
        expected = [f"ramp_rate_down_(i=0, u={u})" for u in self.units[:4]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_variable_resource_availability(self):
        constraints = ca.cnt_variable_resource_availability(self.problem)
        expected = [f"variable_resource_availability(i=0, u={u})"
                    for u in ["Wind", "Solar"]]
        result = list(constraints.keys())
        self.assertEqual(result, expected)


class OtherConstraintTests(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={"Demand": [200, 300, 400]})

        unit_data = pd.DataFrame(data={
            "Unit": ["U1", "U2"],
            "CapacityMW": [100, 100],
            "NumUnits": [2, 1],
            "FuelCost$/GJ": [10/3.6, 20/3.6],
            "VOM$/MWh": [1, 1],
            "ThermalEfficiencyFrac": [1, 0.5],
            "MinimumGenerationFrac": [0.5, 0.2],
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units", list(unit_data.index), master_set=units)
        intervals = pyuc.Set("intervals", list(demand.index))
        sets = {"units": units, "units_commit": units_commit, "intervals": intervals}

        self.problem = {
            "data": {"demand": demand, "units": unit_data, "ValueOfLostLoad$/MWh": 1000},
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

    def test_cnt_commitment_continuity_ignores_first_interval(self):
        constraints = ca.cnt_commitment_continuity(self.problem)

        self.assertFalse("commitment_continuity(i=0, u=U1)" in constraints.keys())
        self.assertFalse("commitment_continuity(i=0, u=U2)" in constraints.keys())

    def test_cnt_commitment_continuity_init_int_only_uses_first_int(self):
        constraints = ca.cnt_commitment_continuity_initial_interval(self.problem)

        expected = [
            "commitment_continuity(i=0, u=U1)",
            "commitment_continuity(i=0, u=U2)",
        ]

        self.assertEqual(list(constraints.keys()), expected)


class OtherFunctions(unittest.TestCase):
    def setUp(self):
        unit_data = pd.DataFrame(data={
            "Unit": ["U1", "U2"],
            "CapacityMW": [100, 80],
            "MinimumUpTimeHrs": [3, 2],
            "MinimumDownTimeHrs": [2, 2],
            "RampRate_pctCapphr": [0.5, 0.4],
            "MinimumGenerationFrac": [0.6, 0.3]
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        intervals = pyuc.Set("intervals", list(range(6)))

        self.problem = {
            "data": {"units": unit_data, "ValueOfLostLoad$/MWh": 1000},
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": {"units": units, "intervals": intervals},
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

    def test_total_power_in_interval(self):
        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(20)
        self.problem["var"]["power_generated"].var[(0, "U2")].setInitialValue(45)

        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(200)
        self.problem["var"]["power_generated"].var[(1, "U2")].setInitialValue(45)

        total_power_in_interval = \
            ca.total_power_in_interval(self.problem["sets"],
                                       self.problem["var"]["power_generated"])

        self.assertEqual(total_power_in_interval[0].value(), 20+45)
        self.assertEqual(total_power_in_interval[1].value(), 200+45)

    def test_num_start_ups_calculator(self):
        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]

        var["num_starting_up"].var[(0, "U1")].setInitialValue(0)
        var["num_starting_up"].var[(1, "U1")].setInitialValue(1)
        var["num_starting_up"].var[(2, "U1")].setInitialValue(2)
        var["num_starting_up"].var[(3, "U1")].setInitialValue(1)
        var["num_starting_up"].var[(4, "U1")].setInitialValue(0)

        num_start_ups_within_up_time = \
            ca.num_start_ups_within_up_time_calculator(sets, data, var)

        self.assertEqual(num_start_ups_within_up_time[(0, "U1")].value(), 0)
        self.assertEqual(num_start_ups_within_up_time[(1, "U1")].value(), 1)
        self.assertEqual(num_start_ups_within_up_time[(2, "U1")].value(), 3)
        self.assertEqual(num_start_ups_within_up_time[(3, "U1")].value(), 4)
        self.assertEqual(num_start_ups_within_up_time[(4, "U1")].value(), 3)

        result_keys = list(num_start_ups_within_up_time.keys())
        expected_keys = [
            (i, u) for i in sets["intervals"].indices for u in sets["units"].indices
        ]

        self.assertEqual(result_keys, expected_keys)

    def test_num_shut_downs_calculator(self):
        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]

        var["num_shutting_down"].var[(0, "U1")].setInitialValue(0)
        var["num_shutting_down"].var[(1, "U1")].setInitialValue(1)
        var["num_shutting_down"].var[(2, "U1")].setInitialValue(2)
        var["num_shutting_down"].var[(3, "U1")].setInitialValue(1)
        var["num_shutting_down"].var[(4, "U1")].setInitialValue(0)

        num_shut_downs_within_down_time = \
            ca.num_shut_downs_within_down_time_calculator(sets, data, var)

        self.assertEqual(num_shut_downs_within_down_time[(0, "U1")].value(), 0)
        self.assertEqual(num_shut_downs_within_down_time[(1, "U1")].value(), 1)
        self.assertEqual(num_shut_downs_within_down_time[(2, "U1")].value(), 3)
        self.assertEqual(num_shut_downs_within_down_time[(3, "U1")].value(), 3)
        self.assertEqual(num_shut_downs_within_down_time[(4, "U1")].value(), 1)

        result_keys = list(num_shut_downs_within_down_time.keys())
        expected_keys = [
            (i, u) for i in sets["intervals"].indices for u in sets["units"].indices
        ]

        self.assertEqual(result_keys, expected_keys)

    def test_up_ramp_calculator_all_intervals_and_units(self):
        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]
        up_ramp = ca.up_ramp_calculator(sets, data, var)

        result_keys = list(up_ramp.keys())
        expected_keys = [
            (i, u) for i in sets["intervals"].indices for u in sets["units"].indices
        ]

        self.assertEqual(sorted(result_keys), sorted(expected_keys))

    def test_up_ramp_calculator_second_interval(self):
        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]

        var["power_generated"].var[(0, "U1")].setInitialValue(20)
        var["power_generated"].var[(1, "U1")].setInitialValue(45)

        up_ramp = ca.up_ramp_calculator(sets, data, var)
        self.assertEqual(up_ramp[(1, "U1")].value(), 45-20)

    def test_down_ramp_calculator_all_intervals_and_units(self):
        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]
        down_ramp = ca.down_ramp_calculator(sets, data, var)

        result_keys = list(down_ramp.keys())
        expected_keys = [
            (i, u) for i in sets["intervals"].indices for u in sets["units"].indices
        ]

        self.assertEqual(sorted(result_keys), sorted(expected_keys))

    def test_down_ramp_calculator_second_interval(self):
        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]

        var["power_generated"].var[(0, "U1")].setInitialValue(20)
        var["power_generated"].var[(1, "U1")].setInitialValue(45)

        down_ramp = ca.down_ramp_calculator(sets, data, var)
        self.assertEqual(down_ramp[(1, "U1")].value(), 20-45)

    def test_online_ramp_calculator(self):
        sets, data = self.problem["sets"], self.problem["data"]
        online_ramp_capacityMW = ca.online_ramp_capacity_calculator(sets, data)

        self.assertEqual(online_ramp_capacityMW["U1"], 0.5*100)
        self.assertEqual(online_ramp_capacityMW["U2"], 0.4*80)

    def test_start_up_ramp_capacity_calculator(self):
        sets, data = self.problem["sets"], self.problem["data"]
        start_up_ramp_capacityMW = ca.start_up_ramp_capacity_calculator(sets, data)

        self.assertEqual(start_up_ramp_capacityMW["U1"], 0.6*100)
        self.assertEqual(start_up_ramp_capacityMW["U2"], 0.4*80)

    def test_shut_down_ramp_capacity_calculator(self):
        sets, data = self.problem["sets"], self.problem["data"]
        shut_down_ramp_capacityMW = ca.shut_down_ramp_capacity_calculator(sets, data)

        self.assertEqual(shut_down_ramp_capacityMW["U1"], 0.6*100)
        self.assertEqual(shut_down_ramp_capacityMW["U2"], 0.4*80)

    def test_minimum_generation_calculator(self):
        sets, data = self.problem["sets"], self.problem["data"]
        minimum_generationMW = ca.minimum_generation_calculator(sets, data)

        self.assertEqual(minimum_generationMW["U1"], 0.6*100)
