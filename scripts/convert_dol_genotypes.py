# This is just to convert the Rqtl2 format genotype files for DOL into a .geno file
# Everything is hard-coded since I doubt this will be re-used and I just wanted to generate the file quickly

import os

geno_dir = "/home/zas1024/gn2-zach/DO_genotypes/"
markers_file = "/home/zas1024/gn2-zach/DO_genotypes/SNP_Map.txt"
gn_geno_path = "/home/zas1024/gn2-zach/DO_genotypes/DOL.geno"

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

sample_names = []
for filename in os.listdir(geno_dir):
    if "gm4qtl2_geno" in filename:
        with open(geno_dir + "/" + filename, "r") as rqtl_geno_fh:
            for i, line in enumerate(rqtl_geno_fh):
                line_items = line.split(",")
                if i < 3:
                    continue
                elif not len(sample_names) and i == 3:
                    sample_names = [item.replace("TLB", "TB") for item in line_items[1:]]
                elif i > 3:
                    marker_data[line_items[0]]['genotypes'] = ["X" if item.strip() == "-" else item.strip() for item in line_items[1:]]

def sort_func(e):
    try:
        return int(e['chr'])
    except:
        if e['chr'] == "X":
            return 20
        elif e['chr'] == "Y":
            return 21
        elif e['chr'] == "M":
            return 22

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

marker_list.sort(key=sort_func)

with open(gn_geno_path, "w") as gn_geno_fh:
    gn_geno_fh.write("\t".join((["Chr", "Locus", "cM", "Mb"] + sample_names)))
    for marker in marker_list:
        row_contents = [
            marker['chr'],
            marker['locus'],
            marker['pos'],
            marker['pos']
        ] + marker['genotypes']
        gn_geno_fh.write("\t".join(row_contents) + "\n")
