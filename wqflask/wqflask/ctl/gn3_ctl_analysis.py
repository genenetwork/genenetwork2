import requests
import itertools

from utility import genofile_parser
from utility.tools import GN3_LOCAL_URL
from utility.tools import locate

from base.trait import create_trait
from base.trait import retrieve_sample_data
from base import data_set


def process_significance_data(significant_data):
    col_names = ["trait", "marker", "trait_2", "LOD", "dcor"]
    dataset_rows = [[] for _ in range(len(significant_data["trait"]))]
    for col in col_names:
        for (index, col_data) in enumerate(significant_data[col]):
            if col in ["dcor", "LOD"]:
                dataset_rows[index].append(round(float(col_data), 2))
            else:
                dataset_rows[index].append(col_data)

    return {
        "col_names": col_names,
        "data_set_rows": dataset_rows
    }


def parse_geno_data(dataset_group_name) -> dict:
    genofile_location = locate(dataset_group_name + ".geno", "genotype")
    parser = genofile_parser.ConvertGenoFile(genofile_location)
    parser.process_csv()
    markers = []
    markernames = []
    for marker in parser.markers:
        markernames.append(marker["name"])
        markers.append(marker["genotypes"])

    return {

        "genotypes": list(itertools.chain(*markers)),
        "markernames": markernames,
        "individuals": parser.individuals


    }


def parse_phenotype_data(trait_db_list, dataset, individuals):
    traits = []
    for trait in trait_db_list:
        if trait != "":
            ts = trait.split(':')
            gt = create_trait(name=ts[0], dataset_name=ts[1])
            gt = retrieve_sample_data(gt, dataset, individuals)
            for ind in individuals:
                if ind in list(gt.data.keys()):
                    traits.append(gt.data[ind].value)
                else:
                    traits.append("-999")

    return {
        "trait_db_list": trait_db_list,
        "traits": traits,
        "individuals": individuals
    }


def parse_form_data(form_data: dict):
    """function to parse/validate form data
    input: dict containing required data
    output: dict with parsed data

    """

    trait_db_list = [trait.strip()
                     for trait in form_data['trait_list'].split(',')]

    form_data["trait_db_list"] = [x for x in trait_db_list if x]
    form_data["nperm"] = int(form_data["nperm"])
    form_data["significance"] = float(form_data["significance"])
    form_data["strategy"] = form_data["strategy"].capitalize()

    return form_data


def run_ctl(requestform):
    """function to make an api call
    to gn3 and run ctl"""
    ctl_api = f"{GN3_LOCAL_URL}/api/ctl/run_ctl"

    form_data = parse_form_data(requestform.to_dict())
    trait_db_list = form_data["trait_db_list"]
    dataset = data_set.create_dataset(trait_db_list[0].split(":")[1])
    geno_data = parse_geno_data(dataset.group.name)
    pheno_data = parse_phenotype_data(
        trait_db_list, dataset, geno_data["individuals"])

    # todo refactor this chunk;;similar to wgcna check

    try:

        response = requests.post(ctl_api, json={

            "genoData": geno_data,
            "phenoData": pheno_data,
            **form_data,

        })
        if response.status_code != 200:
            return {"error": response.json()}
        response = response.json()["results"]
        response["significance_data"] = process_significance_data(
            response["significance_data"])

        return response

    except requests.exceptions.ConnectionError:
        return {
            "error": "A connection error to perform computation occurred"
        }


