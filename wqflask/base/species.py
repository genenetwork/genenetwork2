from __future__ import absolute_import, print_function, division

import collections

from flask import Flask, g

#from MySQLdb import escape_string as escape

from pprint import pformat as pf

class TheSpecies(object):
    def __init__(self, dataset):
        self.dataset = dataset
        print("self.dataset is:", pf(self.dataset.__dict__))
        self.chromosomes = Chromosomes(self.dataset.group.name)
        self.genome_length = self.chromosomes.get_genome_length()
        
    #@property
    #def chromosomes(self):
    #    chromosomes = [("All", -1)]
    #
    #    for counter, genotype in enumerate(self.dataset.group.genotype):
    #        if len(genotype) > 1:
    #            chromosomes.append((genotype.name, counter))
    #            
    #    print("chromosomes is: ", pf(chromosomes))       
    #            
    #    return chromosomes



class Chromosomes(object):
    def __init__(self, group_name):
        self.chromosomes = collections.OrderedDict()

        results = g.db.execute("""
                Select
                        Chr_Length.Name, Length from Chr_Length, InbredSet
                where
                        Chr_Length.SpeciesId = InbredSet.SpeciesId AND
                        InbredSet.Name = %s
                Order by OrderId
                """, group_name).fetchall()
        print("bike:", results)

        for item in results:
            self.chromosomes[item.Name] = item.Length

        print("self.chromosomes:", self.chromosomes)


    def get_mb_length(self):
        """Gets the chromosome length in megabases"""

        mb_lengths = chr_length/1000000.0 for name, chr_length in self.chromosomes

        return mb_lengths

    def get_genome_length(self):
        """Gets the sum of each chromosome's length"""

        genome_length = 0
        for name, value in self.chromosomes.items():
            genome_length += value

        return genome_length