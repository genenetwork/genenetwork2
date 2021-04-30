import collections

from flask import Flask, g


from utility.logger import getLogger
logger = getLogger(__name__)

class TheSpecies:
    def __init__(self, dataset=None, species_name=None):
        if species_name != None:
            self.name = species_name
            self.chromosomes = Chromosomes(species=self.name)
        else:
            self.dataset = dataset
            self.chromosomes = Chromosomes(dataset=self.dataset)

class IndChromosome:
    def __init__(self, name, length):
        self.name = name
        self.length = length

    @property
    def mb_length(self):
        """Chromosome length in megabases"""
        return self.length / 1000000

class Chromosomes:
    def __init__(self, dataset=None, species=None):
        self.chromosomes = collections.OrderedDict()
        if species != None:
            query = """
                Select
                        Chr_Length.Name, Chr_Length.OrderId, Length from Chr_Length, Species
                where
                        Chr_Length.SpeciesId = Species.SpeciesId AND
                        Species.Name = '%s'
                Order by OrderId
                """ % species.capitalize()
        else:
            self.dataset = dataset

            query = """
                Select
                        Chr_Length.Name, Chr_Length.OrderId, Length from Chr_Length, InbredSet
                where
                        Chr_Length.SpeciesId = InbredSet.SpeciesId AND
                        InbredSet.Name = '%s'
                Order by OrderId
                """ % self.dataset.group.name
        logger.sql(query)
        results = g.db.execute(query).fetchall()

        for item in results:
            self.chromosomes[item.OrderId] = IndChromosome(item.Name, item.Length)
