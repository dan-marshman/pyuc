import unittest

import pandas as pd
import pulp as pp
from pyuc import constraints as ca
from pyuc import pyuc


class BasicConstraintEquations(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={'Demand': [200, 300, 400]})

        unit_data = pd.DataFrame(data={
            'Unit': ['U1', 'U2'],
            'CapacityMW': [100, 100],
            'NumUnits': [2, 1],
            'FuelCost$/GJ': [10/3.6, 20/3.6],
            'VOM$/MWh': [1, 1],
            'ThermalEfficiencyFrac': [1, 0.5],
            'MinimumGenerationFrac': [0.5, 0.2],
        }).set_index('Unit')

        units = pyuc.Set('units', list(unit_data.index))
        intervals = pyuc.Set('intervals', list(demand.index))

        self.problem = {
            'data': {'demand': demand, 'units': unit_data, 'ValueOfLostLoad$/MWh': 1000},
            'problem': pp.LpProblem(name='MY_PROB', sense=pp.LpMinimize),
            'sets': {'units': units, 'intervals': intervals},
            'paths': None
        }
        self.problem['var'] = pyuc.create_variables(self.problem['sets'])

        self.problem['var']['power_generated'].var[(0, 'U1')].setInitialValue(20)
        self.problem['var']['power_generated'].var[(0, 'U2')].setInitialValue(45)
        self.problem['var']['power_generated'].var[(1, 'U1')].setInitialValue(200)
        self.problem['var']['power_generated'].var[(1, 'U2')].setInitialValue(45)

        self.problem['var']['unserved_power'].var[(0)].setInitialValue(5)
        self.problem['var']['unserved_power'].var[(1)].setInitialValue(55)

        self.problem['var']['num_committed'].var[(0, 'U1')].setInitialValue(1)
        self.problem['var']['num_committed'].var[(1, 'U1')].setInitialValue(2)
        self.problem['var']['num_committed'].var[(0, 'U2')].setInitialValue(1)
        self.problem['var']['num_committed'].var[(1, 'U2')].setInitialValue(0)

        self.problem['var']['num_starting_up'].var[(0, 'U1')].setInitialValue(1)
        self.problem['var']['num_starting_up'].var[(1, 'U1')].setInitialValue(1)
        self.problem['var']['num_starting_up'].var[(0, 'U2')].setInitialValue(1)
        self.problem['var']['num_starting_up'].var[(1, 'U2')].setInitialValue(0)

        self.problem['var']['num_shutting_down'].var[(0, 'U1')].setInitialValue(0)
        self.problem['var']['num_shutting_down'].var[(1, 'U1')].setInitialValue(0)
        self.problem['var']['num_shutting_down'].var[(0, 'U2')].setInitialValue(0)
        self.problem['var']['num_shutting_down'].var[(1, 'U2')].setInitialValue(1)

    def test_cnt_supply_eq_demand(self):
        constraints = ca.cnt_supply_eq_demand(self.problem)
        self.assertEqual(constraints['supply_eq_demand_(i=0)'].value(), 20+45+5-200)
        self.assertEqual(constraints['supply_eq_demand_(i=1)'].value(), 200+45+55-300)

    def test_cnt_power_lt_capacity(self):
        constraints = ca.cnt_power_lt_capacity(self.problem)

        self.assertEqual(
            constraints['power_lt_capacity_(i=0, u=U1)'].value(),
            20-2*100
        )

        self.assertEqual(
            constraints['power_lt_capacity_(i=1, u=U1)'].value(),
            200-2*100
        )

        self.assertEqual(
            constraints['power_lt_capacity_(i=0, u=U2)'].value(),
            45-1*100
        )

        self.assertEqual(
            constraints['power_lt_capacity_(i=1, u=U2)'].value(),
            45-1*100
        )

    def test_cnt_power_lt_committed_capacity(self):
        constraints = ca.cnt_power_lt_committed_capacity(self.problem)

        self.assertEqual(
            constraints['power_lt_committed_capacity_(i=0, u=U1)'].value(),
            20-1*100
        )

        self.assertEqual(
            constraints['power_lt_committed_capacity_(i=0, u=U2)'].value(),
            45-1*100
        )

        self.assertEqual(
            constraints['power_lt_committed_capacity_(i=1, u=U1)'].value(),
            200-2*100
        )

        self.assertEqual(
            constraints['power_lt_committed_capacity_(i=1, u=U2)'].value(),
            45-0*100
        )

    def test_cnt_power_gt_minimum_generation(self):
        constraints = ca.cnt_power_gt_minimum_generation(self.problem)

        self.assertEqual(
            constraints['power_gt_minimum_generation_(i=0, u=U1)'].value(),
            20-0.5*1*100
        )

        self.assertEqual(
            constraints['power_gt_minimum_generation_(i=1, u=U1)'].value(),
            200-0.5*2*100
        )

        self.assertEqual(
            constraints['power_gt_minimum_generation_(i=0, u=U2)'].value(),
            45-0.2*1*100
        )

        self.assertEqual(
            constraints['power_gt_minimum_generation_(i=1, u=U2)'].value(),
            45-0.2*0*100
        )

    def test_cnt_num_committed_lt_num_units(self):
        constraints = ca.cnt_num_committed_lt_num_units(self.problem)

        self.assertEqual(
            constraints['num_committed_lt_num_units(i=0, u=U1)'].value(),
            1-2
        )

        self.assertEqual(
            constraints['num_committed_lt_num_units(i=1, u=U1)'].value(),
            2-2
        )

        self.assertEqual(
            constraints['num_committed_lt_num_units(i=0, u=U2)'].value(),
            1-1
        )

        self.assertEqual(
            constraints['num_committed_lt_num_units(i=1, u=U2)'].value(),
            0-1
        )

    def test_cnt_commitment_continuity(self):
        constraints = ca.cnt_commitment_continuity(self.problem)

        self.assertEqual(
            constraints['commitment_continuity(i=1, u=U1)'].value(),
            0
        )

        self.assertEqual(
            constraints['commitment_continuity(i=1, u=U2)'].value(),
            2-2
        )

    def test_cnt_commitment_continuity_initial_interval(self):
        constraints = ca.cnt_commitment_continuity_initial_interval(self.problem)

        self.assertEqual(
            constraints['commitment_continuity(i=0, u=U1)'].value(),
            0
        )

        self.assertEqual(
            constraints['commitment_continuity(i=0, u=U2)'].value(),
            2-2
        )


