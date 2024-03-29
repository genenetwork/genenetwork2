"""module contains code to consume gn3-wgcna api
and process data to be rendered by datatables
"""

import requests
from types import SimpleNamespace

from gn2.utility.helper_functions import get_trait_db_obs
from gn2.utility.tools import GN3_LOCAL_URL


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

    for trait in trait_list:
        traits.append(trait[0].name)

        input_data[trait[0].name] = {}
        for strain in trait[0].data:
            strains.append(strain)
            input_data[trait[0].name][strain] = trait[0].data[strain].value

    return {
        "input": input_data,
        "trait_names": traits,
        "sample_names": strains
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


def run_wgcna(form_data):
    """function to run wgcna"""

    wgcna_api = f"{GN3_LOCAL_URL}/api/wgcna/run_wgcna"

    trait_dataset = fetch_trait_data(form_data)
    form_data["minModuleSize"] = int(form_data["MinModuleSize"])

    form_data["SoftThresholds"] = [int(threshold.strip())
                                   for threshold in form_data['SoftThresholds'].rstrip().split(",")]

    try:

        unique_strains = list(set(trait_dataset["sample_names"]))

        response = requests.post(wgcna_api, json={
            "sample_names": unique_strains,
            "trait_names": trait_dataset["trait_names"],
            "trait_sample_data": list(trait_dataset["input"].values()),
            **form_data

        }
        )

        status_code = response.status_code
        response = response.json()

        parameters = {
            "nstrains": len(unique_strains),
            "nphe": len(trait_dataset["trait_names"]),
            **{key: val for key, val in form_data.items() if key not in ["trait_list"]}
        }

        return {"error": response} if status_code != 200 else {
            "error": 'null',
            "parameters": parameters,
            "results": response,
            "data": process_wgcna_data(response["data"]),
            "image": process_image(response["data"])
        }

    except requests.exceptions.ConnectionError:
        return {
            "error": "A connection error to perform computation occurred"
        }
