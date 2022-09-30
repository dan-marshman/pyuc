import csv
import io
import os
import shutil
import unittest

import mock
import pulp as pp
from pyuc import setup_problem


class CollectSettings(unittest.TestCase):
    def test_collect_setting_type_integer(self):
        value = 4.7
        result = setup_problem.collect_setting_type_integer(value)
        expected = 4
        self.assertEqual(result, expected)

        value = 4
        result = setup_problem.collect_setting_type_integer(value)
        expected = 4
        self.assertEqual(result, expected)

    def test_collect_setting_type_float(self):
        value = 4.7
        result = setup_problem.collect_setting_type_float(value)
        expected = 4.7
        self.assertEqual(result, expected)

    def test_collect_setting_type_string(self):
        value = 4.7
        result = setup_problem.collect_setting_type_string(value)
        expected = '4.7'
        self.assertEqual(result, expected)

        value = 'HELLO'
        result = setup_problem.collect_setting_type_string(value)
        expected = 'HELLO'
        self.assertEqual(result, expected)

    def test_collect_setting_type_boolean(self):
        value = 'FALSE'
        result = setup_problem.collect_setting_type_boolean(value)
        expected = False
        self.assertEqual(result, expected)

        value = 'False'
        result = setup_problem.collect_setting_type_boolean(value)
        expected = False
        self.assertEqual(result, expected)

        value = 'false'
        result = setup_problem.collect_setting_type_boolean(value)
        expected = False
        self.assertEqual(result, expected)

        value = 'TRUE'
        result = setup_problem.collect_setting_type_boolean(value)
        expected = True
        self.assertEqual(result, expected)

        value = 'True'
        result = setup_problem.collect_setting_type_boolean(value)
        expected = True
        self.assertEqual(result, expected)

        value = 'true'
        result = setup_problem.collect_setting_type_boolean(value)
        expected = True
        self.assertEqual(result, expected)


class ReadSettings(unittest.TestCase):
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
        result = setup_problem.import_settings_file('dummy_path.csv')
        expected = {
            'Val1': 4,
            'Val2': 4.2,
            'Val3': "HELLO",
            'Val4': False,
        }

        self.assertEqual(result, expected)

    @mock.patch('builtins.open')
    @mock.patch('pyuc.setup_problem.collect_setting_type_integer')
    def test_read_settings_call_collect_int(self, collect_int_mock, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,int,4'
            )
        setup_problem.import_settings_file('dummy_path.csv')

        collect_int_mock.assert_called_once_with('4')

    @mock.patch('builtins.open')
    @mock.patch('pyuc.setup_problem.collect_setting_type_float')
    def test_read_settings_call_collect_float(self, collect_float_mock, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,float,4.2'
            )
        setup_problem.import_settings_file('dummy_path.csv')

        collect_float_mock.assert_called_once_with('4.2')

    @mock.patch('builtins.open')
    @mock.patch('pyuc.setup_problem.collect_setting_type_string')
    def test_read_settings_call_collect_string(self, collect_str_mock, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,str,"HELLO'
            )
        setup_problem.import_settings_file('dummy_path.csv')

        collect_str_mock.assert_called_once_with('HELLO')

    @mock.patch('builtins.open')
    @mock.patch('pyuc.setup_problem.collect_setting_type_boolean')
    def test_read_settings_call_collect_bool(self, collect_bool_mock, open_mock):
        open_mock.return_value = \
            io.StringIO(
                'Parameter,Type,Value\n'
                + 'Val1,bool,FALSE'
            )
        setup_problem.import_settings_file('dummy_path.csv')

        collect_bool_mock.assert_called_once_with('FALSE')


class LoadSettings(unittest.TestCase):
    def setUp(self):
        self.settings_path = 'MY_PATH'

    @mock.patch('pyuc.utils.check_path_exists')
    @mock.patch('pyuc.setup_problem.import_settings_file', return_value={})
    def test_call_import_settings_file(self, load_settings_mock, check_path_mock):
        setup_problem.load_settings(self.settings_path)
        load_settings_mock.assert_called_once_with(self.settings_path)

    @mock.patch('pyuc.utils.check_path_exists')
    @mock.patch('pyuc.setup_problem.import_settings_file', return_value={})
    def test_call_check_path(self, load_settings_mock, check_path_mock):
        setup_problem.load_settings(self.settings_path)
        check_path_mock.assert_called_once_with(self.settings_path, 'Settings File')


