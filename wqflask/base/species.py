from __future__ import print_function, division


class TheSpecies(object):
    def __init__(self, dataset):
        self.dataset = dataset

    @property
    def chromosomes(self):
        chromosomes = [("All", -1)]
  
        for counter, genotype in enumerate(self.dataset.group.genotype):
            if len(genotype) > 1:
                chromosomes.append((genotype.name, counter))
                
        return chromosomes
