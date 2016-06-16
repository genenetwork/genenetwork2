import os

from base import webqtlConfig
from utility.tools import GEMMA_COMMAND

def run_gemma(this_dataset, samples, vals): 
    """Generates p-values for each marker using GEMMA"""
        
    print("INSIDE GEMMA_MAPPING")

    gen_pheno_txt_file(this_dataset, samples, vals)

    # Don't do this!
    # os.chdir("{}gemma".format(webqtlConfig.GENODIR))

    # use GEMMA_RUN in the next one, create a unique temp file
    
    gemma_command = GEMMA_COMMAND + ' -bfile %s/%s -k %s/output/%s.cXX.txt -lmm 1 -o %s_output' % (GEMMA_PATH,
                                                                                    this_dataset.group.name,
                                                                                    GEMMA_PATH,
                                                                                    this_dataset.group.name,
                                                                                    this_dataset.group.name)
    print("gemma_command:" + gemma_command)
        
    os.system(gemma_command)
        
    included_markers, p_values = parse_gemma_output(this_dataset)

    return included_markers, p_values

def gen_pheno_txt_file(this_dataset, samples, vals):
    """Generates phenotype file for GEMMA"""
                
    with open("{}/{}.fam".format(GEMMA_PATH, this_dataset.group.name), "w") as outfile:
        for i, sample in enumerate(samples):
            outfile.write(str(sample) + " " + str(sample) + " 0 0 0 " + str(vals[i]) + "\n")

def parse_gemma_output(this_dataset):
    included_markers = []
    p_values = []
    with open("{}/output/{}_output.assoc.txt".format(GEMMA_PATH, this_dataset.group.name)) as output_file:
        for line in output_file:
            if line.startswith("chr"):
                continue
            else:
                included_markers.append(line.split("\t")[1])
                p_values.append(float(line.split("\t")[10]))

    #print("p_values: ", p_values)
    return included_markers, p_values
