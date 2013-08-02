from __future__ import absolute_import, print_function, division

import os
import glob
import gzip

from base import webqtlConfig


def process_genofiles(geno_dir=webqtlConfig.GENODIR):
    print("Yabba")
    #sys.exit("Dabba")
    os.chdir(geno_dir)
    for geno_file in glob.glob("*"):
        if geno_file.lower().endswith(('.geno', '.geno.gz')):
            #group_name = genofilename.split('.')[0]
            sample_list = get_samplelist(geno_file)


def get_samplelist(geno_file):
    genofilename = os.path.join(webqtlConfig.GENODIR, geno_file)
    if os.path.isfile(genofilename + '.gz'):
        genofilename += '.gz'
        genofile = gzip.open(genofilename)
    else:
        genofile = open(genofilename)
        
    for line in genofile:
        line = line.strip()
        if not line:
            continue
        if line.startswith(("#", "@")):
            continue
        break
    
    headers = line.split()
    
    if headers[3] == "Mb":
        samplelist = headers[4:]
    else:
        samplelist = headers[3:]
    return samplelist

