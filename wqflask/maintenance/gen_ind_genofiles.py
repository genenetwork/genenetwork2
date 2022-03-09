# Example commands:
# python3 gen_ind_genofiles.py /home/zas1024/gn2-zach/genotype_files/genotype/ /home/zas1024/gn2-zach/new_geno/ BXD-Micturition.geno BXD.json
# python3 gen_ind_genofiles.py /home/zas1024/gn2-zach/genotype_files/genotype/ /home/zas1024/gn2-zach/new_geno/ BXD-Micturition.geno BXD.2.geno BXD.4.geno BXD.5.geno

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
    if ".json" in args[4]:
        source_files = [geno_dir + genofile['location'] for genofile in json.load(args[4])['genofile']]
    else:
        source_files = [geno_dir + group + ".geno" if ".geno" not in group else group for group in args[4:]]

    if len(source_files) > 1:
        # Generate a JSON file pointing to the new target genotype files, in situations where there are multiple source .geno files
        target_json_loc = out_dir + args[3].split(".")[:-1] + ".json"
        target_json = {'genofile': []}

    # Generate the output .geno files
    for source_file in source_files:
        filename, samples = generate_new_genofile(source_file, target_file)

        target_json['genofile'].append({
            'location': filename.split("/")[-1],
            'title': filename.split("/")[-1],
            'sample_list': samples
        })

    json.dump(target_json, open(target_json_loc, "w"))

def get_strain_for_sample(sample):
    query = (
        "SELECT CaseAttributeXRefNew.Value "
        "FROM CaseAttributeXRefNew, Strain "
        "WHERE CaseAttributeXRefNew.CaseAttributeId=11 "
        "AND CaseAttributeXRef.New.StrainId = Strain.Id "
        "AND Strain.Name = %(name)s" )

    with conn.cursor() as cursor:
        return cursor.execute(query, {"name": name}).fetchone()[0]

def generate_new_genofiles(source_genofile, target_genofile):
    base_samples = group_samples(source_genofile)
    base_genotypes = strain_genotypes(source_genofile)
    target_samples = group_samples(target_genofile)
    strain_pos_map = map_strain_pos_to_target_group(base_samples, target_samples)


def map_strain_pos_to_target_group(base_samples, target_samples):
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
        pos_map.append(base_samples.index(sample_strain))

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
    marker_genotypes = []
    with open(file_location, "r") as source_geno:
        for i, line in enumerate(source_geno):
            if line[0] == "@":
                if "@type" in line:
                    geno_dict['type'] = line.split(":")[1]
                if "@mat" in line:
                    geno_dict['mat'] = line.split(":")[1]
                elif "@pat" in line:
                    geno_dict['pat'] = line.split(":")[1]
                elif "@het" in line:
                    geno_dict['het'] = line.split(":")[1]
                elif "@unk" in line:
                    geno_dict['unk'] = line.split(":")[1]

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
                marker_genotypes.append(this_marker)

    geno_dict['genotypes'] = marker_genotypes

    return geno_dict
            
if __name__ == "__main__":
    print("command line arguments:\n\t%s" % sys.argv)
    main(sys.argv)

