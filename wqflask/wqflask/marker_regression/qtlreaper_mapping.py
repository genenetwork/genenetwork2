import os
import math
import string
import random
import json
import re

from base import webqtlConfig
from base.trait import GeneralTrait
from base.data_set import create_dataset
from utility.tools import flat_files, get_setting


def run_reaper(this_trait, this_dataset, samples, vals, json_data, num_perm, boot_check, num_bootstrap, do_control, control_marker, manhattan_plot, first_run=True, output_files=None):
    """Generates p-values for each marker using qtlreaper"""

    if first_run:
        if this_dataset.group.genofile != None:
            genofile_name = this_dataset.group.genofile[:-5]
        else:
            genofile_name = this_dataset.group.name

        trait_filename = f"{str(this_trait.name)}_{str(this_dataset.name)}_pheno"
        gen_pheno_txt_file(samples, vals, trait_filename)

        output_filename = (f"{this_dataset.group.name}_GWA_"
                           + ''.join(random.choice(string.ascii_uppercase + string.digits)
                                     for _ in range(6))
                           )
        bootstrap_filename = None
        permu_filename = None

        opt_list = []
        if boot_check and num_bootstrap > 0:
            bootstrap_filename = (f"{this_dataset.group.name}_BOOTSTRAP_"
                                  + ''.join(random.choice(string.ascii_uppercase + string.digits)
                                            for _ in range(6))
                                  )

            opt_list.append("-b")
            opt_list.append(f"--n_bootstrap {str(num_bootstrap)}")
            opt_list.append(
                f"--bootstrap_output {webqtlConfig.GENERATED_IMAGE_DIR}{bootstrap_filename}.txt")
        if num_perm > 0:
            permu_filename = ("{this_dataset.group.name}_PERM_"
                              + ''.join(random.choice(string.ascii_uppercase
                                                      + string.digits) for _ in range(6))
                              )
            opt_list.append("-n " + str(num_perm))
            opt_list.append(
                "--permu_output " + webqtlConfig.GENERATED_IMAGE_DIR + permu_filename + ".txt")
        if control_marker != "" and do_control == "true":
            opt_list.append("-c " + control_marker)
        if manhattan_plot != True:
            opt_list.append("--interval 1")

        reaper_command = (get_setting(app, 'REAPER_COMMAND') +
                          ' --geno {0}/{1}.geno --traits {2}/gn2/{3}.txt {4} -o {5}{6}.txt'.format(flat_files(app, 'genotype'),

                                                                                                   genofile_name,
                                                                                                   get_setting(app, 'TEMPDIR'),
                                                                                                   trait_filename,
                                                                                                   " ".join(
                              opt_list),
                              webqtlConfig.GENERATED_IMAGE_DIR,
                              output_filename))
        os.system(reaper_command)
    else:
        output_filename, permu_filename, bootstrap_filename = output_files

    marker_obs, permu_vals, bootstrap_vals = parse_reaper_output(
        output_filename, permu_filename, bootstrap_filename)

    suggestive = 0
    significant = 0
    if len(permu_vals) > 0:
        suggestive = permu_vals[int(num_perm * 0.37 - 1)]
        significant = permu_vals[int(num_perm * 0.95 - 1)]

    return (marker_obs, permu_vals, suggestive, significant, bootstrap_vals,
            [output_filename, permu_filename, bootstrap_filename])


def gen_pheno_txt_file(samples, vals, trait_filename):
    """Generates phenotype file for GEMMA"""

    with open(f"{get_setting(app, 'TEMPDIR')}/gn2/{trait_filename}.txt", "w") as outfile:
        outfile.write("Trait\t")

        filtered_sample_list = []
        filtered_vals_list = []
        for i, sample in enumerate(samples):
            if vals[i] != "x":
                filtered_sample_list.append(sample)
                filtered_vals_list.append(vals[i])

        samples_string = "\t".join(filtered_sample_list)
        outfile.write(samples_string + "\n")
        outfile.write("T1\t")
        values_string = "\t".join(filtered_vals_list)
        outfile.write(values_string)


def parse_reaper_output(gwa_filename, permu_filename, bootstrap_filename):
    included_markers = []
    p_values = []
    marker_obs = []

    only_cm = False
    only_mb = False

    with open(f"{webqtlConfig.GENERATED_IMAGE_DIR}{gwa_filename}.txt") as output_file:
        for line in output_file:
            if line.startswith("ID\t"):
                if len(line.split("\t")) < 8:
                    if 'cM' in line.split("\t"):
                        only_cm = True
                    else:
                        only_mb = True
                continue
            else:
                marker = {}
                marker['name'] = line.split("\t")[1]
                try:
                    marker['chr'] = int(line.split("\t")[2])
                except:
                    marker['chr'] = line.split("\t")[2]
                if only_cm or only_mb:
                    if only_cm:
                        marker['cM'] = float(line.split("\t")[3])
                    else:
                        if float(line.split("\t")[3]) > 1000:
                            marker['Mb'] = float(line.split("\t")[3]) / 1000000
                        else:
                            marker['Mb'] = float(line.split("\t")[3])
                    if float(line.split("\t")[6]) != 1:
                        marker['p_value'] = float(line.split("\t")[6])
                    marker['lrs_value'] = float(line.split("\t")[4])
                    marker['lod_score'] = marker['lrs_value'] / 4.61
                    marker['additive'] = float(line.split("\t")[5])
                else:
                    marker['cM'] = float(line.split("\t")[3])
                    if float(line.split("\t")[4]) > 1000:
                        marker['Mb'] = float(line.split("\t")[4]) / 1000000
                    else:
                        marker['Mb'] = float(line.split("\t")[4])
                    if float(line.split("\t")[7]) != 1:
                        marker['p_value'] = float(line.split("\t")[7])
                    marker['lrs_value'] = float(line.split("\t")[5])
                    marker['lod_score'] = marker['lrs_value'] / 4.61
                    marker['additive'] = float(line.split("\t")[6])
                marker_obs.append(marker)

    # ZS: Results have to be reordered because the new reaper returns results sorted alphabetically by chr for some reason, resulting in chr 1 being followed by 10, etc
    sorted_indices = natural_sort(marker_obs)

    permu_vals = []
    if permu_filename:
        with open(f"{webqtlConfig.GENERATED_IMAGE_DIR}{permu_filename}.txt") as permu_file:
            for line in permu_file:
                permu_vals.append(float(line))

    bootstrap_vals = []
    if bootstrap_filename:
        with open(f"{webqtlConfig.GENERATED_IMAGE_DIR}{bootstrap_filename}.txt") as bootstrap_file:
            for line in bootstrap_file:
                bootstrap_vals.append(int(line))

    marker_obs = [marker_obs[i] for i in sorted_indices]
    if len(bootstrap_vals) > 0:
        bootstrap_vals = [bootstrap_vals[i] for i in sorted_indices]

    return marker_obs, permu_vals, bootstrap_vals


def natural_sort(marker_list):
    """
    Function to naturally sort numbers + strings, adopted from user Mark Byers here: https://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
    Changed to return indices instead of values, though, since the same reordering needs to be applied to bootstrap results
    """

    def convert(text):
        if text.isdigit():
            return int(text)
        else:
            if text != "M":
                return text.lower()
            else:
                return "z"

    alphanum_key = lambda key: [convert(c) for c in re.split(
        '([0-9]+)', str(marker_list[key]['chr']))]
    return sorted(list(range(len(marker_list))), key=alphanum_key)
