"""Test cases for methods for metadata module"""
import os
import unittest

from unittest import mock

from wqflask.api.metadata import compose_gemma_command
from wqflask.api.metadata import get_hash_of_dirs
from wqflask.api.metadata import lookup_file


class TestMetadata(unittest.TestCase):
    def test_get_get_hash_of_dirs(self):
        """Test that a directory is hashed correctly"""
        self.assertEqual("928a0e2e4846b4b3c2881d9c1d6cfce4",
                         get_hash_of_dirs(
                             os.path.join(
                                 os.path.dirname(__file__),
                                 "test_data")))

    @mock.patch("os.path.isfile")
    @mock.patch.dict(os.environ, {"GENENETWORK_FILES": "/tmp/"})
    def test_lookup_genotype_file_exists(self, mock_isfile):
        """Test whether genotype file exists if file is present"""
        mock_isfile.return_value = True
        self.assertEqual(lookup_file("GENENETWORK_FILES",
                                     "genotype_files", "genotype.txt"),
                         "/tmp/genotype_files/genotype.txt")

    @mock.patch("os.path.isfile")
    @mock.patch.dict(os.environ, {"GENENETWORK_FILES": "/tmp"})
    def test_lookup_genotype_file_does_not_exist(self, mock_isfile):
        """Test whether genotype file exists if file is absent"""
        mock_isfile.return_value = False
        self.assertEqual(lookup_file("GENENETWORK_FILES",
                                     "genotype_files", "genotype.txt"),
                         -1)

    def test_lookup_genotype_file_env_does_not_exist(self):
        """Test whether genotype file exists if GENENETWORK_FILES is absent"""
        self.assertEqual(lookup_file("GENENETWORK_FILES",
                                     "genotype_files", "genotype.txt"),
                         -1)

    @mock.patch("wqflask.api.metadata.GEMMA_WRAPPER_COMMAND", "gemma-wrapper")
    @mock.patch("wqflask.api.metadata.lookup_file")
    def test_compose_gemma_command_no_extra_args(self, mock_lookup_file):
        mock_lookup_file.side_effect = [
            os.path.join(os.path.dirname(__file__),
                         "test_data", "metadata.json"),
            "/tmp/genofile.txt", "/tmp/gf13Ad0tRX/phenofile.txt"]
        self.assertEqual(compose_gemma_command("gf13Ad0tRX", "metadata.txt"),
                         ("gemma-wrapper --json -- "
                          "-g /tmp/genofile.txt "
                          "-p /tmp/gf13Ad0tRX/phenofile.txt"))

    @mock.patch("wqflask.api.metadata.GEMMA_WRAPPER_COMMAND", "gemma-wrapper")
    @mock.patch("wqflask.api.metadata.lookup_file")
    def test_compose_gemma_command_with_opt_args(self, mock_lookup_file):
        mock_lookup_file.side_effect = [
            os.path.join(os.path.dirname(__file__),
                         "test_data", "metadata.json"),
            "/tmp/genofile.txt", "/tmp/gf13Ad0tRX/phenofile.txt"]
        self.assertEqual(compose_gemma_command("gf13Ad0tRX", "metadata.txt",),
                         ("gemma-wrapper --json -- "
                          "-g /tmp/genofile.txt "
                          "-p /tmp/gf13Ad0tRX/phenofile.txt"))
