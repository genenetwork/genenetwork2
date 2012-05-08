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

 # The columns that are to be displayed are chosen at the line about 1000, with categories["info"]; this initializes the columns and assigns a 'variable_name' :and: "Display Name"
columnNames = {
	# The following are for ALL VARIANTS
	        'variant':"Variant Type",
	        'snpname':"SNP ID", # SnpAll.Id
		'chromosome':"Chromosome",
		'mb':"Mb",
		'sourceName':"Source",
		'sourceCreated':"Source Created",
		'sourceAdded':"Source Added",
		'sourceId':"Source", 
		'gene':'Gene',
	# The following are for SNP VARIANTS	
		'source':'Source', 
		'chr':'Chr', 
		'snpId':"Submitter ID", #SnpAll.SnpName
		'mbCelera':"Mb (CDS)",
		'rs':"ID",
		'function':"Function",
		'type':"Type",
		'majorCount':"Major Count",
		'minorCount':"Minor Count",
		'missingCount':"Missing Count",
		'class':"Class",
		'flanking5':"Flanking 5'",
		'flanking3':"Flanking 3'",
		'blatScore':"BLAT Score",
		'majorAllele':"Major Allele",
		'minorAllele':"Minor Allele",
		'shortAlleles':'Reference',
		"Proximal_Gap_bp":"Gap",
		'domain':'Domain',
		'ncbi':'NCBI Annotation',
		'conservation':'ConScore',
       # The following are for INDEL VARIANTS
		'indelId':"ID", # Indel.Id Indel
		'indelName':"ID", # Indel.Name
		'indelType':"Type", # Indel.Type
		'indelChr':"InDel Chr", # Indel.Chromosome
		'indelMb_s':"Mb Start", # Indel.Mb_start
		'indelMb_e':"Mb End", # IndelAll.Mb_end
		'indelStrand':"Strand", # IndelAll.Strand
		'indelSize':"Size", # IndelAll.Size
		'indelSeq':"Sequence", # IndelAll.Sequence
}