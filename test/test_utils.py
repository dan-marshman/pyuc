import unittest

import mock
from pyuc import utils
from pyuc import load_data as ld

import os

class PathExists(unittest.TestCase):
    def setUp(self):
        self.path = "PATH_THAT_DOES_NOT_EXIST"
        self.file_type = "A FILE"

    def test_path_does_not_exist_is_required(self):
        with self.assertRaises(SystemExit):
            utils.check_path_exists(self.path, self.file_type, required_file=True)

    def test_path_does_not_exist_is_not_required(self):
        try:
            utils.check_path_exists(self.path, self.file_type)
        except SystemExit:  # pragma: no cover
            self.fail("utils.check_path_exists exited when the file is not required.")

    @mock.patch("os.path.exists", return_value=True)
    def test_path_does_exist(self, path_exists_mock):
        try:
            utils.check_path_exists(self.path, self.file_type)
        except SystemExit:  # pragma: no cover
            self.fail("utils.check_path_exists exited when the file exists.")

class TestOptimisationStatus(unittest.TestCase):
    def test_valid_statuses(self):
        """Check that all defined status codes return correct string."""
        self.assertEqual(utils.get_optimisation_status(1), "Optimal")
        self.assertEqual(utils.get_optimisation_status(0), "Not Solved")
        self.assertEqual(utils.get_optimisation_status(-1), "Infeasible")
        self.assertEqual(utils.get_optimisation_status(-2), "Unbounded")
        self.assertEqual(utils.get_optimisation_status(-3), "Undefined")

    def test_invalid_status_raises(self):
        """Check that invalid codes raise KeyError."""
        with self.assertRaises(KeyError):
            utils.get_optimisation_status(99)

        with self.assertRaises(KeyError):
            utils.get_optimisation_status(None)

        with self.assertRaises(KeyError):
            utils.get_optimisation_status("Optimal")  # wrong type


class TestInitialStateValidation(unittest.TestCase):
    def setUp(self):

        unit_data_path = os.path.join("test", "test_problems", "Integration", "TestSet2", "unit_data.csv")
        self.unit_data = ld.load_unit_data(unit_data_path)

        initial_state_path = os.path.join("test", "test_problems", "Integration", "TestSet2", "initial_state.csv")
        self.initial_state = ld.load_initial_state(initial_state_path)

        self.unit_data.loc["Coal1", "NumUnits"] = 5
        self.unit_data.loc["Coal1", "CapacityMW"] = 100
        self.unit_data.loc["Coal1", "MinimumGenerationFrac"] = 0.5
        self.unit_data.loc["Coal1", "MinimumUpTimeHrs"] = 6
        self.unit_data.loc["Coal1", "MinimumDownTimeHrs"] = 6

        self.unit_data.loc["Battery1", "NumUnits"] = 2
        self.unit_data.loc["Battery1", "CapacityMW"] = 100
        self.unit_data.loc["Battery1", "StorageHrs"] = 3

        self.unit_data.loc["Wind1", "NumUnits"] = 2
        self.unit_data.loc["Wind1", "CapacityMW"] = 100

    def test_valid_data_passes(self):
        self.initial_state.loc["Coal1", ("num_shutting_down", -1)] = 2
        self.initial_state.loc["Coal1", ("num_shutting_down", -6)] = 0

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }

        try:
            utils.validate_initial_state(data)

        except ValueError as e:
            self.fail(f"validate_initial_state raised ValueError unexpectedly: {e}")

    def test_power_lt_min_gen(self):
        self.initial_state.loc["Coal1", ("power_generated", -1)] = 99
        self.initial_state.loc["Coal1", ("num_committed", -1)] = 2

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }


        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Coal1", str(context.exception))
        self.assertIn("99", str(context.exception))
        self.assertIn("100", str(context.exception))
        self.assertIn("below minimum", str(context.exception))

    def test_power_gt_online_capacity(self):
        self.initial_state.loc["Coal1", ("power_generated", -1)] = 201
        self.initial_state.loc["Coal1", ("num_committed", -1)] = 2

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }


        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Coal1", str(context.exception))
        self.assertIn("201", str(context.exception))
        self.assertIn("200", str(context.exception))
        self.assertIn("exceeds", str(context.exception))

    def test_num_committed_exceeds_num_units(self):
        self.initial_state.loc["Coal1", ("power_generated", -1)] = 800
        self.initial_state.loc["Coal1", ("num_committed", -1)] = 8

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }

        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Coal1", str(context.exception))
        self.assertIn("8", str(context.exception))
        self.assertIn("5", str(context.exception))

    def test_power_gt_capacity_storage(self):
        self.initial_state.loc["Battery1", ("power_generated", -1)] = 201

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }

        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Battery1", str(context.exception))
        self.assertIn("201", str(context.exception))
        self.assertIn("200", str(context.exception))
        self.assertIn("exceeds", str(context.exception))

    def test_power_gt_storage_energy_capacity(self):
        self.initial_state.loc["Battery1", ("stored_energy", -1)] = 601

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }

        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Battery1", str(context.exception))
        self.assertIn("601", str(context.exception))
        self.assertIn("600", str(context.exception))
        self.assertIn("greater than", str(context.exception))

    def test_power_gt_capacity_variable(self):
        self.initial_state.loc["Wind1", ("power_generated", -1)] = 201

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }

        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Wind1", str(context.exception))
        self.assertIn("201", str(context.exception))
        self.assertIn("200", str(context.exception))
        self.assertIn("exceed", str(context.exception))

    def test_number_of_units_starting_and_stopping_A(self):
        self.initial_state.loc["Coal1", ("num_starting_up", -1)] = 1
        self.initial_state.loc["Coal1", ("num_starting_up", -3)] = 1
        self.initial_state.loc["Coal1", ("num_starting_up", -5)] = 2
        self.initial_state.loc["Coal1", ("num_shutting_down", -1)] = 1
        self.initial_state.loc["Coal1", ("num_shutting_down", -6)] = 2

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }

        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Coal1", str(context.exception))
        self.assertIn("4", str(context.exception))
        self.assertIn("3", str(context.exception))
        self.assertIn("5", str(context.exception))
        self.assertIn("exceed", str(context.exception))

    def test_number_of_units_starting_and_stopping_B(self):
        self.initial_state.loc["Coal1", ("num_starting_up", -1)] = 1
        self.initial_state.loc["Coal1", ("num_starting_up", -3)] = 1
        self.initial_state.loc["Coal1", ("num_starting_up", -5)] = 2

        self.initial_state.loc["Coal1", ("num_committed", -1)] = 3

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }

        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Coal1", str(context.exception))
        self.assertIn("4", str(context.exception))
        self.assertIn("3", str(context.exception))
        self.assertIn("exceed", str(context.exception))

    def test_number_of_units_starting_and_stopping_C(self):
        self.initial_state.loc["Coal1", ("num_shutting_down", -1)] = 1
        self.initial_state.loc["Coal1", ("num_shutting_down", -3)] = 1
        self.initial_state.loc["Coal1", ("num_shutting_down", -6)] = 2

        self.initial_state.loc["Coal1", ("num_committed", -1)] = 2

        data = {
            "unit_data": self.unit_data,
            "initial_state": self.initial_state,
            "IntervalDurationHrs": 0.5
            }

        with self.assertRaises(ValueError) as context:
            utils.validate_initial_state(data)

        self.assertIn("Coal1", str(context.exception))
        self.assertIn("4", str(context.exception))
        self.assertIn("5", str(context.exception))
        self.assertIn("2", str(context.exception))
        self.assertIn("exceed", str(context.exception))
