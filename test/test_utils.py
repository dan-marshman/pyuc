import unittest

import mock
from pyuc import utils


class PathExists(unittest.TestCase):
    def setUp(self):
        self.path = "PATH_THAT_DOES_NOT_EXIST"
        self.file_type = "A FILE"

    def test_path_does_not_exist_is_required(self):
        with self.assertRaises(SystemExit):
            utils.check_path_exists(self.path, self.file_type, required_file=True)

    def test_path_does_not_exist_is_not_required(self):
        try:
            utils.check_path_exists(self.path, self.file_type)
        except SystemExit:  # pragma: no cover
            self.fail("utils.check_path_exists exited when the file is not required.")

    @mock.patch("os.path.exists", return_value=True)
    def test_path_does_exist(self, path_exists_mock):
        try:
            utils.check_path_exists(self.path, self.file_type)
        except SystemExit:  # pragma: no cover
            self.fail("utils.check_path_exists exited when the file exists.")
