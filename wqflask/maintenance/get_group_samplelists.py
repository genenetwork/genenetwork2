import os
import glob
import gzip

from base import webqtlConfig


def get_samplelist(file_type, geno_file):
    if file_type == "geno":
        return get_samplelist_from_geno(geno_file)
    elif file_type == "plink":
        return get_samplelist_from_plink(geno_file)


def get_samplelist_from_geno(genofilename):
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

    headers = line.split("\t")

    if headers[3] == "Mb":
        samplelist = headers[4:]
    else:
        samplelist = headers[3:]
    return samplelist


def get_samplelist_from_plink(genofilename):
    genofile = open(genofilename)

    samplelist = []
    for line in genofile:
        line = line.split(" ")
        samplelist.append(line[1])

    return samplelist
