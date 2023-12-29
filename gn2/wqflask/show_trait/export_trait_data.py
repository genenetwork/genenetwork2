import datetime
import simplejson as json

from pprint import pformat as pf
from functools import cmp_to_key
from gn2.base.trait import create_trait
from gn2.base import data_set


def export_sample_table(targs):

    sample_data = json.loads(targs['export_data'])
    trait_name = targs['trait_display_name']

    meta_data = get_export_metadata(targs)

    final_sample_data = meta_data

    column_headers = ["Index", "Name", "Value"]
    attr_pos = 2
    if any(sample["se"] for sample in sample_data['primary_samples']):
        column_headers.append("SE")
        attr_pos = 3
    if any(sample["num_cases"] for sample in sample_data['primary_samples']):
        column_headers.append("N")
        attr_pos = 4

    for key in sample_data["primary_samples"][0].keys():
        if key not in ["name", "value", "se", "num_cases"]:
            column_headers.append(key)

    final_sample_data.append(column_headers)
    for sample_group in ['primary_samples', 'other_samples']:
        for i, row in enumerate(sample_data[sample_group]):
            sorted_row = [i + 1] + dict_to_sorted_list(row)[:attr_pos]
            for attr in sample_data['attributes']:
                sorted_row.append(row[attr])
            final_sample_data.append(sorted_row)

    return trait_name, final_sample_data


def get_export_metadata(trait_metadata):

    trait_id, display_name, dataset_name, group_name = trait_metadata['trait_id'], trait_metadata['trait_display_name'], trait_metadata['dataset'], trait_metadata['group']

    dataset = data_set.create_dataset(dataset_name, group_name=group_name)
    this_trait = create_trait(dataset=dataset,
                              name=trait_id,
                              cellid=None,
                              get_qtl_info=False)

    metadata = []
    if dataset.type == "Publish":
        metadata.append(["Phenotype ID:", display_name])
        metadata.append(["Phenotype URL: ", "http://genenetwork.org/show_trait?trait_id=" + \
                         trait_id + "&dataset=" + dataset_name])
        metadata.append(["Group: ", dataset.group.name])
        metadata.append(
            ["Phenotype: ", this_trait.description_display.replace(",", "\",\"")])
        metadata.append(
            ["Authors: ", (this_trait.authors if this_trait.authors else "N/A")])
        metadata.append(
            ["Title: ", (this_trait.title if this_trait.title else "N/A")])
        metadata.append(
            ["Journal: ", (this_trait.journal if this_trait.journal else "N/A")])

        metadata.append(
            ["Dataset Link: ", "http://gn1.genenetwork.org/webqtl/main.py?FormID=sharinginfo&InfoPageName=" + dataset.name])
    else:
        metadata.append(["Record ID: ", trait_id])
        metadata.append(["Trait URL: ", "http://genenetwork.org/show_trait?trait_id=" + \
                         trait_id + "&dataset=" + dataset_name])
        if this_trait.symbol:
            metadata.append(["Symbol: ", this_trait.symbol])
        metadata.append(["Dataset: ", dataset.name])
        metadata.append(["Group: ", dataset.group.name])
    metadata.append(
        ["Export Date: ", datetime.datetime.now().strftime("%B %d, %Y")])
    metadata.append(
        ["Export Time: ", datetime.datetime.now().strftime("%H:%M GMT")])


    return metadata


def dict_to_sorted_list(dictionary):
    sorted_list = [item for item in list(dictionary.items())]
    sorted_list = sorted(sorted_list, key=cmp_to_key(cmp_samples))
    sorted_values = [item[1] for item in sorted_list]
    return sorted_values


def cmp_samples(a, b):
    if b[0] == 'name':
        return 1
    elif b[0] == 'value':
        if a[0] == 'name':
            return -1
        else:
            return 1
    elif b[0] == 'se':
        if a[0] == 'name' or a[0] == 'value':
            return -1
        else:
            return 1
    elif b[0] == 'num_cases':
        if a[0] == 'name' or a[0] == 'value' or a[0] == 'se':
            return -1
        else:
            return 1
    else:
        return -1
