import re
import itertools

from flask import g
from base import webqtlCaseData
from pprint import pformat as pf

from utility import Plot
from utility import Bunch

class SampleList(object):
    def __init__(self,
                 dataset,
                 sample_names,
                 this_trait,
                 sample_group_type="primary",
                 header="Samples"):

        self.dataset = dataset
        self.this_trait = this_trait
        self.sample_group_type = sample_group_type    # primary or other
        self.header = header

        self.sample_list = []  # The actual list
        self.sample_attribute_values = {}

        self.get_attributes()

        if self.this_trait and self.dataset:
            self.get_extra_attribute_values()

        for counter, sample_name in enumerate(sample_names, 1):
            sample_name = sample_name.replace("_2nd_", "")

            # ZS: self.this_trait will be a list if it is a Temp trait
            if isinstance(self.this_trait, list):
                if (counter <= len(self.this_trait) and
                        str(self.this_trait[counter-1]).upper() != 'X'):
                    sample = webqtlCaseData.webqtlCaseData(
                        name=sample_name,
                        value=float(self.this_trait[counter-1]))
                else:
                    sample = webqtlCaseData.webqtlCaseData(name=sample_name)
            else:
                # ZS - If there's no value for the sample/strain,
                # create the sample object (so samples with no value
                # are still displayed in the table)
                try:
                    sample = self.this_trait.data[sample_name]
                except KeyError:
                    sample = webqtlCaseData.webqtlCaseData(name=sample_name)

            sample.extra_info = {}
            if (self.dataset.group.name == 'AXBXA' and
                    sample_name in ('AXB18/19/20', 'AXB13/14', 'BXA8/17')):
                sample.extra_info['url'] = "/mouseCross.html#AXB/BXA"
                sample.extra_info['css_class'] = "fs12"

            sample.this_id = str(counter)

            # ZS: For extra attribute columns; currently only used by
            # several datasets
            if self.sample_attribute_values:
                sample.extra_attributes = self.sample_attribute_values.get(
                    sample_name, {})

            self.sample_list.append(sample)

        self.se_exists = any(sample.variance for sample in self.sample_list)
        self.num_cases_exists = any(sample.num_cases for sample in self.sample_list)

        first_attr_col = self.get_first_attr_col()
        for sample in self.sample_list:
            sample.first_attr_col = first_attr_col

        self.do_outliers()

    def __repr__(self):
        return "<SampleList> --> %s" % (pf(self.__dict__))

    def do_outliers(self):
        values = [sample.value for sample in self.sample_list
                  if sample.value is not None]
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
            self.attributes[key] = Bunch()
            self.attributes[key].name = name
            self.attributes[key].distinct_values = [
                item.Value for item in values]
            natural_sort(self.attributes[key].distinct_values)
            all_numbers = True
            for value in self.attributes[key].distinct_values:
                try:
                    val_as_float = float(value)
                except:
                    all_numbers = False

            if all_numbers:
                self.attributes[key].alignment = "right"
            else:
                self.attributes[key].alignment = "left"

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

                    # ZS: If it's an int, turn it into one for sorting
                    # (for example, 101 would be lower than 80 if
                    # they're strings instead of ints)
                    try:
                        attribute_value = int(attribute_value)
                    except ValueError:
                        pass

                    attribute_values[self.attributes[item.Id].name] = attribute_value
                self.sample_attribute_values[sample_name] = attribute_values

    def get_first_attr_col(self):
        first_attr_col = 4
        if self.se_exists:
            first_attr_col += 2
        if self.num_cases_exists:
            first_attr_col += 1

        return first_attr_col

def natural_sort(list, key=lambda s: s):
    """
    Sort the list into natural alphanumeric order.
    """
    def get_alphanum_key_func(key):
        def convert(text): return int(text) if text.isdigit() else text
        return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
    sort_key = get_alphanum_key_func(key)
    list.sort(key=sort_key)