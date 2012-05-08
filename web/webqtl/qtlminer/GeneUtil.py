import string
import os


from base import webqtlConfig


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






def loadGenesForQTLminer(cursor, chrName, diffCol, startMb, endMb, webqtlDb =None, species='mouse', databaseA='HC_M2_0606_P', databaseB='HC_M2CB_1205_R', databaseC='Illum_LXS_Hipp_loess0807', str1='C57BL/6J', str2='DBA/2J'):
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


#		fpText = open(os.path.join(webqtlConfig.TMPDIR, "strains") + str(j) + '.txt','wb')
#		fpText.write("strain:  '%d'  \n" % thisone  )
#		fpText.close()
#		strainids.append(thisone)



	
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

## get pathways

			cursor.execute("""
			    select 
					pathway						
				FROM
				    kegg.mmuflat
				where 
					gene = '%s' 
				""" % (newdict["GeneID"]) )
				
			resAAA = cursor.fetchall()
			if resAAA:
				myFields = ['pathways']
				for j, item in enumerate(myFields):
					temp = []
					for k in resAAA:
						temp.append(k[j])
					newdict["pathways"] = temp 
			
			cursor.execute("""
			    select 
					name						
				FROM
				    kegg.mmuflat
				where 
					gene = '%s' 
				""" % (newdict["GeneID"]) )
				
			resAAA = cursor.fetchall()
			if resAAA:
				myFields = ['pathwaynames']
				for j, item in enumerate(myFields):
					temp = []
					for k in resAAA:
						temp.append(k[j])
					newdict["pathwaynames"] = temp 

## get GO terms

			cursor.execute("""
			    SELECT
				  distinct go.term.name
				FROM   go.gene_product
				  INNER JOIN go.dbxref ON (go.gene_product.dbxref_id=go.dbxref.id)
				  INNER JOIN go.association ON (go.gene_product.id=go.association.gene_product_id)
				  INNER JOIN go.term ON (go.association.term_id=go.term.id)
				WHERE
				  go.dbxref.xref_key = (select mgi from go.genemgi where gene='%s' limit 1)
				AND
				  go.dbxref.xref_dbname = 'MGI'
				AND
				  go.term.term_type='biological_process'
				""" % (newdict["GeneID"]) )

			resAAA = cursor.fetchall()
			if resAAA:
				myFields = ['goterms']
				for j, item in enumerate(myFields):
					temp = []
					for k in resAAA:
						temp.append(k[j])
					newdict["goterms"] = temp 
			





			newdict["snpDensity"] = newdict["snpCount"] = newdict["snpCountall"] = newdict["snpCountmis"] = newdict["snpCountBXD"] = newdict["snpCountmissel"] = 0

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



#self.cursor.execute("SELECT geneSymbol, chromosome, txStart, txEnd from GeneList where SpeciesId= 1 and geneSymbol = %s", opt.geneName)



			
			## search with gene name... doesnt matter. it changed to start and end position anyway
			##self.cursor.execute("SELECT geneSymbol, chromosome, txStart, txEnd from GeneList where SpeciesId= 1 and geneSymbol = %s", newdict["GeneSymbol"])


			#count SNPs for all strains
			cursor.execute("""
			     SELECT 
				distinct SnpAll.Id
			     from 
			        SnpAll 
			     where 
			        SpeciesId = '1' and SnpAll.Chromosome = '%s' AND 
				    SnpAll.Position >= %2.6f and SnpAll.Position < %2.6f AND
				    SnpAll.Exon='Y'
				""" % (newdict["Chromosome"], newdict["TxStart"], newdict["TxEnd"]))
			snpfetch = cursor.fetchall()
			newdict["snpCountmis"] = len(snpfetch)

## 			# count SNPs for selected strains
			
			sql = """SELECT 
					distinct SnpAll.Id, `%s`, `%s`
				from 
					SnpAll, SnpPattern 
				where 
					SpeciesId = '1' and SnpAll.Chromosome = '%s' AND 
					SnpAll.Position >= %2.6f and SnpAll.Position < %2.6f and SnpAll.Id = SnpPattern.SnpId AND 
					SnpPattern.`%s` != SnpPattern.`%s` AND
					SnpAll.Exon='Y'
					""" % (str1, str2, newdict["Chromosome"], newdict["TxStart"], newdict["TxEnd"], str1, str2)
			cursor.execute(sql)
			ressnp = cursor.fetchall()
			newdict["snpCountmissel"] = len(ressnp)
			newdict["hassnp"] = 'n'
			if len(ressnp)>0 :
				newdict["hassnp"]= 'y'
