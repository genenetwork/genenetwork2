from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set
from utility import corr_result_helpers

class CorrScatterPlot(object):

    def __init__(self, params):
        self.data_set_1 = data_set.create_dataset(params['dataset_1'])
        self.data_set_2 = data_set.create_dataset(params['dataset_2'])
        self.trait_1 = GeneralTrait(name=params['trait_1'], dataset=self.data_set_1)
        self.trait_2 = GeneralTrait(name=params['trait_2'], dataset=self.data_set_2)
        vals_1 = []
        for sample in self.trait_1.data.keys():
            vals_1.append(self.trait_1.data[sample].value)
        vals_2 = []
        for sample in self.trait_2.data.keys():
            vals_2.append(self.trait_2.data[sample].value)
        samples_1, samples_2, num_overlap = corr_result_helpers.normalize_values_with_samples(self.trait_1.data, self.trait_2.data)
        self.js_data = dict(
            samples_1 = samples_1,
            samples_2 = samples_2
        )