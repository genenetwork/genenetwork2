"""Test cases for methods for metadata module"""
import os
import unittest

from unittest import mock

from wqflask.api.metadata import get_hash_of_dirs
from wqflask.api.metadata import lookup_genotype_file


class TestMetadata(unittest.TestCase):
    def test_get_get_hash_of_dirs(self):
        """Test that a directory is hashed correctly"""
        self.assertEqual("ac75f9bdab86d45d64f52663d6723b0a",
                         get_hash_of_dirs(
                             os.path.join(
                                 os.path.dirname(__file__),
                                 "test_data")))

    @mock.patch("os.path.isfile")
    @mock.patch.dict(os.environ, {"GENENETWORK_FILES": "/tmp/"})
    def test_lookup_genotype_file_exists(self, mock_isfile):
        """Test whether genotype file exists if file is present"""
        mock_isfile.return_value = True
        self.assertEqual(lookup_genotype_file("genotype.txt"),
                         "/tmp/genotype_files/genotype.txt")

    @mock.patch("os.path.isfile")
    @mock.patch.dict(os.environ, {"GENENETWORK_FILES": "/tmp"})
    def test_lookup_genotype_file_does_not_exist(self, mock_isfile):
        """Test whether genotype file exists if file is absent"""
        mock_isfile.return_value = False
        self.assertEqual(lookup_genotype_file("genotype.txt"), -1)

    def test_lookup_genotype_file_env_does_not_exist(self):
        """Test whether genotype file exists if GENENETWORK_FILES is absent"""
        self.assertEqual(lookup_genotype_file("genotype.txt"),
                         -1)
