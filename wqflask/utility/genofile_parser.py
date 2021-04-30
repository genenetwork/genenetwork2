# CTL analysis for GN2
# Author / Maintainer: Danny Arends <Danny.Arends@gmail.com>

import sys
import os
import glob
import traceback
import gzip


import simplejson as json

from pprint import pformat as pf


class Marker:
  def __init__(self):
    self.name = None
    self.chr = None
    self.cM = None
    self.Mb = None
    self.genotypes = []


class ConvertGenoFile:

  def __init__(self, input_file):
    self.mb_exists = False
    self.cm_exists = False
    self.markers = []

    self.latest_row_pos = None
    self.latest_col_pos = None

    self.latest_row_value = None
    self.latest_col_value = None
    self.input_fh = open(input_file)
    print("!!!!!!!!!!!!!!!!PARSER!!!!!!!!!!!!!!!!!!")
    self.haplotype_notation = {
      '@mat': "1",
      '@pat': "2",
      '@het': "-999",
      '@unk': "-999"
    }
    self.configurations = {}

  def process_rows(self):
    for self.latest_row_pos, row in enumerate(self.input_fh):
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
            skip = 2 + self.cm_exists + self.mb_exists
            self.individuals = row.split()[skip:]
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

  def process_csv(self):
    for row in self.process_rows():
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
        if genotype.upper().strip() in self.configurations:
          this_marker.genotypes.append(self.configurations[genotype.upper().strip()])
        else:
          print("WARNING:", genotype.upper())
          this_marker.genotypes.append("NA")
      self.markers.append(this_marker.__dict__)

