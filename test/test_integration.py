import os
import shutil
import unittest
import pandas as pd

from pyuc import pyuc


class IntegrationTestSet1(unittest.TestCase):
    def setUp(self):
        self.output_path = os.path.join("test")

        if os.path.exists(os.path.join(self.output_path, "results")):
            shutil.rmtree(os.path.join(self.output_path, "results"))

    def test_problem_files_made(self):
        self.name = "test_problem_files_made"
        self.input_path = os.path.join("test", "test_problems", "Integration", "TestSet1")

        pyuc.run_opt_problem(self.input_path, self.output_path, self.name)

        files = [
            ("power_generated", "MW"),
            ("num_committed", "#Units"),
            ("num_shutting_down", "#Units"),
            ("num_starting_up", "#Units"),
            ("unserved_power", "MW"),
            ("unserved_reserve", "MW"),
            ("stored_energy", "MWh"),
            ("power_charged", "MW"),
            ("reserve_enabled", "MW")
        ]

        for name, unit in files:
            file_name = f"{name}_{unit}.csv"
            file_path = os.path.join(self.output_path, "results", file_name)
            self.assertTrue(os.path.exists(file_path), msg=f"File not found {file_path}")

class IntegrationComplex(unittest.TestCase):
    def setUp(self):
        self.output_path = os.path.join("test")

        if os.path.exists(os.path.join(self.output_path, "results")):
            shutil.rmtree(os.path.join(self.output_path, "results"))

        self.name = "test_complex_problem"
        self.input_path = os.path.join("test", "test_problems", "Integration", "TestSet2")

        pyuc.run_opt_problem(self.input_path, self.output_path, self.name)

    def test_obj(self):
        result_df = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "results_summary.csv"),
                header=None,
                index_col=0,
            )

        results_summary = result_df.iloc[:, 0]
        results_dict = results_summary.to_dict()
        objective_value = float(results_dict["ObjectiveValue"])

        # Objective function
        unit_data = \
            pd.read_csv(
                os.path.join(self.input_path, "unit_data.csv"),
                index_col=0,
            )

        unit_data["SRMC"] = \
            3.6 * unit_data["FuelCost$/GJ"] / unit_data["ThermalEfficiencyFrac"] \
            + unit_data["VOM$/MWh"]

        power_generated = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "power_generated_MW.csv"),
                index_col=0,
            )

        num_starting_up = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "num_starting_up_#Units.csv"),
                index_col=0,
            )

        # 0.5 = interval duration in hours
        total_generation_cost = unit_data["SRMC"] * power_generated.sum() * 0.5
        total_start_cost = \
            unit_data["CapacityMW"] \
            * unit_data["StartUpFuelUseGJ/MW"] \
            * unit_data["FuelCost$/GJ"] \
            * num_starting_up.sum()

        total_cost = total_generation_cost.sum() + total_start_cost.sum()

        self.assertEqual(objective_value, total_cost)

    def test_min_down_time(self):
        num_committed = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "num_committed_#Units.csv"),
                index_col=0,
            )

        ### Coal1 ###
            # Coal has 8 units total. 3 shut down in interval -1, and 2 shut down in interval -6.
            # Min down time is 12 hours = 24 periods.

            # 3 should be on until period 17 (inclusive).
        self.assertEqual(num_committed["Coal1"][17], 3)

            # 5 should be on from period 18 to 23 (inclusive).
        self.assertEqual(num_committed["Coal1"][18], 5)
        self.assertEqual(num_committed["Coal1"][22], 5)

            # 8 should be on from period 24 to 23 (inclusive).
        self.assertEqual(num_committed["Coal1"][24], 8)

    def test_min_up_time(self):
        num_committed = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "num_committed_#Units.csv"),
                index_col=0,
            )

        ### OCGT1 ###
            # OCGT has 5 units total. 2 start up in interval -1, and 2 start up in interval -3.
            # Min down time is 3 hours = 6 periods.

            # 4 should be on until period 2 (inclusive).
        self.assertEqual(num_committed["OCGT1"][2], 4)

            # 2 should be on from period 3 to 5 (inclusive).
        self.assertEqual(num_committed["OCGT1"][4], 2)

            # 0 should be on in period 6.
        self.assertEqual(num_committed["OCGT1"][5], 0)

    def test_starting_up_initial_interval(self):
        num_committed = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "num_committed_#Units.csv"),
                index_col=0,
            )

        num_starting_up = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "num_starting_up_#Units.csv"),
                index_col=0,
            )

        ### Coal1 ###
            # Coal has 2 units on, and one will want to start up in the first interval.
        self.assertEqual(num_committed["Coal1"][0], 3)
        self.assertEqual(num_starting_up["Coal1"][0], 1)

    def test_shut_down_initial_interval(self):
        num_committed = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "num_committed_#Units.csv"),
                index_col=0,
            )

        num_shutting_down = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "num_shutting_down_#Units.csv"),
                index_col=0,
            )

        ### OCGT1 ###
            # OCGT has 5 units on, and one will want to (and be allowed to) shut down up, but it
            # must ramp to its min gen first, which takes one interval.
        self.assertEqual(num_committed["OCGT1"][0], 5)
        self.assertEqual(num_committed["OCGT1"][1], 4)
        self.assertEqual(num_shutting_down["OCGT1"][0], 0)
        self.assertEqual(num_shutting_down["OCGT1"][1], 1)

    def test_ramp_up(self):
        power_generated = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "power_generated_MW.csv"),
                index_col=0,
            )

        ### Coal1
            # Starts with 2 units on at 160 MW.
            # Ramp capacity is 0.3 * 100 per hour, or 15 MW per interval.
            # 1 Unit turns on in first interval, to minimum generation of 0.5 * 100 = 50 MW.
            # Total ramp capacity is 160 + 30 + 50 = 240
        self.assertEqual(power_generated["Coal1"][0], 240)

    def test_ramp_down(self):
        power_generated = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "power_generated_MW.csv"),
                index_col=0,
            )

        ### OCGT1
            # Starts with 5 units on at 500 MW.
            # Ramp capacity is 5 * 0.6 * 100 per hour, or 150 MW per interval.
            # In first interval, power output should be 350 MW.
        self.assertEqual(power_generated["OCGT1"][0], 350)

            # In second interval, one unit turns off (ramping by 30), and the other 3 ramp by 4 *
            # 0.6 * 100/2 = 120 MW per interval.
        self.assertEqual(power_generated["OCGT1"][1], 200)


    def test_storage_profile(self):
        power_generated = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "power_generated_MW.csv"),
                index_col=0,
            )

        power_charged = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "power_charged_MW.csv"),
                index_col=0,
            )

        stored_energy = \
            pd.read_csv(
                os.path.join(self.output_path, "results", "stored_energy_MWh.csv"),
                index_col=0,
            )

        total_generated = power_generated["Battery1"].sum()
        total_charged = power_charged["Battery1"].sum()
        initial_energy = 100
        actual_final_energy = stored_energy["Battery1"][47]

        # 0.5 = interval duration in hours
        expected_final_energy = \
            initial_energy \
            - total_generated * 0.5 \
            + total_charged * 0.5

        self.assertEqual(expected_final_energy, actual_final_energy)
