#!/usr/bin/python

from __future__ import absolute_import, print_function, division
import numpy

    
class PrepData(object):
    def __init__(self, exprs_file, snps_file):
        self.exprs_file = exprs_file
        self.snps_file = snps_file
        self.empty_columns = set()
        #self.identify_no_genotype_samples()
        self.identify_empty_samples()
        self.trim_files()

    def identify_empty_samples(self):
        with open(self.exprs_file) as fh:
            for line in fh:
                for pos, item in enumerate(line.split()):
                    if item == "NA":
                        self.empty_columns.add(pos)
        #print("self.empty_columns:", self.empty_columns)
        nums = set(range(0, 176))
        print("not included:", nums-self.empty_columns)
            
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
        for this_file in (self.exprs_file, self.snps_file):
            input_file = open(this_file)
            this_file_name_output = this_file + ".new"
            with open(this_file_name_output, "w") as output:
                for line in input_file:
                    data_wanted = []
                    for pos, item in enumerate(line.split()):
                        if pos in self.empty_columns:
                            continue
                        else:
                            data_wanted.append("%2s" % (item))
                    #print("data_wanted is", data_wanted)
                    output.write(" ".join(data_wanted) + "\n")
            print("Done writing file:", this_file_name_output)

if __name__=="__main__":
    exprs_file = """/home/zas1024/gene/wqflask/wqflask/pylmm/data/mdp.exprs.1"""
    snps_file = """/home/zas1024/gene/wqflask/wqflask/pylmm/data/mdp.snps.1000"""
    PrepData(exprs_file, snps_file)