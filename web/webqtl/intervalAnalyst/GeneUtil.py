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

import string

#Just return a list of dictionaries
#each dictionary contains sub-dictionary
def loadGenes(cursor, chrName, diffCol, startMb, endMb, webqtlDb =None, species='mouse'):
	#cursor.execute("desc GeneList")
	#results = cursor.fetchall()
	#fetchFields = map(lambda X:X[0], results)
	fetchFields = ['SpeciesId', 'Id', 'GeneSymbol', 'GeneDescription', 'Chromosome', 'TxStart', 'TxEnd', 
	'Strand', 'GeneID', 'NM_ID', 'kgID', 'GenBankID', 'UnigenID', 'ProteinID', 'AlignID', 
	'exonCount', 'exonStarts', 'exonEnds', 'cdsStart', 'cdsEnd']
	
	##List All Species in the Gene Table
	speciesDict = {}
	cursor.execute("select Species.Name, GeneList.SpeciesId from Species, GeneList where \
			GeneList.SpeciesId = Species.Id group by GeneList.SpeciesId")
	results = cursor.fetchall()
	for item in results:
		speciesDict[item[0]] = item[1]
	
	##List current Species and other Species
	speciesId = speciesDict[species]
	otherSpecies = map(lambda X: [X, speciesDict[X]], speciesDict.keys())
	otherSpecies.remove([species, speciesId])

	cursor.execute("""SELECT %s from GeneList 
						where 
					SpeciesId = %d AND Chromosome = '%s' AND
					((TxStart > %f and TxStart <= %f) OR (TxEnd > %f and TxEnd <= %f))
					order by txStart
					""" 
					% (string.join(fetchFields, ", "), speciesId, chrName, startMb, endMb, startMb, endMb))
	results = cursor.fetchall()
	GeneList = []

	if results:
		for result in results:
			newdict = {}
			for j, item in enumerate(fetchFields):
				newdict[item] = result[j]
			#count SNPs if possible	
			if diffCol and species=='mouse':
				cursor.execute("""
					select 
						count(*) from BXDSnpPosition
					where 
						Chr = '%s' AND Mb >= %2.6f AND Mb < %2.6f AND
						StrainId1 = %d AND StrainId2 = %d
				""" % (chrName, newdict["TxStart"], newdict["TxEnd"], diffCol[0], diffCol[1]))
				newdict["snpCount"] = cursor.fetchone()[0]
				newdict["snpDensity"] = newdict["snpCount"]/(newdict["TxEnd"]-newdict["TxStart"])/1000.0
			else:
				newdict["snpDensity"] = newdict["snpCount"] = 0
			
			try:
				newdict['GeneLength'] = 1000.0*(newdict['TxEnd'] - newdict['TxStart'])
			except:
				pass
			
			#load gene from other Species by the same name
			for item in otherSpecies:
				othSpec, othSpecId = item
				newdict2 = {}
				
				cursor.execute("SELECT %s from GeneList where SpeciesId = %d and geneSymbol= '%s' limit 1" % 
							(string.join(fetchFields, ", "), othSpecId, newdict["GeneSymbol"]))
				resultsOther = cursor.fetchone()
				if resultsOther:
					for j, item in enumerate(fetchFields):
						newdict2[item] = resultsOther[j]
							
					#count SNPs if possible, could be a separate function	
					if diffCol and othSpec == 'mouse':
						cursor.execute("""
							select
								count(*) from BXDSnpPosition
							where
								Chr = '%s' AND Mb >= %2.6f AND Mb < %2.6f AND
								StrainId1 = %d AND StrainId2 = %d
							""" % (chrName, newdict["TxStart"], newdict["TxEnd"], diffCol[0], diffCol[1]))

						newdict2["snpCount"] = cursor.fetchone()[0]
						newdict2["snpDensity"] = newdict2["snpCount"]/(newdict2["TxEnd"]-newdict2["TxStart"])/1000.0
					else:
						newdict2["snpDensity"] = newdict2["snpCount"] = 0
						
					try:
						newdict2['GeneLength'] = 1000.0*(newdict2['TxEnd'] - newdict2['TxStart'])
					except:
						pass
						
				newdict['%sGene' % othSpec] = newdict2
				
			GeneList.append(newdict)

	return GeneList


