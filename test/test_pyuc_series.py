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


class testFilterDays(unittest.TestCase):
    def test_get_days_whole_number(self):
        day_length = 24
        expected = 365
        trace_df = pd.DataFrame(index=range(8760))
        traces = {"demand": trace_df, "variable_traces": trace_df}

        result = pyucs.get_days(traces, day_length)

        self.assertEqual(result, expected)

    def test_get_days_fraction(self):
        day_length = 24
        expected = 366
        trace_df = pd.DataFrame(index=range(8761))
        traces = {"demand": trace_df, "variable_traces": trace_df}

        result = pyucs.get_days(traces, day_length)

        self.assertEqual(result, expected)

    def test_get_days_unequal_length(self):
        day_length = 24
        expected = 366
        demand_df = pd.DataFrame(index=range(8761))
        variable_trace_df = pd.DataFrame(index=range(8760))
        traces = {"demand": demand_df, "variable_traces": variable_trace_df}

        with self.assertRaises(SystemExit) as cm:
            pyucs.get_days(traces, day_length)

        self.assertEqual(cm.exception.code, 1)
