from __future__ import print_function, division

import simplejson as json

from pprint import pformat as pf

def export_sample_table(targs):

    sample_data = json.loads(targs['export_data'])
    final_sample_data = []

    for sample_group in ['primary_samples', 'other_samples']:
        for row in sample_data[sample_group]:
            sorted_row = dict_to_sorted_list(row)
            print("sorted_row is:", pf(sorted_row))
            final_sample_data.append(sorted_row)

    return final_sample_data

def dict_to_sorted_list(dictionary):
    sorted_list = [item for item in dictionary.iteritems()]
    sorted_list = sorted(sorted_list, cmp=cmp_samples)
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