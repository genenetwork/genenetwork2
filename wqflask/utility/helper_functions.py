from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set
from base.species import TheSpecies


def get_species_dataset_trait(self, start_vars):
    #assert type(read_genotype) == type(bool()), "Expecting boolean value for read_genotype"
    self.dataset = data_set.create_dataset(start_vars['dataset'])
    self.species = TheSpecies(dataset=self.dataset)
    self.this_trait = GeneralTrait(dataset=self.dataset.name,
                                   name=start_vars['trait_id'],
                                   cellid=None)

    #if read_genotype:
    self.dataset.group.read_genotype_file()
    #self.genotype = self.dataset.group.genotype
