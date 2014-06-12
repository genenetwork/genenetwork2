from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set
from utility import corr_result_helpers
from scipy import stats
import numpy as np

class CorrScatterPlot(object):

    def __init__(self, params):
        self.data_set_1 = data_set.create_dataset(params['dataset_1'])
        self.data_set_2 = data_set.create_dataset(params['dataset_2'])
        self.trait_1 = GeneralTrait(name=params['trait_1'], dataset=self.data_set_1)
        self.trait_2 = GeneralTrait(name=params['trait_2'], dataset=self.data_set_2)
        
        try:
            width = int(params['width'])
        except:
            width = 800
        self.width = width
        
        try:
            height = int(params['height'])
        except:
            height = 600
        self.height = height
        
        try:
            circle_color = params['circle_color']
        except:
            circle_color = 'steelblue'
        self.circle_color = circle_color
        
        try:
            circle_radius = int(params['circle_radius'])
        except:
            circle_radius = 5
        self.circle_radius = circle_radius
        
        try:
            line_color = params['line_color']
        except:
            line_color = 'red'
        self.line_color = line_color
        
        try:
            line_width = int(params['line_width'])
        except:
            line_width = 1
        self.line_width = line_width
        
        samples_1, samples_2, num_overlap = corr_result_helpers.normalize_values_with_samples(self.trait_1.data, self.trait_2.data)
        
        self.data = []
        self.indIDs = samples_1.keys()
        vals_1 = []
        for sample in samples_1.keys():
            vals_1.append(samples_1[sample].value)
        self.data.append(vals_1)
        vals_2 = []
        for sample in samples_2.keys():
            vals_2.append(samples_2[sample].value)
        self.data.append(vals_2)

        x = np.array(vals_1)
        y = np.array(vals_2)
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        self.js_data = dict(
            data = self.data,
            indIDs = self.indIDs,
            trait_1 = self.trait_1.dataset.name + ": " + str(self.trait_1.name),
            trait_2 = self.trait_2.dataset.name + ": " + str(self.trait_2.name),
            samples_1 = samples_1,
            samples_2 = samples_2,
            num_overlap = num_overlap,
            vals_1 = vals_1,
            vals_2 = vals_2,
            slope = slope,
            intercept = intercept,
            r_value = r_value,
            p_value = p_value,
            width = width,
            height = height,
            circle_color = circle_color,
            circle_radius = circle_radius,
            line_color = line_color,
            line_width = line_width
        )
