from dataclasses import dataclass
from typing import Optional, Union
from collections import OrderedDict

from wqflask.database import database_connection


class TheSpecies:
    """Data related to species."""

    def __init__(self, dataset=None, species_name=None) -> None:
        "Initialise the Species object"
        self.dataset = dataset
        self.name = self.species_name = species_name
        self.chromosomes = Chromosomes(species=species_name,
                                       dataset=dataset)


@dataclass
class IndChromosome:
    """Data related to IndChromosome"""
    name: str
    length: int

    @property
    def mb_length(self) -> Union[int, float]:
        """Chromosome length in mega-bases"""
        return self.length / 1000000


@dataclass
class Chromosomes:
    """Data related to a chromosome"""

    def __init__(self, dataset, species: Optional[str]) -> None:
        "initialise the Chromosome object"
        self.species = species
        if species is None:
            self.dataset = dataset

    def chromosomes(self, db_cursor) -> OrderedDict:
        """Lazily fetch the chromosomes"""
        chromosomes = OrderedDict()
        if self.species is not None:
            db_cursor.execute(
                "SELECT Chr_Length.Name, Chr_Length.OrderId, Length "
                "FROM Chr_Length, Species WHERE "
                "Chr_Length.SpeciesId = Species.SpeciesId AND "
                "Species.Name = %s "
                "ORDER BY OrderId", (self.species.capitalize(),))
        else:
            db_cursor.execute(
                "SELECT Chr_Length.Name, Chr_Length.OrderId, "
                "Length FROM Chr_Length, InbredSet WHERE "
                "Chr_Length.SpeciesId = InbredSet.SpeciesId AND "
                "InbredSet.Name = "
                "%s ORDER BY OrderId", (self.dataset.group.name,))
        for name, _, length in db_cursor.fetchall():
            chromosomes[name] = IndChromosome(
                name=name, length=length)
        return chromosomes
