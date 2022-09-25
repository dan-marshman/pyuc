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
        self.unit_df = pd.DataFrame(index=['A1', 'A2', 'A3', 'A4'])

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


class LoadDataItems(unittest.TestCase):
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


class LoadData(unittest.TestCase):
    def setUp(self):
        self.input_data_path = os.path.join("test", "TEMP", "IN")
        output_data_path = os.path.join("test", "TEMP", "OUT")
        name = 'MY_PROB'

        self.paths = \
            setup_problem.initialise_paths(self.input_data_path, output_data_path, name)

        self.demand_df = pd.DataFrame(index=[1, 2, 3], data={'Demand': [100, 200, 300]})
        self.demand_df.index.name = 'Interval'

        self.unit_data_df = pd.DataFrame(
            index=['U1', 'U2'],
            data={'Capacity': [100, 200], 'MinGen': [0.5, 0.5]}
        )
        self.unit_data_df.index.name = 'Unit'

        if not os.path.exists(self.input_data_path):
            os.makedirs(self.input_data_path)

        self.demand_df.to_csv(self.paths['demand'])
        self.unit_data_df.to_csv(self.paths['unit_data'])

    def tearDown(self):
        shutil.rmtree(self.input_data_path)

    def test_load_data(self):
        result = ld.load_data(self.paths)
        expected = {'demand': self.demand_df, 'unit_data': self.unit_data_df}

        self.assertEqual(list(result.keys()), list(expected.keys()))
        pd.testing.assert_frame_equal(result['demand'], expected['demand'])
        pd.testing.assert_frame_equal(result['unit_data'], expected['unit_data'])
