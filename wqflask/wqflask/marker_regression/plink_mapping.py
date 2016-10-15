import string
import os

from base.webqtlConfig import TMPDIR
from utility import webqtlUtil
from utility.tools import PLINK_COMMAND

import utility.logger
logger = utility.logger.getLogger(__name__ )

def run_plink(this_trait, dataset, species, vals, maf):
    plink_output_filename = webqtlUtil.genRandStr("%s_%s_"%(dataset.group.name, this_trait.name))

    gen_pheno_txt_file_plink(this_trait, dataset, vals, pheno_filename = plink_output_filename)

    plink_command = PLINK_COMMAND + ' --noweb --ped %s/%s.ped --no-fid --no-parents --no-sex --no-pheno --map %s/%s.map --pheno %s%s.txt --pheno-name %s --maf %s --missing-phenotype -9999 --out %s%s --assoc ' % (
        PLINK_PATH, dataset.group.name, PLINK_PATH, dataset.group.name,
        TMPDIR, plink_output_filename, this_trait.name, maf, TMPDIR,
        plink_output_filename)
    logger.debug("plink_command:", plink_command)

    os.system(plink_command)

    count, p_values = parse_plink_output(plink_output_filename, species)

    #for marker in self.dataset.group.markers.markers:
    #    if marker['name'] not in included_markers:
    #        logger.debug("marker:", marker)
    #        self.dataset.group.markers.markers.remove(marker)
    #        #del self.dataset.group.markers.markers[marker]

    logger.debug("p_values:", pf(p_values))
    dataset.group.markers.add_pvalues(p_values)

    return dataset.group.markers.markers


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
    ped_file= open("{}/{}.ped".format(PLINK_PATH, dataset.group.name),"r")
    line = ped_file.readline()
    sample_list=[]

    while line:
        lineList = string.split(string.strip(line), '\t')
        lineList = map(string.strip, lineList)

        sample_name = lineList[0]
        sample_list.append(sample_name)

        line = ped_file.readline()

    return sample_list

def parse_plink_output(output_filename, species):
    plink_results={}

    threshold_p_value = 0.01

    result_fp = open("%s%s.qassoc"% (TMPDIR, output_filename), "rb")

    header_line = result_fp.readline()# read header line
    line = result_fp.readline()

    value_list = [] # initialize value list, this list will include snp, bp and pvalue info
    p_value_dict = {}
    count = 0

    while line:
        #convert line from str to list
        line_list = build_line_list(line=line)

        # only keep the records whose chromosome name is in db
        if species.chromosomes.chromosomes.has_key(int(line_list[0])) and line_list[-1] and line_list[-1].strip()!='NA':

            chr_name = species.chromosomes.chromosomes[int(line_list[0])]
            snp = line_list[1]
            BP = line_list[2]
            p_value = float(line_list[-1])
            if threshold_p_value >= 0 and threshold_p_value <= 1:
                if p_value < threshold_p_value:
                    p_value_dict[snp] = float(p_value)

            if plink_results.has_key(chr_name):
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

    #if p_value_list:
    #    min_p_value = min(p_value_list)
    #else:
    #    min_p_value = 0

    return count, p_value_dict

######################################################
# input: line: str,one line read from file
# function: convert line from str to list;
# output: lineList list
#######################################################
def build_line_list(line=None):
    line_list = string.split(string.strip(line),' ')# irregular number of whitespaces between columns
    line_list = [item for item in line_list if item <>'']
    line_list = map(string.strip, line_list)

    return line_list
