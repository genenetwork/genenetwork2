import os
import math
import string
import random
import json

from base import webqtlConfig
from base.trait import create_trait
from base.data_set import create_dataset
from utility.tools import flat_files
from utility.tools import GEMMA_WRAPPER_COMMAND
from utility.tools import TEMPDIR
from utility.tools import WEBSERVER_MODE

import utility.logger
logger = utility.logger.getLogger(__name__)

GEMMAOPTS = "-debug"
if WEBSERVER_MODE == 'PROD':
    GEMMAOPTS = "-no-check"


def generate_random_n_string(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(n))


def run_gemma(this_trait, this_dataset, samples, vals, covariates, use_loco,
              maf=0.01, first_run=True, output_files=None):
    """Generates p-values for each marker using GEMMA"""
    if this_dataset.group.genofile is not None:
        genofile_name = this_dataset.group.genofile[:-5]
    else:
        genofile_name = this_dataset.group.name

    if first_run:
        trait_filename = (f"{str(this_dataset.group.name)}_"
                          f"{str(this_trait.name)}_"
                          f"{generate_random_n_string(6)}")
        gen_pheno_txt_file(this_dataset, genofile_name, vals, trait_filename)

        if not os.path.isfile(f"{webqtlConfig.GENERATED_IMAGE_DIR}"
                              f"{genofile_name}_output.assoc.txt"):
            open((f"{webqtlConfig.GENERATED_IMAGE_DIR}"
                  f"{genofile_name}_output.assoc.txt"),
                 "w+")

        k_output_filename = (f"{this_dataset.group.name}_K_"
                             f"{generate_random_n_string(6)}")
        gwa_output_filename = (f"{this_dataset.group.name}_GWA_"
                               f"{generate_random_n_string(6)}")

        this_chromosomes = this_dataset.species.chromosomes.chromosomes
        this_chromosomes_name = [this_chromosomes[chromosome].name
                                 for chromosome in this_chromosomes]

        chr_list_string = ",".join(this_chromosomes_name)
        if covariates != "":
            gen_covariates_file(this_dataset, covariates, samples)
        if use_loco == "True":
            generate_k_command = (f"{GEMMA_WRAPPER_COMMAND} --json --loco "
                                  f"{chr_list_string} -- {GEMMAOPTS} "
                                  f"-g {flat_files('genotype/bimbam')}/"
                                  f"{genofile_name}_geno.txt -p "
                                  f"{TEMPDIR}/gn2/{trait_filename}.txt -a "
                                  f"{flat_files('genotype/bimbam')}/"
                                  f"{genofile_name}_snps.txt -gk > "
                                  f"{TEMPDIR}/gn2/{k_output_filename}.json")
            os.system(generate_k_command)

            gemma_command = (f"{GEMMA_WRAPPER_COMMAND} --json --loco "
                             f"--input {TEMPDIR}/gn2/{k_output_filename}.json "
                             f"-- {GEMMAOPTS} "
                             f"-g {flat_files('genotype/bimbam')}/"
                             f"{genofile_name}_geno.txt "
                             f"-p {TEMPDIR}/gn2/{trait_filename}.txt ")
            if covariates != "":
                gemma_command += (f"-c {flat_files('mapping')}/"
                                  f"{this_dataset.group.name}_covariates.txt "
                                  f"-a {flat_files('genotype/bimbam')}/"
                                  f"{genofile_name}_snps.txt "
                                  f"-lmm 9 -maf {maf} > {TEMPDIR}/gn2/"
                                  f"{gwa_output_filename}.json")
            else:
                gemma_command += (f"-a {flat_files('genotype/bimbam')}/"
                                  f"{genofile_name}_snps.txt -lmm 9 -maf "
                                  f"{maf} > "
                                  f"{TEMPDIR}/gn2/{gwa_output_filename}.json")

        else:
            generate_k_command = (f"{GEMMA_WRAPPER_COMMAND} --json -- "
                                  f"{GEMMAOPTS} "
                                  f" -g {flat_files('genotype/bimbam')}/"
                                  f"{genofile_name}_geno.txt -p "
                                  f"{TEMPDIR}/gn2/{trait_filename}.txt -a "
                                  f"{flat_files('genotype/bimbam')}/"
                                  f"{genofile_name}_snps.txt -gk > "
                                  f"{TEMPDIR}/gn2/{k_output_filename}.json")

            os.system(generate_k_command)

            gemma_command = (f"{GEMMA_WRAPPER_COMMAND} --json --input "
                             f"{TEMPDIR}/gn2/{k_output_filename}.json -- "
                             f"{GEMMAOPTS} "
                             f"-a {flat_files('genotype/bimbam')}/"
                             f"{genofile_name}_snps.txt "
                             f"-lmm 9 -g {flat_files('genotype/bimbam')}/"
                             f"{genofile_name}_geno.txt -p "
                             f"{TEMPDIR}/gn2/{trait_filename}.txt ")

            if covariates != "":
                gemma_command += (f" -c {flat_files('mapping')}/"
                                  f"{this_dataset.group.name}"
                                  f"_covariates.txt > "
                                  f"{TEMPDIR}/gn2/{gwa_output_filename}.json")
            else:
                gemma_command += f" > {TEMPDIR}/gn2/{gwa_output_filename}.json"

        os.system(gemma_command)
    else:
        gwa_output_filename = output_files

    if use_loco == "True":
        marker_obs = parse_loco_output(this_dataset, gwa_output_filename)
        return marker_obs, gwa_output_filename
    else:
        marker_obs = parse_loco_output(
            this_dataset, gwa_output_filename, use_loco)
        return marker_obs, gwa_output_filename


