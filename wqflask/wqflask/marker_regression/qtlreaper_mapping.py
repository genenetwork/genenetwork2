import os, math, string, random, json, re

from base import webqtlConfig
from base.trait import GeneralTrait
from base.data_set import create_dataset
from utility.tools import flat_files, REAPER_COMMAND, TEMPDIR

import utility.logger
logger = utility.logger.getLogger(__name__ )

def run_reaper(this_trait, this_dataset, samples, vals, json_data, num_perm, boot_check, num_bootstrap, do_control, control_marker, manhattan_plot, first_run=True, output_files=None):
    """Generates p-values for each marker using qtlreaper"""

    if first_run:
        if this_dataset.group.genofile != None:
            genofile_name = this_dataset.group.genofile[:-5]
        else:
            genofile_name = this_dataset.group.name

        trait_filename = str(this_trait.name) + "_" + str(this_dataset.name) + "_pheno"
        gen_pheno_txt_file(samples, vals, trait_filename)

        output_filename = this_dataset.group.name + "_GWA_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        bootstrap_filename = None
        permu_filename = None

        opt_list = []
        if boot_check and num_bootstrap > 0:
            bootstrap_filename = this_dataset.group.name + "_BOOTSTRAP_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

            opt_list.append("-b")
            opt_list.append("--n_bootstrap " + str(num_bootstrap))
            opt_list.append("--bootstrap_output " + webqtlConfig.GENERATED_IMAGE_DIR + bootstrap_filename + ".txt")
        if num_perm > 0:
            permu_filename = this_dataset.group.name + "_PERM_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            opt_list.append("-n " + str(num_perm))
            opt_list.append("--permu_output " + webqtlConfig.GENERATED_IMAGE_DIR + permu_filename + ".txt")
        if control_marker != "" and do_control == "true":
            opt_list.append("-c " + control_marker)

        reaper_command = REAPER_COMMAND + ' --geno {0}/{1}.geno --traits {2}/gn2/{3}.txt {4} -o {5}{6}.txt'.format(flat_files('genotype'),
                                                                                                                genofile_name,
                                                                                                                TEMPDIR,
                                                                                                                trait_filename,
                                                                                                                " ".join(opt_list),
                                                                                                                webqtlConfig.GENERATED_IMAGE_DIR,
                                                                                                                output_filename)

        logger.debug("reaper_command:" + reaper_command)
        os.system(reaper_command)
    else:
        output_filename, permu_filename, bootstrap_filename = output_files

    marker_obs, permu_vals, bootstrap_vals = parse_reaper_output(output_filename, permu_filename, bootstrap_filename)

    suggestive = 0
    significant = 0
    if len(permu_vals) > 0:
        suggestive = permu_vals[int(num_perm*0.37-1)]
        significant = permu_vals[int(num_perm*0.95-1)]

    return marker_obs, permu_vals, suggestive, significant, bootstrap_vals, [output_filename, permu_filename, bootstrap_filename]

