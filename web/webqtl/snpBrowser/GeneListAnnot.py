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

####################################################################
## Extracting Annotation using GeneList table
## using transcript start and end, cds start and end
## and exon starts and ednds
####################################################################

from base.templatePage import templatePage
from GeneAnnot import GeneAnnot


class GeneListAnnot (templatePage):
    geneAnnot_list = []
    def __init__(self, species, chr, start, end, strand):
       end = "%f"%(float(end)+0.002)          # extend a little bit
       start = "%f"%(float(start)-0.002)
       query_genelist = ''' 
           SELECT GeneSymbol, TxStart, TxEnd, Strand, exonStarts, exonEnds, cdsStart, cdsEnd
           From GeneList
           Where SpeciesId=%d and Chromosome="%s" 
                 and not (TxStart<%s and TxEnd<%s) and not (TxStart>%s and TxEnd>%s)   
           ''' % (species, chr, start, start, end, end)
       #debug.printoutFile(query_genelist)         # old condition: TxStart<=%s and TxEnd>=%s 
       self.openMysql()
       self.cursor.execute(query_genelist)
       gene_results = self.cursor.fetchall();       
       for oneresult in gene_results:
           oneGeneAnnot = GeneAnnot(oneresult)
           self.geneAnnot_list.append(oneGeneAnnot)
           
    def getAnnot4Pos(self, pos):
        #if not self.geneAnnot_list:
         #   return [None, None, None]
        annot_gene = None
        annot_domain = None
        annot_func = None
        min_dist = 99999
        for oneAnnot in self.geneAnnot_list:
            in_transcript, dist = oneAnnot.matchTranscript(pos)
            #debug.printoutFile(in_transcript)
            if in_transcript == 1:
               annot_gene = oneAnnot.geneSymbol
               annot_domain, annot_func = oneAnnot.matchDomain(pos)  
               #annot_domain, annot_func = annots                            
               min_dist = 0
            elif in_transcript == 2:
                # putative promoter
                if dist < min_dist:
                   annot_gene = oneAnnot.geneSymbol
                   if oneAnnot.Strand == '+':
                     annot_domain = "Intergenic;possible promoter"
                   elif oneAnnot.Strand == '-':
                     annot_domain = "Intergenic;possible terminator"
                   min_dist = dist
            elif in_transcript == 3:
                # putative terminator:
                if dist < min_dist:
                   annot_gene = oneAnnot.geneSymbol
                   if oneAnnot.Strand == '+':
                      annot_domain = "Intergenic;possible terminator"
                   if oneAnnot.Strand == '-':
                      annot_domain = "Intergenic;possible promoter"
                   min_dist = dist  
                
        return [annot_gene, annot_domain, annot_func]  