class MinUpAndDownTimes(unittest.TestCase):
    def setUp(self):
        unit_data = pd.DataFrame(data={
            'Unit': ['U1'],
            'NumUnits': [10],
            'MinimumUpTimeHrs': [3],
            'MinimumDownTimeHrs': [2],
        }).set_index('Unit')

        units = pyuc.Set('units', list(unit_data.index))
        intervals = pyuc.Set('intervals', list(range(24)))

        self.problem = {
            'data': {'units': unit_data},
            'problem': pp.LpProblem(name='MY_PROB', sense=pp.LpMinimize),
            'sets': {'units': units, 'intervals': intervals},
            'paths': None
        }
        self.problem['var'] = pyuc.create_variables(self.problem['sets'])

        self.problem['var']['num_starting_up'].var[(0, 'U1')].setInitialValue(1)
        self.problem['var']['num_starting_up'].var[(1, 'U1')].setInitialValue(2)
        self.problem['var']['num_starting_up'].var[(2, 'U1')].setInitialValue(3)
        self.problem['var']['num_starting_up'].var[(3, 'U1')].setInitialValue(2)

        self.problem['var']['num_shutting_down'].var[(0, 'U1')].setInitialValue(1)
        self.problem['var']['num_shutting_down'].var[(1, 'U1')].setInitialValue(2)
        self.problem['var']['num_shutting_down'].var[(2, 'U1')].setInitialValue(3)
        self.problem['var']['num_shutting_down'].var[(3, 'U1')].setInitialValue(2)

    def test_minimum_up_time(self):
        constraints = ca.cnt_minimum_up_time(self.problem)

        self.problem['var']['num_committed'].var[(3, 'U1')].setInitialValue(3)
        self.assertEqual(
            constraints['minimum_up_time(i=3, u=U1)'].value(),
            3 - (2 + 3 + 2)
        )

        self.problem['var']['num_committed'].var[(3, 'U1')].setInitialValue(7)
        self.assertEqual(
            constraints['minimum_up_time(i=3, u=U1)'].value(),
            7 - (2 + 3 + 2)
        )

    def test_minimum_down_time(self):
        constraints = ca.cnt_minimum_down_time(self.problem)

        self.problem['var']['num_committed'].var[(3, 'U1')].setInitialValue(6)
        self.assertEqual(
            constraints['minimum_down_time(i=3, u=U1)'].value(),
            10 - 6 - (2 + 3)
        )

        self.problem['var']['num_committed'].var[(3, 'U1')].setInitialValue(5)
        self.assertEqual(
            constraints['minimum_down_time(i=3, u=U1)'].value(),
            10- 5 - (2 + 3)
        )


