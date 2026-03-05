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
        * data["ScenarioProbability"]
        * var["power_generated"].var[(s, i, u)]
        * fuel_cost_per_mwh_calculator(data["units"], u)
        for s in sets["scenarios"].indices for u in sets["units_commit"].indices for i in sets["intervals"].indices
    ])


@objective_adder
def start_cost_term(sets, data, var):
    return pp.lpSum([
        var["num_starting_up"].var[(i, u)]
        * fuel_cost_per_start_calculator(data["units"], u)
        for u in sets["units_commit"].indices for i in sets["intervals"].indices
    ])


@objective_adder
def vom_cost_term(sets, data, var):
    return pp.lpSum([
        data["IntervalDurationHrs"]
        * data["ScenarioProbability"]
        * var["power_generated"].var[(s, i, u)]
        * data["units"]["VOMDollarsPerMWh"][u]
        for s in sets["scenarios"].indices for u in sets["units"].indices for i in sets["intervals"].indices
    ])


@objective_adder
def carbon_cost_term(sets, data, var):
    return pp.lpSum([
        data["IntervalDurationHrs"]
        * data["ScenarioProbability"]
        * data["units"]["CarbonIntensityTonnesPerMWh"][u]
        * var["power_generated"].var[(s, i, u)]
        * data["carbon_price$pT"]
        for s in sets["scenarios"].indices for u in sets["units"].indices for i in sets["intervals"].indices
    ])


@objective_adder
def rec_benefit_term(sets, data, var):
    return pp.lpSum([
        data["IntervalDurationHrs"]
        * data["ScenarioProbability"]
        * var["power_generated"].var[(s, i, u)]
        * data["rec_price$pMWh"]
        for s in sets["scenarios"].indices for u in sets["units_renewable"].indices for i in sets["intervals"].indices
    ])


@objective_adder
def unserved_energy_cost_term(sets, data, var):
    return pp.lpSum([
        data["IntervalDurationHrs"]
        * data["ScenarioProbability"]
        * var["unserved_power"].var[(s, i)]
        * data["ValueOfLostLoad$/MWh"]
        for s in sets["scenarios"].indices for i in sets["intervals"].indices
    ])


def make_objective_function(problem):
    fuel_cost = fuel_cost_term(problem)
    start_cost = start_cost_term(problem)
    vom_cost = vom_cost_term(problem)
    unserved_energy_cost = unserved_energy_cost_term(problem)

    objective_function = fuel_cost + start_cost + vom_cost + unserved_energy_cost

    if problem["data"]["carbon_price"] != 0:
        carbon_cost = carbon_cost_term(problem)
        objective_function += carbon_cost

    if problem["data"]["rec_price"] != 0:
        rec_benefit = rec_benefit_term(problem)
        objective_function -= rec_benefit

    problem["problem"] += objective_function

    return problem["problem"]


def fuel_cost_per_mwh_calculator(unit_data, u):
    """
    Calculate fuel cost in $/MWh

    :param unit_data DataFrame: unit_data df
    :param u str: unit name
    """

    return 3.6 * unit_data["FuelCostDollarsPerGJ"][u] / unit_data["ThermalEfficiencyFrac"][u]


def fuel_cost_per_start_calculator(unit_data, u):
    """
    Calculate fuel cost per start

    :param unit_data DataFrame: unit_data df
    :param u str: unit name
    """

    return unit_data["FuelCostDollarsPerGJ"][u] * unit_data["StartUpFuelUseGJPerMW"][u] * unit_data["CapacityMW"][u]