##          ####################################### NEW NEW NEW







			# count Indels for BXD mice
			cursor.execute("""
				SELECT 
				   distinct IndelAll.Name, IndelAll.Chromosome, IndelAll.SourceId, IndelAll.Mb_start,
				   IndelAll.Mb_end, IndelAll.Strand, IndelAll.Type, IndelAll.Size, IndelAll.InDelSequence,
				   SnpSource.Name  
				from 
				   SnpSource, IndelAll
				where 
				   IndelAll.SpeciesId = '1' and IndelAll.Chromosome = '%s' AND 
				   IndelAll.Mb_start >= %2.6f and IndelAll.Mb_start < (%2.6f+.0010) AND
				   SnpSource.Id = IndelAll.SourceId 
				   order by IndelAll.Mb_start
				""" % (newdict["Chromosome"], newdict["TxStart"], newdict["TxEnd"]))
				
			ressnp = cursor.fetchall()
			newdict["indelCountBXD"] = len(ressnp)
			newdict["hasindel"] = 'n'
			newdict["hasexpr"] = 'n'
			newdict["hascis"] = 'n'
			newdict["score"] = 0
			if len(ressnp)>0 :
				newdict["hasindel"]= 'y'

## #			cursor.execute("""
## #				select 
## #					Name from ProbeSet
## #				where 
## #					GeneId = '%s' AND ChipId=4 limit 1
## #			""" % (newdict["GeneID"]))
## #			if species=='mouse':
## #				cursor.execute("""
## #					select 
## #						Name from ProbeSet
## #					where 
## #						GeneId = '%s' AND ChipId=4
## #				""" % (newdict["GeneID"]))
## #				results = cursor.fetchall()
## #				psets = []
## #				for item in results:
## #					psets.append(item)
## #				newdict["probeset"] = psets 
## #				
## #			else:
## #				newdict["probeset"] = "empty"




			if species=='mouse':
				cursor.execute("""
					select 
						distinct 0,
						ProbeSet.Name as TNAME,
						round(ProbeSetXRef.Mean,1) as TMEAN,
						round(ProbeSetXRef.LRS,1) as TLRS,
						ProbeSet.Chr_num as TCHR_NUM,
						ProbeSet.Mb as TMB,
						ProbeSet.Symbol as TSYMBOL,
						ProbeSet.name_num as TNAME_NUM
						FROM  ProbeSetXRef, ProbeSetFreeze, ProbeSet
					where 
						( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,
						alias,GenbankId,UniGeneId, Probe_Target_Description)
						AGAINST ('%s' IN BOOLEAN MODE) )
						and ProbeSet.symbol = '%s'
						and ProbeSet.Id = ProbeSetXRef.ProbeSetId
						and ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
						and ProbeSetFreeze.Id = (select Id from ProbeSetFreeze where Name='%s' limit 1)
				""" % (newdict["GeneSymbol"],newdict["GeneSymbol"],databaseA))
				resA = cursor.fetchall()
				
				if resA:
					myFields = ['dummyA','probesetA','meanA','newlrsA','probesetchrA','probesetmbA','probesetsymbolA','probesetnamenumA']

