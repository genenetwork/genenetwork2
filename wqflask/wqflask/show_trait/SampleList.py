from __future__ import absolute_import, print_function, division

from flask import Flask, g

from base import webqtlCaseData
from utility import webqtlUtil, Plot, Bunch
from base.webqtlTrait import GeneralTrait

from pprint import pformat as pf

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

        self.get_attributes()
        
        print("camera: attributes are:", pf(self.attributes))

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
            if self.this_trait and self.dataset and self.dataset.type == 'ProbeSet':
                sample.extra_attributes = self.get_extra_attribute_values(sample_name)
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
        
        #ZS: Id and name values for this trait's extra attributes
        case_attributes = g.db.execute('''SELECT CaseAttribute.Id, CaseAttribute.Name
                                        FROM CaseAttribute, CaseAttributeXRef
                                        WHERE CaseAttributeXRef.ProbeSetFreezeId = %s AND
                                            CaseAttribute.Id = CaseAttributeXRef.CaseAttributeId
                                                group by CaseAttributeXRef.CaseAttributeId''',
                                                (str(self.dataset.id),))


        self.attributes = {}
        for key, value in case_attributes.fetchall():
            print("radish: %s - %s" % (key, value))
            self.attributes[key] = Bunch()
            self.attributes[key].name = value

            attribute_values = g.db.execute('''SELECT DISTINCT CaseAttributeXRef.Value
                                               FROM CaseAttribute, CaseAttributeXRef
                                               WHERE CaseAttribute.Name = %s AND
                                CaseAttributeXRef.CaseAttributeId = CaseAttribute.Id''', (value,))

            self.attributes[key].distinct_values = [item[0] for item in attribute_values.fetchall()]
            self.attributes[key].distinct_values.sort(key=natural_sort_key)


    def get_extra_attribute_values(self, sample_name):

        attribute_values = {}

        if self.attributes:

            #ZS: Get StrainId value for the next query
            result = g.db.execute("""SELECT Strain.Id
                                        FROM Strain, StrainXRef, InbredSet
                                        WHERE Strain.Name = %s and
                                            StrainXRef.StrainId = Strain.Id and
                                            InbredSet.Id = StrainXRef.InbredSetId and
                                            InbredSet.Name = %s""", (sample_name,
                                                                     self.dataset.group.name))

            sample_id = result.fetchone().Id

            for attribute in self.attributes:

                #ZS: Add extra case attribute values (if any)
                result = g.db.execute("""SELECT Value
                                                FROM CaseAttributeXRef
                                        WHERE ProbeSetFreezeId = %s AND
                                                StrainId = %s AND
                                                CaseAttributeId = %s
                                        group by CaseAttributeXRef.CaseAttributeId""", (
                                            self.this_trait.db.id, sample_id, str(attribute)))

                attribute_value = result.fetchone().Value #Trait-specific attributes, if any

                #ZS: If it's an int, turn it into one for sorting
                #(for example, 101 would be lower than 80 if they're strings instead of ints)
                try:
                    attribute_value = int(attribute_value)
                except ValueError:
                    pass
                
                attribute_values[self.attributes[attribute].name] = attribute_value
               
        return attribute_values
    
    def se_exists(self):
        """Returns true if SE values exist for any samples, otherwise false"""
        
        return any(sample.variance for sample in self.sample_list)


def natural_sort_key(x):
    """Get expected results when using as a key for sort - ints or strings are sorted properly"""
    
    try:
        x = int(x)
    except ValueError:
        pass
    return x        