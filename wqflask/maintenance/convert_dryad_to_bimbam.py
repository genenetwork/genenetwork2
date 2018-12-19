#!/usr/bin/python

"""
Convert data dryad files to a BIMBAM _geno and _snps file


"""

from __future__ import print_function, division, absolute_import
import sys
sys.path.append("..")


def read_dryad_file(filename):
    exclude_count = 0
    marker_list = []
    sample_dict = {}
    sample_list = []
    geno_rows = []
    with open(filename, 'r') as the_file:
        for i, line in enumerate(the_file):
            if i > 0:
                if line.split(" ")[1] == "no":
                    sample_name = line.split(" ")[0]
                    sample_list.append(sample_name)
                    sample_dict[sample_name] = line.split(" ")[2:]
                else:
                    exclude_count += 1
            else:
                marker_list = line.split(" ")[2:]

    for i, marker in enumerate(marker_list):
        this_row = []
        this_row.append(marker)
        this_row.append("X")
        this_row.append("Y")
        for sample in sample_list:
            this_row.append(sample_dict[sample][i])
        geno_rows.append(this_row)

    print(exclude_count)

    return geno_rows

    #for i, marker in enumerate(marker_list):
    #    this_row = []
    #    this_row.append(marker)
    #    this_row.append("X")
    #    this_row.append("Y")
    #    with open(filename, 'r') as the_file:
    #        for j, line in enumerate(the_file):
    #            if j > 0:
    #                this_row.append(line.split(" ")[i+2])
    #        print("row: " + str(i))
    #        geno_rows.append(this_row)
    #            
    #return geno_rows

def write_bimbam_files(geno_rows):
    with open('/home/zas1024/cfw_data/CFW_geno.txt', 'w') as geno_fh:
        for row in geno_rows:
            geno_fh.write(", ".join(row) + "\n")

def convert_dryad_to_bimbam(filename):
    geno_file_rows = read_dryad_file(filename)
    write_bimbam_files(geno_file_rows)

if __name__=="__main__":
    input_filename = "/home/zas1024/cfw_data/" + sys.argv[1] + ".txt"
    convert_dryad_to_bimbam(input_filename)