#					fpText = open(os.path.join(webqtlConfig.TMPDIR, "res") + '.txt','wb')
					#fpText.write("newdictgeneid  '%s'  \n" % newdict["GeneId"])
					for j, item in enumerate(myFields):
						temp = []
						for k in resA:
							#							fpText.write("j: result:  '%s'  \n" % k[j])
							temp.append(k[j])
						newdict[item] = temp 
					#					fpText.close()


					# put probesetcisA here
				
					cursor.execute("""
					select 
						distinct 0,
						if( (ProbeSet.Chr = Geno.Chr AND ProbeSetXRef.LRS > 10.0000000  and ABS(ProbeSet.Mb-Geno.Mb) < 10.0000000  ) , concat('yes(',round(ProbeSetXRef.LRS,1),')') , 'no') as cis
						FROM  Geno, ProbeSetXRef, ProbeSetFreeze, ProbeSet
					where 
						( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,
						alias,GenbankId,UniGeneId, Probe_Target_Description)
						AGAINST ('%s' IN BOOLEAN MODE) )
						and ProbeSet.symbol = '%s'
						and ProbeSet.Id = ProbeSetXRef.ProbeSetId
						and Geno.SpeciesId=1 #XZ: I add this line to speed up query
						and ProbeSetXRef.Locus = Geno.name
						and ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
						and ProbeSetFreeze.Id = (select Id from ProbeSetFreeze where Name='%s' limit 1)
						""" % (newdict["GeneSymbol"],newdict["GeneSymbol"],databaseA))

					resA2 = cursor.fetchall()
					if resA2:
						myFields = ['dummyA2','probesetcisA']
						for j, item in enumerate(myFields):
							temp = []
							for k in resA2:
								#							fpText.write("j: result:  '%s'  \n" % k[j])
								temp.append(k[j])
							newdict[item] = temp 
					else:
						newdict['probesetcisA'] = ''



					# specially for this dataset only
					newdict["hasexpr"] = 'n'
					if len(newdict["meanA"])>0:
						for mym in newdict["meanA"]:
							if mym>8:
								newdict["hasexpr"] = 'y'

					# specially for this dataset only
					newdict["hascis"] = 'n'
					if len(newdict["probesetcisA"])>0:
						for mym in newdict["probesetcisA"]:
							if mym != 'no':
								newdict["hascis"] = 'y'
			
			else:
				myFields = ['dummyA','probesetA,''meanA','newlrsA','probesetchrA','probesetmbA','probesetsymbolA','probesetnamenumA', 'probesetcisA']
				for j, item in enumerate(myFields):
					newdict[item] = "--"

				# specially for this dataset only
				newdict["hasexpr"] = 'n'
				newdict["hascis"] = 'n'
				newdict["score"] = 0

##########################  FOR B

			newdict["score"] = 0
			if newdict["hassnp"] == 'y':
				newdict["score"] = newdict["score"] + 1					
			if newdict["hasexpr"] == 'y':
				newdict["score"] = newdict["score"] + 1					
			if newdict["hasindel"] == 'y':
				newdict["score"] = newdict["score"] + 1					
			if newdict["hascis"] == 'y':
				newdict["score"] = newdict["score"] + 1					
							
							
					
			if species=='mouse':
				cursor.execute("""
					select 
						distinct 0,
						ProbeSet.Name as TNAME,
						round(ProbeSetXRef.Mean,1) as TMEAN,
						round(ProbeSetXRef.LRS,1) as TLRS,
						ProbeSet.Chr_num as TCHR_NUM,
						ProbeSet.Mb as TMB,
						ProbeSet.Symbol as TSYMBOL,
						ProbeSet.name_num as TNAME_NUM
						FROM  ProbeSetXRef, ProbeSetFreeze, ProbeSet
					where 
						( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,
						alias,GenbankId,UniGeneId, Probe_Target_Description)
						AGAINST ('%s' IN BOOLEAN MODE) )
						and ProbeSet.symbol = '%s'
						and ProbeSet.Id = ProbeSetXRef.ProbeSetId
						and ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
						and ProbeSetFreeze.Id = (select Id from ProbeSetFreeze where Name='%s' limit 1)
				""" % (newdict["GeneSymbol"],newdict["GeneSymbol"],databaseB))

				resB = cursor.fetchall()
				if resB:
					myFields = ['dummyB','probesetB','meanB','newlrsB','probesetchrB','probesetmbB','probesetsymbolB','probesetnamenumB']

#					fpText = open(os.path.join(webqtlConfig.TMPDIR, "res") + '.txt','wb')
					#fpText.write("newdictgeneid  '%s'  \n" % newdict["GeneId"])
					for j, item in enumerate(myFields):
						temp = []
						for k in resB:
							#							fpText.write("j: result:  '%s'  \n" % k[j])
							temp.append(k[j])
						newdict[item] = temp 
					#					fpText.close()


					# put probesetcisB here
					cursor.execute("""
					select 
						distinct 0,
						if( (ProbeSet.Chr = Geno.Chr AND ProbeSetXRef.LRS > 10.0000000  and ABS(ProbeSet.Mb-Geno.Mb) < 10.0000000  ) , concat('yes(',round(ProbeSetXRef.LRS,1),')') , 'no') as cis
						FROM  Geno, ProbeSetXRef, ProbeSetFreeze, ProbeSet
					where 
						( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,
						alias,GenbankId,UniGeneId, Probe_Target_Description)
						AGAINST ('%s' IN BOOLEAN MODE) )
						and ProbeSet.symbol = '%s'
						and ProbeSet.Id = ProbeSetXRef.ProbeSetId
						and Geno.SpeciesId=1 #XZ: I add this line to speed up query
						and ProbeSetXRef.Locus = Geno.name
						and ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
						and ProbeSetFreeze.Id = (select Id from ProbeSetFreeze where Name='%s' limit 1)
						""" % (newdict["GeneSymbol"],newdict["GeneSymbol"],databaseB))

					resB2 = cursor.fetchall()
					if resB2:
						myFields = ['dummyB2','probesetcisB']
						for j, item in enumerate(myFields):
							temp = []
							for k in resB2:
								#							fpText.write("j: result:  '%s'  \n" % k[j])
								temp.append(k[j])
							newdict[item] = temp 
					else:
						newdict['probesetcisB'] = ''

				
			else:
				myFields = ['dummyB','probesetB,''meanB','newlrsB','probesetchrB','probesetmbB','probesetsymbolB','probesetnamenumB', 'probesetcisB']
				for j, item in enumerate(myFields):
					newdict[item] = "--"



