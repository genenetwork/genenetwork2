from __future__ import absolute_import, print_function, division

from flask import Flask, g

from base import webqtlCaseData
from utility import webqtlUtil, Plot, Bunch
from base.trait import GeneralTrait

import numpy as np
from scipy import stats
from pprint import pformat as pf

import simplejson as json

import itertools

from utility.elasticsearch_tools import get_elasticsearch_connection

import utility.logger
logger = utility.logger.getLogger(__name__ )

class SampleList(object):
    def __init__(self,
                 dataset,
                 sample_names,
                 this_trait,
                 sample_group_type,
                 header):

        self.dataset = dataset
        self.this_trait = this_trait
        self.sample_group_type = sample_group_type    # primary or other
        self.header = header

        self.sample_list = [] # The actual list
        self.sample_attribute_values = {}

        self.get_attributes()

        #self.sample_qnorm = get_transform_vals(self.dataset, this_trait)

        if self.this_trait and self.dataset:
            self.get_extra_attribute_values()

        for counter, sample_name in enumerate(sample_names, 1):
            sample_name = sample_name.replace("_2nd_", "")

            if type(self.this_trait) is list: #ZS: self.this_trait will be a list if it is a Temp trait
                if counter <= len(self.this_trait) and str(self.this_trait[counter-1]).upper() != 'X':
                    sample = webqtlCaseData.webqtlCaseData(name=sample_name, value=float(self.this_trait[counter-1]))
                else:
                    sample = webqtlCaseData.webqtlCaseData(name=sample_name)
            else:
                #ZS - If there's no value for the sample/strain, create the sample object (so samples with no value are still displayed in the table)
                try:
                    sample = self.this_trait.data[sample_name]
                except KeyError:
                    logger.debug("No sample %s, let's create it now" % sample_name)
                    sample = webqtlCaseData.webqtlCaseData(name=sample_name)

            sample.extra_info = {}
            if self.dataset.group.name == 'AXBXA' and sample_name in ('AXB18/19/20','AXB13/14','BXA8/17'):
                sample.extra_info['url'] = "/mouseCross.html#AXB/BXA"
                sample.extra_info['css_class'] = "fs12"

            sample.this_id = str(counter)

            #### For extra attribute columns; currently only used by several datasets - Zach
            if self.sample_attribute_values:
                sample.extra_attributes = self.sample_attribute_values.get(sample_name, {})
                #logger.debug("sample.extra_attributes is", pf(sample.extra_attributes))

            self.sample_list.append(sample)

        #logger.debug("attribute vals are", pf(self.sample_attribute_values))

        self.do_outliers()

    def __repr__(self):
        return "<SampleList> --> %s" % (pf(self.__dict__))

    def do_outliers(self):
        values = [sample.value for sample in self.sample_list if sample.value != None]
        upper_bound, lower_bound = Plot.find_outliers(values)

        for sample in self.sample_list:
            if sample.value:
                if upper_bound and sample.value > upper_bound:
                    sample.outlier = True
                elif lower_bound and sample.value < lower_bound:
                    sample.outlier = True
                else:
                    sample.outlier = False

    def get_attributes(self):
        """Finds which extra attributes apply to this dataset"""

        # Get attribute names and distinct values for each attribute
        results = g.db.execute('''
                        SELECT DISTINCT CaseAttribute.Id, CaseAttribute.Name, CaseAttributeXRefNew.Value
                        FROM CaseAttribute, CaseAttributeXRefNew
                        WHERE CaseAttributeXRefNew.CaseAttributeId = CaseAttribute.Id
                        AND CaseAttributeXRefNew.InbredSetId = %s
                        ORDER BY CaseAttribute.Name''', (str(self.dataset.group.id),))

        self.attributes = {}
        for attr, values in itertools.groupby(results.fetchall(), lambda row: (row.Id, row.Name)):
            key, name = attr
            logger.debug("radish: %s - %s" % (key, name))
            self.attributes[key] = Bunch()
            self.attributes[key].name = name
            self.attributes[key].distinct_values = [item.Value for item in values]
            self.attributes[key].distinct_values.sort(key=natural_sort_key)

    def get_extra_attribute_values(self):
        if self.attributes:
            query = '''
                        SELECT Strain.Name AS SampleName, CaseAttributeId AS Id, CaseAttributeXRefNew.Value
                        FROM Strain, StrainXRef, InbredSet, CaseAttributeXRefNew
                        WHERE StrainXRef.StrainId = Strain.Id
                        AND InbredSet.Id = StrainXRef.InbredSetId
                        AND CaseAttributeXRefNew.StrainId = Strain.Id
                        AND InbredSet.Id = CaseAttributeXRefNew.InbredSetId
                        AND CaseAttributeXRefNew.InbredSetId = %s
                        ORDER BY SampleName''' % self.dataset.group.id

            results = g.db.execute(query)

            for sample_name, items in itertools.groupby(results.fetchall(), lambda row: row.SampleName):
                attribute_values = {}
                for item in items:
                    attribute_value = item.Value

                    #ZS: If it's an int, turn it into one for sorting
                    #(for example, 101 would be lower than 80 if they're strings instead of ints)
                    try:
                        attribute_value = int(attribute_value)
                    except ValueError:
                        pass

                    attribute_values[self.attributes[item.Id].name] = attribute_value
                self.sample_attribute_values[sample_name] = attribute_values

    def se_exists(self):
        """Returns true if SE values exist for any samples, otherwise false"""

        return any(sample.variance for sample in self.sample_list)

def get_transform_vals(dataset, trait):
    es = get_elasticsearch_connection(for_user=False)

    logger.info("DATASET NAME:", dataset.name)

    query = '{"bool": {"must": [{"match": {"name": "%s"}}, {"match": {"dataset": "%s"}}]}}' % (trait.name, dataset.name)

    es_body = {
          "query": {
            "bool": {
              "must": [
                {
                  "match": {
                    "name": "%s" % (trait.name)
                  }
                },
                {
                  "match": {
                    "dataset": "%s" % (dataset.name)
                  }
                }
              ]
            }
          }
    }

    response = es.search( index = "traits", doc_type = "trait", body = es_body )
    logger.info("THE RESPONSE:", response)
    results = response['hits']['hits']

    if len(results) > 0:
        samples = results[0]['_source']['samples']

        sample_dict = {}
        for sample in samples:
            sample_dict[sample['name']] = sample['qnorm']

        logger.info("SAMPLE DICT:", sample_dict)
        return sample_dict
    else:
        return None

def natural_sort_key(x):
    """Get expected results when using as a key for sort - ints or strings are sorted properly"""

    try:
        x = int(x)
    except ValueError:
        pass
    return x
