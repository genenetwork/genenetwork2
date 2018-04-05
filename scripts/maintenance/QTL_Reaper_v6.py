####### To run this program do: python QTL_Reaper_v2.py 235
#Where 163 is the ProbeSetFreeze Id of the database that we want to calculate #the LRS
#!/usr/bin/python
import sys
import os
import reaper
import MySQLdb
import time

con = MySQLdb.Connect(db='db_webqtl',user='username',passwd='', host="localhost")
cursor = con.cursor()

genotypeDir = '/gnshare/gn/web/genotypes/'
genotype_1 = reaper.Dataset()

#####get all of the genotypes
cursor.execute('select Id, Name from InbredSet')
results = cursor.fetchall()
InbredSets = {}
for item in results:
	InbredSets[item[0]] = genotypeDir+str(item[1])+'.geno'

ProbeSetFreezeIds=sys.argv[1:]
if ProbeSetFreezeIds:
	#####convert the Ids to integer
	ProbeSetFreezeIds=map(int, ProbeSetFreezeIds)

else:
	#####get all of the dataset that need be updated
	cursor.execute('select distinct(ProbeSetFreezeId) from ProbeSetXRef where pValue is NULL order by ProbeSetFreezeId desc')
	results = cursor.fetchall()
	ProbeSetFreezeIds = []
	for item in results:
		ProbeSetFreezeIds.append(item[0])

####human dataset can NOT use this program calculate the LRS, ignore it
if ProbeSetFreezeIds.__contains__(215):
	ProbeSetFreezeIds.remove(215)

#output_file = open ('/home/xzhou/work/DatabaseTools/cal_LRS_Additive_result.txt', 'w')

#####update 
for ProbeSetFreezeId in ProbeSetFreezeIds:
	cursor.execute("""
		select InbredSetId 
		from ProbeFreeze, ProbeSetFreeze 
		where ProbeFreeze.Id=ProbeSetFreeze.ProbeFreezeId and ProbeSetFreeze.Id=%d
	"""%ProbeSetFreezeId);

	InbredSetId = cursor.fetchone()[0]
	if InbredSetId==3:
		InbredSetId=1
	#if InbredSetId==12:
	#	InbredSetId=2

	print ProbeSetFreezeId, InbredSets[InbredSetId]

	genotype_1.read(InbredSets[InbredSetId])
	locuses = []
	for geno in genotype_1:
		for locus in geno:
			locuses.append(locus.name)

	cursor.execute('select ProbeSetId, Locus, DataId from ProbeSetXRef where ProbeSetFreezeId=%s'%ProbeSetFreezeId)
	ProbeSetXRefInfos = cursor.fetchall()

	kj=0
	for aProbeSetXRef in ProbeSetXRefInfos:
		ProbeSetId, Locus, DataId = aProbeSetXRef
		prgy = genotype_1.prgy

		cursor.execute("select Strain.Name, ProbeSetData.value from Strain, ProbeSetData where Strain.Id = ProbeSetData.StrainId and ProbeSetData.Id = %d" % DataId)
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
		if not _strains or not _values:
			continue
		
		if len(_strains) < 8:
			continue
		qtlresults = genotype_1.regression(strains = _strains, trait = _values)
		_max = max(qtlresults)
		_locus = _max.locus.name
		_additive = _max.additive
		_max = _max.lrs

		#output_file.write('%s\t%s\t%s\t%s\t%s\n' % (ProbeSetFreezeId, ProbeSetId, _locus, _max, _additive))
		
		# _max(LRS) maybe is infinite sometimes, so define it as a very big number
		if _max == float('inf'):
			_max = 10000

		cursor.execute('update ProbeSetXRef set Locus=%s, LRS=%s, additive=%s where ProbeSetId=%s and ProbeSetFreezeId=%s', \
				(_locus, _max, _additive, ProbeSetId, ProbeSetFreezeId))

		kj += 1
		if kj%1000==0:
			print ProbeSetFreezeId, InbredSets[InbredSetId],kj


	print ProbeSetFreezeIds
