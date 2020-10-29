import simplejson as json

from pprint import pformat as pf
from functools import cmp_to_key
from base.trait import create_trait
from base import data_set

def export_sample_table(targs):

    sample_data = json.loads(targs['export_data'])
    trait_name = targs['trait_display_name']

    meta_data = get_export_metadata(targs['trait_id'], targs['dataset'])

    final_sample_data = meta_data

    column_headers = ["Name", "Value"]
    if any(sample["se"] for sample in sample_data['primary_samples']):
        column_headers.append("SE")
    if any(sample["num_cases"] for sample in sample_data['primary_samples']):
        column_headers.append("N")

    final_sample_data.append(column_headers)
    for sample_group in ['primary_samples', 'other_samples']:
        for row in sample_data[sample_group]:
            sorted_row = dict_to_sorted_list(row)
            final_sample_data.append(sorted_row)

    return trait_name, final_sample_data

def get_export_metadata(trait_id, dataset_name):
    dataset = data_set.create_dataset(dataset_name)
    this_trait = create_trait(dataset=dataset,
                              name=trait_id,
                              cellid=None,
                              get_qtl_info=False)

    metadata = []
    if dataset.type == "Publish":
        metadata.append(["Phenotype ID: " + trait_id])
        metadata.append(["Phenotype URL: " + "http://genenetwork.org/show_trait?trait_id=" + trait_id + "&dataset=" + dataset_name])
        metadata.append(["Group: " + dataset.group.name])
        metadata.append(["Phenotype: " + this_trait.description_display.replace(",", "\",\"")])
        metadata.append(["Authors: " + (this_trait.authors if this_trait.authors else "N/A")])
        metadata.append(["Title: " + (this_trait.title if this_trait.title else "N/A")])
        metadata.append(["Journal: " + (this_trait.journal if this_trait.journal else "N/A")])
        metadata.append(["Dataset Link: http://gn1.genenetwork.org/webqtl/main.py?FormID=sharinginfo&InfoPageName=" + dataset.name])
    else:
        metadata.append(["Record ID: " + trait_id])
        metadata.append(["Trait URL: " + "http://genenetwork.org/show_trait?trait_id=" + trait_id + "&dataset=" + dataset_name])
        if this_trait.symbol:
            metadata.append(["Symbol: " + this_trait.symbol])
        metadata.append(["Dataset: " + dataset.name])
        metadata.append(["Group: " + dataset.group.name])

    metadata.append([])

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
