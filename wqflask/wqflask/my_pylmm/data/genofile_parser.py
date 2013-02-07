#!/usr/bin/python

from __future__ import print_function, division, absolute_import
import csv
import os
import glob
import traceback

class EmptyConfigurations(Exception): pass

class ConvertGenoFile(object):

    def __init__(self, input_file, output_file):
        
        self.input_file = input_file
        self.output_file = output_file
        
        self.latest_row_pos = None
        self.latest_col_pos = None
        
        self.latest_row_value = None
        self.latest_col_value = None
        
    def convert(self):

        self.prefer_config = {
            '@mat': "1",
            '@pat': "0",
            '@het': "0.5",
            '@unk': "NA"
            }
        
        self.configurations = {}
        self.skipped_cols = 3
        
        self.input_fh = open(self.input_file)
        
        
        with open(self.output_file, "w") as self.output_fh:
            self.process_csv()
     
            
        
    #def process_row(self, row):
    #    counter = 0
    #    for char in row:
    #        if char 
    #        counter += 1
     
    def process_csv(self):
        for row_count, row in enumerate(self.process_rows()):
            #self.latest_row_pos = row_count

            for item_count, item in enumerate(row.split()[self.skipped_cols:]):
                # print('configurations:', str(configurations))
                self.latest_col_pos = item_count + self.skipped_cols
                self.latest_col_value = item
                if item_count != 0:
                    self.output_fh.write(" ")
                self.output_fh.write(self.configurations[item.upper()])
                    
            self.output_fh.write("\n")
            
    def process_rows(self):
        for self.latest_row_pos, row in enumerate(self.input_fh):
            self.latest_row_value = row
            # Take care of headers
            if row.startswith('#'):
                continue
            if row.startswith('Chr'):
                if 'Mb' in row.split():
                    self.skipped_cols = 4
                continue
            if row.startswith('@'):
                key, _separater, value = row.partition(':')
                key = key.strip()
                value = value.strip()
                if key in self.prefer_config:
                    self.configurations[value] = self.prefer_config[key]
                continue
            if not len(self.configurations):
                raise EmptyConfigurations
            yield row

    @classmethod
    def process_all(cls, old_directory, new_directory):
        os.chdir(old_directory)
        for input_file in glob.glob("*.geno"):
            group_name = input_file.split('.')[0]
            output_file = os.path.join(new_directory, group_name + ".snps")
            print("%s -> %s" % (input_file, output_file))
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
                print("    Found in row %i at tabular column %i" % (convertob.latest_row_pos,
                                                                convertob.latest_col_pos))
                print("    Column is:", convertob.latest_col_value)
                print("    Row is:", convertob.latest_row_value)
                break


if __name__=="__main__":
    Old_Geno_Directory = """/home/zas1024/gene/web/genotypes/"""
    New_Geno_Directory = """/home/zas1024/gene/web/new_genotypes/"""
    #Input_File = """/home/zas1024/gene/web/genotypes/BXD.geno"""
    #Output_File = """/home/zas1024/gene/wqflask/wqflask/pylmm/data/bxd.snps""" 
    ConvertGenoFile.process_all(Old_Geno_Directory, New_Geno_Directory)
    #ConvertGenoFiles(Geno_Directory)
    
    #process_csv(Input_File, Output_File)