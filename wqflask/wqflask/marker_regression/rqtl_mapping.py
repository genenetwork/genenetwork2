import csv
import hashlib
import io
import requests
import shutil
from typing import Dict
from typing import List
from typing import Optional
from typing import TextIO

from base.webqtlConfig import TMPDIR
from base.trait import create_trait
from utility.tools import locate

import utility.logger
logger = utility.logger.getLogger(__name__)

GN3_RQTL_URL = "http://localhost:8086/api/rqtl/compute"
GN3_TMP_PATH = "/export/local/home/zas1024/genenetwork3/tmp"

def run_rqtl(trait_name, vals, samples, dataset, mapping_scale, method, model, permCheck, num_perm, perm_strata_list, do_control, control_marker, manhattan_plot, pair_scan, cofactors):
    """Run R/qtl by making a request to the GN3 endpoint and reading in the output file(s)"""

    pheno_file = write_phenotype_file(trait_name, samples, vals, cofactors)
    if dataset.group.genofile:
        geno_file = locate(dataset.group.genofile, "genotype")
    else:
        geno_file = locate(dataset.group.name + ".geno", "genotype")

    post_data = {
        "pheno_file": pheno_file,
        "geno_file": geno_file,
        "model": model,
        "method": method,
        "nperm": num_perm,
        "scale": mapping_scale
    }

    if do_control == "true" and control_marker:
        post_data["control_marker"] = control_marker

    if not manhattan_plot:
        post_data["interval"] = True
    if cofactors:
        post_data["addcovar"] = True

    out_file = requests.post(GN3_RQTL_URL, data=post_data).json()['output_file']

    return process_rqtl_results(out_file)


def process_rqtl_results(out_file: str) -> List:
    """Given the output filename, read in results and
    return as a list of dictionaries representing each
    marker

    """

    marker_obs = []
    # Later I should probably redo this using csv.read to avoid the
    # awkwardness with removing quotes with [1:-1]
    with open(GN3_TMP_PATH + "/output/" + out_file, "r") as the_file:
        for line in the_file:
            line_items = line.split(",")
            if line_items[1][1:-1] == "chr" or not line_items:
                continue
            else:
                # Convert chr to int if possible
                try:
                    the_chr = int(line_items[1][1:-1])
                except:
                    the_chr = line_items[1][1:-1]
                this_marker = {
                    "name": line_items[0][1:-1],
                    "chr": the_chr,
                    "cM": float(line_items[2]),
                    "Mb": float(line_items[2]),
                    "lod_score": float(line_items[3])
                }
                marker_obs.append(this_marker)

    return marker_obs

def get_hash_of_textio(the_file: TextIO) -> str:
    """Given a StringIO, return the hash of its contents"""

    the_file.seek(0)
    hash_of_file = hashlib.md5(the_file.read().encode()).hexdigest()

    return hash_of_file


def write_phenotype_file(trait_name: str,
                         samples: List[str],
                         vals: List,
                         dataset_ob,
                         cofactors: Optional[str] = None) -> TextIO:
    """Given trait name, sample list, value list, dataset ob, and optional string
    representing cofactors, return the file's full path/name

    """

    cofactor_data = cofactors_to_dict(cofactors, dataset_ob, samples)

    pheno_file = io.StringIO()
    writer = csv.writer(pheno_file, delimiter="\t", quoting=csv.QUOTE_NONE)

    header_row = ["Samples", trait_name]
    header_row += [cofactor for cofactor in cofactor_data]

    writer.writerow(header_row)
    for i, sample in enumerate(samples):
        this_row = [sample]
        if vals[i] != "x":
            this_row.append(vals[i])
        else:
            this_row.append("NA")
        for cofactor in cofactor_data:
            this_row.append(cofactor_data[cofactor][i])
        writer.writerow(this_row)

    hash_of_file = get_hash_of_textio(pheno_file)
    file_path = TMPDIR + hash_of_file + ".csv"

    with open(file_path, "w") as fd:
        pheno_file.seek(0)
        shutil.copyfileobj(pheno_file, fd)

    return file_path


def cofactors_to_dict(cofactors: str, dataset_ob, samples) -> Dict:
    """Given a string of cofactors, the trait being mapped's dataset ob,
    and list of samples, return cofactor data as a Dict

    """
    cofactors = {}
    if cofactors:
        dataset_ob.group.get_samplelist()
        sample_list = dataset_ob.group.samplelist
        for cofactor in cofactors.split(","):
            cofactor_name, cofactor_dataset = cofactor.split(":")
            if cofactor_dataset == this_dataset.name:
                cofactors[cofactor_name] = []
                trait_ob = create_trait(dataset=dataset_ob,
                                        name=cofactor_name)
                sample_data = trait_ob.data
                for index, sample in enumerate(samples):
                    #if (sample in sample_list) and (sample in sample_data):
                    if sample in sample_data:
                        sample_value = sample_data[sample].value
                        cofactors[cofactor_name].append(sample_value)
                    else:
                        cofactors[cofactor_name].append("NA")
    return cofactors