"""Test cases for methods for metadata module"""
import os
import unittest

from wqflask.api.metadata import get_hash_of_dirs


class TestHashADirectory(unittest.TestCase):
    def test_get_get_hash_of_dirs(self):
        """Test that a directory is hashed correctly"""
        self.assertEqual("ac75f9bdab86d45d64f52663d6723b0a",
                         get_hash_of_dirs(
                             os.path.join(
                                 os.path.dirname(__file__),
                                 "test_data")))
