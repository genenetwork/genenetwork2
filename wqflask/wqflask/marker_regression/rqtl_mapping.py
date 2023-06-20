import csv
import hashlib
import io
import json
import requests
import shutil
from typing import Dict
from typing import List
from typing import Optional
from typing import TextIO

import numpy as np
from flask import current_app as app

from base.trait import create_trait
from utility.redis_tools import get_redis_conn
from utility.configuration import get_setting, locate
from wqflask.database import database_connection


def run_rqtl(trait_name, vals, samples, dataset, pair_scan, mapping_scale, model, method, num_perm, perm_strata_list, do_control, control_marker, manhattan_plot, cofactors):
    """Run R/qtl by making a request to the GN3 endpoint and reading in the output file(s)"""

    pheno_file = write_phenotype_file(trait_name, samples, vals, dataset, cofactors, perm_strata_list)
    if dataset.group.genofile:
        geno_file = locate(app, dataset.group.genofile, "genotype")
    else:
        geno_file = locate(app, dataset.group.name + ".geno", "genotype")

    post_data = {
        "pheno_file": pheno_file,
        "geno_file": geno_file,
        "model": model,
        "method": method,
        "nperm": num_perm,
        "scale": mapping_scale
    }

    if pair_scan:
        post_data["pairscan"] = True

    if cofactors:
        covarstruct_file = write_covarstruct_file(cofactors)
        post_data["covarstruct"] = covarstruct_file

    if do_control == "true" and control_marker:
        post_data["control"] = control_marker

    if not manhattan_plot and not pair_scan:
        post_data["interval"] = True
    if cofactors:
        post_data["addcovar"] = True

    if perm_strata_list:
        post_data["pstrata"] = True

    rqtl_output = requests.post(get_setting(app, "GN3_LOCAL_URL") + "api/rqtl/compute", data=post_data).json()
    if num_perm > 0:
        return rqtl_output['perm_results'], rqtl_output['suggestive'], rqtl_output['significant'], rqtl_output['results']
    else:
        return rqtl_output['results']


def get_hash_of_textio(the_file: TextIO) -> str:
    """Given a StringIO, return the hash of its contents"""

    the_file.seek(0)
    hash_of_file = hashlib.md5(the_file.read().encode()).hexdigest()
    hash_of_file = hash_of_file.replace("/", "_") # Replace / with _ to prevent issue with filenames being translated to directories

    return hash_of_file


def write_covarstruct_file(cofactors: str) -> str:
    """
    Given list of cofactors (as comma-delimited string), write
    a comma-delimited file where the first column consists of cofactor names
    and the second column indicates whether they're numerical or categorical
    """
    trait_datatype_json = None
    with database_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT value FROM TraitMetadata WHERE type='trait_data_type'")
        trait_datatype_json = json.loads(cursor.fetchone()[0])

    covar_struct_file = io.StringIO()
    writer = csv.writer(covar_struct_file, delimiter="\t", quoting = csv.QUOTE_NONE)
    for cofactor in cofactors.split(","):
        datatype = trait_datatype_json[cofactor] if cofactor in trait_datatype_json else "numerical"
        cofactor_name = cofactor.split(":")[0]
        writer.writerow([cofactor_name, datatype])

    hash_of_file = get_hash_of_textio(covar_struct_file)
    file_path = get_setting(app, "TMPDIR") + hash_of_file + ".csv"

    with open(file_path, "w") as fd:
        covar_struct_file.seek(0)
        shutil.copyfileobj(covar_struct_file, fd)

    return file_path


def write_phenotype_file(trait_name: str,
                         samples: List[str],
                         vals: List,
                         dataset_ob,
                         cofactors: Optional[str] = None,
                         perm_strata_list: Optional[List] = None) -> TextIO:
    """Given trait name, sample list, value list, dataset ob, and optional string
    representing cofactors, return the file's full path/name

    """
    cofactor_data = cofactors_to_dict(cofactors, dataset_ob, samples)

    pheno_file = io.StringIO()
    writer = csv.writer(pheno_file, delimiter="\t", quoting=csv.QUOTE_NONE)

    header_row = ["Samples", trait_name]
    header_row += [cofactor for cofactor in cofactor_data]
    if perm_strata_list:
        header_row.append("Strata")

    writer.writerow(header_row)
    for i, sample in enumerate(samples):
        this_row = [sample]
        if vals[i] != "x":
            this_row.append(str(round(float(vals[i]), 3)))
        else:
            this_row.append("NA")
        for cofactor in cofactor_data:
            this_row.append(cofactor_data[cofactor][i])
        if perm_strata_list:
            this_row.append(perm_strata_list[i])
        writer.writerow(this_row)

    hash_of_file = get_hash_of_textio(pheno_file)
    file_path = get_setting(app, "TMPDIR") + hash_of_file + ".csv"

    with open(file_path, "w") as fd:
        pheno_file.seek(0)
        shutil.copyfileobj(pheno_file, fd)

    return file_path


def cofactors_to_dict(cofactors: str, dataset_ob, samples) -> Dict:
    """Given a string of cofactors, the trait being mapped's dataset ob,
    and list of samples, return cofactor data as a Dict

    """
    cofactor_dict = {}
    if cofactors:
        dataset_ob.group.get_samplelist(redis_conn=get_redis_conn())
        sample_list = dataset_ob.group.samplelist
        for cofactor in cofactors.split(","):
            cofactor_name, cofactor_dataset = cofactor.split(":")
            if cofactor_dataset == dataset_ob.name:
                cofactor_dict[cofactor_name] = []
                trait_ob = create_trait(dataset=dataset_ob,
                                        name=cofactor_name)
                sample_data = trait_ob.data
                for index, sample in enumerate(samples):
                    if sample in sample_data:
                        sample_value = str(round(float(sample_data[sample].value), 3))
                        cofactor_dict[cofactor_name].append(sample_value)
                    else:
                        cofactor_dict[cofactor_name].append("NA")
    return cofactor_dict
