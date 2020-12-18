import math

from flask import g

from base.trait import create_trait, retrieve_sample_data
from base import data_set
from utility import corr_result_helpers
from scipy import stats
import numpy as np

import utility.logger
logger = utility.logger.getLogger(__name__ )

class CorrScatterPlot(object):
    """Page that displays a correlation scatterplot with a line fitted to it"""

    def __init__(self, params):
        if "Temp" in params['dataset_1']:
            self.dataset_1 = data_set.create_dataset(dataset_name = "Temp", dataset_type = "Temp", group_name = params['dataset_1'].split("_")[1])
        else:
            self.dataset_1 = data_set.create_dataset(params['dataset_1'])
        if "Temp" in params['dataset_2']:
            self.dataset_2 = data_set.create_dataset(dataset_name = "Temp", dataset_type = "Temp", group_name = params['dataset_2'].split("_")[1])
        else:
            self.dataset_2 = data_set.create_dataset(params['dataset_2'])

        #self.dataset_3 = data_set.create_dataset(params['dataset_3'])
        self.trait_1 = create_trait(name=params['trait_1'], dataset=self.dataset_1)
        self.trait_2 = create_trait(name=params['trait_2'], dataset=self.dataset_2)
        #self.trait_3 = create_trait(name=params['trait_3'], dataset=self.dataset_3)

        self.method = params['method']

        primary_samples = self.dataset_1.group.samplelist
        if self.dataset_1.group.parlist != None:
            primary_samples += self.dataset_1.group.parlist
        if self.dataset_1.group.f1list != None:
            primary_samples += self.dataset_1.group.f1list

        self.trait_1 = retrieve_sample_data(self.trait_1, self.dataset_1, primary_samples)
        self.trait_2 = retrieve_sample_data(self.trait_2, self.dataset_2, primary_samples)

        samples_1, samples_2, num_overlap = corr_result_helpers.normalize_values_with_samples(self.trait_1.data, self.trait_2.data)

        self.data = []
        self.indIDs = list(samples_1.keys())
        vals_1 = []
        for sample in list(samples_1.keys()):
            vals_1.append(samples_1[sample].value)
        self.data.append(vals_1)
        vals_2 = []
        for sample in list(samples_2.keys()):
            vals_2.append(samples_2[sample].value)
        self.data.append(vals_2)

        slope, intercept, r_value, p_value, std_err = stats.linregress(vals_1, vals_2)

        if slope < 0.001:
            slope_string = '%.3E' % slope
        else:
            slope_string = '%.3f' % slope
        
        x_buffer = (max(vals_1) - min(vals_1))*0.1
        y_buffer = (max(vals_2) - min(vals_2))*0.1

        x_range = [min(vals_1) - x_buffer, max(vals_1) + x_buffer]
        y_range = [min(vals_2) - y_buffer, max(vals_2) + y_buffer]

        intercept_coords = get_intercept_coords(slope, intercept, x_range, y_range)

        rx = stats.rankdata(vals_1)
        ry = stats.rankdata(vals_2)
        self.rdata = []
        self.rdata.append(rx.tolist())
        self.rdata.append(ry.tolist())        
        srslope, srintercept, srr_value, srp_value, srstd_err = stats.linregress(rx, ry)

        if srslope < 0.001:
            srslope_string = '%.3E' % srslope
        else:
            srslope_string = '%.3f' % srslope

        x_buffer = (max(rx) - min(rx))*0.1
        y_buffer = (max(ry) - min(ry))*0.1

        sr_range = [min(rx) - x_buffer, max(rx) + x_buffer]

        sr_intercept_coords = get_intercept_coords(srslope, srintercept, sr_range, sr_range)

        self.collections_exist = "False"
        if g.user_session.num_collections > 0:
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
            x_range = x_range,
            y_range = y_range,
            sr_range = sr_range,
            intercept_coords = intercept_coords,
            sr_intercept_coords = sr_intercept_coords,

            slope = slope,
            slope_string = slope_string,
            intercept = intercept,
            r_value = r_value,
            p_value = p_value,

            srslope = srslope,
            srslope_string = srslope_string,
            srintercept = srintercept,
            srr_value = srr_value,
            srp_value = srp_value

            #trait3 = self.trait_3.data,
            #vals_3 = vals_3
        )
        self.jsdata = self.js_data


def get_intercept_coords(slope, intercept, x_range, y_range):
    intercept_coords = []

    y1 = slope*x_range[0] + intercept
    y2 = slope*x_range[1] + intercept
    x1 = (y1-intercept)/slope
    x2 = (y2-intercept)/slope

    intercept_coords.append([x1, y1])
    intercept_coords.append([x2, y2])

    return intercept_coords
