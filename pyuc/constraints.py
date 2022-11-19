import pulp as pp


def constraint_adder(constraint_func):
    def extractor_wrapper(problem):
        sets, data, var = problem["sets"], problem["data"], problem["var"]
        constraints = constraint_func(sets, data, var)

        return constraints

    return extractor_wrapper


@constraint_adder
def cnt_supply_eq_demand(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    total_power_generated = \
        total_power_generated_in_interval(sets, var["power_generated"])

    total_power_charged = \
        total_power_charged_in_interval(sets, data, var["power_charged"])

    for i in sets["intervals"].indices:
        label = f"supply_eq_demand_(i={i})"

        condition = (
            total_power_generated[i]
            + var["unserved_power"].var[(i)]
            ==
            data["demand"]["Demand"][i]
            + total_power_charged[i]
            )

        constraints[label] = condition

    return constraints


@constraint_adder
def cnt_power_lt_capacity(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    for i in sets["intervals"].indices:
        for u in sets["units"].indices:
            label = f"power_lt_capacity_(i={i}, u={u})"

            condition = (
                var["power_generated"].var[(i, u)]
                <=
                data["units"]["CapacityMW"][u]
                * data["units"]["NumUnits"][u]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_power_lt_committed_capacity(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    for i in sets["intervals"].indices:
        for u in sets["units_commit"].indices:
            label = f"power_lt_committed_capacity_(i={i}, u={u})"

            condition = (
                var["power_generated"].var[(i, u)]
                <=
                var["num_committed"].var[(i, u)]
                * data["units"]["CapacityMW"][u]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_power_gt_minimum_generation(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    for i in sets["intervals"].indices:
        for u in sets["units_commit"].indices:
            label = f"power_gt_minimum_generation_(i={i}, u={u})"

            condition = (
                var["power_generated"].var[(i, u)]
                >=
                var["num_committed"].var[(i, u)]
                * data["units"]["CapacityMW"][u]
                * data["units"]["MinimumGenerationFrac"][u]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_num_committed_lt_num_units(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    for i in sets["intervals"].indices:
        for u in sets["units_commit"].indices:
            label = f"num_committed_lt_num_units(i={i}, u={u})"

            condition = (
                var["num_committed"].var[(i, u)]
                <=
                data["units"]["NumUnits"][u]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_commitment_continuity(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    for i in sets["intervals"].indices[1:]:
        for u in sets["units_commit"].indices:
            label = f"commitment_continuity(i={i}, u={u})"

            condition = (
                var["num_committed"].var[(i, u)]
                ==
                var["num_committed"].var[(i-1, u)]
                + var["num_starting_up"].var[(i, u)]
                - var["num_shutting_down"].var[(i, u)]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_commitment_continuity_initial_interval(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    i = sets["intervals"].indices[0]
    initial_units_committed = get_initial_units_committed(sets, data)

    for u in sets["units_commit"].indices:
        label = f"commitment_continuity(i={i}, u={u})"

        condition = (
            var["num_committed"].var[(i, u)]
            ==
            initial_units_committed[u]
            + var["num_starting_up"].var[(i, u)]
            - var["num_shutting_down"].var[(i, u)]
            )

        constraints[label] = condition

    return constraints


@constraint_adder
def cnt_minimum_up_time(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    num_start_ups_within_up_time = \
        num_start_ups_within_up_time_calculator(sets, data, var)

    for i in sets["intervals"].indices:

        for u in sets["units_commit"].indices:
            label = f"minimum_up_time(i={i}, u={u})"

            condition = (
                var["num_committed"].var[(i, u)]
                >=
                num_start_ups_within_up_time[(i, u)]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_minimum_down_time(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    num_shut_downs_within_down_time = \
        num_shut_downs_within_down_time_calculator(sets, data, var)

    for i in sets["intervals"].indices:

        for u in sets["units_commit"].indices:
            label = f"minimum_down_time(i={i}, u={u})"

            condition = (
                data["units"]["NumUnits"][u]
                - var["num_committed"].var[(i, u)]
                >=
                num_shut_downs_within_down_time[(i, u)]
                )

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_ramp_rate_up(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    rampMW = ramp_calculator(sets, data, var)
    start_up_ramp_capacityMW = start_up_ramp_capacity_calculator(sets, data)
    online_ramp_capacityMW = online_ramp_capacity_calculator(sets, data)
    minimum_generationMW = minimum_generation_calculator(sets, data)

    for i in sets["intervals"].indices:

        for u in sets["units_commit"].indices:
            label = f"ramp_rate_up_(i={i}, u={u})"

            condition = \
                rampMW[(i, u)] \
                <= \
                (var["num_committed"].var[(i, u)] - var["num_starting_up"].var[(i, u)]) \
                * online_ramp_capacityMW[u] \
                + var["num_starting_up"].var[(i, u)] * start_up_ramp_capacityMW[u] \
                - var["num_shutting_down"].var[(i, u)] * minimum_generationMW[u]

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_ramp_rate_down(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    rampMW = ramp_calculator(sets, data, var)
    shut_down_ramp_capacityMW = shut_down_ramp_capacity_calculator(sets, data)
    online_ramp_capacityMW = online_ramp_capacity_calculator(sets, data)
    minimum_generationMW = minimum_generation_calculator(sets, data)

    for i in sets["intervals"].indices:

        for u in sets["units_commit"].indices:
            label = f"ramp_rate_down_(i={i}, u={u})"

            condition = \
                -1 * rampMW[(i, u)] \
                <= \
                (var["num_committed"].var[(i, u)] - var["num_starting_up"].var[(i, u)]) \
                * online_ramp_capacityMW[u] \
                + var["num_shutting_down"].var[(i, u)] * shut_down_ramp_capacityMW[u] \
                - var["num_starting_up"].var[(i, u)] * minimum_generationMW[u]

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_variable_resource_availability(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    technology_type = data["units"]["Technology"].to_dict()

    for i in sets["intervals"].indices:

        for u in sets["units_variable"].indices:
            label = f"variable_resource_availability(i={i}, u={u})"

            condition = \
                var["power_generated"].var[(i, u)] \
                <= \
                data["variable_traces"][technology_type[u]][i] \
                * data["units"]["NumUnits"][u] \
                * data["units"]["CapacityMW"][u]

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_charge_lt_rt_loss_adjusted_capacity(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    for i in sets["intervals"].indices:

        for u in sets["units_storage"].indices:
            label = f"charge_lt_rt_loss_adjusted_capacity(i={i}, u={u})"

            condition = \
                var["power_charged"].var[(i, u)] \
                <= \
                data["units"]["NumUnits"][u] \
                * data["units"]["CapacityMW"][u] \
                * data["units"]["RoundTripEfficiencyFrac"][u]

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_storage_energy_continuity(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    for i in sets["intervals"].indices[1:]:

        for u in sets["units_storage"].indices:
            label = f"storage_energy_continuity(i={i}, u={u})"

            condition = \
                var["stored_energy"].var[(i-1, u)] \
                - var["stored_energy"].var[(i, u)] \
                + data["IntervalDurationHrs"] * (
                    + var["power_charged"].var[(i, u)]
                    - var["power_generated"].var[(i, u)]
                ) \
                == \
                0

            constraints[label] = condition

    return constraints


@constraint_adder
def cnt_storage_energy_continuity_initial_interval(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    i = sets["intervals"].indices[0]

    for u in sets["units_storage"].indices:
        label = f"storage_energy_continuity(i={i}, u={u})"

        if data["initial_state"] is not None:
            if ("stored_energy", -1) in data["initial_state"].columns:
                initial_energy = data["initial_state"][("stored_energy", -1)][u]
        else:
            initial_energy = 0

        condition = \
            initial_energy \
            - var["stored_energy"].var[(i, u)] \
            + data["IntervalDurationHrs"] * (
                + var["power_charged"].var[(i, u)]
                - var["power_generated"].var[(i, u)]
            ) \
            == \
            0

        constraints[label] = condition

    return constraints


@constraint_adder
def cnt_stored_energy_lt_storage_capacity(sets, data, var, constraints={}):
    constraints = {}  # No idea why this is needed

    for i in sets["intervals"].indices:

        for u in sets["units_storage"].indices:
            label = f"stored_energy_lt_storage_capacity(i={i}, u={u})"

            condition = \
                var["stored_energy"].var[(i, u)] \
                <= \
                data["units"]["NumUnits"][u] \
                * data["units"]["CapacityMW"][u] \
                * data["units"]["StorageHrs"][u] \
                * data["IntervalDurationHrs"]

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

    def get_var_starts(i, i_low_var, u):
        var_starts = \
            pp.lpSum([
                var["num_starting_up"].var[(i2, u)] for i2 in range(i_low_var, i+1)
            ])

        return var_starts

    def get_initial_state_starts(initial_state, i, i_low, u):
        if initial_state is not None:
            initial_state_filt = initial_state.xs("num_starting_up", level=0, axis=1)
            sum_cols = [i2 for i2 in range(i_low, i+1) if i2 in initial_state_filt.columns]
            initial_state_starts = initial_state_filt.loc[u, sum_cols].sum()
        else:
            initial_state_starts = 0

        return initial_state_starts

    i0 = min(sets["intervals"].indices)
    num_start_ups_within_up_time = {}

    for i in sets["intervals"].indices:

        for u in sets["units_commit"].indices:
            up_time = data["units"]["MinimumUpTimeHrs"][u]
            i_low = i - up_time + 1
            i_low_var = max(i0, i_low)

            var_starts = get_var_starts(i, i_low_var, u)
            initial_state_starts = get_initial_state_starts(data["initial_state"], i, i_low, u)
            num_start_ups_within_up_time[(i, u)] = var_starts + initial_state_starts

    return num_start_ups_within_up_time


def num_shut_downs_within_down_time_calculator(sets, data, var):
    """
    Return a dictionary that sums the shut down events within a units minimum down time (counting
    backwards), for each unit and interval.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    :param var dict: var dictionary
    """

    def get_var_stops(i, i_low_var, u):
        var_stops = \
            pp.lpSum([
                var["num_shutting_down"].var[(i2, u)] for i2 in range(i_low_var, i+1)
            ])

        return var_stops

    def get_initial_state_stops(initial_state, i, i_low, u):
        if initial_state is not None:
            initial_state_filt = initial_state.xs("num_shutting_down", level=0, axis=1)
            sum_cols = [i2 for i2 in range(i_low, i+1) if i2 in initial_state_filt.columns]
            initial_state_stops = initial_state_filt.loc[u, sum_cols].sum()
        else:
            initial_state_stops = 0

        return initial_state_stops

    i0 = min(sets["intervals"].indices)
    num_shut_downs_within_down_time = {}

    for i in sets["intervals"].indices:
        for u in sets["units_commit"].indices:
            down_time = data["units"]["MinimumDownTimeHrs"][u]
            i_low = i - down_time + 1
            i_low_var = max(i0, i_low)

            var_stops = get_var_stops(i, i_low_var, u)
            initial_state_stops = get_initial_state_stops(data["initial_state"], i, i_low, u)
            num_shut_downs_within_down_time[(i, u)] = var_stops + initial_state_stops

    return num_shut_downs_within_down_time


def get_initial_units_committed(sets, data):
    """
    Get dictionary of number of units committed in initial interval.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    """

    init_state_df = data["initial_state"]
    init_commit_col = ("num_committed", -1)
    units_commit = sets["units_commit"].indices

    if init_state_df is not None:
        return init_state_df.loc[units_commit, init_commit_col].to_dict()
    else:
        return {u: 0 for u in units_commit}


def total_power_generated_in_interval(sets, power_generated):
    """
    Produce a dictionary with intervals for keys, and values that are the sum of the poewr output
    variables from each unit.

    :param sets dict: sets dictionary
    :param power_generated pulp.LpVariable: power generated variable
    """

    intervals = sets["intervals"].indices
    units = sets["units"].indices
    power_generated = power_generated.var

    return {i: pp.lpSum([power_generated[(i, u)] for u in units]) for i in intervals}


def total_power_charged_in_interval(sets, data, power_charged):
    """
    Produce a dictionary with intervals for keys, and values that are the sum of the
    poewr charged including losses
    variables from each unit.

    :param sets dict: sets dictionary
    :param power_generated pulp.LpVariable: power generated variable
    """

    intervals = sets["intervals"].indices
    units_storage = sets["units_storage"].indices
    power_charged = power_charged.var

    charge_dict = {
        i: pp.lpSum([
            (1 / data["units"]["RoundTripEfficiencyFrac"][u])
            * power_charged[(i, u)]
            for u in units_storage]) for i in intervals
    }

    return charge_dict


def ramp_calculator(sets, data, var):
    """
    Return a dictionary of the ramp (difference in power output) for each unit and
    interval.  For the first interval, the ramp is relative to the initial state power
    generation.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    :param var dict: var dictionary
    """

    rampMW = dict()
    first_interval = sets["intervals"].indices[0]

    for u in sets["units"].indices:
        try:
            units_initial_power = \
                float(data["initial_state"][("power_generated", -1)][u])
        except KeyError:
            units_initial_power = 0
        except TypeError:
            units_initial_power = 0

        rampMW[(first_interval, u)] = \
            var["power_generated"].var[(first_interval, u)] - units_initial_power

        for i in sets["intervals"].indices[1:]:
            rampMW[(i, u)] = \
                var["power_generated"].var[(i, u)] \
                - var["power_generated"].var[(i-1, u)]

    return rampMW


def start_up_ramp_capacity_calculator(sets, data):
    """
    Return a dictionary of the start up ramp rate in MW per unit that has just started up.
    Calcuclated as the product of the ramp rate per capacity, and the capacity,
    but must be greater than to the minimum generation.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    """
    start_up_ramp_capacityMW = dict()

    for u in sets["units_commit"].indices:
        start_up_ramp_capacityMW[u] = \
            max(
                data["units"]["RampRate_pctCapphr"][u],
                data["units"]["MinimumGenerationFrac"][u]
            ) \
            * data["units"]["CapacityMW"][u]

    return start_up_ramp_capacityMW


def shut_down_ramp_capacity_calculator(sets, data):
    """
    Return a dictionary of the shut down ramp rate in MW per unit that has just started up.
    Calcuclated as the product of the ramp rate per capacity, and the capacity,
    but must be greater than to the minimum generation.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    """

    shut_down_ramp_capacityMW = dict()

    for u in sets["units_commit"].indices:
        shut_down_ramp_capacityMW[u] = \
            max(
                data["units"]["RampRate_pctCapphr"][u],
                data["units"]["MinimumGenerationFrac"][u]
            ) \
            * data["units"]["CapacityMW"][u]

    return shut_down_ramp_capacityMW


def online_ramp_capacity_calculator(sets, data):
    """
    Return a dictionary of the ramp rate in MW per unit that is online.  Calcuclated as the
    product of the ramp rate per capacity, and the capacity.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    """

    online_ramp_capacityMW = dict()

    for u in sets["units"].indices:
        online_ramp_capacityMW[u] = \
            data["units"]["RampRate_pctCapphr"][u] \
            * data["units"]["CapacityMW"][u]

    return online_ramp_capacityMW


def minimum_generation_calculator(sets, data):
    """
    Return a dictionary of the minimum generation in MW.  Calcuclated as the product of the
    minimum generation fraction, and the capacity.

    :param sets dict: sets dictionary
    :param data dict: data dictionary
    """

    return {
        u: data["units"]["MinimumGenerationFrac"][u] * data["units"]["CapacityMW"][u]
        for u in sets["units"].indices
    }
