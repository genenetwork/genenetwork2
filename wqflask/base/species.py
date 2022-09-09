from collections import OrderedDict
from dataclasses import dataclass
from dataclasses import InitVar
from typing import Optional, Dict, Any, Union
from wqflask.database import database_connection


@dataclass
class TheSpecies:
    """Data related to species."""
    dataset: Optional[Dict] = None
    species_name: Optional[str] = None

    def __post_init__(self) -> None:
        # Just an alias of species_name.  It's safe for this to be None.
        self.name = self.species_name
        with database_connection() as conn:
            self.chromosomes = Chromosomes(conn=conn,
                                           species=self.species_name,
                                           dataset=self.dataset)


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
    conn: Any
    dataset: InitVar[Dict] = None
    species: Optional[str] = None

    def __post_init__(self, dataset) -> None:
        if self.species is None:
            self.dataset = dataset

    @property
    def chromosomes(self) -> OrderedDict:
        """Lazily fetch the chromosomes"""
        chromosomes = OrderedDict()
        with database_connection() as conn, conn.cursor() as cursor:
            if self.species is not None:
                cursor.execute(
                    "SELECT Chr_Length.Name, Chr_Length.OrderId, Length "
                    "FROM Chr_Length, Species WHERE "
                    "Chr_Length.SpeciesId = Species.SpeciesId AND "
                    "Species.Name = %s "
                    "ORDER BY OrderId", (self.species.capitalize(),))
            else:
                cursor.execute(
                    "SELECT Chr_Length.Name, Chr_Length.OrderId, "
                    "Length FROM Chr_Length, InbredSet WHERE "
                    "Chr_Length.SpeciesId = InbredSet.SpeciesId AND "
                    "InbredSet.Name = "
                    "%s ORDER BY OrderId", (self.dataset.group.name,))
            for name, _, length in cursor.fetchall():
                chromosomes[name] = IndChromosome(
                    name=name, length=length)
            return chromosomes
