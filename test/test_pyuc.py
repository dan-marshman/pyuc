import io
import os
import unittest

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
    def test_collect_setting_type_integer(self):
        value = 4.7
        result = pyuc.collect_setting_type_integer(value)
        expected = 4
        self.assertEqual(result, expected)

        value = 4
        result = pyuc.collect_setting_type_integer(value)
        expected = 4
        self.assertEqual(result, expected)

    def test_collect_setting_type_float(self):
        value = 4.7
        result = pyuc.collect_setting_type_float(value)
        expected = 4.7
        self.assertEqual(result, expected)

    def test_collect_setting_type_string(self):
        value = 4.7
        result = pyuc.collect_setting_type_string(value)
        expected = '4.7'
        self.assertEqual(result, expected)

        value = 'HELLO'
        result = pyuc.collect_setting_type_string(value)
        expected = 'HELLO'
        self.assertEqual(result, expected)

    def test_collect_setting_type_boolean(self):
        value = 'FALSE'
        result = pyuc.collect_setting_type_boolean(value)
        expected = False
        self.assertEqual(result, expected)

        value = 'False'
        result = pyuc.collect_setting_type_boolean(value)
        expected = False
        self.assertEqual(result, expected)

        value = 'false'
        result = pyuc.collect_setting_type_boolean(value)
        expected = False
        self.assertEqual(result, expected)

        value = 'TRUE'
        result = pyuc.collect_setting_type_boolean(value)
        expected = True
        self.assertEqual(result, expected)

        value = 'True'
        result = pyuc.collect_setting_type_boolean(value)
        expected = True
        self.assertEqual(result, expected)

        value = 'true'
        result = pyuc.collect_setting_type_boolean(value)
        expected = True
        self.assertEqual(result, expected)

    @mock.patch('builtins.open')
    def test_read_settings(self, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,int,4\n'
                + 'Val2,float,4.2\n'
                + 'Val3,str,HELLO\n'
                + 'Val4,bool,FALSE'
            )
        result = pyuc.load_settings('dummy_path.csv')

        expected = {
            'Val1': 4,
            'Val2': 4.2,
            'Val3': "HELLO",
            'Val4': False,
        }

        self.assertEqual(result, expected)

    @mock.patch('builtins.open')
    @mock.patch('pyuc.pyuc.collect_setting_type_integer')
    def test_read_settings_call_collect_int(self, collect_int_mock, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,int,4'
            )
        pyuc.load_settings('dummy_path.csv')

        collect_int_mock.assert_called_once_with('4')

    @mock.patch('builtins.open')
    @mock.patch('pyuc.pyuc.collect_setting_type_float')
    def test_read_settings_call_collect_float(self, collect_float_mock, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,float,4.2'
            )
        pyuc.load_settings('dummy_path.csv')

        collect_float_mock.assert_called_once_with('4.2')

    @mock.patch('builtins.open')
    @mock.patch('pyuc.pyuc.collect_setting_type_string')
    def test_read_settings_call_collect_string(self, collect_str_mock, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,str,"HELLO'
            )
        pyuc.load_settings('dummy_path.csv')

        collect_str_mock.assert_called_once_with('HELLO')

    @mock.patch('builtins.open')
    @mock.patch('pyuc.pyuc.collect_setting_type_boolean')
    def test_read_settings_call_collect_bool(self, collect_bool_mock, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,bool,FALSE'
            )
        pyuc.load_settings('dummy_path.csv')

        collect_bool_mock.assert_called_once_with('FALSE')
