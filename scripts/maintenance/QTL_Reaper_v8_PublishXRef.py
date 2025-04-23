# Edited by Zach 2022-08-23	

#!/usr/bin/python

# To run this program do: python QTL_Reaper_cal_lrs.py
# To run this program do: python QTL_Reaper_cal_lrs.py 1 4 (PublishFreeze id list)

# Where 1,4 are the PublishFreeze Id of the database that we want to calculate the LRS

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
# Contact Drs. Robert W. Williams and Lei Yan (2012)
# at rwilliams@uthsc.edu and lyan6@uthsc.edu
#
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2012/05/02
# Last updated by GeneNetwork Core Team 2012/05/03

import sys
import os
import reaper
import MySQLdb
import time

db='db_webqtl'
genotypeDir='/mount/space2/lily-clone/gnshare/gn/web/genotypes/'

#con = MySQLdb.Connect(db=db,user='webqtl',passwd='webqtl', host="localhost")
#con = MySQLdb.Connect(db=db,user='*',passwd='*', host="172.23.18.213")
#con = MySQLdb.Connect(db=db,user='*',passwd='*', host="tux04.genenetwork.org")
con = MySQLdb.Connect(db=db,user='*',passwd='*', host="tux02.genenetwork.org")
cursor = con.cursor()
genotype_1 = reaper.Dataset()
#####get all of the genotypes
cursor.execute('select Id, Name from InbredSet')
results = cursor.fetchall()
InbredSets = {}
for item in results:
	InbredSets[item[0]] = genotypeDir+str(item[1])+'.geno'
print("InbredSets: %s\n" % InbredSets)

PublishFreezeIds=sys.argv[1:]
if PublishFreezeIds:
	#####convert the Ids to integer
	PublishFreezeIds=map(int, PublishFreezeIds)
else:
	#####get all of the dataset that need be updated
	cursor.execute('select distinct(PublishFreeze.Id) from PublishFreeze, PublishXRef, InbredSet where PublishFreeze.InbredSetId = PublishXRef.InbredSetId \
					and PublishFreeze.InbredSetId = InbredSet.Id and not InbredSet.SpeciesId = 4 order by PublishFreeze.Id desc')
	results = cursor.fetchall()
	PublishFreezeIds = []
	for item in results:
		PublishFreezeIds.append(item[0])
print("PublishFreezeIds: %s" % PublishFreezeIds)
#####update 
for PublishFreezeId in PublishFreezeIds:
	print("")
	cursor.execute("""
		select InbredSetId 
		from PublishFreeze 
		where PublishFreeze.Id=%d
	"""%PublishFreezeId);

	InbredSetId = cursor.fetchone()[0]
	if InbredSetId==3:
		InbredSetId=1
	#if InbredSetId==12:
	#	InbredSetId=2

	print("PublishFreezeId=%s, InbredSetId=%s, InbredSetName=%s" % (PublishFreezeId, InbredSetId, InbredSets[InbredSetId]))

	genotype_1.read(InbredSets[InbredSetId])
	locuses = []
	for geno in genotype_1:
		for locus in geno:
			locuses.append(locus.name)
	print("locuses: %s" % len(locuses))

	if len(locuses) == 0:
		continue

	cursor.execute('select PhenotypeId, Locus, DataId, Phenotype.Post_publication_description from PublishXRef, Phenotype where PublishXRef.PhenotypeId = Phenotype.Id and InbredSetId=%s' % InbredSetId)
	PublishXRefInfos = cursor.fetchall()
	print("PublishXRefInfos: %s" % len(PublishXRefInfos))

	kj=0
	for aPublishXRef in PublishXRefInfos:
		print(aPublishXRef)
		PhenotypeId, Locus, DataId, Phenotype_description = aPublishXRef
		cursor.execute('select LRS from PublishXRef where PhenotypeId=%s and InbredSetId=%s' % (PhenotypeId, InbredSetId))
		#if not cursor.fetchone()[0] is None:
	#		#continue
	#		pass
		prgy = genotype_1.prgy

		cursor.execute("select Strain.Name, PublishData.value from Strain, PublishData where Strain.Id = PublishData.StrainId and PublishData.Id = %d" % DataId)
		results = cursor.fetchall()
		if not results:
			continue
		_strains = []
		_values = []
		for item2 in results:
			strain, value = item2
			if strain in prgy:
				_strains.append(strain)
				_values.append(value)

		if not _strains or not _values or len(_values) < 8 or len(_strains) < 8:
			continue
		qtlresults = genotype_1.regression(strains = _strains, trait = _values)
		_max = max(qtlresults)
		if _max == 0:
			print("TRAIT:", PhenotypeId)
			print("VALUES:", str(_values))
		_locus = _max.locus.name
		_additive = _max.additive
		_max = _max.lrs

		if str(_max) == 'inf': # if the calculation returns 'inf' (infinite) then replace with a very high non-infinite value (LOD=100, LRS=460). This happens when the phenotype and genotypes are identical (r = 1 or -1).
			_max = 460

		cursor.execute('update PublishXRef set Locus=%s, LRS=%s, additive=%s where PhenotypeId=%s and InbredSetId=%s', (_locus, _max, _additive, PhenotypeId, InbredSetId))
		con.commit()

		if kj%1000==0:
			print("[%s]" % kj)
		kj += 1

	print("finish")
