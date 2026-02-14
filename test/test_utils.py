import unittest

import mock
from pyuc import utils


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
