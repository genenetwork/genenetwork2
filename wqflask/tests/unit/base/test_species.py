"""Tests wqflask/base/species.py"""

import unittest
from unittest import mock
from base.species import TheSpecies
from base.species import IndChromosome
from base.species import Chromosomes
from collections import OrderedDict
from wqflask import app
from dataclasses import dataclass


@dataclass
class MockChromosome:
    OrderId: int
    Name: str
    Length: int


@dataclass
class MockGroup:
    name: str


@dataclass
class MockDataset:
    group: MockGroup


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


class TestIndChromosome(unittest.TestCase):
    """Tests for IndChromosome class"""

    def test_create_ind_chromosome(self):
        """Test that IndChromosome is instantiated correctly"""
        test_ind_chromosome = IndChromosome(name="Test", length=10000000)
        self.assertEqual(test_ind_chromosome.name, "Test")
        self.assertEqual(test_ind_chromosome.length, 10000000)
        self.assertEqual(test_ind_chromosome.mb_length, 10)


class TestChromosomes(unittest.TestCase):
    """Tests for Chromosomes class"""
    maxDiff = None

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @mock.patch("base.species.g")
    def test_create_chromosomes_with_no_species(self, mock_db):
        """Test instantiating a chromosome without a species"""
        mock_db.db.execute.return_value.fetchall.return_value = [
            MockChromosome(1, "X", 100),
            MockChromosome(2, "Y", 1000),
            MockChromosome(3, "Z", 10000),
        ]
        mock_dataset = MockDataset(MockGroup("Random"))
        test_chromosomes = Chromosomes(dataset=mock_dataset)
        self.assertEqual(
            list(test_chromosomes.chromosomes.keys()),
            [1, 2, 3]
        )
        self.assertEqual(test_chromosomes.dataset, mock_dataset)
        mock_db.db.execute.assert_called_with(
            "SELECT Chr_Length.Name, Chr_Length.OrderId, Length "
            "FROM Chr_Length, InbredSet WHERE "
            "Chr_Length.SpeciesId = InbredSet.SpeciesId AND "
            "InbredSet.Name = 'Random' ORDER BY OrderId"
        )

    @mock.patch("base.species.g")
    def test_create_chromosomes_with_species(self, mock_db):
        """Test instantiating a chromosome with a species"""
        mock_db.db.execute.return_value.fetchall.return_value = [
            MockChromosome(1, "X", 100),
            MockChromosome(2, "Y", 1000),
            MockChromosome(3, "Z", 10000),
        ]
        mock_dataset = MockDataset(MockGroup("Random"))
        test_chromosomes = Chromosomes(dataset=mock_dataset,
                                       species="testSpecies")
        self.assertEqual(
            list(test_chromosomes.chromosomes.keys()),
            [1, 2, 3]
        )
        mock_db.db.execute.assert_called_with(
            "SELECT Chr_Length.Name, Chr_Length.OrderId, Length "
            "FROM Chr_Length, Species WHERE "
            "Chr_Length.SpeciesId = Species.SpeciesId AND "
            "Species.Name = 'Testspecies' ORDER BY OrderId"
        )
