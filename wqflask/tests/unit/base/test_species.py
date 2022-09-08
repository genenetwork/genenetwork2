"""Tests wqflask/base/species.py"""
import pytest
from base.species import TheSpecies
from base.species import IndChromosome
from base.species import Chromosomes
from collections import OrderedDict
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


@pytest.mark.parametrize(
    ("species_name", "dataset", "expected_name", "chromosome_param"),
    (("BXD", None, "BXD", 1),
     (None, "Random Dataset", None, 1)))
def test_species(mocker, species_name, dataset,
                 expected_name, chromosome_param):
    mock_conn = mocker.patch("base.species.database_connection")
    mock_conn.return_value.__enter__.return_value = mocker.MagicMock()
    _c = mocker.patch("base.species.Chromosomes",
                      return_value=chromosome_param)
    with mock_conn() as conn:
        test_species = TheSpecies(dataset=dataset,
                                  species_name=species_name)
        _c.assert_called_with(conn=conn, species=species_name,
                              dataset=dataset)
        assert test_species.name == expected_name
        assert test_species.chromosomes == chromosome_param


@pytest.mark.parametrize(
    ("name", "length", "mb_length"),
    (("Test A", 10000000, 10),
     ("Test B", 100, 0.0001)))
def test_create_ind_chromosome(name, length, mb_length):
    _ind = IndChromosome(name=name, length=length)
    assert _ind.name == name
    assert _ind.length == length
    assert _ind.mb_length == mb_length


@pytest.mark.parametrize(
    ("species", "dataset", "expected_call"),
    (("bxd", MockDataset(MockGroup("Random")),
      ("SELECT Chr_Length.Name, Chr_Length.OrderId, Length "
       "FROM Chr_Length, Species WHERE "
       "Chr_Length.SpeciesId = Species.SpeciesId AND "
       "Species.Name = %s "
       "ORDER BY OrderId", ("Bxd",))),
     (None, MockDataset(MockGroup("Random")),
      ("SELECT Chr_Length.Name, Chr_Length.OrderId, "
       "Length FROM Chr_Length, InbredSet WHERE "
       "Chr_Length.SpeciesId = InbredSet.SpeciesId AND "
       "InbredSet.Name = "
       "%s ORDER BY OrderId", ("Random",)))))
def test_create_chromosomes(mocker, species, dataset, expected_call):
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        cursor.fetchall.return_value = (("1", 2, 10,),
                                        ("2", 3, 11,),
                                        ("4", 5, 15,),)
        _c = Chromosomes(conn=mock_conn,
                         dataset=dataset, species=species)
        assert _c.chromosomes == OrderedDict([
            ("1", IndChromosome("1", 10)),
            ("2", IndChromosome("2", 11)),
            ("4", IndChromosome("4", 15)),
        ])
        cursor.execute.assert_called_with(*expected_call)