class InitialiseProblem(unittest.TestCase):
    def test_initialise_problem_with_str(self):
        result = setup_problem.initialise_uc_problem('my_problem')
        expected = {'name': 'my_problem'}

        self.assertEqual(result, expected)

    def test_initialise_uc_problem_as_dict(self):
        result = setup_problem.initialise_uc_problem('my_problem')
        expected = dict

        self.assertIsInstance(result, expected)

    def test_make_pulp_problem(self):
        name = 'MY_NAME'
        result = setup_problem.make_pulp_problem(name)

        expected = pp.LpProblem(name='MY_NAME', sense=pp.LpMinimize)
        self.assertEqual(result.name, expected.name)
        self.assertEqual(result.sense, expected.sense)


class Paths(unittest.TestCase):
    def test_initialise_paths(self):
        result = setup_problem.initialise_paths('input_data_path', 'output_data_path', 'MY_PROB')
        expected = {
            'input_data': 'input_data_path',
            'settings': os.path.join('input_data_path', 'settings.csv'),
            'unit_data': os.path.join('input_data_path', 'unit_data.csv'),
            'demand': os.path.join('input_data_path', 'demand.csv'),
            'constraint_list': os.path.join('input_data_path', 'constraint_list.csv'),
            'outputs': os.path.join('output_data_path', 'MY_PROB'),
            'results': os.path.join('output_data_path', 'MY_PROB', 'results')
        }

        self.assertEqual(result, expected)

    def test_make_results_folders(self):
        paths = {
            'outputs': os.path.join('test', 'TEMP', 'outputs'),
            'results': os.path.join('test', 'TEMP', 'outputs', 'results')
        }
        test_folder = os.path.join(paths['results'], 'test')

        for dir in [paths['outputs'], paths['results'], test_folder]:
            if not os.path.exists(dir):
                os.makedirs(dir)

        setup_problem.make_results_folders(paths)

        self.assertTrue(os.path.exists(paths['outputs']))
        self.assertTrue(os.path.exists(paths['results']))
        self.assertEqual(os.listdir(paths['results']), [])


class SetUpProblem(unittest.TestCase):
    def setUp(self):
        self.name = "MY_NAME"
        self.input_data_path = os.path.join("test", "TEMP", "IN")
        self.output_data_path = os.path.join("test", "TEMP", "OUT")

        if not os.path.exists(self.input_data_path):
            os.makedirs(self.input_data_path)

        if not os.path.exists(self.output_data_path):
            os.makedirs(self.output_data_path)

        self.settings_path = os.path.join(self.input_data_path, 'settings.csv')
        with open(self.settings_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['Parameter', 'Type', 'Value'])
            writer.writerow(['P1', 'int', 101])
            writer.writerow(['P2', 'str', 'A_STRING'])
            writer.writerow(['P3', 'bool', 'FALSE'])

    def tearDown(self):
        shutil.rmtree(self.input_data_path)
        shutil.rmtree(self.output_data_path)

    @mock.patch('pyuc.setup_problem.make_results_folders')
    @mock.patch('pyuc.setup_problem.make_pulp_problem')
    @mock.patch('pyuc.setup_problem.initialise_uc_problem')
    @mock.patch('pyuc.setup_problem.initialise_paths')
    @mock.patch('pyuc.setup_problem.load_settings')
    def test_each_fn_is_called(self,
                               load_settings_mock,
                               init_paths_mock,
                               init_prob_mock,
                               make_pulp_prob_mock,
                               make_results_folders_mock
                               ):

        init_prob_mock.return_value = {}
        init_paths_mock.return_value = {'settings': 'A_PATH'}

        setup_problem.setup_problem(self.name,
                                    self.input_data_path,
                                    self.output_data_path)

        init_prob_mock.assert_called_once_with(self.name)
        init_paths_mock.assert_called_once_with(self.input_data_path,
                                                self.output_data_path,
                                                self.name)
        load_settings_mock.assert_called_once_with('A_PATH')
        make_results_folders_mock.assert_called_once_with({'settings': 'A_PATH'})

    def test_setup_problem(self):
        result = setup_problem.setup_problem(self.name,
                                             self.input_data_path,
                                             self.output_data_path)
        expected = {
            'name': 'MY_NAME',
            'paths': {
                'input_data': self.input_data_path,
                'settings': self.settings_path,
                'unit_data': os.path.join(self.input_data_path, 'unit_data.csv'),
                'demand': os.path.join(self.input_data_path, 'demand.csv'),
                'constraint_list': os.path.join(self.input_data_path, 'constraint_list.csv'),
                'outputs': os.path.join(self.output_data_path, self.name),
                'results': os.path.join(self.output_data_path, self.name, 'results'),
            },
            'settings': {'P1': 101, 'P2': 'A_STRING', 'P3': False},
            'problem': mock.ANY
        }
        self.assertEqual(result, expected)
