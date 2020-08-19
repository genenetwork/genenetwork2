import string
import os

from base.webqtlConfig import TMPDIR
from utility import webqtlUtil
from utility.tools import flat_files, PLINK_COMMAND

import utility.logger
logger = utility.logger.getLogger(__name__ )

def run_plink(this_trait, dataset, species, vals, maf):
    plink_output_filename = webqtlUtil.genRandStr("%s_%s_"%(dataset.group.name, this_trait.name))
    gen_pheno_txt_file(dataset, vals)

    plink_command = PLINK_COMMAND + ' --noweb --bfile %s/%s --no-pheno --no-fid --no-parents --no-sex --maf %s --out %s%s --assoc ' % (
        flat_files('mapping'), dataset.group.name, maf, TMPDIR, plink_output_filename)
    logger.debug("plink_command:", plink_command)

    os.system(plink_command)

    count, p_values = parse_plink_output(plink_output_filename, species)

    logger.debug("p_values:", p_values)
    dataset.group.markers.add_pvalues(p_values)

    return dataset.group.markers.markers

def gen_pheno_txt_file(this_dataset, vals):
    """Generates phenotype file for GEMMA/PLINK"""

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
            outfile.write("0 " + line[1] + " " + line[2] + " " + line[3] + " " + line[4] + " " + str(this_val) + "\n")

def gen_pheno_txt_file_plink(this_trait, dataset, vals, pheno_filename = ''):
    ped_sample_list = get_samples_from_ped_file(dataset)
    output_file = open("%s%s.txt" % (TMPDIR, pheno_filename), "wb")
    header = 'FID\tIID\t%s\n' % this_trait.name
    output_file.write(header)

    new_value_list = []

    #if valueDict does not include some strain, value will be set to -9999 as missing value
    for i, sample in enumerate(ped_sample_list):
        try:
            value = vals[i]
            value = str(value).replace('value=','')
            value = value.strip()
        except:
            value = -9999

        new_value_list.append(value)

    new_line = ''
    for i, sample in enumerate(ped_sample_list):
        j = i+1
        value = new_value_list[i]
        new_line += '%s\t%s\t%s\n'%(sample, sample, value)

        if j%1000 == 0:
            output_file.write(newLine)
            new_line = ''

    if new_line:
        output_file.write(new_line)

    output_file.close()

# get strain name from ped file in order
def get_samples_from_ped_file(dataset):
    ped_file= open("{}{}.ped".format(flat_files('mapping'), dataset.group.name),"r")
    line = ped_file.readline()
    sample_list=[]

    while line:
        lineList = string.split(string.strip(line), '\t')
        lineList = list(map(string.strip, lineList))

        sample_name = lineList[0]
        sample_list.append(sample_name)

        line = ped_file.readline()

    return sample_list

def parse_plink_output(output_filename, species):
    plink_results={}

    threshold_p_value = 1

    result_fp = open("%s%s.qassoc"% (TMPDIR, output_filename), "rb")

    line = result_fp.readline()

    value_list = [] # initialize value list, this list will include snp, bp and pvalue info
    p_value_dict = {}
    count = 0

    while line:
        #convert line from str to list
        line_list = build_line_list(line=line)

        # only keep the records whose chromosome name is in db
        if int(line_list[0]) in species.chromosomes.chromosomes and line_list[-1] and line_list[-1].strip()!='NA':

            chr_name = species.chromosomes.chromosomes[int(line_list[0])]
            snp = line_list[1]
            BP = line_list[2]
            p_value = float(line_list[-1])
            if threshold_p_value >= 0 and threshold_p_value <= 1:
                if p_value < threshold_p_value:
                    p_value_dict[snp] = float(p_value)

            if chr_name in plink_results:
                value_list = plink_results[chr_name]

                # pvalue range is [0,1]
                if threshold_p_value >=0 and threshold_p_value <= 1:
                    if p_value < threshold_p_value:
                        value_list.append((snp, BP, p_value))
                        count += 1

                plink_results[chr_name] = value_list
                value_list = []
            else:
                if threshold_p_value >= 0 and threshold_p_value <= 1:
                    if p_value < threshold_p_value:
                        value_list.append((snp, BP, p_value))
                        count += 1

                if value_list:
                    plink_results[chr_name] = value_list

                value_list=[]

            line = result_fp.readline()
        else:
            line = result_fp.readline()

    return count, p_value_dict

######################################################
# input: line: str,one line read from file
# function: convert line from str to list;
# output: lineList list
#######################################################
def build_line_list(line=None):
    line_list = string.split(string.strip(line),' ')# irregular number of whitespaces between columns
    line_list = [item for item in line_list if item !='']
    line_list = list(map(string.strip, line_list))

    return line_list