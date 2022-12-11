import unittest

import numpy as np
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

        initial_state = pd.DataFrame(
            np.array([[0], [2]]),
            columns=pd.MultiIndex.from_tuples([("num_committed", -1)]),
            index=["U1", "U2"]
        )

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", list(unit_data.index), master_set=units)
        units_variable = pyuc.Set("units_variable", [], master_set=units)
        units_storage = pyuc.Set("units_storage", [], master_set=units)
        units_reserve = pyuc.Set("units_reserve", [], master_set=units)
        intervals = pyuc.Set("intervals", list(range(3)))
        reserves = pyuc.Set("reserves", [])

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_variable": units_variable,
            "units_storage": units_storage,
            "units_reserve": units_reserve,
            "intervals": intervals,
            "reserves": reserves
        }

        data = {
            "demand": demand,
            "initial_state": initial_state,
            "units": unit_data,
            "ValueOfLostLoad$/MWh": 1000
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
            -2
        )


class MinUpAndDownTimes(unittest.TestCase):
    def setUp(self):
        unit_data = pd.DataFrame(data={
            "Unit": ["U1"],
            "NumUnits": [10],
            "MinimumUpTimeHrs": [3],
            "MinimumDownTimeHrs": [2],
        }).set_index("Unit")

        initial_state = pd.DataFrame(
            np.array([[2, 1, 5]]),
            columns=pd.MultiIndex.from_tuples([
                ("num_starting_up", -2), ("num_starting_up", -1), ("num_shutting_down", -1)]),
            index=["U1"]
        )

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", list(unit_data.index), master_set=units)
        units_variable = pyuc.Set("units_variable", [], master_set=units)
        units_storage = pyuc.Set("units_storage", [], master_set=units)
        units_reserve = pyuc.Set("units_reserve", [], master_set=units)
        intervals = pyuc.Set("intervals", list(range(24)))
        reserves = pyuc.Set("reserves", [])

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_variable": units_variable,
            "units_storage": units_storage,
            "units_reserve": units_reserve,
            "intervals": intervals,
            "reserves": reserves
        }

        self.problem = {
            "data": {"units": unit_data, "initial_state": initial_state},
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

        self.problem["var"]["num_committed"].var[(0, "U1")].setInitialValue(3)
        self.assertEqual(
            constraints["minimum_up_time(i=0, u=U1)"].value(),
            3 - (2 + 1 + 1)
        )

        self.problem["var"]["num_committed"].var[(3, "U1")].setInitialValue(3)
        self.assertEqual(
            constraints["minimum_up_time(i=3, u=U1)"].value(),
            3 - (2 + 3 + 2)
        )

    def test_minimum_down_time(self):
        constraints = ca.cnt_minimum_down_time(self.problem)

        self.problem["var"]["num_committed"].var[(0, "U1")].setInitialValue(6)
        self.assertEqual(
            constraints["minimum_down_time(i=0, u=U1)"].value(),
            (10 - 6) - (5 + 1)
        )

        self.problem["var"]["num_committed"].var[(3, "U1")].setInitialValue(6)
        self.assertEqual(
            constraints["minimum_down_time(i=3, u=U1)"].value(),
            (10 - 6) - (2 + 3)
        )

        self.problem["var"]["num_committed"].var[(3, "U1")].setInitialValue(5)
        self.assertEqual(
            constraints["minimum_down_time(i=3, u=U1)"].value(),
            (10 - 5) - (2 + 3)
        )


class RampRatesConstraints(unittest.TestCase):
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
        units_variable = pyuc.Set("units_variable", [], master_set=units)
        units_storage = pyuc.Set("units_storage", [], master_set=units)
        units_reserve = pyuc.Set("units_reserve", [], master_set=units)
        intervals = pyuc.Set("intervals", list(range(24)))
        reserves = pyuc.Set("reserves", [])

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_variable": units_variable,
            "units_reserve": units_reserve,
            "units_storage": units_storage,
            "intervals": intervals,
            "reserves": reserves
        }

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
        units_commit = pyuc.Set("units_commit", [], master_set=units)
        units_variable = \
            pyuc.Set("units_variable", list(unit_data.index), master_set=units)
        units_storage = pyuc.Set("units_storage", [], master_set=units)
        units_reserve = pyuc.Set("units_reserve", [], master_set=units)
        intervals = pyuc.Set("intervals", list(range(2)))
        reserves = pyuc.Set("reserves", [])

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_variable": units_variable,
            "units_storage": units_storage,
            "units_reserve": units_reserve,
            "intervals": intervals,
            "reserves": reserves
        }

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


