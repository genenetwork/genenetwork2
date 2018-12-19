#!/usr/bin/python

"""
Convert .geno files to json

This file goes through all of the genofiles in the genofile directory (.geno)
and converts them to json files that are used when running the marker regression
code

"""

from __future__ import print_function, division, absolute_import
import sys
sys.path.append("..")
import os
import glob
import traceback
import gzip

#import numpy as np
#from pyLMM import lmm

import simplejson as json

from pprint import pformat as pf

#from utility.tools import flat_files

class EmptyConfigurations(Exception): pass

        

class Marker(object):
    def __init__(self):
        self.name = None
        self.chr = None
        self.cM = None
        self.Mb = None
        self.genotypes = []

class ConvertGenoFile(object):

    def __init__(self, input_file, output_file):
        
        self.input_file = input_file
        self.output_file = output_file
        
        self.mb_exists = False
        self.cm_exists = False
        self.markers = []
        
        self.latest_row_pos = None
        self.latest_col_pos = None
        
        self.latest_row_value = None
        self.latest_col_value = None
        
    def convert(self):

        self.haplotype_notation = {
            '@mat': "1",
            '@pat': "0",
            '@het': "0.5",
            '@unk': "NA"
            }
        
        self.configurations = {}
        #self.skipped_cols = 3
        
        #if self.input_file.endswith(".geno.gz"):
        #    print("self.input_file: ", self.input_file)
        #    self.input_fh = gzip.open(self.input_file)
        #else:
        self.input_fh = open(self.input_file)
        
        with open(self.output_file, "w") as self.output_fh:
            #if self.file_type == "geno":
            self.process_csv()
            #elif self.file_type == "snps":
            #    self.process_snps_file()


    def process_csv(self):
        for row_count, row in enumerate(self.process_rows()):
            row_items = row.split("\t")

            this_marker = Marker()
            this_marker.name = row_items[1]
            this_marker.chr = row_items[0]
            if self.cm_exists and self.mb_exists:
                this_marker.cM = row_items[2]
                this_marker.Mb = row_items[3]
                genotypes = row_items[4:]
            elif self.cm_exists:
                this_marker.cM = row_items[2]
                genotypes = row_items[3:]
            elif self.mb_exists:
                this_marker.Mb = row_items[2]
                genotypes = row_items[3:]
            else:
                genotypes = row_items[2:]
            for item_count, genotype in enumerate(genotypes):
                if genotype.upper() in self.configurations:
                    this_marker.genotypes.append(self.configurations[genotype.upper()])
                else:
                    this_marker.genotypes.append("NA")
                
            #print("this_marker is:", pf(this_marker.__dict__))   
            #if this_marker.chr == "14":
            self.markers.append(this_marker.__dict__)

        with open(self.output_file, 'w') as fh:
            json.dump(self.markers, fh, indent="   ", sort_keys=True)
                
                # print('configurations:', str(configurations))
                #self.latest_col_pos = item_count + self.skipped_cols
                #self.latest_col_value = item
                
                #if item_count != 0:
                #    self.output_fh.write(" ")
                #self.output_fh.write(self.configurations[item.upper()])
                    
            #self.output_fh.write("\n")


    def process_rows(self):
        for self.latest_row_pos, row in enumerate(self.input_fh):
            #if self.input_file.endswith(".geno.gz"):
            #    print("row: ", row)
            self.latest_row_value = row
            # Take care of headers
            if not row.strip():
                continue
            if row.startswith('#'):
                continue
            if row.startswith('Chr'):
                if 'Mb' in row.split():
                    self.mb_exists = True
                if 'cM' in row.split():
                    self.cm_exists = True
                continue
            if row.startswith('@'):
                key, _separater, value = row.partition(':')
                key = key.strip()
                value = value.strip()
                if key in self.haplotype_notation:
                    self.configurations[value] = self.haplotype_notation[key]
                continue
            if not len(self.configurations):
                raise EmptyConfigurations
            yield row

    @classmethod
    def process_all(cls, old_directory, new_directory):
        os.chdir(old_directory)
        for input_file in glob.glob("*"):
            if not input_file.endswith(('geno', '.geno.gz')):
                continue
            group_name = ".".join(input_file.split('.')[:-1])
            output_file = os.path.join(new_directory, group_name + ".json")
            print("%s -> %s" % (
                os.path.join(old_directory, input_file), output_file))
            convertob = ConvertGenoFile(input_file, output_file)
            try:
                convertob.convert()
            except EmptyConfigurations as why:
                print("  No config info? Continuing...")
                #excepted = True
                continue
            except Exception as why:

                print("  Exception:", why)
                print(traceback.print_exc())
                print("    Found in row %s at tabular column %s" % (convertob.latest_row_pos,
                                                                convertob.latest_col_pos))
                print("    Column is:", convertob.latest_col_value)
                print("    Row is:", convertob.latest_row_value)
                break
            
    #def process_snps_file(cls, snps_file, new_directory):
    #    output_file = os.path.join(new_directory, "mouse_families.json")
    #    print("%s -> %s" % (snps_file, output_file))
    #    convertob = ConvertGenoFile(input_file, output_file)
        


if __name__=="__main__":
    Old_Geno_Directory = """/export/local/home/zas1024/gn2-zach/genotype_files/genotype"""
    New_Geno_Directory = """/export/local/home/zas1024/gn2-zach/genotype_files/genotype/json"""
    #Input_File = """/home/zas1024/gene/genotype_files/genotypes/BXD.geno"""
    #Output_File = """/home/zas1024/gene/wqflask/wqflask/pylmm/data/bxd.snps"""
    #convertob = ConvertGenoFile("/home/zas1024/gene/genotype_files/genotypes/SRxSHRSPF2.geno", "/home/zas1024/gene/genotype_files/new_genotypes/SRxSHRSPF2.json")
    #convertob.convert()
    ConvertGenoFile.process_all(Old_Geno_Directory, New_Geno_Directory)
    #ConvertGenoFiles(Geno_Directory)
    
    #process_csv(Input_File, Output_File)