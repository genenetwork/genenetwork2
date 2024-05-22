import re
import itertools

from gn2.wqflask.database import database_connection
from gn2.base import webqtlCaseData, webqtlConfig
from pprint import pformat as pf

from gn2.utility import Plot
from gn2.utility import Bunch
from gn2.utility.tools import get_setting

class SampleList:
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

            # self.this_trait will be a list if it is a Temp trait
            if isinstance(self.this_trait, list):
                sample = webqtlCaseData.webqtlCaseData(name=sample_name)
                if counter <= len(self.this_trait):
                    if isinstance(self.this_trait[counter - 1], (bytes, bytearray)):
                        if (self.this_trait[counter - 1].decode("utf-8").lower() != 'x'):
                            sample = webqtlCaseData.webqtlCaseData(
                                name=sample_name,
                                value=float(self.this_trait[counter - 1]))
                    else:
                        if (self.this_trait[counter - 1].lower() != 'x'):
                            sample = webqtlCaseData.webqtlCaseData(
                                name=sample_name,
                                value=float(self.this_trait[counter - 1]))
            else:
                # If there's no value for the sample/strain,
                # create the sample object (so samples with no value
                # are still displayed in the table)
                try:
                    sample = self.this_trait.data[sample_name]
                except KeyError:
                    sample = webqtlCaseData.webqtlCaseData(name=sample_name)

            sample.extra_info = {}
            if (self.dataset.group.name == 'AXBXA'
                    and sample_name in ('AXB18/19/20', 'AXB13/14', 'BXA8/17')):
                sample.extra_info['url'] = "/mouseCross.html#AXB/BXA"
                sample.extra_info['css_class'] = "fs12"

            sample.this_id = str(counter)

            # For extra attribute columns; currently only used by
            # several datasets
            if self.sample_attribute_values:
                sample.extra_attributes = self.sample_attribute_values.get(
                    sample_name, {})

                # Add a url so RRID case attributes can be displayed as links
                if '36' in sample.extra_attributes:
                    rrid_string = str(sample.extra_attributes['36'])
                    if self.dataset.group.species == "mouse":
                        if len(rrid_string.split(":")) > 1:
                            the_rrid = rrid_string.split(":")[1]
                            sample.extra_attributes['36'] = [
                                rrid_string]
                            sample.extra_attributes['36'].append(
                                webqtlConfig.RRID_MOUSE_URL % the_rrid)
                    elif self.dataset.group.species == "rat":
                        # Check if it's a list just in case a parent/f1 strain also shows up in the .geno file, to avoid being added twice
                        if len(rrid_string) and not isinstance(sample.extra_attributes['36'], list):
                            the_rrid = rrid_string.split("_")[1]
                            sample.extra_attributes['36'] = [
                                rrid_string]
                            sample.extra_attributes['36'].append(
                                webqtlConfig.RRID_RAT_URL % the_rrid)

            self.sample_list.append(sample)

        self.se_exists = any(sample.variance for sample in self.sample_list)
        self.num_cases_exists = False
        if (any(sample.num_cases for sample in self.sample_list) and
            any((sample.num_cases and sample.num_cases != "1") for sample in self.sample_list)):
            self.num_cases_exists = True

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
        with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT CaseAttribute.CaseAttributeId, "
                "CaseAttribute.Name, CaseAttribute.Description, "
                "CaseAttributeXRefNew.Value FROM "
                "CaseAttribute, CaseAttributeXRefNew WHERE "
                "CaseAttributeXRefNew.CaseAttributeId = CaseAttribute.CaseAttributeId "
                "AND CaseAttributeXRefNew.InbredSetId = %s "
                "ORDER BY CaseAttribute.CaseAttributeId", (str(self.dataset.group.id),)
            )

            self.attributes = {}
            for attr, values in itertools.groupby(
                    cursor.fetchall(), lambda row: (row[0], row[1], row[2])
            ):
                key, name, description = attr
                self.attributes[key] = Bunch()
                self.attributes[key].id = key
                self.attributes[key].name = name
                self.attributes[key].description = description
                self.attributes[key].distinct_values = [
                    item[3] for item in values]
                self.attributes[key].distinct_values = natural_sort(
                    self.attributes[key].distinct_values)
                all_numbers = True
                for value in self.attributes[key].distinct_values:
                    try:
                        val_as_float = float(value)
                    except:
                        all_numbers = False
                        break

                if all_numbers:
                    self.attributes[key].alignment = "right"
                else:
                    self.attributes[key].alignment = "left"

    def get_extra_attribute_values(self):
        if self.attributes:
            with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT Strain.Name AS SampleName, "
                    "CaseAttributeId AS Id, "
                    "CaseAttributeXRefNew.Value FROM Strain, "
                    "StrainXRef, InbredSet, CaseAttributeXRefNew "
                    "WHERE StrainXRef.StrainId = Strain.Id "
                    "AND InbredSet.Id = StrainXRef.InbredSetId "
                    "AND CaseAttributeXRefNew.StrainId = Strain.Id "
                    "AND InbredSet.Id = CaseAttributeXRefNew.InbredSetId "
                    "AND CaseAttributeXRefNew.InbredSetId = %s "
                    "ORDER BY SampleName", (self.dataset.group.id,)
                )

                for sample_name, items in itertools.groupby(
                        cursor.fetchall(), lambda row: row[0]
                ):
                    attribute_values = {}
                    # Make a list of attr IDs without values (that have values for other samples)
                    valueless_attr_ids = [self.attributes[key].id for key in self.attributes.keys()]
                    for item in items:
                        sample_name, _id, value = item
                        valueless_attr_ids.remove(_id)
                        attribute_value = value

                        # If it's an int, turn it into one for sorting
                        # (for example, 101 would be lower than 80 if
                        # they're strings instead of ints)
                        try:
                            attribute_value = int(attribute_value)
                        except ValueError:
                            pass

                        attribute_values[str(_id)] = attribute_value
                    for attr_id in valueless_attr_ids:
                        attribute_values[str(attr_id)] = ""

                    self.sample_attribute_values[sample_name] = attribute_values

    def get_first_attr_col(self):
        first_attr_col = 4
        if self.se_exists:
            first_attr_col += 2
        if self.num_cases_exists:
            first_attr_col += 1

        return first_attr_col


def natural_sort(a_list, key=lambda s: s):
    """
    Sort the list into natural alphanumeric order.
    """
    def get_alphanum_key_func(key):
        def convert(text): return int(text) if text.isdigit() else text
        return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
    sort_key = get_alphanum_key_func(key)
    sorted_list = sorted(a_list, key=sort_key)
    return sorted_list
