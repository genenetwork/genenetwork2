#!/usr/bin/python

from __future__ import absolute_import, print_function, division
import os

import numpy

from base import webqtlConfig


class PrepData(object):
    def __init__(self, pheno_vector, group_name):
        self.pheno_vector = pheno_vector
        self.group_name = group_name
        self.no_val_samples = set()
        #self.identify_no_genotype_samples()
        self.identify_empty_samples()
        self.trim_files()

    def identify_empty_samples(self):
        for sample_count, val in enumerate(self.pheno_vector):
            if val == "x":
                self.no_val_samples.add(sample_count)
        print("self.no_val_samples:", self.no_val_samples)
        #nums = set(range(0, 176))
        #print("not included:", nums-self.empty_columns)
            
    #def identify_no_genotype_samples(self):
    #    #for this_file in (self.exprs_file, self.snps_file):
    #        #with open(this_file) as fh:
    #        no_geno_samples = []
    #        has_genotypes = False
    #        with open(self.snps_file) as fh:
    #            for line in fh:
    #                num_samples = len(line.split())
    #                break
    #            for sample in range (num_samples):
    #                for line in fh:
    #                    if line.split()[sample] != "NA":
    #                        has_genotypes = True
    #                        break
    #                if has_genotypes == False:
    #                    no_geno_samples.append(sample)
    #                    
    #        print(no_geno_samples)

    def trim_files(self):
        input_file = open(os.path.join(webqtlConfig.NEWGENODIR, self.group_name+'.snps'))
        output_file = os.path.join(webqtlConfig.TMPDIR, self.group_name + '.snps.new')
        with open(output_file, "w") as output_file:
            for line in input_file:
                data_to_write = []
                for pos, item in enumerate(line.split()):
                    if pos in self.no_val_samples:
                        continue
                    else:
                        data_to_write.append("%s" % (item))
                output_file.write(" ".join(data_to_write) + "\n")
        
        print("Done writing:", output_file)
        
        #for this_file in (self.exprs_file, self.genotype_file):
        #    input_file = open(this_file)
        #    this_file_name_output = this_file + ".new"
        #    with open(this_file_name_output, "w") as output_file:
        #        for line in input_file:
        #            data_wanted = []
        #            for pos, item in enumerate(line.split()):
        #                if pos in self.empty_columns:
        #                    continue
        #                else:
        #                    data_wanted.append("%2s" % (item))
        #            #print("data_wanted is", data_wanted)
        #            output_file.write(" ".join(data_wanted) + "\n")
        #    print("Done writing file:", this_file_name_output)

if __name__=="__main__":
    exprs_file = """/home/zas1024/gene/wqflask/wqflask/pylmm/data/mdp.exprs.1"""
    genotype_file = """/home/zas1024/gene/wqflask/wqflask/pylmm/data/mdp.snps.1000"""
    PrepData(pheno_vector, genotype_file)