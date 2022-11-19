import pulp as pp


def objective_adder(objective_term_func):
    def extractor_wrapper(problem):
        sets, data, var = problem["sets"], problem["data"], problem["var"]
        objective_term = objective_term_func(sets, data, var)

        return objective_term

    return extractor_wrapper


@objective_adder
def fuel_cost_term(sets, data, var):
    return pp.lpSum([
        data["IntervalDurationHrs"]
        * var["power_generated"].var[(i, u)]
        * fuel_cost_per_mwh_calculator(data["units"], u)
        for u in sets["units_commit"].indices for i in sets["intervals"].indices
    ])


@objective_adder
def vom_cost_term(sets, data, var):
    return pp.lpSum([
        data["IntervalDurationHrs"]
        * var["power_generated"].var[(i, u)]
        * data["units"]["VOM$/MWh"][u]
        for u in sets["units"].indices for i in sets["intervals"].indices
    ])


@objective_adder
def unserved_energy_cost_term(sets, data, var):
    return pp.lpSum([
        data["IntervalDurationHrs"]
        * var["unserved_power"].var[(i)]
        * data["ValueOfLostLoad$/MWh"]
        for i in sets["intervals"].indices
    ])


def make_objective_function(problem):
    fuel_cost = fuel_cost_term(problem)
    vom_cost = vom_cost_term(problem)
    unserved_energy_cost = unserved_energy_cost_term(problem)

    objective_function = fuel_cost + vom_cost + unserved_energy_cost
    problem["problem"] += objective_function

    return problem["problem"]


def fuel_cost_per_mwh_calculator(unit_data, u):
    """
    Calculate fuel cost in $/MWh

    :param unit_data DataFrame: unit_data df
    :param u str: unit name
    """

    return 3.6 * unit_data["FuelCost$/GJ"][u] / unit_data["ThermalEfficiencyFrac"][u]
