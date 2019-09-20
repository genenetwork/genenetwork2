import os, math, string, random, json

from base import webqtlConfig
from base.trait import GeneralTrait
from base.data_set import create_dataset
from utility.tools import flat_files, GEMMA_COMMAND, GEMMA_WRAPPER_COMMAND, TEMPDIR, WEBSERVER_MODE

import utility.logger
logger = utility.logger.getLogger(__name__ )

GEMMAOPTS = "-debug"
if WEBSERVER_MODE == 'PROD':
  GEMMAOPTS = "-no-check"

def run_gemma(this_trait, this_dataset, samples, vals, covariates, use_loco, maf=0.01, first_run=True, output_files=None):
    """Generates p-values for each marker using GEMMA"""

    if this_dataset.group.genofile != None:
        genofile_name = this_dataset.group.genofile[:-5]
    else:
        genofile_name = this_dataset.group.name

    if first_run:
      trait_filename = str(this_trait.name) + "_" + str(this_dataset.name) + "_pheno"
      gen_pheno_txt_file(this_dataset, genofile_name, vals, trait_filename)

      if not os.path.isfile("{}{}_output.assoc.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, genofile_name)):
          open("{}{}_output.assoc.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, genofile_name), "w+")

      k_output_filename = this_dataset.group.name + "_K_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
      gwa_output_filename = this_dataset.group.name + "_GWA_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

      this_chromosomes = this_dataset.species.chromosomes.chromosomes
      chr_list_string = ""
      for i in range(len(this_chromosomes)):
          if i < (len(this_chromosomes) - 1):
              chr_list_string += this_chromosomes[i+1].name + ","
          else:
              chr_list_string += this_chromosomes[i+1].name

      if covariates != "":
          gen_covariates_file(this_dataset, covariates)

      if use_loco == "True":
          generate_k_command = GEMMA_WRAPPER_COMMAND + ' --json --loco ' + chr_list_string + ' -- ' + GEMMAOPTS + ' -g %s/%s_geno.txt -p %s/gn2/%s.txt -a %s/%s_snps.txt -gk > %s/gn2/%s.json' % (flat_files('genotype/bimbam'),
                                                                                          genofile_name,
                                                                                          TEMPDIR,
                                                                                          trait_filename,
                                                                                          flat_files('genotype/bimbam'),
                                                                                          genofile_name,
                                                                                          TEMPDIR,
                                                                                          k_output_filename)
          logger.debug("k_command:" + generate_k_command)
          os.system(generate_k_command)

          gemma_command = GEMMA_WRAPPER_COMMAND + ' --json --loco --input %s/gn2/%s.json -- ' % (TEMPDIR, k_output_filename) + GEMMAOPTS + ' -g %s/%s_geno.txt -p %s/gn2/%s.txt' % (flat_files('genotype/bimbam'),
                                                                                          genofile_name,
                                                                                          TEMPDIR,
                                                                                          trait_filename)
          if covariates != "":
              gemma_command += ' -c %s/%s_covariates.txt -a %s/%s_snps.txt -lmm 2 -maf %s > %s/gn2/%s.json' % (flat_files('mapping'),
                                                                                                                this_dataset.group.name,
                                                                                                                flat_files('genotype/bimbam'),
                                                                                                                genofile_name,
                                                                                                                maf,
                                                                                                                TEMPDIR,
                                                                                                                gwa_output_filename)
          else:
              gemma_command += ' -a %s/%s_snps.txt -lmm 2 -maf %s > %s/gn2/%s.json' % (flat_files('genotype/bimbam'),
                                                                                                               genofile_name,
                                                                                                               maf,
                                                                                                               TEMPDIR,
                                                                                                               gwa_output_filename)

      else:
          generate_k_command = GEMMA_WRAPPER_COMMAND + ' --json -- ' + GEMMAOPTS + ' -g %s/%s_geno.txt -p %s/gn2/%s.txt -a %s/%s_snps.txt -gk > %s/gn2/%s.json' % (flat_files('genotype/bimbam'),
                                                                                         genofile_name,
                                                                                         TEMPDIR,
                                                                                         trait_filename,
                                                                                         flat_files('genotype/bimbam'),
                                                                                         genofile_name,
                                                                                         TEMPDIR,
                                                                                         k_output_filename)

          logger.debug("k_command:" + generate_k_command)
          os.system(generate_k_command)

          gemma_command = GEMMA_WRAPPER_COMMAND + ' --json --input %s/gn2/%s.json -- ' % (TEMPDIR, k_output_filename) + GEMMAOPTS + ' -a %s/%s_snps.txt -lmm 2 -g %s/%s_geno.txt -p %s/gn2/%s.txt' % (flat_files('genotype/bimbam'),
                                                                                         genofile_name,
                                                                                         flat_files('genotype/bimbam'),
                                                                                         genofile_name,
                                                                                         TEMPDIR,
                                                                                         trait_filename)


          if covariates != "":
              gemma_command += ' -c %s/%s_covariates.txt > %s/gn2/%s.json' % (flat_files('mapping'), this_dataset.group.name, TEMPDIR, gwa_output_filename)
          else:
              gemma_command += ' > %s/gn2/%s.json' % (TEMPDIR, gwa_output_filename)


      logger.debug("gemma_command:" + gemma_command)
      os.system(gemma_command)
    else:
      gwa_output_filename = output_files

    if use_loco == "True":
        marker_obs = parse_loco_output(this_dataset, gwa_output_filename)
        return marker_obs, gwa_output_filename
    else:
        marker_obs = parse_loco_output(this_dataset, gwa_output_filename)
        return marker_obs, gwa_output_filename

def gen_pheno_txt_file(this_dataset, genofile_name, vals, trait_filename):
    """Generates phenotype file for GEMMA"""

    current_file_data = []
    with open("{}/gn2/{}.txt".format(TEMPDIR, trait_filename), "w") as outfile:
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

    with open("{}{}_output.assoc.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, genofile_name)) as output_file:
        for line in output_file:
            if line.startswith("chr\t"):
                continue
            else:
                marker = {}
                marker['name'] = line.split("\t")[1]
                if line.split("\t")[0] != "X" and line.split("\t")[0] != "X/Y":
                    if "chr" in line.split("\t")[0]:
                        marker['chr'] = int(line.split("\t")[0][3:])
                    else:
                        marker['chr'] = int(line.split("\t")[0])
                else:
                    marker['chr'] = line.split("\t")[0]
                marker['Mb'] = float(line.split("\t")[2]) / 1000000
                marker['p_value'] = float(line.split("\t")[9])
                if math.isnan(marker['p_value']) or (marker['p_value'] <= 0):
                    marker['lod_score'] = 0
                    #marker['lrs_value'] = 0
                else:
                    marker['lod_score'] = -math.log10(marker['p_value'])
                    #marker['lrs_value'] = -math.log10(marker['p_value']) * 4.61
                marker_obs.append(marker)

                included_markers.append(line.split("\t")[1])
                p_values.append(float(line.split("\t")[9]))

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

    no_results = False
    for this_file in output_filelist:
        if not os.path.isfile(this_file):
            no_results = True
            break
        with open(this_file) as output_file:
            for line in output_file:
                if line.startswith("chr\t"):
                    continue
                else:
                    marker = {}
                    marker['name'] = line.split("\t")[1]
                    if line.split("\t")[0] != "X" and line.split("\t")[0] != "X/Y":
                        if "chr" in line.split("\t")[0]:
                            marker['chr'] = int(line.split("\t")[0][3:])
                        else:
                            marker['chr'] = int(line.split("\t")[0])
                        if marker['chr'] > previous_chr:
                            previous_chr = marker['chr']
                        elif marker['chr'] < previous_chr:
                            break
                    else:
                        marker['chr'] = line.split("\t")[0]
                    marker['Mb'] = float(line.split("\t")[2]) / 1000000
                    marker['p_value'] = float(line.split("\t")[9])
                    if math.isnan(marker['p_value']) or (marker['p_value'] <= 0):
                        marker['lod_score'] = 0
                        #marker['lrs_value'] = 0
                    else:
                        marker['lod_score'] = -math.log10(marker['p_value'])
                        #marker['lrs_value'] = -math.log10(marker['p_value']) * 4.61
                    marker_obs.append(marker)

                    included_markers.append(line.split("\t")[1])
                    p_values.append(float(line.split("\t")[9]))

    return marker_obs
