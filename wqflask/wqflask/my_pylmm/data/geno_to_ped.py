from __future__ import absolute_import, division, print_function

import csv

class ConvertToPed(object):

    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        
    def convert(self):
    
        self.haplotype_notation = {
        '@mat': "1",
        '@pat': "0",
        '@het': "0.5",
        '@unk': "NA"
        }
        
        with open(self.output_file, "w") as self.output_fh:
            self.process_csv()
        