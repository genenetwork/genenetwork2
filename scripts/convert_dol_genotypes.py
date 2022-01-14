# This is just to convert the Rqtl2 format genotype files for DOL into a .geno file
# Everything is hard-coded since I doubt this will be re-used and I just wanted to generate the file quickly

# This is to be used on the files generated as described by Karl Broman here - https://kbroman.org/qtl2/pages/prep_do_data.html

import os

geno_dir = "/home/zas1024/gn2-zach/DO_genotypes/"
markers_file = "/home/zas1024/gn2-zach/DO_genotypes/SNP_Map.txt"
gn_geno_path = "/home/zas1024/gn2-zach/DO_genotypes/DOL.geno"

# Iterate through the SNP_Map.txt file to get marker positions
marker_data = {}
with open(markers_file, "r") as markers_fh:
    for i, line in enumerate(markers_fh):
        if i == 0:
            continue
        else:
            line_items = line.split("\t")
            this_marker = {}
            this_marker['chr'] = line_items[2] if line_items[2] != "0" else "M"
            this_marker['pos'] = f'{float(line_items[3])/1000000:.6f}'
            marker_data[line_items[1]] = this_marker

# Iterate through R/qtl2 format genotype files and pull out the samplelist and genotypes for each marker
sample_names = []
for filename in os.listdir(geno_dir):
    if "gm4qtl2_geno" in filename:
        with open(geno_dir + "/" + filename, "r") as rqtl_geno_fh:
            for i, line in enumerate(rqtl_geno_fh):
                line_items = line.split(",")
                if i < 3:
                    continue
                elif not len(sample_names) and i == 3:
                    sample_names_positions = [[item.replace("TLB", "TB").strip(), i] for i, item in enumerate(line_items[1:])]
                    sample_names_positions.sort(key = lambda x: x[0][2:])
                    sample_names = [sample[0] for sample in sample_names_positions]
                elif i > 3:
                    genotypes = ["X" if item.strip() == "-" else item.strip() for item in line_items[1:]]
                    ordered_genotypes = [genotypes[i].strip() for i in [pos[1] for pos in sample_names_positions]]
                    marker_data[line_items[0]]['genotypes'] = ordered_genotypes

# Generate list of marker obs to iterate through when writing to .geno file
marker_list = []
for key, value in marker_data.items():
    if 'genotypes' in value:
        this_marker = {
            'chr': value['chr'],
            'locus': key,
            'pos': value['pos'],
            'genotypes': value['genotypes']
        }
        marker_list.append(this_marker)


def sort_func(e):
    """For ensuring that X/Y chromosomes/mitochondria are sorted to the end correctly"""
    try:
        return float((e['chr']))*1000 + float(e['pos'])
    except:
        if e['chr'] == "X":
            return 20000 + float(e['pos'])
        elif e['chr'] == "Y":
            return 21000 + float(e['pos'])
        elif e['chr'] == "M":
            return 22000 + float(e['pos'])

# Sort markers by chromosome
marker_list.sort(key=sort_func)

# Write lines to .geno file
with open(gn_geno_path, "w") as gn_geno_fh:
    gn_geno_fh.write("\t".join((["Chr", "Locus", "cM", "Mb"] + sample_names)) + "\n")
    for marker in marker_list:
        row_contents = [
            marker['chr'],
            marker['locus'],
            marker['pos'],
            marker['pos']
        ] + marker['genotypes']
        gn_geno_fh.write("\t".join(row_contents) + "\n")

