import io
import os
import shutil
import unittest

import mock
import pandas as pd
from pyuc import load_data as ld
from pyuc import setup_problem


class LoadSets(unittest.TestCase):
    def setUp(self):
        self.demand_df = pd.DataFrame(index=range(100))
        self.unit_df = pd.DataFrame(
            index=['A1', 'A2', 'A3', 'A4'],
            data={'Technology': ['Coal', 'Coal', 'Coal', 'Coal']})

        self.data = {
            'demand': self.demand_df,
            'units': self.unit_df
        }

        self.sets = ld.create_single_sets(self.data)

    def test_create_master_set_check_keys(self):
        result = list(self.sets.keys())
        self.assertEqual(result, ['intervals', 'units'])

    def test_load_intervals_master_set(self):
        result = self.sets['intervals']

        self.assertEqual(result.name, 'intervals')
        self.assertEqual(result.indices, list(range(100)))

    def test_load_units_master_set(self):
        self.assertEqual(self.sets['units'].name, 'units')
        self.assertEqual(self.sets['units'].indices, ['A1', 'A2', 'A3', 'A4'])

    @mock.patch('pyuc.load_data.create_single_sets')
    @mock.patch('pyuc.load_data.create_subsets')
    def test_create_single_sets_is_called(self,
                                          create_subsets_mock,
                                          create_single_sets_mock):
        ld.create_sets(self.data)
        create_single_sets_mock.assert_called_once_with(self.data)

    @mock.patch('pyuc.load_data.create_single_sets')
    @mock.patch('pyuc.load_data.create_combination_sets')
    @mock.patch('pyuc.load_data.create_subsets')
    def test_create_subsets_is_called(self,
                                      create_subsets_mock,
                                      create_combination_sets_mock,
                                      create_single_sets_mock,
                                      ):
        create_single_sets_mock.return_value = 'sets'
        ld.create_sets(self.data)
        create_subsets_mock.assert_called_once_with('sets', self.data)

    @mock.patch('pyuc.load_data.create_single_sets')
    @mock.patch('pyuc.load_data.create_combination_sets')
    @mock.patch('pyuc.load_data.create_subsets')
    def test_create_combination_sets_is_called(self,
                                               create_subsets_mock,
                                               create_combination_sets_mock,
                                               create_single_sets_mock,
                                               ):
        create_single_sets_mock.return_value = 'sets'
        create_subsets_mock.return_value = 'sets'
        ld.create_sets(self.data)
        create_combination_sets_mock.assert_called_once_with('sets')


class LoadSubSets(unittest.TestCase):
    def setUp(self):
        self.demand_df = pd.DataFrame(index=range(100))
        self.unit_df = pd.DataFrame(
            index=['Co', 'CC', 'OC', 'Nu', 'Wi', 'So', 'St'],
            data={'Technology': ['Coal', 'CCGT', 'OCGT', 'Nuclear', 'Wind', 'Solar', 'Storage']})

        self.data = {
            'demand': self.demand_df,
            'units': self.unit_df
        }

        self.sets = ld.create_single_sets(self.data)
        self.sets = ld.create_subsets(self.sets, self.data)

    def test_units_commit_subset(self):
        result = self.sets['units_commit'].indices
        expected = ['Co', 'CC', 'OC', 'Nu']
        self.assertEqual(result, expected)

    def test_units_variable_generator_subset(self):
        result = self.sets['units_variable'].indices
        expected = ['Wi', 'So']
        self.assertEqual(result, expected)

    def test_units_storage_subset(self):
        result = self.sets['units_storage'].indices
        expected = ['St']
        self.assertEqual(result, expected)


