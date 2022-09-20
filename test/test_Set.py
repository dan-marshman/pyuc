import unittest

import mock
from pyuc import pyuc


class TestMasterSetInit(unittest.TestCase):
    def setUp(self):
        self.name = 'MY_SET'
        self.indices = range(10)
        self.masterSet = pyuc.Set(self.name, self.indices)

    def test_init_name(self):
        self.assertEqual(self.masterSet.name, self.name)

    def test_init_indices(self):
        self.assertEqual(self.masterSet.indices, self.indices)

    def test_init_subsets(self):
        self.assertEqual(self.masterSet.subsets, [])

    def test_set___str__(self):
        self.assertEqual(self.masterSet.__str__(), self.name)

    def test_set___repr__(self):
        self.assertEqual(self.masterSet.__repr__(), "Set(MY_SET)")

    @mock.patch('pyuc.pyuc.Set.validate_set')
    @mock.patch('pyuc.pyuc.Set.append_subset')
    def test_master_set_fns_not_called(self, append_subset_mock, validate_set_mock):
        pyuc.Set(self.name, self.indices)
        validate_set_mock.assert_not_called()
        append_subset_mock.assert_not_called()


class TestSubSetInit(unittest.TestCase):
    def setUp(self):
        self.name = 'MY_SET'
        self.indices = range(10)
        self.masterSet = pyuc.Set(self.name, self.indices)

        self.sub_set_name = 'MY_SUBSET'
        self.sub_set_indices = range(5)
        self.subSet = pyuc.Set(self.sub_set_name, self.sub_set_indices, master_set=self.masterSet)

    @mock.patch('pyuc.pyuc.Set.validate_set')
    def test_validate_set_is_called(self, validate_set_mock):
        pyuc.Set(self.name, self.indices, master_set=self.masterSet)
        validate_set_mock.assert_called_once_with(self.masterSet)

    @mock.patch('pyuc.pyuc.Set.append_subset')
    def test_append_subset_is_called(self, append_subset_mock):
        subSet = pyuc.Set(self.name, self.indices, master_set=self.masterSet)
        append_subset_mock.assert_called_once_with(subSet)

    def test_subset_is_appended(self):
        self.assertEqual(self.masterSet.subsets, [self.subSet])

    def test_subset_is_not_valid(self):
        self.sub_set_indices = range(20)
        with self.assertRaises(ValueError):
            self.subSet = \
                pyuc.Set(self.sub_set_name, self.sub_set_indices, master_set=self.masterSet)
