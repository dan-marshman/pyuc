from pyuc import setup_problem as sp


def run_opt_problem(name, input_data_path, output_data_path):
    problem = sp.setup_problem(name, input_data_path, output_data_path)


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
