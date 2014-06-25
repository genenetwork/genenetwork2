from __future__ import absolute_import, print_function, division

import collections

from flask import Flask, g

#from MySQLdb import escape_string as escape

from utility import Bunch

from pprint import pformat as pf

class TheSpecies(object):
    def __init__(self, dataset):
        self.dataset = dataset
        #print("self.dataset is:", pf(self.dataset.__dict__))
        self.chromosomes = Chromosomes(self.dataset)
        self.genome_mb_length = self.chromosomes.get_genome_mb_length()

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

class IndChromosome(object):
    def __init__(self, name, length):
        self.name = name
        self.length = length
        
    @property
    def mb_length(self):
        """Chromosome length in megabases"""
        return self.length / 1000000
    
    def set_cm_length(self, genofile_chr):
        self.cm_length = genofile_chr[-1].cM - genofile_chr[0].cM


class Chromosomes(object):
    def __init__(self, dataset):
        self.dataset = dataset
        self.chromosomes = collections.OrderedDict()

        results = g.db.execute("""
                Select
                        Chr_Length.Name, Chr_Length.OrderId, Length from Chr_Length, InbredSet
                where
                        Chr_Length.SpeciesId = InbredSet.SpeciesId AND
                        InbredSet.Name = %s
                Order by OrderId
                """, self.dataset.group.name).fetchall()
        #print("group: ", self.dataset.group.name)
        #print("bike:", results)

        for item in results:
            self.chromosomes[item.OrderId] = IndChromosome(item.Name, item.Length)
        
        self.set_mb_graph_interval()
        #self.get_cm_length_list()


    def set_mb_graph_interval(self):
        """Empirical megabase interval"""
        
        if self.chromosomes:
            self.mb_graph_interval = self.get_genome_mb_length()/(len(self.chromosomes)*12)
        else:
            self.mb_graph_interval = 1
            
        #if self.chromosomes:
        #assert self.chromosomes, "Have to add some code back in apparently to set it to 1"
        #self.mb_graph_interval = self.get_genome_mb_length()/(len(self.chromosomes)*12)
        #else:
            #self.mb_graph_interval = 1


    def get_genome_mb_length(self):
        """Gets the sum of each chromosome's length in megabases"""

        return sum([ind_chromosome.mb_length for ind_chromosome in self.chromosomes.values()])


    def get_genome_cm_length(self):
        """Gets the sum of each chromosome's length in centimorgans"""

        return sum([ind_chromosome.cm_length for ind_chromosome in self.chromosomes.values()])

    def get_cm_length_list(self):
        """Chromosome length in centimorgans
        
        Calculates the length in centimorgans by subtracting the centimorgan position
        of the last marker in a chromosome by the position of the first marker
        
        """
        
        self.dataset.group.read_genotype_file()
        
        self.cm_length_list = []
        
        for chromosome in self.dataset.group.genotype:
            self.cm_length_list.append(chromosome[-1].cM - chromosome[0].cM)
            
        print("self.cm_length_list:", pf(self.cm_length_list))
        
        assert len(self.cm_length_list) == len(self.chromosomes), "Uh-oh lengths should be equal!"
        for counter, chromosome in enumerate(self.chromosomes.values()):
            chromosome.cm_length = self.cm_length_list[counter]
            #self.chromosomes[counter].cm_length = item
            
        for key, value in self.chromosomes.items():
            print("bread - %s: %s" % (key, pf(vars(value))))
        

# Testing                
#if __name__ == '__main__':    
#    foo = dict(bar=dict(length))