class OtherConstraintTests(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={'Demand': [200, 300, 400]})

        unit_data = pd.DataFrame(data={
            'Unit': ['U1', 'U2'],
            'CapacityMW': [100, 100],
            'NumUnits': [2, 1],
            'FuelCost$/GJ': [10/3.6, 20/3.6],
            'VOM$/MWh': [1, 1],
            'ThermalEfficiencyFrac': [1, 0.5],
            'MinimumGenerationFrac': [0.5, 0.2],
        }).set_index('Unit')

        units = pyuc.Set('units', list(unit_data.index))
        intervals = pyuc.Set('intervals', list(demand.index))

        self.problem = {
            'data': {'demand': demand, 'units': unit_data, 'ValueOfLostLoad$/MWh': 1000},
            'problem': pp.LpProblem(name='MY_PROB', sense=pp.LpMinimize),
            'sets': {'units': units, 'intervals': intervals},
            'paths': None
        }

        self.problem['var'] = pyuc.create_variables(self.problem['sets'])

    def test_cnt_commitment_continuity_ignores_first_interval(self):
        constraints = ca.cnt_commitment_continuity(self.problem)

        self.assertFalse('commitment_continuity(i=0, u=U1)' in constraints.keys())
        self.assertFalse('commitment_continuity(i=0, u=U2)' in constraints.keys())

    def test_cnt_commitment_continuity_init_int_only_uses_first_int(self):
        constraints = ca.cnt_commitment_continuity_initial_interval(self.problem)

        expected = [
            'commitment_continuity(i=0, u=U1)',
            'commitment_continuity(i=0, u=U2)',
        ]

        self.assertEqual(list(constraints.keys()), expected)


