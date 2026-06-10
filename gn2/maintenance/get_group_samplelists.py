import os
import json
import glob
import gzip
from pathlib import Path

from gn2.base import webqtlConfig


def get_samplelist(file_type, geno_file):
    if file_type == "geno":
        return get_samplelist_from_geno(geno_file)
    elif file_type == "plink":
        return get_samplelist_from_plink(geno_file)


def get_samplelist_from_json(group_name):
    """
    Get the main samplelist for a group from its JSON file.
    Returns the samplelist from the group's {group_name}.json file,
    or None if the file or field doesn't exist.
    """
    try:
        genotype_dir = webqtlConfig.GENODIR
        json_file = Path(genotype_dir) / f"{group_name}.json"

        if not json_file.exists():
            return None

        with open(json_file) as f:
            data = json.load(f)

        # Return the top-level samplelist field if it exists
        return data.get('samplelist', None)
    except Exception as e:
        print(f"Error reading samplelist from {group_name}.json: {e}")
        return None


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