def gen_pheno_txt_file(samples, vals, trait_filename):
    """Generates phenotype file for GEMMA"""

    with open("{}/gn2/{}.txt".format(TEMPDIR, trait_filename), "w") as outfile:
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

    with open("{}{}.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, gwa_filename)) as output_file:
        for line in output_file:
            if line.startswith("ID\t"):
                continue
            else:
                marker = {}
                marker['name'] = line.split("\t")[1]
                try:
                    marker['chr'] = int(line.split("\t")[2])
                except:
                    marker['chr'] = line.split("\t")[2]
                marker['cM'] = float(line.split("\t")[3])
                marker['Mb'] = float(line.split("\t")[4])
                if float(line.split("\t")[7]) != 1:
                    marker['p_value'] = float(line.split("\t")[7])
                marker['lrs_value'] = float(line.split("\t")[5])
                marker['lod_score'] = marker['lrs_value'] / 4.61
                marker['additive'] = float(line.split("\t")[6])
                marker_obs.append(marker)

    #ZS: Results have to be reordered because the new reaper returns results sorted alphabetically by chr for some reason, resulting in chr 1 being followed by 10, etc
    sorted_indices = natural_sort(marker_obs)

    permu_vals = []
    if permu_filename:
        with open("{}{}.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, permu_filename)) as permu_file:
            for line in permu_file:
                permu_vals.append(float(line))

    bootstrap_vals = []
    if bootstrap_filename:
        with open("{}{}.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, bootstrap_filename)) as bootstrap_file:
            for line in bootstrap_file:
                bootstrap_vals.append(int(line))

    marker_obs = [marker_obs[i] for i in sorted_indices]
    bootstrap_vals = [bootstrap_vals[i] for i in sorted_indices]

    return marker_obs, permu_vals, bootstrap_vals

def run_original_reaper(this_trait, dataset, samples_before, trait_vals, json_data, num_perm, bootCheck, num_bootstrap, do_control, control_marker, manhattan_plot):
    genotype = dataset.group.read_genotype_file(use_reaper=True)

    if manhattan_plot != True:
        genotype = genotype.addinterval()

    trimmed_samples = []
    trimmed_values = []
    for i in range(0, len(samples_before)):
        try:
            trimmed_values.append(float(trait_vals[i]))
            trimmed_samples.append(str(samples_before[i]))
        except:
            pass

    perm_output = []
    bootstrap_results = []

    if num_perm < 100:
        suggestive = 0
        significant = 0
    else:
        perm_output = genotype.permutation(strains = trimmed_samples, trait = trimmed_values, nperm=num_perm)
        suggestive = perm_output[int(num_perm*0.37-1)]
        significant = perm_output[int(num_perm*0.95-1)]
        #highly_significant = perm_output[int(num_perm*0.99-1)] #ZS: Currently not used, but leaving it here just in case

    json_data['suggestive'] = suggestive
    json_data['significant'] = significant

    if control_marker != "" and do_control == "true":
        reaper_results = genotype.regression(strains = trimmed_samples,
                                             trait = trimmed_values,
                                             control = str(control_marker))
        if bootCheck:
            control_geno = []
            control_geno2 = []
            _FIND = 0
            for _chr in genotype:
                for _locus in _chr:
                    if _locus.name == control_marker:
                        control_geno2 = _locus.genotype
                        _FIND = 1
                        break
                if _FIND:
                    break
            if control_geno2:
                _prgy = list(genotype.prgy)
                for _strain in trimmed_samples:
                    _idx = _prgy.index(_strain)
                    control_geno.append(control_geno2[_idx])

            bootstrap_results = genotype.bootstrap(strains = trimmed_samples,
                                                        trait = trimmed_values,
                                                        control = control_geno,
                                                        nboot = num_bootstrap)
    else:
        reaper_results = genotype.regression(strains = trimmed_samples,
                                             trait = trimmed_values)

        if bootCheck:
            bootstrap_results = genotype.bootstrap(strains = trimmed_samples,
                                                        trait = trimmed_values,
                                                        nboot = num_bootstrap)

    json_data['chr'] = []
    json_data['pos'] = []
    json_data['lod.hk'] = []
    json_data['markernames'] = []
    #if self.additive:
    #    self.json_data['additive'] = []

    #Need to convert the QTL objects that qtl reaper returns into a json serializable dictionary
    qtl_results = []
    for qtl in reaper_results:
        reaper_locus = qtl.locus
        #ZS: Convert chr to int
        converted_chr = reaper_locus.chr
        if reaper_locus.chr != "X" and reaper_locus.chr != "X/Y":
            converted_chr = int(reaper_locus.chr)
        json_data['chr'].append(converted_chr)
        json_data['pos'].append(reaper_locus.Mb)
        json_data['lod.hk'].append(qtl.lrs)
        json_data['markernames'].append(reaper_locus.name)
        #if self.additive:
        #    self.json_data['additive'].append(qtl.additive)
        locus = {"name":reaper_locus.name, "chr":reaper_locus.chr, "cM":reaper_locus.cM, "Mb":reaper_locus.Mb}
        qtl = {"lrs_value": qtl.lrs, "chr":converted_chr, "Mb":reaper_locus.Mb,
               "cM":reaper_locus.cM, "name":reaper_locus.name, "additive":qtl.additive, "dominance":qtl.dominance}
        qtl_results.append(qtl)
    return qtl_results, json_data, perm_output, suggestive, significant, bootstrap_results

def natural_sort(marker_list):
    """
    Function to naturally sort numbers + strings, adopted from user Mark Byers here: https://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
    Changed to return indices instead of values, though, since the same reordering needs to be applied to bootstrap results
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', str(marker_list[key]['chr'])) ]
    return sorted(range(len(marker_list)), key = alphanum_key)