def gen_pheno_txt_file(this_dataset, genofile_name, vals, trait_filename):
    """Generates phenotype file for GEMMA"""

    with open(f"{TEMPDIR}/gn2/{trait_filename}.txt", "w") as outfile:
        for value in vals:
            if value == "x":
                outfile.write("NA\n")
            else:
                outfile.write(value + "\n")


def gen_covariates_file(this_dataset, covariates, samples):
    covariate_list = covariates.split(",")
    covariate_data_object = []
    for covariate in covariate_list:
        this_covariate_data = []
        trait_name = covariate.split(":")[0]
        dataset_name = covariate.split(":")[1]
        if dataset_name == "Temp":
            temp_group = trait_name.split("_")[2]
            dataset_ob = create_dataset(dataset_name="Temp", dataset_type="Temp", group_name = temp_group)
        else:
            dataset_ob = create_dataset(covariate.split(":")[1])
        trait_ob = create_trait(dataset=dataset_ob,
                                name=trait_name,
                                cellid=None)
        this_dataset.group.get_samplelist()
        trait_samples = this_dataset.group.samplelist
        trait_sample_data = trait_ob.data
        for index, sample in enumerate(trait_samples):
            if sample in samples:
                if sample in trait_sample_data:
                    sample_value = trait_sample_data[sample].value
                    this_covariate_data.append(sample_value)
                else:
                    this_covariate_data.append("-9")
        covariate_data_object.append(this_covariate_data)

    with open((f"{flat_files('mapping')}/"
               f"{this_dataset.group.name}_covariates.txt"),
              "w") as outfile:
        for i in range(len(covariate_data_object[0])):
            for this_covariate in covariate_data_object:
                outfile.write(str(this_covariate[i]) + "\t")
            outfile.write("\n")


def parse_loco_output(this_dataset, gwa_output_filename, loco="True"):

    output_filelist = []
    with open(f"{TEMPDIR}/gn2/{gwa_output_filename}.json") as data_file:
        data = json.load(data_file)

    files = data['files']
    for file in files:
        output_filelist.append(file[2])

    included_markers = []
    p_values = []
    marker_obs = []
    previous_chr = 0

    for this_file in output_filelist:
        if not os.path.isfile(this_file):
            break
        with open(this_file) as output_file:
            for line in output_file:
                if line.startswith("chr\t"):
                    continue
                else:
                    marker = {}
                    marker['name'] = line.split("\t")[1]
                    if line.split("\t")[0] != "X" and line.split("\t")[0] != "X/Y" and line.split("\t")[0] != "Y" and line.split("\t")[0] != "M":
                        if "chr" in line.split("\t")[0]:
                            marker['chr'] = int(line.split("\t")[0][3:])
                        else:
                            marker['chr'] = int(line.split("\t")[0])
                        if marker['chr'] > int(previous_chr):
                            previous_chr = marker['chr']
                        elif marker['chr'] < int(previous_chr):
                            break
                    else:
                        marker['chr'] = line.split("\t")[0]
                    marker['Mb'] = float(line.split("\t")[2]) / 1000000
                    marker['p_value'] = float(line.split("\t")[10])
                    marker['additive'] = float(line.split("\t")[7])
                    if math.isnan(marker['p_value']) or (marker['p_value'] <= 0):
                        marker['lod_score'] = 0
                    else:
                        marker['lod_score'] = -math.log10(marker['p_value'])
                    marker_obs.append(marker)

                    included_markers.append(line.split("\t")[1])
                    p_values.append(float(line.split("\t")[9]))

    return marker_obs
