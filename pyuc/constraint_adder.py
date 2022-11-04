import pandas as pd

from pyuc import constraints as cnsts


def make_constraint_index():
    """
    Builds a DataFrame of constraint functions against their name.
    """

    def add_constraint(name, constraint):
        constraint_index.loc[name, "Function"] = constraint

    def init_df():
        return pd.DataFrame(columns=["ID", "Function"]).set_index("ID")

    constraint_index = init_df()

    add_constraint("Supply==Demand", cnsts.cnt_supply_eq_demand)
    add_constraint("Power<=Capacity", cnsts.cnt_power_lt_capacity)
    add_constraint("Power<=CommittedCapacity", cnsts.cnt_power_lt_committed_capacity)
    add_constraint("Power>=MinimumGeneration", cnsts.cnt_power_gt_minimum_generation)
    add_constraint("NumCommitted<=NumUnits", cnsts.cnt_num_committed_lt_num_units)
    add_constraint("CommitmentContinuity", cnsts.cnt_commitment_continuity)
    add_constraint("CommitmentContinuityInitialInterval",
                   cnsts.cnt_commitment_continuity_initial_interval)

    add_constraint("VariablePower<=ResourceAvailability",
                   cnsts.cnt_variable_resource_availability)

    add_constraint("MinimumUpTime", cnsts.cnt_minimum_up_time)
    add_constraint("MinimumDownTime", cnsts.cnt_minimum_down_time)

    add_constraint("RampRateUp", cnsts.cnt_ramp_rate_up)
    add_constraint("RampRateDown", cnsts.cnt_ramp_rate_down)

    return constraint_index


def constraint_selector(paths):
    """
    Reads the constraints to be included (constraint list), and the constraint index,
    combining.

    :param paths dict: problem paths
    """

    def read_constraint_list():
        constraint_list = pd.read_csv(paths["constraint_list"]).set_index("ID")
        constraint_list = constraint_list.replace(["TRUE", "True", "true"], True)
        constraint_list = constraint_list.replace(["FALSE", "False", "false"], False)

        return constraint_list

    constraint_index = make_constraint_index()
    constraint_list = read_constraint_list()
    constraint_list["Function"] = constraint_index.Function

    return constraint_list


def add_all_constraints_to_pulp_problem(problem, constraints):
    """
    Adds the condition-label tuples in constraints to the pulp problem.

    :param constraints list: list of condition-label tuples
    :param problem dict: all problem data
    """

    for label, condition in constraints.items():
        problem["problem"] += condition, label

    return problem["problem"]


def build_constraints(problem, constraints={}):
    """
    Adds constraints that have been specified for inclusion to the constraint list.

    :param problem dict: main problem
    """

    constraint_index = problem["data"]["constraint_index"]
    filt_constraint_index = constraint_index[constraint_index.ToInclude == True]

    for cnt_fn in filt_constraint_index["Function"]:
        cnt_fn_constraints = cnt_fn(problem)
        constraints = {**constraints, **cnt_fn_constraints}

    return constraints


def add_constraints(problem):
    problem["data"]["constraint_index"] = constraint_selector(problem["paths"])
    constraints = build_constraints(problem)
    problem["problem"] = add_all_constraints_to_pulp_problem(problem, constraints)

    return problem["problem"]
