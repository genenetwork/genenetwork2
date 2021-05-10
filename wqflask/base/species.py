from collections import OrderedDict
from dataclasses import dataclass
from dataclasses import InitVar
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


@dataclass
class Chromosomes:
    """Data related to a chromosome"""
    dataset: InitVar[Dict] = None
    species: Optional[str] = None

    def __post_init__(self, dataset):
        if self.species is None:
            self.dataset = dataset

    @property
    def chromosomes(self):
        """Lazily fetch the chromosomes"""
        chromosomes = OrderedDict()
        if self.species is not None:
            query = (
                "SELECT Chr_Length.Name, Chr_Length.OrderId, Length "
                "FROM Chr_Length, Species WHERE "
                "Chr_Length.SpeciesId = Species.SpeciesId AND "
                "Species.Name = "
                "'%s' ORDER BY OrderId" % self.species.capitalize())
        else:
            query = (
                "SELECT Chr_Length.Name, Chr_Length.OrderId, "
                "Length FROM Chr_Length, InbredSet WHERE "
                "Chr_Length.SpeciesId = InbredSet.SpeciesId AND "
                "InbredSet.Name = "
                "'%s' ORDER BY OrderId" % self.dataset.group.name)
        results = g.db.execute(query).fetchall()
        for item in results:
            chromosomes[item.OrderId] = IndChromosome(
                item.Name, item.Length)
        return chromosomes
