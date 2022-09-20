import os
import unittest

import mock
import pandas as pd
from pyuc import pyuc


class RunOptProblem(unittest.TestCase):
    def setUp(self):
        self.name = "MY_NAME"
        self.input_data_path = "IN"
        self.output_data_path = "OUT"

    @mock.patch('pyuc.pyuc.create_variables')
    @mock.patch('pyuc.load_data.create_sets')
    @mock.patch('pyuc.load_data.load_data')
    @mock.patch('pyuc.setup_problem.setup_problem')
    def test_setup_problem_is_called(self,
                                     setup_problem_mock,
                                     load_data_mock,
                                     create_sets_mock,
                                     create_variables_mock,
                                  ):

        pyuc.run_opt_problem(self.name, self.input_data_path, self.output_data_path)
        setup_problem_mock.assert_called_once_with(
            self.name, self.input_data_path, self.output_data_path
        )

    @mock.patch('pyuc.pyuc.create_variables')
    @mock.patch('pyuc.load_data.create_sets')
    @mock.patch('pyuc.load_data.load_data')
    @mock.patch('pyuc.setup_problem.setup_problem', )
    def test_load_data_is_called(self,
                                 setup_problem_mock,
                                 load_data_mock,
                                 create_sets_mock,
                                 create_variables_mock,
                                 ):

        setup_problem_mock.return_value = {'paths': {'path': 'path'}}

        pyuc.run_opt_problem(self.name, self.input_data_path, self.output_data_path)
        load_data_mock.assert_called_once_with({'path': 'path'})

    @mock.patch('pyuc.pyuc.create_variables')
    @mock.patch('pyuc.load_data.create_sets')
    @mock.patch('pyuc.load_data.load_data')
    @mock.patch('pyuc.setup_problem.setup_problem', )
    def test_create_sets_is_called(self,
                                   setup_problem_mock,
                                   load_data_mock,
                                   create_sets_mock,
                                   create_variables_mock,
                                   ):

        setup_problem_mock.return_value = {'paths': {'path': 'path'}}
        load_data_mock.return_value = 'data'

        pyuc.run_opt_problem(self.name, self.input_data_path, self.output_data_path)
        create_sets_mock.assert_called_once_with('data')

    @mock.patch('pyuc.pyuc.create_variables')
    @mock.patch('pyuc.load_data.create_sets')
    @mock.patch('pyuc.load_data.load_data')
    @mock.patch('pyuc.setup_problem.setup_problem', )
    def test_create_variables_is_called(self,
                                        setup_problem_mock,
                                        load_data_mock,
                                        create_sets_mock,
                                        create_variables_mock,
                                        ):

        setup_problem_mock.return_value = {'paths': {'path': 'path'}}
        create_sets_mock.return_value = 'sets'

        pyuc.run_opt_problem(self.name, self.input_data_path, self.output_data_path)
        create_variables_mock.assert_called_once_with('sets')


class testVarBasic(unittest.TestCase):
    def setUp(self):
        self.sets = [
            pyuc.Set("intervals", list(range(3))),
            pyuc.Set("units", ['U1', 'U2']),
        ]

        self.name = "NAME"
        self.units = "MW"
        self.var = pyuc.Var(self.name, self.units, self.sets)

    def test_var_init_name(self):
        self.assertEqual(self.var.name, self.name)

    def test_var_init_units(self):
        self.assertEqual(self.var.units, self.units)

    def test_var_init_sets(self):
        self.assertEqual(self.var.sets, self.sets)

    def test_var_init_type(self):
        self.assertEqual(self.var.type, 'Continuous')

    def test_var_init_type_specified(self):
        var = pyuc.Var(self.name, self.units, self.sets, 'Binary')
        self.assertEqual(var.type, 'Binary')

    def test_var_init_indices(self):
        expected = ((0, 'U1'), (1, 'U1'), (2, 'U1'), (0, 'U2'), (1, 'U2'), (2, 'U2'))
        self.assertCountEqual(self.var.sets_indices, expected)

    @mock.patch('pyuc.pyuc.Var.make_pulp_variable')
    def test_make_pulp_variable_is_called(self, make_pulp_variable_mock):
        self.var = pyuc.Var(self.name, self.units, self.sets)
        make_pulp_variable_mock.assert_called_once_with()

    @mock.patch('pyuc.pyuc.Var.make_var_indices')
    def test_make_var_indices_is_called(self, make_var_indices_mock):
        self.var = pyuc.Var(self.name, self.units, self.sets)
        make_var_indices_mock.assert_called_once_with()

    def test___str__(self):
        self.assertEqual(self.var.__str__(), self.var.name)

    def test___repr__(self):
        set_str = ''.join([str(s.__str__()) + ', ' for s in self.var.sets])
        set_str = set_str[0:len(set_str)-2]

        expected = "Var(%s); units=%s, Sets=[%s]" % (self.name, self.units, set_str)
        self.assertEqual(self.var.__repr__(), expected)


