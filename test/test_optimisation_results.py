import unittest

import mock
import pandas as pd
import pulp as pp
from pyuc import constraint_adder as ca
from pyuc import objective_function, pyuc


class testBasicProblems(unittest.TestCase):
    def setUp(self):
        demand = pd.DataFrame(data={'Demand': [200, 300, 400]})

        unit_data = pd.DataFrame(data={
            'Unit': ['U1', 'U2'],
            'CapacityMW': [100, 100],
            'NumUnits': [2, 1],
            'FuelCost$/GJ': [10/3.6, 20/3.6],
            'VOM$/MWh': [1, 1],
            'ThermalEfficiencyFrac': [1, 0.5],
            'MinimumGenerationFrac': [1, 1],
        }).set_index('Unit')

        units = pyuc.Set('units', list(unit_data.index))
        intervals = pyuc.Set('intervals', list(demand.index))

        self.problem = {
            'data': {
                'demand': demand,
                'units': unit_data,
                'ValueOfLostLoad$/MWh': 1000,
                'IntervalDurationHrs': 0.5
            },
            'problem': pp.LpProblem(name='MY_PROB', sense=pp.LpMinimize),
            'sets': {'units': units, 'intervals': intervals},
            'paths': None
        }
        self.problem['var'] = pyuc.create_variables(self.problem['sets'])

        self.constraint_list = ca.make_constraint_index()
        self.constraint_list['ToInclude'] = True

    @mock.patch('pyuc.constraint_adder.constraint_selector')
    def test_problem1(self, constraint_selector_mock):
        constraint_selector_mock.return_value = self.constraint_list
        self.problem['problem'] = ca.add_constraints(self.problem)
        self.problem['problem']  \
            = objective_function.make_objective_function(self.problem)
        self.problem['problem'].solve(solver=pp.apis.PULP_CBC_CMD(msg=False))

        # Unit 1: 3 hours producing 200 MW.
        # Unit 2: 2 hour producing 100 MW.
        # Unserved Energy: 1 hour producing 100 MW.
        expected = (200*(10+1)*3) + (100*(40+1)*2) + (100*1000*1)
        expected *= 0.5  # Interval Duration
        result = self.problem['problem'].objective.value()

        self.assertEqual(result, expected)
