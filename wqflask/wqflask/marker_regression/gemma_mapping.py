import os, math, string, random, json

from base import webqtlConfig
from base.trait import GeneralTrait
from base.data_set import create_dataset
from utility.tools import flat_files, GEMMA_COMMAND, GEMMA_WRAPPER_COMMAND, TEMPDIR

import utility.logger
logger = utility.logger.getLogger(__name__ )

def run_gemma(this_dataset, samples, vals, covariates, method, use_loco):
    """Generates p-values for each marker using GEMMA"""

    if this_dataset.group.genofile != None:
        genofile_name = this_dataset.group.genofile[:-5]
    else:
        genofile_name = this_dataset.group.name

    gen_pheno_txt_file(this_dataset, genofile_name, vals, method)

    if not os.path.isfile("{}{}_output.assoc.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, genofile_name)):
        open("{}{}_output.assoc.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, genofile_name), "w+")

    this_chromosomes = this_dataset.species.chromosomes.chromosomes
    chr_list_string = ""
    for i in range(len(this_chromosomes)):
        if i < (len(this_chromosomes) - 1):
            chr_list_string += this_chromosomes[i+1].name + ","
        else:
            chr_list_string += this_chromosomes[i+1].name

    if covariates != "":
        gen_covariates_file(this_dataset, covariates)

    if method == "gemma_plink":
        gemma_command = GEMMA_COMMAND + ' -bfile %s/%s -k %s/%s.cXX.txt -lmm 1 -maf 0.1' % (flat_files('mapping'),
                                                                                        this_dataset.group.name,
                                                                                        flat_files('mapping'),
                                                                                        this_dataset.group.name)
        if covariates != "":
            gemma_command += ' -c %s/%s_covariates.txt -outdir %s -o %s_output' % (flat_files('mapping'),
                                                                                   this_dataset.group.name,
                                                                                   webqtlConfig.GENERATED_IMAGE_DIR,
                                                                                   this_dataset.group.name)
        else:
            #gemma_command = GEMMA_COMMAND + ' -bfile %s/%s -k %s/%s.sXX.txt -lmm 1 -maf 0.1 -o %s_output' % (flat_files('mapping'),
            gemma_command += ' -outdir %s -o %s_output' % (webqtlConfig.GENERATED_IMAGE_DIR,
                                                           this_dataset.group.name)
    else:
        if use_loco == "True":
            k_output_filename = this_dataset.group.name + "_K_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            generate_k_command = GEMMA_WRAPPER_COMMAND + ' --json --loco ' + chr_list_string + ' -- -g %s/%s_geno.txt -p %s/%s_pheno.txt -a %s/%s_snps.txt -gk -debug > %s/gn2/%s.json' % (flat_files('genotype/bimbam'),
                                                                                            genofile_name,
                                                                                            flat_files('genotype/bimbam'),
                                                                                            genofile_name,
                                                                                            flat_files('genotype/bimbam'),
                                                                                            genofile_name,
                                                                                            TEMPDIR,
                                                                                            k_output_filename)
            logger.debug("k_command:" + generate_k_command)
            os.system(generate_k_command)

            gemma_command = GEMMA_WRAPPER_COMMAND + ' --json --loco --input %s/gn2/%s.json -- -g %s/%s_geno.txt -p %s/%s_pheno.txt' % (TEMPDIR,
                                                                                            k_output_filename,
                                                                                            flat_files('genotype/bimbam'),
                                                                                            genofile_name,
                                                                                            flat_files('genotype/bimbam'),
                                                                                            genofile_name)

            gwa_output_filename = this_dataset.group.name + "_GWA_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            if covariates != "":
                gemma_command += ' -c %s/%s_covariates.txt -a %s/%s_snps.txt -lmm 1 -maf 0.1 -debug > %s/gn2/%s.json' % (flat_files('mapping'),
                                                                                                                                         this_dataset.group.name,
                                                                                                                                         flat_files('genotype/bimbam'),
                                                                                                                                         genofile_name,
                                                                                                                                         TEMPDIR,
                                                                                                                                         gwa_output_filename)
            else:
                gemma_command += ' -a %s/%s_snps.txt -lmm 1 -maf 0.1 -debug > %s/gn2/%s.json' % (flat_files('genotype/bimbam'),
                                                                                                                 genofile_name,
                                                                                                                 TEMPDIR,
                                                                                                                 gwa_output_filename)

        else:
            gemma_command = GEMMA_COMMAND + ' -g %s/%s_geno.txt -p %s/%s_pheno.txt -a %s/%s_snps.txt -k %s/%s.cXX.txt -lmm 1 -maf 0.1' % (flat_files('genotype/bimbam'),
                                                                                            genofile_name,
                                                                                            flat_files('genotype/bimbam'),
                                                                                            genofile_name,
                                                                                            flat_files('genotype/bimbam'),
                                                                                            genofile_name,
                                                                                            flat_files('genotype/bimbam'),
                                                                                            genofile_name)

            if covariates != "":
                gemma_command += ' -c %s/%s_covariates.txt -outdir %s -debug -o %s_output' % (flat_files('mapping'),
                                                                                                             this_dataset.group.name,
                                                                                                             webqtlConfig.GENERATED_IMAGE_DIR,
                                                                                                             genofile_name)
            else:
                gemma_command += ' -outdir %s -debug -o %s_output' % (webqtlConfig.GENERATED_IMAGE_DIR,
                                                                      genofile_name)

    logger.debug("gemma_command:" + gemma_command)
    os.system(gemma_command)

    if use_loco == "True":
        marker_obs = parse_loco_output(this_dataset, gwa_output_filename)
    else:
        marker_obs = parse_gemma_output(genofile_name)

    return marker_obs

def gen_pheno_txt_file(this_dataset, genofile_name, vals, method):
    """Generates phenotype file for GEMMA"""

    if method == "gemma_plink":
        current_file_data = []
        with open("{}/{}.fam".format(flat_files('mapping'), this_dataset.group.name), "r") as outfile:
            for i, line in enumerate(outfile):
                split_line = line.split()
                current_file_data.append(split_line)

        with open("{}/{}.fam".format(flat_files('mapping'), this_dataset.group.name), "w") as outfile:
            for i, line in enumerate(current_file_data):
                if vals[i] == "x":
                    this_val = -9
                else:
                    this_val = vals[i]
                outfile.write("0" + " " + line[1] + " " + line[2] + " " + line[3] + " " + line[4] + " " + str(this_val) + "\n")
    else:
        current_file_data = []
        with open("{}/{}_pheno.txt".format(flat_files('genotype/bimbam'), genofile_name), "w") as outfile:
            for value in vals:
                if value == "x":
                    outfile.write("NA\n")
                else:
                    outfile.write(value + "\n")

def gen_covariates_file(this_dataset, covariates):
    covariate_list = covariates.split(",")
    covariate_data_object = []
    for covariate in covariate_list:
        this_covariate_data = []
        trait_name = covariate.split(":")[0]
        dataset_ob = create_dataset(covariate.split(":")[1])
        trait_ob = GeneralTrait(dataset=dataset_ob,
                                name=trait_name,
                                cellid=None)

        #trait_samples = this_dataset.group.all_samples_ordered()
        this_dataset.group.get_samplelist()
        trait_samples = this_dataset.group.samplelist
        logger.debug("SAMPLES:", trait_samples)
        trait_sample_data = trait_ob.data
        logger.debug("SAMPLE DATA:", trait_sample_data)
        for index, sample in enumerate(trait_samples):
            if sample in trait_sample_data:
                sample_value = trait_sample_data[sample].value
                this_covariate_data.append(sample_value)
            else:
                this_covariate_data.append("-9")
        covariate_data_object.append(this_covariate_data)

    with open("{}/{}_covariates.txt".format(flat_files('mapping'), this_dataset.group.name), "w") as outfile:
        for i in range(len(covariate_data_object[0])):
            for this_covariate in covariate_data_object:
                outfile.write(str(this_covariate[i]) + "\t")
            outfile.write("\n")

def parse_gemma_output(genofile_name):
    included_markers = []
    p_values = []
    marker_obs = []
    previous_chr = 0

    #with open("/home/zas1024/gene/wqflask/output/{}_output.assoc.txt".format(this_dataset.group.name)) as output_file:
    with open("{}{}_output.assoc.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, genofile_name)) as output_file:
        for line in output_file:
            if line.startswith("chr"):
                continue
            else:
                marker = {}
                marker['name'] = line.split("\t")[1]
                if line.split("\t")[0] != "X" and line.split("\t")[0] != "X/Y":
                    marker['chr'] = int(line.split("\t")[0])
                else:
                    marker['chr'] = line.split("\t")[0]
                # try:
                    # marker['chr'] = int(line.split("\t")[0])
                # except:
                    # marker['chr'] = previous_chr + 1
                # if marker['chr'] != previous_chr:
                    # previous_chr = marker['chr']
                marker['Mb'] = float(line.split("\t")[2]) / 1000000
                marker['p_value'] = float(line.split("\t")[11])
                if math.isnan(marker['p_value']) or (marker['p_value'] <= 0):
                    marker['lod_score'] = 0
                    #marker['lrs_value'] = 0
                else:
                    marker['lod_score'] = -math.log10(marker['p_value'])
                    #marker['lrs_value'] = -math.log10(marker['p_value']) * 4.61
                marker_obs.append(marker)

                included_markers.append(line.split("\t")[1])
                p_values.append(float(line.split("\t")[11]))

    return marker_obs

def parse_loco_output(this_dataset, gwa_output_filename):

    output_filelist = []
    with open("{}/gn2/".format(TEMPDIR) + gwa_output_filename + ".json") as data_file:
       data = json.load(data_file)

    files = data['files']
    for file in files:
        output_filelist.append(file[2])

    included_markers = []
    p_values = []
    marker_obs = []
    previous_chr = 0

    for this_file in output_filelist:
        #with open("/home/zas1024/gene/wqflask/output/{}_output.assoc.txt".format(this_dataset.group.name)) as output_file:
        with open(this_file) as output_file:
            for line in output_file:
                if line.startswith("chr"):
                    continue
                else:
                    marker = {}
                    marker['name'] = line.split("\t")[1]
                    if line.split("\t")[0] != "X" and line.split("\t")[0] != "X/Y":
                        marker['chr'] = int(line.split("\t")[0])
                    else:
                        marker['chr'] = line.split("\t")[0]
                    marker['Mb'] = float(line.split("\t")[2]) / 1000000
                    marker['p_value'] = float(line.split("\t")[11])
                    if math.isnan(marker['p_value']) or (marker['p_value'] <= 0):
                        marker['lod_score'] = 0
                        #marker['lrs_value'] = 0
                    else:
                        marker['lod_score'] = -math.log10(marker['p_value'])
                        #marker['lrs_value'] = -math.log10(marker['p_value']) * 4.61
                    marker_obs.append(marker)

                    included_markers.append(line.split("\t")[1])
                    p_values.append(float(line.split("\t")[11]))

    return marker_obs