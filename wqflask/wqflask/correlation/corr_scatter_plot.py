from __future__ import absolute_import, print_function, division

from flask import g

from base.trait import GeneralTrait
from base import data_set
from utility import corr_result_helpers
from scipy import stats
import numpy as np

import utility.logger
logger = utility.logger.getLogger(__name__ )

class CorrScatterPlot(object):
    """Page that displays a correlation scatterplot with a line fitted to it"""

    def __init__(self, params):
        self.data_set_1 = data_set.create_dataset(params['dataset_1'])
        self.data_set_2 = data_set.create_dataset(params['dataset_2'])
        #self.data_set_3 = data_set.create_dataset(params['dataset_3'])
        self.trait_1 = GeneralTrait(name=params['trait_1'], dataset=self.data_set_1)
        self.trait_2 = GeneralTrait(name=params['trait_2'], dataset=self.data_set_2)
        #self.trait_3 = GeneralTrait(name=params['trait_3'], dataset=self.data_set_3)

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
        
        rx = stats.rankdata(x)
        ry = stats.rankdata(y)        
        self.rdata = []
        self.rdata.append(rx.tolist())
        self.rdata.append(ry.tolist())        
        srslope, srintercept, srr_value, srp_value, srstd_err = stats.linregress(rx, ry)

        #vals_3 = []
        #for sample in self.trait_3.data:
        #    vals_3.append(self.trait_3.data[sample].value)

        self.collections_exist = "False"
        if g.user_session.logged_in:
            if g.user_session.num_collections > 0:
                self.collections_exist = "True"
        elif g.cookie_session.display_num_collections() != "":
            self.collections_exist = "True"

        self.js_data = dict(
            data = self.data,
            rdata = self.rdata,
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

            srslope = srslope,
            srintercept = srintercept,
            srr_value = srr_value,
            srp_value = srp_value

            #trait3 = self.trait_3.data,
            #vals_3 = vals_3
        )
        self.jsdata = self.js_data