class StorageConstraints(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={"Demand": [200, 300]})

        unit_data = pd.DataFrame(data={
            "Unit": ["S1"],
            "NumUnits": [10],
            "CapacityMW": [100],
            "StorageHrs": [4],
            "RoundTripEfficiencyFrac": [0.8],
        }).set_index("Unit")

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", [], master_set=units)
        units_storage = pyuc.Set("units_storage", list(unit_data.index), master_set=units)
        units_variable = pyuc.Set("units_variable", [], master_set=units)
        units_reserve = pyuc.Set("units_reserve", [], master_set=units)
        intervals = pyuc.Set("intervals", list(range(2)))
        reserves = pyuc.Set("reserves", [])

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_reserve": units_reserve,
            "units_storage": units_storage,
            "units_variable": units_variable,
            "intervals": intervals,
            "reserves": reserves
        }

        initial_state = pd.DataFrame(
            np.array([[100]]),
            columns=pd.MultiIndex.from_tuples([("stored_energy", -1)]),
            index=["S1"]
        )

        data = {
            "demand": demand,
            "units": unit_data,
            "initial_state": initial_state,
            "IntervalDurationHrs": 0.5
        }

        self.problem = {
            "data": data,
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }
        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

    def test_stored_energy_lt_storage_capacity(self):
        self.problem["var"]["stored_energy"].var[(0, "S1")].setInitialValue(10*100*4/2)
        constraints = ca.cnt_stored_energy_lt_storage_capacity(self.problem)
        result = constraints["stored_energy_lt_storage_capacity(i=0, u=S1)"].value()
        self.assertEqual(result, 0)

    def test_charge_lt_rt_loss_adjusted_capacity(self):
        self.problem["var"]["power_charged"].var[(0, "S1")].setInitialValue(10*100*0.8)

        constraints = ca.cnt_charge_lt_rt_loss_adjusted_capacity(self.problem)
        self.assertEqual(constraints["charge_lt_rt_loss_adjusted_capacity(i=0, u=S1)"].value(), 0)

    def test_storage_energy_continuity(self):
        self.problem["var"]["stored_energy"].var[(0, "S1")].setInitialValue(10)
        self.problem["var"]["power_generated"].var[(1, "S1")].setInitialValue(5)
        self.problem["var"]["power_charged"].var[(1, "S1")].setInitialValue(20)

        final_val = 10 + 0.5 * (-5 + 20)
        self.problem["var"]["stored_energy"].var[(1, "S1")].setInitialValue(final_val)

        constraints = ca.cnt_storage_energy_continuity(self.problem)
        self.assertEqual(constraints["storage_energy_continuity(i=1, u=S1)"].value(), 0)

    def test_storage_energy_continuity_initial_interval(self):
        self.problem["var"]["power_generated"].var[(0, "S1")].setInitialValue(5)
        self.problem["var"]["power_charged"].var[(0, "S1")].setInitialValue(20)

        final_val = 100 + 0.5 * (-5 + 20)
        self.problem["var"]["stored_energy"].var[(0, "S1")].setInitialValue(final_val)

        constraints = ca.cnt_storage_energy_continuity_initial_interval(self.problem)
        self.assertEqual(constraints["storage_energy_continuity(i=0, u=S1)"].value(), 0)

    def test_storage_adds_to_demand(self):
        self.problem["var"]["power_charged"].var[(0, "S1")].setInitialValue(10)
        self.problem["var"]["unserved_power"].var[0].setInitialValue(200+10/0.8)
        self.problem["var"]["power_generated"].var[(0, "S1")].setInitialValue(0)

        constraints = ca.cnt_supply_eq_demand(self.problem)
        self.assertEqual(constraints["supply_eq_demand_(i=0)"].value(), 0)


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
                "RampRate_pctCapphr": [1] * len(self.units),
                "StorageHrs": [1] * len(self.units),
                "RoundTripEfficiencyFrac": [1] * len(self.units)
            }
        ).set_index("Unit")

        variable_traces = pd.DataFrame(data={"Wind": [1], "Solar": [1]})

        data = {
            "demand": demand,
            "units": self.unit_data,
            "initial_state": None,
            "variable_traces": variable_traces,
            "ValueOfLostLoad$/MWh": 1000,
            "IntervalDurationHrs": 1
        }

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

    def test_sets_cnt_charge_lt_rt_loss_adjusted_capacity(self):
        constraints = ca.cnt_charge_lt_rt_loss_adjusted_capacity(self.problem)
        expected = ["charge_lt_rt_loss_adjusted_capacity(i=0, u=Storage)"]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_storage_energy_continuity(self):
        demand = pd.DataFrame(data={"Demand": [200, 200]})
        data = {
            "demand": demand,
            "units": self.unit_data,
            "ValueOfLostLoad$/MWh": 1000,
            "IntervalDurationHrs": 1
        }
        sets = load_data.create_sets(data)

        self.problem = {
            "data": data,
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }
        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

        constraints = ca.cnt_storage_energy_continuity(self.problem)
        expected = ["storage_energy_continuity(i=1, u=Storage)"]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_storage_energy_continuity_initial_interval(self):
        initial_state = pd.DataFrame(
            np.array([[100]]),
            columns=pd.MultiIndex.from_tuples([("stored_energy", -1)]),
            index=["Storage"]
        )

        demand = pd.DataFrame(data={"Demand": [200, 200]})
        data = {
            "demand": demand,
            "units": self.unit_data,
            "initial_state": initial_state,
            "IntervalDurationHrs": 1
        }
        sets = load_data.create_sets(data)

        self.problem = {
            "data": data,
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

        constraints = ca.cnt_storage_energy_continuity_initial_interval(self.problem)
        expected = ["storage_energy_continuity(i=0, u=Storage)"]
        result = list(constraints.keys())
        self.assertEqual(result, expected)

    def test_sets_cnt_stored_energy_lt_storage_capacity(self):
        constraints = ca.cnt_stored_energy_lt_storage_capacity(self.problem)
        expected = ["stored_energy_lt_storage_capacity(i=0, u=Storage)"]
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
        units_commit = pyuc.Set("units_commit", list(unit_data.index), master_set=units)
        units_variable = pyuc.Set("units_variable", [], master_set=units)
        units_storage = pyuc.Set("units_storage", [], master_set=units)
        units_reserve = pyuc.Set("units_reserve", [], master_set=units)
        intervals = pyuc.Set("intervals", list(range(24)))
        reserves = pyuc.Set("reserves", [])

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_variable": units_variable,
            "units_storage": units_storage,
            "units_reserve": units_reserve,
            "intervals": intervals,
            "reserves": reserves
        }

        data = {
            "demand": demand,
            "units": unit_data,
            "initial_state": None,
            "ValueOfLostLoad$/MWh": 1000
        }

        self.problem = {
            "data": data,
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
            "Unit": ["U1", "U2", "S1"],
            "Technology": ["Coal", "Coal", "Storage"],
            "CapacityMW": [100, 80, 100],
            "MinimumUpTimeHrs": [3, 2, 0],
            "MinimumDownTimeHrs": [2, 2, 0],
            "RampRate_pctCapphr": [0.5, 0.4, 1],
            "MinimumGenerationFrac": [0.6, 0.3, 1],
            "RoundTripEfficiencyFrac": [1, 1, 0.8],
        }).set_index("Unit")

        initial_state = pd.DataFrame(
            np.array([[1, 1, 2, 5], [2, 0, 0, 0]]),
            columns=pd.MultiIndex.from_tuples([
                ("num_committed", -1),
                ("num_starting_up", -1),
                ("num_starting_up", -2),
                ("num_shutting_down", -1)
            ]),
            index=["U1", "U2"]
        )

        units = pyuc.Set("units", list(unit_data.index))
        units_commit = pyuc.Set("units_commit", ["U1", "U2"], master_set=units)
        units_variable = pyuc.Set("units_variable", [], master_set=units)
        units_storage = pyuc.Set("units_storage", ["S1"], master_set=units)
        units_reserve = pyuc.Set("units_reserve", [], master_set=units)
        intervals = pyuc.Set("intervals", list(range(24)))
        reserves = pyuc.Set("reserves", [])

        sets = {
            "units": units,
            "units_commit": units_commit,
            "units_variable": units_variable,
            "units_reserve": units_reserve,
            "units_storage": units_storage,
            "intervals": intervals,
            "reserves": reserves
        }

        self.problem = {
            "data": {"units": unit_data,
                     "initial_state": initial_state,
                     "ValueOfLostLoad$/MWh": 1000},
            "problem": pp.LpProblem(name="MY_PROB", sense=pp.LpMinimize),
            "sets": sets,
            "paths": None
        }

        self.problem["var"] = pyuc.create_variables(self.problem["sets"])

    def test_total_power_generated_in_interval(self):
        self.problem["var"]["power_generated"].var[(0, "U1")].setInitialValue(20)
        self.problem["var"]["power_generated"].var[(0, "U2")].setInitialValue(45)
        self.problem["var"]["power_generated"].var[(0, "S1")].setInitialValue(10)

        self.problem["var"]["power_generated"].var[(1, "U1")].setInitialValue(200)
        self.problem["var"]["power_generated"].var[(1, "U2")].setInitialValue(45)
        self.problem["var"]["power_generated"].var[(1, "S1")].setInitialValue(10)

        total_power_generated = \
            ca.total_power_generated_in_interval(self.problem["sets"],
                                                 self.problem["var"]["power_generated"]
                                                 )

        self.assertEqual(total_power_generated[0].value(), 20+45+10)
        self.assertEqual(total_power_generated[1].value(), 200+45+10)

    def test_total_power_charged_in_interval(self):
        self.problem["var"]["power_charged"].var[(0, "S1")].setInitialValue(20)
        self.problem["var"]["power_charged"].var[(1, "S1")].setInitialValue(40)

        total_power_charged = \
            ca.total_power_charged_in_interval(
                self.problem["sets"],
                self.problem["data"],
                self.problem["var"]["power_charged"]
            )

        self.assertEqual(total_power_charged[0].value(), 20/0.8)
        self.assertEqual(total_power_charged[1].value(), 40/0.8)

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

        self.assertEqual(num_start_ups_within_up_time[(0, "U1")].value(), 3)
        self.assertEqual(num_start_ups_within_up_time[(1, "U1")].value(), 2)
        self.assertEqual(num_start_ups_within_up_time[(2, "U1")].value(), 3)
        self.assertEqual(num_start_ups_within_up_time[(3, "U1")].value(), 4)
        self.assertEqual(num_start_ups_within_up_time[(4, "U1")].value(), 3)

        result_keys = list(num_start_ups_within_up_time.keys())
        expected_keys = [
            (i, u) for i in sets["intervals"].indices for u in sets["units_commit"].indices
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

        self.assertEqual(num_shut_downs_within_down_time[(0, "U1")].value(), 5)
        self.assertEqual(num_shut_downs_within_down_time[(1, "U1")].value(), 1)
        self.assertEqual(num_shut_downs_within_down_time[(2, "U1")].value(), 3)
        self.assertEqual(num_shut_downs_within_down_time[(3, "U1")].value(), 3)
        self.assertEqual(num_shut_downs_within_down_time[(4, "U1")].value(), 1)

        result_keys = list(num_shut_downs_within_down_time.keys())
        expected_keys = [
            (i, u) for i in sets["intervals"].indices for u in sets["units_commit"].indices
        ]

        self.assertEqual(result_keys, expected_keys)

    def test_ramp_calculator_all_intervals_and_units(self):
        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]
        rampMW = ca.ramp_calculator(sets, data, var)

        result_keys = list(rampMW.keys())
        expected_keys = [
            (i, u) for i in sets["intervals"].indices for u in sets["units"].indices
        ]

        self.assertEqual(sorted(result_keys), sorted(expected_keys))

    def test_ramp_calculator_first_interval_without_initial_state(self):
        initial_state = None

        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]

        data["initial_state"] = initial_state

        var["power_generated"].var[(0, "U1")].setInitialValue(20)
        var["power_generated"].var[(0, "U2")].setInitialValue(20)

        rampMW = ca.ramp_calculator(sets, data, var)
        self.assertEqual(rampMW[(0, "U1")].value(), 20-0)
        self.assertEqual(rampMW[(0, "U2")].value(), 20-0)

    def test_ramp_calculator_first_interval_with_initial_state(self):
        initial_state = pd.DataFrame(
            np.array([10, pd.NA]),
            index=["U1", "U2"],
            columns=pd.MultiIndex.from_tuples([("power_generated", -1)])
        )

        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]

        data["initial_state"] = initial_state

        var["power_generated"].var[(0, "U1")].setInitialValue(20)
        var["power_generated"].var[(0, "U2")].setInitialValue(20)

        rampMW = ca.ramp_calculator(sets, data, var)
        self.assertEqual(rampMW[(0, "U1")].value(), 20-10)
        self.assertEqual(rampMW[(0, "U2")].value(), 20-0)

    def test_ramp_calculator_second_interval(self):
        sets, data, var = \
            self.problem["sets"], self.problem["data"], self.problem["var"]

        var["power_generated"].var[(0, "U1")].setInitialValue(20)
        var["power_generated"].var[(1, "U1")].setInitialValue(45)

        rampMW = ca.ramp_calculator(sets, data, var)
        self.assertEqual(rampMW[(1, "U1")].value(), 45-20)

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

    def test_get_initial_units_committed_init_state_defined(self):
        sets, data = self.problem["sets"], self.problem["data"]
        result = ca.get_initial_units_committed(sets, data)
        expected = {"U1": 1, "U2": 2}

        self.assertEqual(result, expected)

    def test_get_initial_units_committed_init_state_undefined(self):
        sets, data = self.problem["sets"], self.problem["data"]
        data["initial_state"] = None
        result = ca.get_initial_units_committed(sets, data)
        expected = {"U1": 0, "U2": 0}

        self.assertEqual(result, expected)
