import itertools
import os

import pandas as pd
import pulp as pp

from pyuc import load_data
from pyuc import setup_problem as sp


def run_opt_problem(name, input_data_path, output_data_path):
    problem = sp.setup_problem(name, input_data_path, output_data_path)
    problem['data'] = load_data.load_data(problem['paths'])
    problem['sets'] = load_data.create_sets(problem['data'])
    problem['var'] = create_variables(problem['sets'])
    problem = add_constraints(problem)


class Set():
    def __init__(self, name, indices, master_set=None):
        """
        Set the name, indicies and - if a subset - the master_set

        :param name str: Name of the set
        :param indices list: Indicies of the set
        :param master_set Set: The master set that the subset belongs to
        """

        self.name = name
        self.indices = indices
        self.subsets = list()

        if master_set is not None:
            self.validate_set(master_set)
            master_set.append_subset(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Set(%s)" % self.name

    def validate_set(self, master_set):
        """
        Ensure that each indice of the self subset belongs to the master set.

        :param master_set Set: Master set
        :raises ValueError: If a subset indice doesn't belong to the master set.
        """

        for ind in self.indices:
            if ind not in master_set.indices:
                print('\nMember of set called %s (%s) is not a member' % (self.name, str(ind)),
                      'of the master set %s\n' % master_set.name)
                raise ValueError('Subset validation error')

    def append_subset(self, subset):
        """
        Append the subset to the master set's subsets

        :param subset Set: Subset to be appended
        """

        self.subsets.append(subset)


class Var():
    def __init__(self, name, units, sets, var_type='Continuous'):
        """
        Initiate the variable

        :param name str: variable name
        :param units str: variable units e.g., MWh
        :param sets list: list of Sets
        :param var_type str: Continuous/Binary/Integer etc
        """

        self.name = name
        self.units = units
        self.sets = sets
        self.type = var_type
        self.filename = self.name + '_' + self.units + '.csv'
        self.sets_indices = self.make_var_indices()
        self.var = self.make_pulp_variable()

    def __str__(self):
        return self.name

    def __repr__(self):
        set_str = ''.join([str(s.__str__()) + ', ' for s in self.sets])
        set_str = set_str[0:len(set_str)-2]

        return "Var(%s); units=%s, Sets=[%s]" % (self.name, self.units, set_str)

    def make_var_indices(self):
        """Make all combinations of indices. """

        list_of_set_indices = [x.indices for x in self.sets]

        next_set = list_of_set_indices.pop(0)
        indices_permut = itertools.product(next_set)
        indices_permut_list = [x[0] for x in indices_permut]

        for n in range(len(list_of_set_indices)):
            next_set = list_of_set_indices.pop(0)
            indices_permut = itertools.product(indices_permut_list, next_set)
            indices_permut_list = list(indices_permut)

            if n > 0:
                temp_list = list()

                for x in indices_permut_list:
                    xlist = list(x[0])
                    xlist.append(x[1])
                    temp_list.append(tuple(xlist))
                indices_permut_list = temp_list

        return indices_permut_list

    def make_pulp_variable(self):
        return pp.LpVariable.dicts(self.name, self.sets_indices, lowBound=0, cat=self.type)

    def one_dim_to_df(self):
        """
        Pass optimal variable values to a pandas Series
        """

        values = [self.var[i].value() for i in self.sets_indices]
        self.result_df = pd.Series(data=values, index=self.sets_indices, name=self.name)

    def two_dim_to_df(self):
        """
        Pass optimal variable values to a DataFrame
        """

        self.result_df = \
            pd.DataFrame(index=self.sets[0].indices, columns=self.sets[1].indices)

        for x0 in self.sets[0].indices:
            for x1 in self.sets[1].indices:
                self.result_df.loc[x0, x1] = self.var[(x0, x1)].value()

    def three_dim_to_df(self):
        """
        Pass optimal variable values to a 3D MultiIndex DataFrame
        """

        index = pd.MultiIndex.from_product(
            [self.sets[i].indices for i in range(2)],
            names=[self.sets[i].name for i in range(2)]
        )

        self.result_df = pd.DataFrame(index=index)

        for x0 in self.sets[0].indices:
            for x1 in self.sets[1].indices:
                for x2 in self.sets[2].indices:
                    self.result_df.loc[(x0, x1), x2] = self.var[(x0, x1, x2)].value()

    def four_dim_to_df(self):
        """
        Pass optimal variable values to a 4D MultiIndex DataFrame
        """

        index = pd.MultiIndex.from_product(
            [self.sets[i].indices for i in range(3)],
            names=[self.sets[i].name for i in range(3)]
        )

        self.result_df = pd.DataFrame(index=index)

        for x0 in self.sets[0].indices:
            for x1 in self.sets[1].indices:
                for x2 in self.sets[2].indices:
                    for x3 in self.sets[3].indices:
                        self.result_df.loc[(x0, x1, x2), x3] = \
                            self.var[(x0, x1, x2, x3)].value()

    def to_df_fn_chooser(self):
        """Calls the appropriate function to build the dataframe, based on number of sets. """

        function_dict = {
            1: self.one_dim_to_df,
            2: self.two_dim_to_df,
            3: self.three_dim_to_df,
            4: self.four_dim_to_df,
        }

        function_dict[len(self.sets)]()
        self.result_df_clean_up()

    def result_df_clean_up(self):
        """Performs some simple post processing of the data frame."""

        self.result_df.index.name = self.sets[0].name

        if self.type in ['Binary', 'Integer']:
            self.result_df = self.result_df.astype(int)
        else:
            self.result_df = self.result_df.astype(float)

    # def remove_LA_int_from_results(self, main_intervals):
        # if 'intervals' not in [setx.name for setx in self.sets]:
            # self.result_df_trimmed = self.result_df

            # return
        # else:
            # self.result_df_trimmed = self.result_df.loc[main_intervals]

    def to_csv(self, write_directory):
        """
        Write the results dataframe to a CSV file.

        :param write_directory str: directory to write to.
        """

        write_path = os.path.join(write_directory, self.filename)
        self.result_df.to_csv(write_path)


def create_variables(sets):
    vars = dict()

    vars['power_generated'] = \
        Var('power_generated', 'MW', [sets['intervals'], sets['units']], 'Continuous')

    vars['num_committed'] = \
        Var('num_committed', '#Units', [sets['intervals'], sets['units']], 'Integer')

    vars['num_shutting_down'] = \
        Var('num_shutting_down', '#Units', [sets['intervals'], sets['units']], 'Integer')

    vars['num_starting_up'] = \
        Var('num_starting_up', '#Units', [sets['intervals'], sets['units']], 'Integer')

    vars['unserved_power'] = \
        Var('unserved_power', 'MW', [sets['intervals']], 'Continuous')

    return vars


def add_constraints(problem):
    pass
