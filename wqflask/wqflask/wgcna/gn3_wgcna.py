"""module contains code to consume gn3-wgcna api
and process data to be rendered by datatables
"""



def process_wgcna_data(response):
    """function for processing modeigene genes
    for create row data for datataba"""
    mod_eigens = response["output"]["ModEigens"]

    sample_names = response["input"]["sample_names"]

    mod_dataset = [[sample] for sample in sample_names]

    for _, mod_values in mod_eigens.items():
        for (index, _sample) in enumerate(sample_names):
            mod_dataset[index].append(round(mod_values[index], 3))

    return {
        "col_names": ["sample_names", *mod_eigens.keys()],
        "mod_dataset": mod_dataset
    }


def process_image():
    pass