# Example commands:
# python3 gen_ind_genofiles.py /home/zas1024/gn2-zach/genotype_files/genotype/ /home/zas1024/gn2-zach/new_geno/ BXD-Micturition.geno BXD.json
# python3 gen_ind_genofiles.py /home/zas1024/gn2-zach/genotype_files/genotype/ /home/zas1024/gn2-zach/new_geno/ BXD-Micturition.geno BXD.2.geno BXD.4.geno BXD.5.geno

import json
import os
import sys
from typing import List

import MySQLdb

def conn():
    return MySQLdb.Connect(db=os.environ.get("DB_NAME"),
                           user=os.environ.get("DB_USER"),
                           passwd=os.environ.get("DB_PASS"),
                           host=os.environ.get("DB_HOST"))

def main(args):

    # Directory in which .geno files are located
    geno_dir = args[1]

    # Directory in which to output new files
    out_dir = args[2]

    # The individuals group that we want to generate a .geno file for
    target_file = geno_dir + args[3]

    # The source group(s) we're generating the .geno files from
    # This can be passed as either a specific .geno file (or set of files as multiple arguments),
    # or as a JSON file containing a set of .geno files (and their corresponding file names and sample lists)
    geno_json = {}
    source_files = []
    if ".json" in args[4]:
        geno_json = json.load(open(geno_dir + args[4], "r"))
        par_f1s = {
            "mat": geno_json['mat'],
            "pat": geno_json['pat'],
            "f1s": geno_json['f1s']
        }

        # List of file titles and locations from JSON
        source_files = [{'title': genofile['title'], 'location': geno_dir + genofile['location']} for genofile in geno_json['genofile']]
    else:
        par_f1s = {}
        # List of files directly taken from command line arguments, with titles just set to the filename
        for group in args[4:]:
            file_name = geno_dir + group + ".geno" if ".geno" not in group else group
            source_files.append({'title': file_name[:-5], 'location': file_name})

    if len(source_files) > 1:
        # Generate a JSON file pointing to the new target genotype files, in situations where there are multiple source .geno files
        target_json_loc = out_dir + ".".join(args[3].split(".")[:-1]) + ".json"
        target_json = {'genofile': []}

    # Generate the output .geno files
    for source_file in source_files:
        filename, samples = generate_new_genofile(source_file['location'], target_file, par_f1s, out_dir)

        target_json['genofile'].append({
            'location': filename.split("/")[-1],
            'title': source_file['title'],
            'sample_list': samples
        })

    json.dump(target_json, open(target_json_loc, "w"))

def get_strain_for_sample(sample):
    query = (
        "SELECT CaseAttributeXRefNew.Value "
        "FROM CaseAttributeXRefNew, Strain "
        "WHERE CaseAttributeXRefNew.CaseAttributeId=11 "
        "AND CaseAttributeXRefNew.StrainId = Strain.Id "
        "AND Strain.Name = %(name)s" )

    with conn().cursor() as cursor:
        cursor.execute(query, {"name": sample.strip()})
        return cursor.fetchone()[0]

def generate_new_genofile(source_genofile, target_genofile, par_f1s, out_dir):
    source_samples = group_samples(source_genofile)
    source_genotypes = strain_genotypes(source_genofile)
    target_samples = group_samples(target_genofile)
    strain_pos_map = map_strain_pos_to_target_group(source_samples, target_samples, par_f1s)

    if len(source_genofile.split("/")[-1].split(".")) > 2:
        # The number in the source genofile; for example 4 in BXD.4.geno
        source_num = source_genofile.split("/")[-1].split(".")[-2]
        target_filename = ".".join(target_genofile.split("/")[-1].split(".")[:-1]) + "." + source_num + ".geno"
    else:
        target_filename = ".".join(target_genofile.split("/")[-1].split(".")[:-1]) + ".geno"

    file_location = out_dir + target_filename

    with open(file_location, "w") as fh:
        for metadata in ["name", "type", "mat", "pat", "het", "unk"]:
            fh.write("@" + metadata + ":" + source_genotypes[metadata] + "\n")

        header_line = ["Chr", "Locus", "cM", "Mb"] + target_samples
        fh.write("\t".join(header_line))

        for marker in source_genotypes['markers']:
            line_items = [
                marker['Chr'],
                marker['Locus'],
                marker['cM'],
                marker['Mb']
            ]

            for pos in strain_pos_map:
                if isinstance(pos, int):
                    line_items.append(marker['genotypes'][pos])
                else:
                    if pos in ["mat", "pat"]:
                        line_items.append(source_genotypes[pos])
                    elif pos == "f1s":
                        line_items.append("H")
                    else:
                        line_items.append("U")

            fh.write("\t".join(line_items) + "\n")

    return file_location, target_samples

