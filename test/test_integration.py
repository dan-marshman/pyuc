import os
import shutil
import unittest

from pyuc import pyuc


class Integration(unittest.TestCase):
    def setUp(self):
        self.name = "MY_PROB"
        self.input_path = os.path.join("test", "test_problem")
        self.output_path = os.path.join("test", "test_problem")

        if os.path.exists(os.path.join(self.output_path, "results")):
            shutil.rmtree(os.path.join(self.output_path, "MY_PROB", "results"))

    def test_problem_files_made(self):
        pyuc.run_opt_problem(self.name, self.input_path, self.output_path)

        power_generated_path = \
            os.path.join(self.output_path, "MY_PROB", "results", "power_generated_MW.csv")

        self.assertTrue(os.path.exists(power_generated_path))
