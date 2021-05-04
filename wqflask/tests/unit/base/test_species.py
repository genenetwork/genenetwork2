"""Tests wqflask/base/species.py"""

import unittest
from unittest import mock
from base.species import TheSpecies


class TestTheSpecies(unittest.TestCase):
    """Tests for TheSpecies class"""
    @mock.patch('base.species.Chromosomes')
    def test_create_species_with_null_species_name(self, mock_chromosome):
        """Test that TheSpecies is instantiated correctly when the
species_name is provided."""
        mock_chromosome.return_value = 1
        test_species = TheSpecies(dataset="random_dataset", species_name="a")
        self.assertEqual(test_species.name, "a")
        self.assertEqual(test_species.chromosomes, 1)

    @mock.patch('base.species.Chromosomes')
    def test_create_species_with_species_name(self, mock_chromosome):
        """Test that TheSpecies is instantiated correctly when the
species_name is not provided."""
        mock_chromosome.return_value = 1
        test_species = TheSpecies(dataset="random_dataset")
        self.assertEqual(test_species.dataset, "random_dataset")
        self.assertEqual(test_species.chromosomes, 1)
        mock_chromosome.assert_called_once_with(dataset="random_dataset")
