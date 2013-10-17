from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set
from utility import corr_result_helpers

class CorrScatterPlot(object):

    def __init__(self, params):
        print("params  are:", params)
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
            
        vals_1, vals_2, num_overlap = corr_result_helpers.normalize_values(vals_1, vals_2)
        
        self.js_data = dict(
            vals_1 = vals_1,
            vals_2 = vals_2
        )