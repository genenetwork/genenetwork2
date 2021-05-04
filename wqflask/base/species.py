import collections

from dataclasses import dataclass
from typing import Optional, Dict
from flask import g


@dataclass
class TheSpecies:
    """Data related to species."""
    dataset: Optional[Dict] = None
    species_name: Optional[str] = None

    def __post_init__(self):
        if self.species_name is not None:
            self.name = self.species_name
            self.chromosomes = Chromosomes(species=self.name)
        else:
            self.dataset = self.dataset
            self.chromosomes = Chromosomes(dataset=self.dataset)


@dataclass
class IndChromosome:
    """Data related to IndChromosome"""
    name: str
    length: int

    @property
    def mb_length(self):
        """Chromosome length in mega-bases"""
        return self.length / 1000000


class Chromosomes:
    def __init__(self, dataset=None, species=None):
        self.chromosomes = collections.OrderedDict()
        if species != None:
            query = (
                "SELECT Chr_Length.Name, Chr_Length.OrderId, Length "
                "FROM Chr_Length, Species WHERE "
                "Chr_Length.SpeciesId = Species.SpeciesId AND "
                "Species.Name = "
                "'%s' ORDER BY OrderId" % species.capitalize()
                )
        else:
            self.dataset = dataset
            query = (
                "SELECT Chr_Length.Name, Chr_Length.OrderId, "
                "Length FROM Chr_Length, InbredSet WHERE "
                "Chr_Length.SpeciesId = InbredSet.SpeciesId AND "
                "InbredSet.Name = "
                "'%s' ORDER BY OrderId" % self.dataset.group.name)
        results = g.db.execute(query).fetchall()
        for item in results:
            self.chromosomes[item.OrderId] = IndChromosome(
                item.Name, item.Length)