class testVarMethods(unittest.TestCase):
    def setUp(self):
        self.sets = [
            pyuc.Set("intervals", list(range(3))),
            pyuc.Set("units", ['U1', 'U2']),
        ]

        self.name = "NAME"
        self.units = "UNITS"
        self.var = pyuc.Var(self.name, self.units, self.sets)
        self.var.result_df = pd.DataFrame()

    @mock.patch('pulp.LpVariable.dicts')
    def test_make_pulp_indices(self, dict_variable_mock):
        self.var.make_pulp_variable()
        dict_variable_mock.assert_called_once_with(self.var.name, self.var.sets_indices,
                                                   lowBound=0, cat='Continuous')

    def test_make_var_indices(self):
        expected = ((0, 'U1'), (1, 'U1'), (2, 'U1'), (0, 'U2'), (1, 'U2'), (2, 'U2'))
        self.assertCountEqual(self.var.sets_indices, expected)

    @mock.patch('pandas.DataFrame.to_csv')
    def test_write_to_csv(self, pd_to_csv_mock):
        write_path = "A_DIRECTORY"
        self.var.to_csv(write_path)
        pd_to_csv_mock.assert_called_once_with(os.path.join(write_path, "NAME_UNITS.csv"))

    def test_df_clean_up_name(self):
        self.var.result_df = pd.DataFrame()
        self.var.result_df_clean_up()
        self.assertEqual(self.var.result_df.index.name, self.sets[0].name)

    def test_df_clean_up_dtype_continuous(self):
        self.var.result_df = pd.DataFrame(data={'A': range(4)})
        self.var.result_df_clean_up()
        self.assertEqual(self.var.result_df.dtypes['A'], float)

    def test_df_clean_up_dtype_integer(self):
        self.var.result_df = pd.DataFrame(data={'A': range(4)})
        self.var.type = 'Integer'
        self.var.result_df_clean_up()
        self.assertEqual(self.var.result_df.dtypes['A'], int)

    def test_df_clean_up_dtype_binary(self):
        self.var.result_df = pd.DataFrame(data={'A': range(4)})
        self.var.type = 'Binary'
        self.var.result_df_clean_up()
        self.assertEqual(self.var.result_df.dtypes['A'], int)


class testVarDfFnChooser(unittest.TestCase):
    def setUp(self):
        self.name = "NAME"
        self.units = "UNITS"

    @mock.patch('pyuc.pyuc.Var.result_df_clean_up')
    @mock.patch('pyuc.pyuc.Var.one_dim_to_df')
    def test_df_chooser_one(self, one_dim_mock, clean_up_mock):
        self.sets = [pyuc.Set("intervals", list(range(3)))]
        self.var = pyuc.Var(self.name, self.units, self.sets)
        self.var.to_df_fn_chooser()
        one_dim_mock.assert_called_once_with()

    @mock.patch('pyuc.pyuc.Var.result_df_clean_up')
    @mock.patch('pyuc.pyuc.Var.two_dim_to_df')
    def test_df_chooser_two(self, two_dim_mock, clean_up_mock):
        self.sets = 2 * [pyuc.Set("intervals", list(range(3)))]
        self.var = pyuc.Var(self.name, self.units, self.sets)
        self.var.to_df_fn_chooser()
        two_dim_mock.assert_called_once_with()

    @mock.patch('pyuc.pyuc.Var.result_df_clean_up')
    @mock.patch('pyuc.pyuc.Var.three_dim_to_df')
    def test_df_chooser_three(self, three_dim_mock, clean_up_mock):
        self.sets = 3 * [pyuc.Set("intervals", list(range(3)))]
        self.var = pyuc.Var(self.name, self.units, self.sets)
        self.var.to_df_fn_chooser()
        three_dim_mock.assert_called_once_with()

    @mock.patch('pyuc.pyuc.Var.result_df_clean_up')
    @mock.patch('pyuc.pyuc.Var.four_dim_to_df')
    def test_df_chooser_four(self, four_dim_mock, clean_up_mock):
        self.sets = 4 * [pyuc.Set("intervals", list(range(3)))]
        self.var = pyuc.Var(self.name, self.units, self.sets)
        self.var.to_df_fn_chooser()
        four_dim_mock.assert_called_once_with()


