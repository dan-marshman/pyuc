import unittest

import mock
from pyuc import misc_functions


class PathExists(unittest.TestCase):
    def setUp(self):
        self.path = "PATH_THAT_DOES_NOT_EXIST"
        self.file_type = "A FILE"

    def test_path_does_exist(self):
        with self.assertRaises(SystemExit):
            misc_functions.check_path_exists(self.path, self.file_type)

    @mock.patch('os.path.exists', return_value=True)
    def test_path_does_not_exist(self, path_exists_mock):
        try:
            misc_functions.check_path_exists(self.path, self.file_type)
        except SystemExit:
            self.fail("misc_functions.check_path_exists exited when the file exists")
