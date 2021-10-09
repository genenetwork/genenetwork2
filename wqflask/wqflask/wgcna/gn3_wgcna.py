"""module contains code to consume gn3-wgcna api
and process data to be rendered by datatables
"""
from utility.helper_functions import get_trait_db_obs


def fetch_trait_data(requestform):
    """fetch trait data"""
    db_obj = SimpleNamespace()
    get_trait_db_obs(db_obj,
                     [trait.strip()
                      for trait in requestform['trait_list'].split(',')])

    return process_dataset(db_obj.trait_list)


def process_dataset(trait_list):
    """process datasets and strains"""

    input_data = {}
    traits = []
    strains = []

    # xtodo unique traits and strains

    for trait in trait_list:
        traits.append(trait[0].name)

        input_data[trait[0].name] = {}
        for strain in trait[0].data:
            strains.append(strain)
            input_data[trait[0].name][strain] = trait[0].data[strain].value

    return {
        "wgcna_input": input_data
    }

    def process_dataset(trait_list):
    """process datasets and strains"""

    input_data = {}
    traits = []
    strains = []

    # xtodo unique traits and strains

    for trait in trait_list:
        traits.append(trait[0].name)

        input_data[trait[0].name] = {}
        for strain in trait[0].data:
            strains.append(strain)
            input_data[trait[0].name][strain] = trait[0].data[strain].value

    return {
        "wgcna_input": input_data
    }


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


def process_image(response):
    """function to process image check if byte string is empty"""
    image_data = response["output"]["image_data"]
    return ({
        "image_generated": True,
        "image_data": image_data
    } if image_data else {
        "image_generated": False
    })
