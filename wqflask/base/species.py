from __future__ import absolute_import, print_function, division

import collections

from flask import Flask, g

#from MySQLdb import escape_string as escape

from utility import Bunch

from pprint import pformat as pf

from utility.logger import getLogger
logger = getLogger(__name__ )

class TheSpecies(object):
    def __init__(self, dataset):
        self.dataset = dataset
        #print("self.dataset is:", pf(self.dataset.__dict__))
        self.chromosomes = Chromosomes(self.dataset)

class IndChromosome(object):
    def __init__(self, name, length):
        self.name = name
        self.length = length

    @property
    def mb_length(self):
        """Chromosome length in megabases"""
        return self.length / 1000000

class Chromosomes(object):
    def __init__(self, dataset):
        self.dataset = dataset
        self.chromosomes = collections.OrderedDict()

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