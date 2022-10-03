import unittest

from pyuc import pyuc


class makeVariables(unittest.TestCase):
    def setUp(self):
        self.sets = {
            'intervals': pyuc.Set('intervals', list(range(3))),
            'units': pyuc.Set('units', ['U1', 'U2'])
        }

        self.vars = pyuc.create_variables(self.sets)

    def test_required_variables_are_made(self):
        expected = [
            'power_generated',
            'num_committed',
            'num_shutting_down',
            'num_starting_up',
            'unserved_power'
        ]

        self.assertEqual(list(self.vars.keys()), expected)

    def test_indices_intervals_x_units(self):
        relevant_variables = [
            'power_generated',
            'num_committed',
            'num_shutting_down',
            'num_starting_up',
        ]

        expected = [(0, 'U1'), (1, 'U1'), (2, 'U1'), (0, 'U2'), (1, 'U2'), (2, 'U2')]

        for var in relevant_variables:
            result = self.vars[var].sets_indices
            self.assertEqual(sorted(result), sorted(expected))

    def test_indices_intervals(self):
        relevant_variables = ['unserved_power']

        expected = list(range(3))

        for var in relevant_variables:
            result = self.vars[var].sets_indices
            self.assertEqual(sorted(result), sorted(expected))
