#!/usr/bin/python

"""
Generate relatedness matrix files for GEMMA from BIMBAM genotype/phenotype files

This file goes through all of the BIMBAM files in the bimbam diretory
and uses GEMMA to generate their corresponding kinship/relatedness matrix file

"""

from __future__ import print_function, division, absolute_import
import sys
sys.path.append("..")
import os
import glob

class GenerateKinshipMatrices(object):
    def __init__(self, group_name, geno_file, pheno_file):
        self.group_name = group_name
        self.geno_file = geno_file
        self.pheno_file = pheno_file
    
    def generate_kinship(self):
        gemma_command = "/gnu/store/xhzgjr0jvakxv6h3blj8z496xjig69b0-profile/bin/gemma -g " + self.geno_file + " -p " + self.pheno_file + " -gk 1 -outdir /home/zas1024/genotype_files/genotype/bimbam/ -o " + self.group_name
        print("command:", gemma_command)
        os.system(gemma_command)

    @classmethod
    def process_all(self, geno_dir, bimbam_dir):
        os.chdir(geno_dir)
        for input_file in glob.glob("*"):
            if not input_file.endswith(('geno', '.geno.gz')):
                continue
            group_name = ".".join(input_file.split('.')[:-1])
            geno_input_file = os.path.join(bimbam_dir, group_name + "_geno.txt")
            pheno_input_file = os.path.join(bimbam_dir, group_name + "_pheno.txt")
            convertob = GenerateKinshipMatrices(group_name, geno_input_file, pheno_input_file)
            try:
                convertob.generate_kinship()
            except EmptyConfigurations as why:
                print("  No config info? Continuing...")
                continue
            except Exception as why:

                print("  Exception:", why)
                print(traceback.print_exc())
                print("    Found in row %s at tabular column %s" % (convertob.latest_row_pos,
                                                                convertob.latest_col_pos))
                print("    Column is:", convertob.latest_col_value)
                print("    Row is:", convertob.latest_row_value)
                break
    
    
if __name__=="__main__":
    Geno_Directory = """/home/zas1024/genotype_files/genotype/"""
    Bimbam_Directory = """/home/zas1024/genotype_files/genotype/bimbam/"""
    GenerateKinshipMatrices.process_all(Geno_Directory, Bimbam_Directory)
    
    #./gemma -g /home/zas1024/genotype_files/genotype/bimbam/BXD_geno.txt -p /home/zas1024/genotype_files/genotype/bimbam/BXD_pheno.txt -gk 1 -o BXD