class testDimToDf(unittest.TestCase):
    def setUp(self):
        self.indices1 = range(3, 8)
        self.indices2 = ['A', 'B', 'C']
        self.indices3 = ['e', 'f', 'g']
        self.indices4 = range(4)

        self.sets = [
            pyuc.Set('S1', self.indices1),
            pyuc.Set('S2', self.indices2),
            pyuc.Set('S3', self.indices3),
            pyuc.Set('S4', self.indices4)
        ]

    def test_one_dim_to_df(self):
        var = pyuc.Var('var1', 'MY_UNITS', self.sets[0:1])

        for i in self.indices1:
            var.var[i].setInitialValue(2*i)

        var.one_dim_to_df()
        result = var.result_df

        expected = pd.Series(
                data=[2*i for i in self.indices1],
                name='var1',
                index=self.indices1
        )

        pd.testing.assert_series_equal(result, expected)

    def test_two_dim_to_df(self):
        var = pyuc.Var('var1', 'MY_UNITS', self.sets[0:2])

        for i in self.indices1:
            for jj, j in enumerate(self.indices2):
                var.var[(i, j)].setInitialValue(2*i + jj)

        var.two_dim_to_df()
        result = var.result_df

        expected = pd.DataFrame(
            {j: [2*i+jj for i in self.indices1] for jj, j in enumerate(self.indices2)},
            index=self.indices1
        )

        pd.testing.assert_frame_equal(result, expected, check_dtype=False)

    def test_three_dim_to_df(self):
        var = pyuc.Var('var1', 'MY_UNITS', self.sets[0:3])

        for i in self.indices1:
            for jj, j in enumerate(self.indices2):
                for kk, k in enumerate(self.indices3):
                    var.var[(i, j, k)].setInitialValue(2*i + jj - kk)

        var.three_dim_to_df()
        result = var.result_df

        expected = pd.DataFrame(
            index=pd.MultiIndex.from_product(
                [self.sets[i].indices for i in range(2)],
                names=[self.sets[i].name for i in range(2)]
            ),
        )

        for i in self.indices1:
            for jj, j in enumerate(self.indices2):
                for kk, k in enumerate(self.indices3):
                    expected.loc[(i, j), k] = 2*i + jj - kk

        pd.testing.assert_frame_equal(result, expected, check_dtype=False)

    def test_four_dim_to_df(self):
        var = pyuc.Var('var1', 'MY_UNITS', self.sets[0:4])

        for i in self.indices1:
            for jj, j in enumerate(self.indices2):
                for kk, k in enumerate(self.indices3):
                    for m in self.indices4:
                        var.var[(i, j, k, m)].setInitialValue(2*i + jj - kk + 3*m)

        var.four_dim_to_df()
        result = var.result_df

        expected = pd.DataFrame(
            index=pd.MultiIndex.from_product(
                [self.sets[i].indices for i in range(3)],
                names=[self.sets[i].name for i in range(3)]
            ),
        )

        for i in self.indices1:
            for jj, j in enumerate(self.indices2):
                for kk, k in enumerate(self.indices3):
                    for m in self.indices4:
                        expected.loc[(i, j, k), m] = 2*i + jj - kk + 3*m

        pd.testing.assert_frame_equal(result, expected, check_dtype=False)