class LoadDataItems(unittest.TestCase):
    def setUp(self):
        self.  settings = {'IntervalDurationHrs': 1, 'ValueOfLostLoad$/MWh': 99}

    @mock.patch('pyuc.utils.check_path_exists')
    def test_load_unit_data(self, check_path_mock):
        test_file = io.StringIO(
            'Unit,Capacity,MinGen\n'
            + 'U1,100,0.5\n'
            + 'U2,200,0.5'
        )
        result = ld.load_unit_data(test_file)

        expected = pd.DataFrame(
            index=['U1', 'U2'],
            data={'Capacity': [100, 200], 'MinGen': [0.5, 0.5]}
        )
        expected.index.name = 'Unit'

        pd.testing.assert_frame_equal(result, expected)

    @mock.patch('pyuc.utils.check_path_exists')
    def test_load_demand_data(self, check_path_mock):
        test_file = io.StringIO(
            'Interval,Demand\n'
            + '1,100\n'
            + '2,200\n'
            + '3,300'
        )
        result = ld.load_demand_data(test_file)

        expected = pd.DataFrame(index=[1, 2, 3], data={'Demand': [100, 200, 300]})
        expected.index.name = 'Interval'

        pd.testing.assert_frame_equal(result, expected)

    @mock.patch('pyuc.utils.check_path_exists')
    def test_load_variable_data_file_exists(self, check_path_mock):
        test_file = io.StringIO(
            'Interval,Wind,Solar\n'
            + '1,1,0.2\n'
            + '2,0.5,0.2'
        )
        result = ld.load_variable_data(test_file)

        expected = pd.DataFrame(
            index=[1, 2],
            data={'Wind': [1, 0.5], 'Solar': [0.2, 0.2]}
        )
        expected.index.name = 'Interval'

        pd.testing.assert_frame_equal(result, expected)

    def test_load_variable_data_file_does_not_exist(self):
        test_file = "path_does_not_exist"
        result = ld.load_variable_data(test_file)
        self.assertEqual(result, None)

    def test_load_voll(self):
        result = ld.load_voll(self.settings)
        self.assertEqual(result, 99)

    def test_load_interval_duration(self):
        result = ld.load_interval_duration(self.settings)
        self.assertEqual(result, 1)


class LoadData(unittest.TestCase):
    def setUp(self):
        self.input_data_path = os.path.join("test", "TEMP", "IN")
        output_data_path = os.path.join("test", "TEMP", "OUT")
        name = 'MY_PROB'

        self.paths = \
            setup_problem.initialise_paths(self.input_data_path, output_data_path, name)

        self.problem = {
            'paths': self.paths,
            'settings': {'ValueOfLostLoad$/MWh': 10, 'IntervalDurationHrs': 0.5}
        }

        self.demand_df = pd.DataFrame(index=[1, 2, 3], data={'Demand': [100, 200, 300]})
        self.demand_df.index.name = 'Interval'

        self.unit_data_df = pd.DataFrame(
            index=['U1', 'U2'],
            data={'Capacity': [100, 200], 'MinGen': [0.5, 0.5]}
        )
        self.unit_data_df.index.name = 'Unit'

        self.variable_data_df = pd.DataFrame(
            index=[1, 2, 3],
            data={'Wind': [0.5, 0.5, 0.5]}
        )
        self.variable_data_df.index.name = 'Interval'

        if not os.path.exists(self.input_data_path):
            os.makedirs(self.input_data_path)

        self.demand_df.to_csv(self.paths['demand'])
        self.unit_data_df.to_csv(self.paths['unit_data'])
        self.variable_data_df.to_csv(self.paths['variable_traces'])

    def tearDown(self):
        shutil.rmtree(self.input_data_path)

    def test_load_data(self):
        result = ld.load_data(self.problem)
        expected = {
            'demand': self.demand_df,
            'units': self.unit_data_df,
            'variable_traces': self.variable_data_df,
            'ValueOfLostLoad$/MWh': 10,
            'IntervalDurationHrs': 0.5
        }

        self.assertEqual(list(result.keys()), list(expected.keys()))
        pd.testing.assert_frame_equal(result['demand'], expected['demand'])
        pd.testing.assert_frame_equal(result['units'], expected['units'])
        pd.testing.assert_frame_equal(result['variable_traces'],
                                      expected['variable_traces'])
