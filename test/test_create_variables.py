import unittest

from pyuc import pyuc


class makeVariables(unittest.TestCase):
    def setUp(self):
        self.sets = {
            "intervals": pyuc.Set("intervals", list(range(3))),
            "units": pyuc.Set("units", ["U1", "U2", "S1", "V1"]),
        }

        self.sets["units_commit"] = \
            pyuc.Set("units_commit", ["U1", "U2"], master_set=self.sets["units"])

        self.sets["units_storage"] = \
            pyuc.Set("units_storage", ["S1"], master_set=self.sets["units"])

        self.sets["units_variable"] = \
            pyuc.Set("units_variable", ["V1"], master_set=self.sets["units"])

        self.sets["units_reserve"] = \
            pyuc.Set("units_reserve", ["U1", "U2", "S1"], master_set=self.sets["units"])

        self.sets["reserves"] = pyuc.Set("units_reserve", ["raise", "lower"])

        self.vars = pyuc.create_variables(self.sets)

    def test_required_variables_are_made(self):
        expected = [
            "power_generated",
            "num_committed",
            "num_shutting_down",
            "num_starting_up",
            "unserved_power",
            "stored_energy",
            "power_charged",
            "reserve_enabled"
        ]

        self.assertEqual(list(self.vars.keys()), expected)

    def test_indices_intervals_x_units(self):
        expected = [
            (0, "U1"), (1, "U1"), (2, "U1"),
            (0, "U2"), (1, "U2"), (2, "U2"),
            (0, "S1"), (1, "S1"), (2, "S1"),
            (0, "V1"), (1, "V1"), (2, "V1"),
        ]

        result = self.vars["power_generated"].sets_indices
        self.assertEqual(sorted(result), sorted(expected))

    def test_indices_intervals_x_units_commit(self):
        relevant_variables = ["num_committed", "num_shutting_down", "num_starting_up"]

        expected = [
            (0, "U1"), (1, "U1"), (2, "U1"),
            (0, "U2"), (1, "U2"), (2, "U2")
        ]

        for var in relevant_variables:
            result = self.vars[var].sets_indices
            self.assertEqual(sorted(result), sorted(expected))

    def test_indices_intervals_x_units_storage(self):
        relevant_variables = ["stored_energy", "power_charged"]

        expected = [(0, "S1"), (1, "S1"), (2, "S1")]

        for var in relevant_variables:
            result = self.vars[var].sets_indices
            self.assertEqual(sorted(result), sorted(expected))

    def test_indices_intervals(self):
        relevant_variables = ["unserved_power"]

        expected = list(range(3))

        for var in relevant_variables:
            result = self.vars[var].sets_indices
            self.assertEqual(sorted(result), sorted(expected))
