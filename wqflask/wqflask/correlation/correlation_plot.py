#!/usr/bin/python

from __future__ import print_function, division

from base.trait import GeneralTrait
from base import data_set
from wqflask.show_trait.SampleList import SampleList

class CorrelationPlot(object):
    """Page that displays a correlation scatterplot with a line fitted to it"""

    def __init__(self, start_vars):
        self.dataset1 = data_set.create_dataset(start_vars['dataset1'])
        self.trait1 = GeneralTrait(dataset=self.dataset1.name,
                                   name=start_vars['trait1'])        

        self.dataset2 = data_set.create_dataset(start_vars['dataset2'])
        self.trait2 = GeneralTrait(dataset=self.dataset2.name,
                                   name=start_vars['trait2'])

        sample_names_1 = self.get_sample_names(self.dataset1)
        sample_names_2 = self.get_sample_names(self.dataset2)
        
        self.samples_1 = self.get_samples(self.dataset1, sample_names_1, self.trait1)
        self.samples_2 = self.get_samples(self.dataset2, sample_names_2, self.trait2)

        coords = {}
        for sample in self.samples_1:
            coords[sample.name] = (sample.val)


    def get_sample_names(self, dataset):
        if dataset.group.parlist:
            sample_names = (dataset.group.parlist +
                                   dataset.group.f1list +
                                   dataset.group.samplelist)
        elif dataset.group.f1list:
            sample_names = dataset.group.f1list + dataset.group.samplelist
        else:
            sample_names = dataset.group.samplelist

        return sample_names


    def get_samples(self, dataset, sample_names, trait):
        samples = SampleList(dataset = dataset,
                            sample_names=sample_names,
                            this_trait=trait,
                            sample_group_type='primary',
                            header="%s Only" % (dataset.group.name))

        return samples
        