def map_strain_pos_to_target_group(source_samples, target_samples, par_f1s):
    """
    Retrieve corresponding strain position for each sample in the target group

    This is so the genotypes from the base genofile can be mapped to the samples in the target group

    For example:
    Base strains: BXD1, BXD2, BXD3
    Target samples: BXD1_1, BXD1_2, BXD2_1, BXD3_1, BXD3_2, BXD3_3
    Returns: [0, 0, 1, 2, 2, 2]
    """
    pos_map = []
    for sample in target_samples:
        sample_strain = get_strain_for_sample(sample)
        if sample_strain in source_samples:
            pos_map.append(source_samples.index(sample_strain))
        else:
            val = "U"
            for key in par_f1s.keys():
                if sample_strain in par_f1s[key]:
                    val = key
            pos_map.append(val)

    return pos_map

def group_samples(target_file: str) -> List:
    """
    Get the group samples from its "dummy" .geno file (which still contains the sample list)
    """

    sample_list = []
    with open(target_file, "r") as target_geno:
        for i, line in enumerate(target_geno):
            # Skip header lines
            if line[0] in ["#", "@"] or not len(line):
                continue
    
            line_items = line.split("\t")
            sample_list = [item for item in line_items if item not in ["Chr", "Locus", "Mb", "cM"]]
            break

    return sample_list

def strain_genotypes(strain_genofile: str) -> List:
    """
    Read genotypes from source strain .geno file

    :param strain_genofile: string of genofile filename
    :return: a list of dictionaries representing each marker's genotypes

    Example output: [
        {
            'Chr': '1',
            'Locus': 'marker1',
            'Mb': '10.0',
            'cM': '8.0',
            'genotypes': [('BXD1', 'B'), ('BXD2', 'D'), ('BXD3', 'H'), ...]
        },
        ...
    ]
    """

    geno_dict = {}

    geno_start_col = None
    header_columns = []
    sample_list = []
    markers = []
    with open(strain_genofile, "r") as source_geno:
        for i, line in enumerate(source_geno):
            if line[0] == "@":
                metadata_type = line[1:].split(":")[0]
                if metadata_type in ['name', 'type', 'mat', 'pat', 'het', 'unk']:
                    geno_dict[metadata_type] = line.split(":")[1].strip()

                continue

            # Skip other header lines
            if line[0] == "#" or not len(line):
                continue

            line_items = line.split("\t")
            if "Chr" in line_items: # Header row
                # Get the first column index containing genotypes
                header_columns = line_items
                for j, item in enumerate(line_items):
                    if item not in ["Chr", "Locus", "Mb", "cM"]:
                        geno_start_col = j
                        break

                sample_list = line_items[geno_start_col:]
                if not geno_start_col:
                    print("Check .geno file - expected columns not found")
                    sys.exit()
            else: # Marker rows
                this_marker = {
                    'Chr': line_items[header_columns.index("Chr")],
                    'Locus': line_items[header_columns.index("Locus")],
                    'Mb': line_items[header_columns.index("Mb")],
                    'cM': line_items[header_columns.index("cM")],
                    'genotypes': [item.strip() for item in line_items][geno_start_col:]
                }

                markers.append(this_marker)

    geno_dict['markers'] = markers

    return geno_dict
            
if __name__ == "__main__":
    print("command line arguments:\n\t%s" % sys.argv)
    main(sys.argv)

