import os
import unittest

import mock
import pandas as pd
import pulp as pp
from pyuc import pyuc
from pyuc import pyuc_series as pyucs


class testLoadDataAndPaths(unittest.TestCase):
    @mock.patch("pyuc.load_data.load_variable_data", return_value="abc")
    @mock.patch("pyuc.load_data.load_demand_data", return_value="xyz")
    def test_read_traces_series(self, demand_trace_mock, variable_trace_mock):
        dummy_paths = {"demand": "dummy", "variable_traces": "dummy"}
        result = pyucs.read_traces_series(dummy_paths)
        expected = {"demand": "xyz", "variable_traces": "abc"}
        self.assertEqual(result, expected)