##########################


##########################  FOR C

					
			if species=='mouse':
				cursor.execute("""
					select 
						distinct 0,
						ProbeSet.Name as TNAME,
						round(ProbeSetXRef.Mean,1) as TMEAN,
						round(ProbeSetXRef.LRS,1) as TLRS,
						ProbeSet.Chr_num as TCHR_NUM,
						ProbeSet.Mb as TMB,
						ProbeSet.Symbol as TSYMBOL,
						ProbeSet.name_num as TNAME_NUM
						FROM  ProbeSetXRef, ProbeSetFreeze, ProbeSet
					where 
						( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,
						alias,GenbankId,UniGeneId, Probe_Target_Description)
						AGAINST ('%s' IN BOOLEAN MODE) )
						and ProbeSet.symbol = '%s'
						and ProbeSet.Id = ProbeSetXRef.ProbeSetId
						and ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
						and ProbeSetFreeze.Id = (select Id from ProbeSetFreeze where Name='%s' limit 1)
				""" % (newdict["GeneSymbol"],newdict["GeneSymbol"],databaseC))

				resC = cursor.fetchall()
				if resC:
					myFields = ['dummyC','probesetC','meanC','newlrsC','probesetchrC','probesetmbC','probesetsymbolC','probesetnamenumC']

#					fpText = open(os.path.join(webqtlConfig.TMPDIR, "res") + '.txt','wb')
					#fpText.write("newdictgeneid  '%s'  \n" % newdict["GeneId"])
					for j, item in enumerate(myFields):
						temp = []
						for k in resC:
							#							fpText.write("j: result:  '%s'  \n" % k[j])
							temp.append(k[j])
						newdict[item] = temp 
					#					fpText.close()


					# put probesetcisC here
					cursor.execute("""
					select 
						distinct 0,
						if( (ProbeSet.Chr = Geno.Chr AND ProbeSetXRef.LRS > 10.0000000  and ABS(ProbeSet.Mb-Geno.Mb) < 10.0000000  ) , concat('yes(',round(ProbeSetXRef.LRS,1),')') , 'no') as cis
						FROM  Geno, ProbeSetXRef, ProbeSetFreeze, ProbeSet
					where 
						( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,
						alias,GenbankId,UniGeneId, Probe_Target_Description)
						AGAINST ('%s' IN BOOLEAN MODE) )
						and ProbeSet.symbol = '%s'
						and ProbeSet.Id = ProbeSetXRef.ProbeSetId
						and Geno.SpeciesId=1 #XZ: I add this line to speed up query
						and ProbeSetXRef.Locus = Geno.name
						and ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
						and ProbeSetFreeze.Id = (select Id from ProbeSetFreeze where Name='%s' limit 1)
						""" % (newdict["GeneSymbol"],newdict["GeneSymbol"],databaseC))

					resC2 = cursor.fetchall()
					if resC2:
						myFields = ['dummyC2','probesetcisC']
						for j, item in enumerate(myFields):
							temp = []
							for k in resC2:
								#							fpText.write("j: result:  '%s'  \n" % k[j])
								temp.append(k[j])
							newdict[item] = temp 
					else:
						newdict['probesetcisC'] = ''

			else:
				myFields = ['dummyC','probesetC,''meanC','newlrsC','probesetchrC','probesetmbC','probesetsymbolC','probesetnamenumC', 'probesetcisC']
				for j, item in enumerate(myFields):
					newdict[item] = "--"


			             
			
			


			
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

			#newdict['RUDI']='hallo allemaal'
				
			GeneList.append(newdict)

					
	return GeneList


