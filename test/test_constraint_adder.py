import unittest

import mock
import pandas as pd
import pulp as pp
from pyuc import constraint_adder as ca
from pyuc import constraints as cnsts


class testConstraintSelector(unittest.TestCase):
    def setUp(self):
        def add_constraint(name, constraint):
            self.constraint_index.loc[name, 'Function'] = constraint

        self.paths = {'constraint_list': 'MY_PATH'}

        self.constraint_index = \
            pd.DataFrame(columns=['ID', 'ToInclude', 'Function']).set_index('ID')
        add_constraint('Supply==Demand', cnsts.cnt_supply_eq_demand)
        add_constraint('Power<=Capacity', cnsts.cnt_power_lt_capacity)

    @mock.patch('pyuc.constraint_adder.make_constraint_index')
    @mock.patch('pandas.read_csv')
    def test_constraint_selector(self, read_csv_mock, make_constraint_index_mock):
        constraint_list = pd.DataFrame(
            {'ID': ['Supply==Demand', 'Power<=Capacity'], 'ToInclude': ["TRUE", "False"]}
        )

        read_csv_mock.return_value = constraint_list
        make_constraint_index_mock.return_value = self.constraint_index

        result = ca.constraint_selector(self.paths)

        expected = self.constraint_index.copy()
        expected['ToInclude'] = [True, False]

        pd.testing.assert_frame_equal(result, expected, check_dtype=False)


class testBuildAndAddConstraints(unittest.TestCase):
    def setUp(self):
        def constraint_func1(problem):
            return {label1: condition1}

        def constraint_func2(problem):
            return {label2: condition2}  # pragma: no cover

        x, y = pp.LpVariable('x'), pp.LpVariable('y')
        condition1, condition2 = (x + y <= 5), (x + 2*y <= 10)
        label1, label2 = 'Constraint1', 'Constraint2'

        self.constraints = {label1: condition1, label2: condition2}

        self.constraint_index = pd.DataFrame({
            'ID': [label1, label2],
            'ToInclude': [True, False],
            'Function': [constraint_func1, constraint_func2]
        })

        self.constraint1 = {label1: condition1}

    def test_add_all_constraints_to_pulp_problem(self):
        problem = {'problem': pp.LpProblem("MY_PROB")}
        problem['problem'] = \
            ca.add_all_constraints_to_pulp_problem(problem, self.constraints)

        result = list(problem['problem'].constraints.keys())
        expected = ['Constraint1', 'Constraint2']

        self.assertEqual(result, expected)

    def test_build_constraints(self):
        problem = {'data': {'constraint_index': self.constraint_index}}
        result = ca.build_constraints(problem)
        expected = self.constraint1
        self.assertEqual(result, expected)
