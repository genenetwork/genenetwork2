# Example command: env GN2_PROFILE=/usr/local/guix-profiles/gn-latest-20220122 TMPDIR=/export/local/home/zas1024/gn2-zach/tmp WEBSERVER_MODE=DEBUG LOG_LEVEL=DEBUG SERVER_PORT=5002 GENENETWORK_FILES=/export/local/home/zas1024/gn2-zach/genotype_files SQL_URI=mysql://webqtlout:webqtlout@localhost/db_webqtl ./bin/genenetwork2 ./etc/default_settings.py -c ./maintenance/gen_ind_genofiles.py

import sys
from typing import List

import MySQLdb

from wqflask import app

def conn():
    return MySQLdb.Connect(db=app.config.get("DB_NAME"),
                           user=app.config.get("DB_USER"),
                           passwd=app.config.get("DB_PASS"),
                           host=app.config.get("DB_HOST"))

def main(args):

    # The file of the "main" .geno file for the group in question
    # For example: BXD.geno or BXD.6.geno if converting to BXD individual genofiles
    source_genofile = args[1] 

    # The target individuals/samples group(s) we're generating the .geno files for
    # This can be passed as either a specific .geno file, or as a JSON file
    # containing a set of .geno files (and their corresponding file names and sample lists)
    if ".json" in args[2]:
        target_groups = json.load(args[2])['genofile']
    else:
        target_groups = [args[2]]

    # Generate the output .geno files
    generate_new_genofiles(source_genofile, strain_genotypes(source_genofile), target_groups)

def get_strain_for_sample(sample):
    query = (
        "SELECT CaseAttributeXRefNew.Value "
        "FROM CaseAttributeXRefNew, Strain "
        "WHERE CaseAttributeXRefNew.CaseAttributeId=11 "
        "AND CaseAttributeXRef.New.StrainId = Strain.Id "
        "AND Strain.Name = %(name)s" )

    with conn.cursor() as cursor:
        return cursor.execute(query, {"name": name}).fetchone()[0]

def generate_new_genofiles(source_genofile, strain_genotypes, target_groups):
    for group in target_groups:
        base_samples = group_samples(source_genofile)
        target_samples = group_samples(group)
        strain_pos_map = map_strain_pos_to_target_group(base_samples, target_samples)

        new_genofile = app.config.get("GENENETWORK_FILES") + "/genotype/_" + group


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
    for i, sample in enumerate(target_samples):
        sample_strain = get_strain_for_sample(sample)
        pos_map.append(base_samples.index(sample_strain))

    return pos_map

def group_samples(target_group: str) -> List:
    """
    Get the group samples from its "dummy" .geno file (which still contains the sample list)
    """

    # Allow for inputting the target group as either the group name or .geno file
    file_location = app.config.get("GENENETWORK_FILES") + "/genotype/" + target_group
    if ".geno" not in target_group:
        file_location += ".geno"

    sample_list = []
    with open(file_location, "r") as target_geno:
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

    file_location = app.config.get("GENENETWORK_FILES") + "/genotype/" + strain_genofile

    geno_start_col = None
    header_columns = []
    sample_list = []
    marker_genotypes = []
    with open(file_location, "r") as source_geno:
        for i, line in enumerate(source_geno):
            # Skip header lines
            if line[0] in ["#", "@"] or not len(line):
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
                    'genotypes': list(zip(sample_list, [item.strip() for item in line_items][geno_start_col:]))
                }
                marker_genotypes.append(this_marker)

    return marker_genotypes
            
if __name__ == "__main__":
    print("command line arguments:\n\t%s" % sys.argv)
    main(sys.argv)

