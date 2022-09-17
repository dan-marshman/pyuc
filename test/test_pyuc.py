import unittest

import mock
from pyuc import pyuc


class RunOptProblem(unittest.TestCase):
    def setUp(self):
        self.name = "MY_NAME"
        self.input_data_path = "IN"
        self.output_data_path = "OUT"

    @mock.patch('pyuc.setup_problem.setup_problem')
    def test_setup_problem_is_called(self, setup_problem_mock):
        pyuc.run_opt_problem(self.name, self.input_data_path, self.output_data_path)
        setup_problem_mock.assert_called_once_with(self.name, self.input_data_path,
                                     self.output_data_path)
