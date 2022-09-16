import os
import unittest
from io import StringIO

import mock
import pandas as pd
from pyuc import pyuc


class ProblemSetup(unittest.TestCase):
    def test_initialise_problem_with_str(self):
        result = pyuc.initialise_problem('my_problem')
        expected = {'name': 'my_problem'}

        self.assertEqual(result, expected)

    def test_initialise_problem_as_dict(self):
        result = pyuc.initialise_problem('my_problem')
        expected = dict

        self.assertIsInstance(result, expected)


class Paths(unittest.TestCase):
    def test_initialise_paths(self):
        result = pyuc.initialise_paths('input_data_path', 'output_data_path')
        expected = {
            'input_data': 'input_data_path',
            'output_data': 'output_data_path',
            'settings': os.path.join('input_data_path', 'settings.csv'),
        }

        self.assertEqual(result, expected)


class Settings(unittest.TestCase):

    @mock.patch('builtins.open')
    def test_read_settings(self, open_mock):
        open_mock.return_value = StringIO('A,B\n1,2\n3,4')
        result = pyuc.read_settings_file('dummy_path.csv')
        expected = pd.DataFrame(data={'A': [1, 3], 'B': [2, 4]})
        pd.testing.assert_frame_equal(result, expected)
