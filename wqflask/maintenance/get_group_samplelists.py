from __future__ import absolute_import, print_function, division

import os
import glob
import gzip

from base import webqtlConfig


def get_sample_list_dir(geno_dir="/home/zas1024/gene/web/genotypes/"):
    os.chdir(geno_dir)
    
    for group_file in glob.glob("*"):
        if group_file.lower().endswith(('.geno', '.geno.gz')):
            #group_name = genofilename.split('.')[0]
            sample_list = get_sample_list(group_file)
            print("\n\n{}\n\n".format(sample_list))


def get_sample_list(group_file):
    print(group_file)
    genofilename = str(os.path.join(webqtlConfig.GENODIR, group_file))
    if genofilename.lower().endswith('.geno.gz'):
        genofile = gzip.open(genofilename)
    else:
        genofile = open(genofilename)
    for line in genofile:
        line = line.strip()
        if not line:
            continue
        if line.startswith(("#", "@")):
            continue
        headline = line
        break
    headers = headline.split("\t")
    if headers[3] == "Mb":
        samplelist = headers[4:]
    else:
        samplelist = headers[3:]
    return samplelist

if __name__ == '__main__':
    get_sample_list_dir()
