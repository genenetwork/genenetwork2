# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Drs. Robert W. Williams and Xiaodong Zhou (2010)
# at rwilliams@uthsc.edu and xzhou15@uthsc.edu
#
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/08/10
#
# Last updated by GeneNetwork Core Team 2010/10/20

#########################################
# A class for the information of a gene
# An instance of this will be a gene
# it is used by GeneListAnnot class
#########################################


class GeneAnnot:
   geneSymbol = None # Initialize variables
   txStart = -1
   txEnd = -1
   Strand = ''
   exon_start = []
   exon_end = []
   cdsStart = -1
   cdsEnd = -1
   def __init__(self, query_result):
      self.geneSymbol, self.txStart, self.txEnd, self.Strand, exonStart, exonEnd, self.cdsStart, self.cdsEnd = query_result
      if exonStart and exonEnd:
         exon_s= exonStart.split(',')
         exon_e = exonEnd.split(',')
         self.exon_start = [int(s) for s in exon_s[:-1]]
         self.exon_end = [int(s) for s in exon_e[:-1]]
         #debug.appendoutFile("%d %d"%(self.exon_start[0], self.exon_end[0]))
      
   def matchTranscript(self, pos):
      ''' 1: cds; 2: 2k upstream; 3: 2k downstream; -1: outside; -2: no data'''
      locus_type = -1
      distance = 0
      
      if (not self.txStart) or (not self.txEnd):             # no data
          locus_type = -2
      elif (pos >= self.txStart) and (pos <=self.txEnd):
          locus_type = 1  
      elif (pos <self.txStart) and (pos > self.txStart - 0.002):
          locus_type = 2
          distance = self.txStart - pos
      elif (pos > self.txEnd) and (pos < self.txEnd + 0.002):
          locus_type = 3
          distance = pos - self.txEnd
                         
      return [locus_type, distance]
   
   def matchDomain(self, pos):    
      domain_type = None
      function = None

      num =  len(self.exon_start)             
      if not domain_type:        #not UTR        
        bp = pos * 1000000    
        for i in range(0, num):
         if (bp >= self.exon_start[i]) and (bp <= self.exon_end[i]):
           num_index = i +1
           if self.Strand == '-':
              num_index = num - i
           domain_type = "Exon %d"% (num_index)         
           if self.cdsStart and self.cdsEnd:         # then this site in exon can be UTR or stop codon, given cds
            if self.Strand == '+':
               if pos < self.cdsStart:
                  domain_type = "5' UTR"
               elif pos > self.cdsEnd:
                  domain_type = "3' UTR"        
               elif (pos <= self.cdsEnd) and (pos > self.cdsEnd-0.000003):
                  function =  "Stop Codon"            
            elif self.Strand == '-':
               if pos < self.cdsStart:
                  domain_type = "3' UTR"
               elif pos > self.cdsEnd:
                  domain_type = "5' UTR"
               elif (pos >= self.cdsStart) and (pos < self.cdsStart+0.000003):  
                  function = "Stop Codon"              
         
        if not domain_type:
           for j in range (0, len(self.exon_start) -1) :                      # not the last exon
                num_index = j +1
                if self.Strand == '-':
                    num_index = num - j-1           
                if (bp <= self.exon_end[j] + 2) and (bp > self.exon_end[j]) :
                    domain_type = "Intron %d; Splice"% (num_index)                  #start splice 
                    
        if not domain_type: 
           for k in range (1, len(self.exon_start)):                          # not the first exon
                num_index = k +1
                if self.Strand == '-':
                    num_index = num - k -1              
                if (bp >= self.exon_start[k] -2) and (bp <  self.exon_start[k]):
                    domain_type = "Intron %d; Splice"% (num_index)                    # end splice
                    
        if not domain_type: 
           for i in range (1, len(self.exon_start)):
                num_index = i
                if self.Strand == '-':
                    num_index = num - i               
                if (bp > self.exon_end[i-1]) and (bp < self.exon_start[i]):
                   domain_type = "Intron %d"%num_index
    
      return [domain_type, function] 
      
