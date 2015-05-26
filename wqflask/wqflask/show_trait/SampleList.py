from __future__ import absolute_import, print_function, division

from flask import Flask, g

from base import webqtlCaseData
from utility import webqtlUtil, Plot, Bunch
from base.trait import GeneralTrait

import numpy as np
from scipy import stats
from pprint import pformat as pf

import itertools

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
        print("camera: attributes are:", pf(self.attributes))

        if self.this_trait and self.dataset and self.dataset.type == 'ProbeSet':
            self.get_extra_attribute_values()

        for counter, sample_name in enumerate(sample_names, 1):
            sample_name = sample_name.replace("_2nd_", "")

            #ZS - If there's no value for the sample/strain, create the sample object (so samples with no value are still displayed in the table)
            try:
                sample = self.this_trait.data[sample_name]
            except KeyError:
                print("No sample %s, let's create it now" % sample_name)
                sample = webqtlCaseData.webqtlCaseData(sample_name)
            
            #sampleNameAdd = ''
            #if fd.RISet == 'AXBXA' and sampleName in ('AXB18/19/20','AXB13/14','BXA8/17'):
            #    sampleNameAdd = HT.Href(url='/mouseCross.html#AXB/BXA', text=HT.Sup('#'), Class='fs12', target="_blank")
            sample.extra_info = {}
            if self.dataset.group.name == 'AXBXA' and sample_name in ('AXB18/19/20','AXB13/14','BXA8/17'):   
                sample.extra_info['url'] = "/mouseCross.html#AXB/BXA"
                sample.extra_info['css_class'] = "fs12" 

            print("  type of sample:", type(sample))

            if sample_group_type == 'primary':
                sample.this_id = "Primary_" + str(counter)
            else:
                sample.this_id = "Other_" + str(counter)

            #### For extra attribute columns; currently only used by several datasets - Zach
            if self.sample_attribute_values:
                sample.extra_attributes = self.sample_attribute_values.get(sample_name, {})
                print("sample.extra_attributes is", pf(sample.extra_attributes))
            
            self.sample_list.append(sample)

        print("self.attributes is", pf(self.attributes))

        self.do_outliers()
        #do_outliers(the_samples)
        print("*the_samples are [%i]: %s" % (len(self.sample_list), pf(self.sample_list)))
        for sample in self.sample_list:
            print("apple:", type(sample), sample)
        #return the_samples

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
                        SELECT DISTINCT CaseAttribute.Id, CaseAttribute.Name, CaseAttributeXRef.Value
                        FROM CaseAttribute, CaseAttributeXRef
                        WHERE CaseAttributeXRef.CaseAttributeId = CaseAttribute.Id
                        AND CaseAttributeXRef.ProbeSetFreezeId = %s
                        ORDER BY CaseAttribute.Name''', (str(self.dataset.id),))

        self.attributes = {}
        for attr, values in itertools.groupby(results.fetchall(), lambda row: (row.Id, row.Name)):
            key, name = attr
            print("radish: %s - %s" % (key, name))
            self.attributes[key] = Bunch()
            self.attributes[key].name = name
            self.attributes[key].distinct_values = [item.Value for item in values]
            self.attributes[key].distinct_values.sort(key=natural_sort_key)

    def get_extra_attribute_values(self):
        if self.attributes:
            results = g.db.execute('''
                        SELECT Strain.Name AS SampleName, CaseAttributeId AS Id, CaseAttributeXRef.Value
                        FROM Strain, StrainXRef, InbredSet, CaseAttributeXRef
                        WHERE StrainXRef.StrainId = Strain.Id
                        AND InbredSet.Id = StrainXRef.InbredSetId
                        AND CaseAttributeXRef.StrainId = Strain.Id
                        AND InbredSet.Name = %s
                        AND CaseAttributeXRef.ProbeSetFreezeId = %s
                        ORDER BY SampleName''',
                       (self.dataset.group.name, self.this_trait.dataset.id))

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

#def z_score(vals):
#    vals_array = np.array(vals)
#    mean = np.mean(vals_array)
#    stdv = np.std(vals_array)
#    
#    z_scores = []
#    for val in vals_array:
#        z_score = (val - mean)/stdv
#        z_scores.append(z_score)
#        
#        
#        
#    return z_scores


#def z_score(row):
#    L = [n for n in row if not np.isnan(n)]
#    m = np.mean(L)
#    s = np.std(L)
#    zL = [1.0 * (n - m) / s for n in L]
#    if len(L) == len(row):  return zL
#    # deal with nan
#    retL = list()
#    for n in row:
#        if np.isnan(n):
#            retL.append(nan)
#        else:
#            retL.append(zL.pop(0))
#    assert len(zL) == 0
#    return retL

def natural_sort_key(x):
    """Get expected results when using as a key for sort - ints or strings are sorted properly"""
    
    try:
        x = int(x)
    except ValueError:
        pass
    return x
