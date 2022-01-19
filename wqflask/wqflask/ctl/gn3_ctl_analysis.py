import requests
from dataclasses import dataclass

from utility import genofile_parser
from utility.tools import GN3_LOCAL_URL
from utility.tools import locate

from base.trait import create_trait
from base.trait import retrieve_sample_data


@dataclass
class CtlDatabase:
    """class for keeping track of ctl db data"""

    dataset: dict

    trait_db_list: list


def parse_geno_data(dataset_group_name) ->dict:
	"""function to parse geno file data"""
	genofile_location = locate(dataset.group.name + ".geno", "genotype")
	parser = genofile_parser.ConvertGenoFile(genofilelocation)

	parser.process_csv()

	# get marker and marker names

	return parser

    markers = []
    markernames = []
    for marker in parser.markers:
        markernames.append(marker["name"])
        markers.append(marker["genotypes"])

    return {

    "genotypes":list(itertools.chain(*markers)),
    "markernames":markernames
    "individuals":parser.individuals,


    }


def parse_phenotype_data(trait_db_list):
	"""function to parse and generate phenodata"""

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


    # missing inviduals 

    return {
    "trait_db_list":trait_db_list,
    "traits":traits
    }



def parse_form_data(form_data: dict):
    """function to parse/validate form data
    input: dict containing required data
    output: dict with parsed data

    """

    trait_db_list = [trait.strip()
                          for trait in requestform['trait_list'].split(',')]
    form_data["trait_db_list"] = [x for x in  trait_db_list if x]

    form_data["nperm"] = int(form_data["nperm"])
    form_data["significance"] = float(int(form_data["significance"]))
    form_data["strategy"] = form_data["strategy"].capitalize()

    return form_data


def run_ctl(requestform):
    """function to make an api call
    to gn3 and run ctl"""

    CtlObj = CtlDatabase()

    ctl_api = f"{GN3_LOCAL_URL}/api/ctl/run_ctl"

    form_data = parse_form_data(requestform)

    pheno_data = parse_geno_data(CtlObj.dataset.group.name)


    geno_data = parse_phenotype_data(form_data["trait_db_list"])

    # refactor below

    pheno_data["individuals"] = geno_data["individuals"]


    response = requests.post(ctl_api, json={

    	"genoData":geno_data,
    	"phenoData":pheno_data,

    	**form_data,

    })

    # todo check for errors

    return response.json()
