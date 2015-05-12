import os

from base import webqtlConfig

def run_gemma(this_dataset, samples, vals): 
    """Generates p-values for each marker using GEMMA"""
        
    print("INSIDE GEMMA_MAPPING")

    gen_pheno_txt_file(this_dataset, samples, vals)

    os.chdir("{}gemma".format(webqtlConfig.HTMLPATH))

    gemma_command = './gemma -bfile %s -k output_%s.cXX.txt -lmm 1 -o output/%s_output' % (this_dataset.group.name,
                                                                                    this_dataset.group.name,
                                                                                    this_dataset.group.name)
    print("gemma_command:" + gemma_command)
        
    os.system(gemma_command)
        
    included_markers, p_values = parse_gemma_output(this_dataset)

    return included_markers, p_values

def gen_pheno_txt_file(this_dataset, samples, vals):
    """Generates phenotype file for GEMMA"""
                
    with open("{}gemma/{}.fam".format(webqtlConfig.HTMLPATH, this_dataset.group.name), "w") as outfile:
        for i, sample in enumerate(samples):
            outfile.write(str(sample) + " " + str(sample) + " 0 0 0 " + str(vals[i]) + "\n")

def parse_gemma_output(this_dataset):
    included_markers = []
    p_values = []
    with open("{}gemma/output/{}_output.assoc.txt".format(webqtlConfig.HTMLPATH, this_dataset.group.name)) as output_file:
        for line in output_file:
            if line.startswith("chr"):
                continue
            else:
                included_markers.append(line.split("\t")[1])
                p_values.append(float(line.split("\t")[10]))

    print("p_values: ", p_values)
    return included_markers, p_values