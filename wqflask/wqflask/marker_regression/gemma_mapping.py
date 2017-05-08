import os, math

from base import webqtlConfig
from utility.tools import flat_files, GEMMA_COMMAND

def run_gemma(this_dataset, samples, vals):
    """Generates p-values for each marker using GEMMA"""

    print("INSIDE GEMMA_MAPPING")

    gen_pheno_txt_file(this_dataset, vals)

    # use GEMMA_RUN in the next one, create a unique temp file

    gemma_command = GEMMA_COMMAND + ' -bfile %s/%s -k %s/%s.sXX.txt -lmm 1 -maf 0.1 -outdir %s -o %s_output' % (flat_files('mapping'),
                                                                                    this_dataset.group.name,
                                                                                    flat_files('mapping'),
                                                                                    this_dataset.group.name,
                                                                                    webqtlConfig.GENERATED_IMAGE_DIR,
                                                                                    this_dataset.group.name)
    print("gemma_command:" + gemma_command)

    os.system(gemma_command)

    marker_obs = parse_gemma_output(this_dataset)

    return marker_obs

def gen_pheno_txt_file(this_dataset, vals):
    """Generates phenotype file for GEMMA"""

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

def parse_gemma_output(this_dataset):
    included_markers = []
    p_values = []
    marker_obs = []
    with open("{}{}_output.assoc.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, this_dataset.group.name)) as output_file:
        for line in output_file:
            if line.startswith("chr"):
                continue
            else:
                marker = {}
                marker['name'] = line.split("\t")[1]
                marker['chr'] = int(line.split("\t")[0])
                marker['Mb'] = float(line.split("\t")[2]) / 1000000
                marker['p_value'] = float(line.split("\t")[10])
                if math.isnan(marker['p_value']) or (marker['p_value'] <= 0):
                    marker['lod_score'] = 0
                    #marker['lrs_value'] = 0
                else:
                    marker['lod_score'] = -math.log10(marker['p_value'])
                    #marker['lrs_value'] = -math.log10(marker['p_value']) * 4.61
                marker_obs.append(marker)

                included_markers.append(line.split("\t")[1])
                p_values.append(float(line.split("\t")[10]))

    return marker_obs
