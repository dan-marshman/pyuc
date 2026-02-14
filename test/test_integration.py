import os
import shutil
import unittest

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

    def test_correct_objective(self):
        self.name = "test_problem_files_made"
        self.input_path = os.path.join("test", "test_problems", "Integration", "TestSet1")

        pyuc.run_opt_problem(self.input_path, self.output_path, self.name)