class OtherFunctions(unittest.TestCase):
    def setUp(self):
        unit_data = pd.DataFrame(data={
            'Unit': ['U1', 'U2'],
            'MinimumUpTimeHrs': [3, 2],
            'MinimumDownTimeHrs': [2, 2]
        }).set_index('Unit')

        units = pyuc.Set('units', list(unit_data.index))
        intervals = pyuc.Set('intervals', list(range(6)))

        self.problem = {
            'data': {'units': unit_data, 'ValueOfLostLoad$/MWh': 1000},
            'problem': pp.LpProblem(name='MY_PROB', sense=pp.LpMinimize),
            'sets': {'units': units, 'intervals': intervals},
            'paths': None
        }

        self.problem['var'] = pyuc.create_variables(self.problem['sets'])

    def test_total_power_in_interval(self):
        self.problem['var']['power_generated'].var[(0, 'U1')].setInitialValue(20)
        self.problem['var']['power_generated'].var[(0, 'U2')].setInitialValue(45)

        self.problem['var']['power_generated'].var[(1, 'U1')].setInitialValue(200)
        self.problem['var']['power_generated'].var[(1, 'U2')].setInitialValue(45)

        total_power_in_interval = \
            ca.total_power_in_interval(self.problem['sets'],
                                       self.problem['var']['power_generated'])

        self.assertEqual(total_power_in_interval[0].value(), 20+45)
        self.assertEqual(total_power_in_interval[1].value(), 200+45)

    def test_num_start_ups_calculator(self):
        sets, data, var = \
            self.problem['sets'], self.problem['data'], self.problem['var']

        var['num_starting_up'].var[(0, 'U1')].setInitialValue(0)
        var['num_starting_up'].var[(1, 'U1')].setInitialValue(1)
        var['num_starting_up'].var[(2, 'U1')].setInitialValue(2)
        var['num_starting_up'].var[(3, 'U1')].setInitialValue(1)
        var['num_starting_up'].var[(4, 'U1')].setInitialValue(0)

        num_start_ups_within_up_time = \
            ca.num_start_ups_within_up_time_calculator(sets, data, var)

        self.assertEqual(num_start_ups_within_up_time[(0, 'U1')].value(), 0)
        self.assertEqual(num_start_ups_within_up_time[(1, 'U1')].value(), 1)
        self.assertEqual(num_start_ups_within_up_time[(2, 'U1')].value(), 3)
        self.assertEqual(num_start_ups_within_up_time[(3, 'U1')].value(), 4)
        self.assertEqual(num_start_ups_within_up_time[(4, 'U1')].value(), 3)

        result_keys = list(num_start_ups_within_up_time.keys())
        expected_keys = [
            (i, u) for i in sets['intervals'].indices for u in sets['units'].indices
        ]

        self.assertEqual(result_keys, expected_keys)

    def test_num_shut_downs_calculator(self):
        sets, data, var = \
            self.problem['sets'], self.problem['data'], self.problem['var']

        var['num_shutting_down'].var[(0, 'U1')].setInitialValue(0)
        var['num_shutting_down'].var[(1, 'U1')].setInitialValue(1)
        var['num_shutting_down'].var[(2, 'U1')].setInitialValue(2)
        var['num_shutting_down'].var[(3, 'U1')].setInitialValue(1)
        var['num_shutting_down'].var[(4, 'U1')].setInitialValue(0)

        num_shut_downs_within_down_time = \
            ca.num_shut_downs_within_down_time_calculator(sets, data, var)

        self.assertEqual(num_shut_downs_within_down_time[(0, 'U1')].value(), 0)
        self.assertEqual(num_shut_downs_within_down_time[(1, 'U1')].value(), 1)
        self.assertEqual(num_shut_downs_within_down_time[(2, 'U1')].value(), 3)
        self.assertEqual(num_shut_downs_within_down_time[(3, 'U1')].value(), 3)
        self.assertEqual(num_shut_downs_within_down_time[(4, 'U1')].value(), 1)

        result_keys = list(num_shut_downs_within_down_time.keys())
        expected_keys = [
            (i, u) for i in sets['intervals'].indices for u in sets['units'].indices
        ]

        self.assertEqual(result_keys, expected_keys)

    def test_up_ramp_calculator_all_intervals_and_units(self):
        sets, data, var = \
            self.problem['sets'], self.problem['data'], self.problem['var']
        up_ramp = ca.up_ramp_calculator(sets, data, var)

        result_keys = list(up_ramp.keys())
        expected_keys = [
            (i, u) for i in sets['intervals'].indices for u in sets['units'].indices
        ]

        self.assertEqual(sorted(result_keys), sorted(expected_keys))

    def test_up_ramp_calculator_second_interval(self):
        sets, data, var = \
            self.problem['sets'], self.problem['data'], self.problem['var']

        var['power_generated'].var[(0, 'U1')].setInitialValue(20)
        var['power_generated'].var[(1, 'U1')].setInitialValue(45)

        up_ramp = ca.up_ramp_calculator(sets, data, var)
        self.assertEqual(up_ramp[(1, 'U1')].value(), 45-20)

    def test_down_ramp_calculator_all_intervals_and_units(self):
        sets, data, var = \
            self.problem['sets'], self.problem['data'], self.problem['var']
        down_ramp = ca.down_ramp_calculator(sets, data, var)

        result_keys = list(down_ramp.keys())
        expected_keys = [
            (i, u) for i in sets['intervals'].indices for u in sets['units'].indices
        ]

        self.assertEqual(sorted(result_keys), sorted(expected_keys))

    def test_down_ramp_calculator_second_interval(self):
        sets, data, var = \
            self.problem['sets'], self.problem['data'], self.problem['var']

        var['power_generated'].var[(0, 'U1')].setInitialValue(20)
        var['power_generated'].var[(1, 'U1')].setInitialValue(45)

        down_ramp = ca.down_ramp_calculator(sets, data, var)
        self.assertEqual(down_ramp[(1, 'U1')].value(), 20-45)
