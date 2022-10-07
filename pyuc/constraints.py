import pulp as pp


def constraint_adder(constraint_func):
    def extractor_wrapper(problem):
        sets, data, var = problem['sets'], problem['data'], problem['var']
        constraints = constraint_func(sets, data, var)

        return constraints

    return extractor_wrapper


@constraint_adder
def cnt_supply_eq_demand(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    total_power = total_power_in_interval(sets, var['power_generated'])

    for i in sets['intervals'].indices:
        label = 'supply_eq_demand_(i=%d)' % i

        condition = (
            total_power[i]
            + var['unserved_power'].var[(i)]
            ==
            data['demand']['Demand'][i]
            )

        constraints[label] = condition

    return constraints


@constraint_adder
def cnt_power_lt_capacity(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    for i in sets['intervals'].indices:
        for u in sets['units'].indices:
            label = 'power_lt_capacity_(i=%d, u=%s)' % (i, u)

            condition = (
                var['power_generated'].var[(i, u)]
                <=
                data['units']['CapacityMW'][u]
                * data['units']['NumUnits'][u]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_power_lt_committed_capacity(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    for i in sets['intervals'].indices:
        for u in sets['units'].indices:
            label = 'power_lt_committed_capacity_(i=%d, u=%s)' % (i, u)

            condition = (
                var['power_generated'].var[(i, u)]
                <=
                var['num_committed'].var[(i, u)]
                * data['units']['CapacityMW'][u]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_power_gt_minimum_generation(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    for i in sets['intervals'].indices:
        for u in sets['units'].indices:
            label = 'power_gt_minimum_generation_(i=%d, u=%s)' % (i, u)

            condition = (
                var['power_generated'].var[(i, u)]
                >=
                var['num_committed'].var[(i, u)]
                * data['units']['CapacityMW'][u]
                * data['units']['MinimumGenerationFrac'][u]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_num_committed_lt_num_units(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    for i in sets['intervals'].indices:
        for u in sets['units'].indices:
            label = 'num_committed_lt_num_units(i=%d, u=%s)' % (i, u)

            condition = (
                var['num_committed'].var[(i, u)]
                <=
                data['units']['NumUnits'][u]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_commitment_continuity(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    for i in sets['intervals'].indices[1:]:
        for u in sets['units'].indices:
            label = 'commitment_continuity(i=%d, u=%s)' % (i, u)

            condition = (
                var['num_committed'].var[(i, u)]
                ==
                var['num_committed'].var[(i-1, u)]
                + var['num_starting_up'].var[(i, u)]
                - var['num_shutting_down'].var[(i, u)]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_commitment_continuity_initial_interval(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    i = sets['intervals'].indices[0]
    initial_units_on = 0

    for u in sets['units'].indices:
        label = 'commitment_continuity(i=%d, u=%s)' % (i, u)

        condition = (
            var['num_committed'].var[(i, u)]
            ==
            initial_units_on
            + var['num_starting_up'].var[(i, u)]
            - var['num_shutting_down'].var[(i, u)]
            )

        constraints[label] = condition

    return constraints


@constraint_adder
def cnt_minimum_up_time(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    num_start_ups_within_up_time = \
        num_start_ups_within_up_time_calculator(sets, data, var)

    for i in sets['intervals'].indices:

        for u in sets['units'].indices:
            label = 'minimum_up_time(i=%d, u=%s)' % (i, u)

            condition = (
                var['num_committed'].var[(i, u)]
                >=
                num_start_ups_within_up_time[(i, u)]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_minimum_down_time(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    num_shut_downs_within_down_time = \
        num_shut_downs_within_down_time_calculator(sets, data, var)

    for i in sets['intervals'].indices:

        for u in sets['units'].indices:
            label = 'minimum_down_time(i=%d, u=%s)' % (i, u)

            condition = (
                data['units']['NumUnits'][u]
                - var['num_committed'].var[(i, u)]
                >=
                num_shut_downs_within_down_time[(i, u)]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_ramp_rate_up(sets, data, var, constraints=[]):
    constraints = {}  # No idea why this is needed

    up_ramp_MW = up_ramp_calculator(sets, data, var)
    start_up_ramp_capacity_MW = start_up_ramp_capacity_calculator(sets, data, var)
    online_ramp_capacity_MW = online_ramp_capacity_calculator(sets, data, var)

    for i in sets['intervals'].indices:

        for u in sets['units_commit'].indices:
            label = 'ramp_rate_up_(i=%s, u_%d)' % (i, u)

            condition = \
                up_ramp_MW \
                <= \
                var['num_committed'].var[(i, u)] * online_ramp_capacity_MW[u] \
                + var['num_starting_up'].var[(i, u)] * start_up_ramp_capacity_MW[u]

            constraints[label] = condition

    return constraints


def num_start_ups_within_up_time_calculator(sets, data, var):
    """
    Return a dictionary that sums the start up events within a units minimum up time (counting
    backwards), for each unit and interval.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    :param var dict: var dictionary
    """

    i0 = min(sets['intervals'].indices)
    num_start_ups_within_up_time = {}

    for i in sets['intervals'].indices:
        for u in sets['units'].indices:
            up_time = data['units']['MinimumUpTimeHrs'][u]
            i_low = max(i0, i - up_time + 1)

            num_start_ups_within_up_time[(i, u)] = \
                pp.lpSum([
                    var['num_starting_up'].var[(i2, u)] for i2 in range(i_low, i+1)
                ])

    return num_start_ups_within_up_time


def num_shut_downs_within_down_time_calculator(sets, data, var):
    """
    Return a dictionary that sums the shut down events within a units minimum down time (counting
    backwards), for each unit and interval.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    :param var dict: var dictionary
    """

    i0 = min(sets['intervals'].indices)
    num_shut_downs_within_down_time = {}

    for i in sets['intervals'].indices:
        for u in sets['units'].indices:
            up_time = data['units']['MinimumDownTimeHrs'][u]
            i_low = max(i0, i - up_time + 1)

            num_shut_downs_within_down_time[(i, u)] = \
                pp.lpSum([
                    var['num_shutting_down'].var[(i2, u)] for i2 in range(i_low, i+1)
                ])

    return num_shut_downs_within_down_time


def total_power_in_interval(sets, power_generated):
    """
    Produce a dictionary with intervals for keys, and values that are the sum of the poewr output
    variables from each unit.

    :param sets dict: sets dictionary
    :param power_generated pulp.LpVariable: power generated variable
    """

    intervals = sets['intervals'].indices
    units = sets['units'].indices
    power_generated = power_generated.var

    return {i: pp.lpSum([power_generated[(i, u)] for u in units]) for i in intervals}


def up_ramp_calculator(sets, data, var):
    """
    Return a dictionary of the up ramp rate (positive difference in power output) for each unit and
    interval.  For the first interval, the ramp is relative to the initial state power
    generation.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    :param var dict: var dictionary
    """

    up_ramp_MW = dict()
    first_interval = sets['intervals'].indices[0]

    for u in sets['units'].indices:
        up_ramp_MW[(first_interval, u)] = \
            0
            # var['power_generated'].var[(first_interval, u)] \
            # - data['initial_state']['PowerGeneration_MW'][u]

        for i in sets['intervals'].indices[1:]:
            up_ramp_MW[(i, u)] = \
                var['power_generated'].var[(i, u)] \
                - var['power_generated'].var[(i-1, u)]

    return up_ramp_MW


def down_ramp_calculator(sets, data, var):
    """
    Return a dictionary of the down ramp rate (negative difference in power output) for each unit
    and interval.  For the first interval, the ramp is relative to the initial state power
    generation.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    :param var dict: var dictionary
    """

    down_ramp_MW = dict()
    first_interval = sets['intervals'].indices[0]

    for u in sets['units'].indices:
        down_ramp_MW[(first_interval, u)] = \
            0
            # data['initial_state']['PowerGeneration_MW'][u] \
            # - var['power_generated'].var[(first_interval, u)]

        for i in sets['intervals'].indices[1:]:
            down_ramp_MW[(i, u)] = \
                var['power_generated'].var[(i-1, u)] \
                - var['power_generated'].var[(i, u)]

    return down_ramp_MW


def start_up_ramp_capacity_calculator(sets, data, var):
    start_up_ramp_capacity_MW = dict()

    for u in sets['units'].indices:
        start_up_ramp_capacity_MW = \
            max(
                data['units']['RampRate_pctCapphr'][u],
                data['units']['MinGen_pctCap'][u]
            ) \
            * data['units']['Capacity_MW'][u]

    return start_up_ramp_capacity_MW


def shut_down_ramp_capacity_calculator(sets, data, var):
    shut_down_ramp_capacity_MW = dict()

    for u in sets['units'].indices:
        shut_down_ramp_capacity_MW = \
            max(
                data['units']['RampRate_pctCapphr'][u],
                data['units']['MinGen_pctCap'][u]
            ) \
            * data['units']['Capacity_MW'][u]

    return shut_down_ramp_capacity_MW


def online_ramp_capacity_calculator(sets, data, var):
    online_ramp_capacity_MW = dict()

    for u in sets['units'].indices:
        online_ramp_capacity_MW = \
            data['units']['RampRate_pctCapphr'][u] \
            * data['units']['Capacity_MW'][u]

    return online_ramp_capacity_MW
