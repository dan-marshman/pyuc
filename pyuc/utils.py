import os


def check_path_exists(path, file_type, required_file=False):
    """
    Check that the file exists, or provide an error if it doesn"t.

    :param path string: Path to the file.
    :param file_type string: The purpose of the file.
    """

    if not os.path.exists(path):
        print("The file used for ", file_type, "does not exist. The provided path is:")
        print(path)

        if required_file:
            print("This is a required file - exiting.")
            exit()
        else:
            return False
    else:
        return True


def get_optimisation_status(problem_status):
    status_dict = {
        1:  "Optimal",
        0:  "Not Solved",
        -1: "Infeasible",
        -2: "Unbounded",
        -3: "Undefined"
    }

    return status_dict[problem_status]

def validate_initial_state(data):
    def thermal_validation(initial_state, unit_data, invalid_msgs):
        for unit in initial_state.index:
            if unit_data.loc[unit, "Type"] != "Thermal":
                continue

            num_units = unit_data.loc[unit, "NumUnits"]

            power_generated = initial_state.loc[unit, ("power_generated", -1)]
            num_committed = initial_state.loc[unit, ("num_committed", -1)]

            up_time_periods = \
                unit_data.loc[unit, "MinimumUpTimeHrs"] / data["IntervalDurationHrs"]

            up_time_cols = [col for col in initial_state.columns if col[0] == "num_starting_up"
                            and col[1] * -1 <= up_time_periods]

            num_starting_within_up_time = \
                sum(initial_state.loc[unit, col] for col in up_time_cols)

            down_time_periods = \
                unit_data.loc[unit, "MinimumDownTimeHrs"] / data["IntervalDurationHrs"]

            down_time_cols = [col for col in initial_state.columns if col[0] == "num_shutting_down"
                              and col[1] * -1 <= down_time_periods]

            num_shutting_down_within_down_time = \
                sum(initial_state.loc[unit, col] for col in down_time_cols)

            min_frac = unit_data.loc[unit, "MinimumGenerationFrac"]
            capacity = unit_data.loc[unit, "CapacityMW"]

            min_allowed = num_committed * min_frac * capacity
            max_allowed = num_committed * capacity

            # check minimum output
            if power_generated < min_allowed:
                invalid_msgs.append(
                    f"Unit {unit}: power_generated={power_generated} "
                    f"is below minimum online capacity {min_allowed}"
                )

            # check maximum output
            if power_generated > max_allowed:
                invalid_msgs.append(
                    f"Unit {unit}: power_generated={power_generated} "
                    f"exceeds online capacity {max_allowed}"
                )

            # check units committed
            if num_committed > num_units:
                invalid_msgs.append(
                    f"Unit {unit}: num_committed ({num_committed}) cannot"
                    f"be greater than NumUnits ({num_units})."
                )

            # check units starting and stopping - A
            num_starting_and_stopping = \
                num_starting_within_up_time + num_shutting_down_within_down_time

            if  num_starting_and_stopping > num_units:
                invalid_msgs.append(
                    f"Unit {unit}: total of num_starting_up ({num_starting_within_up_time}) plus "
                    f"num_shutting_down {num_shutting_down_within_down_time} may not exceed "
                    f"NumUnits ({num_units})."
                )

            # check units starting and stopping - B
            if  num_starting_within_up_time > num_committed:
                invalid_msgs.append(
                    f"Unit {unit}: total of num_starting_up ({num_starting_within_up_time}) "
                    f"cannot exceed number of units online ({num_committed})."
                )

            # check units starting and stopping - C
            if  num_shutting_down_within_down_time > num_units - num_committed:
                invalid_msgs.append(
                    f"Unit {unit}: total of num_shutting_down ({num_shutting_down_within_down_time}) "
                    f"cannot exceed number of units {num_units} less "
                    f"number of units committed ({num_committed})."
                )

        return invalid_msgs

    def storage_validation(initial_state, unit_data, invalid_msgs):
        for unit in initial_state.index:
            if unit_data.loc[unit, "Type"] != "Storage":
                continue

            num_units = unit_data.loc[unit, "NumUnits"]

            power_generated = initial_state.loc[unit, ("power_generated", -1)]
            stored_energy = initial_state.loc[unit, ("stored_energy", -1)]

            capacity = unit_data.loc[unit, "CapacityMW"]
            storage_capacity = unit_data.loc[unit, "StorageHrs"] *  capacity * num_units

            max_allowed = num_units * capacity

            # check maximum output
            if power_generated > max_allowed:
                invalid_msgs.append(
                    f"Unit {unit}: power_generated={power_generated} "
                    f"exceeds capacity {max_allowed}"
                )

            # check stored energy
            if stored_energy > storage_capacity:
                invalid_msgs.append(
                    f"Unit {unit}: stored_energy ({stored_energy}) cannot"
                    f"be greater than storage capacity ({storage_capacity})."
                )

        return invalid_msgs

    def variable_validation(initial_state, unit_data, invalid_msgs):
        for unit in initial_state.index:
            if unit_data.loc[unit, "Type"] != "Variable":
                continue

            num_units = unit_data.loc[unit, "NumUnits"]

            power_generated = initial_state.loc[unit, ("power_generated", -1)]

            capacity = unit_data.loc[unit, "CapacityMW"]

            max_allowed = num_units * capacity

            # check maximum output
            if power_generated > max_allowed:
                invalid_msgs.append(
                    f"Unit {unit}: power_generated={power_generated} "
                    f"exceeds online capacity {max_allowed}"
                )

        return invalid_msgs

    initial_state = data["initial_state"]
    unit_data = data["unit_data"]

    invalid_msgs = []
    invalid_msgs = thermal_validation(initial_state, unit_data, invalid_msgs)
    invalid_msgs = storage_validation(initial_state, unit_data, invalid_msgs)
    invalid_msgs = variable_validation(initial_state, unit_data, invalid_msgs)

    if invalid_msgs:
        raise ValueError(
            "Invalid initial_state.csv:\n" + "\n".join(invalid_msgs)
        )
