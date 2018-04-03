#!/usr/bin/python2
"""This script use the nearest marker to the transcript as control, increasing permutation rounds according to the p-value"""
########################################################################
# Last Updated Sep 27, 2011 by Xiaodong
# This version fix the bug that incorrectly exclude the first 2 probesetIDs
########################################################################

import string
import sys
import MySQLdb
import getpass
import time


def translateAlias(str):
	if str == "B6":
		return "C57BL/6J"
	elif str == "D2":
		return "DBA/2J"
	else:
		return str

########################################################################
#
#  Indicate Data Start Position, ProbeFreezeId, GeneChipId, DataFile
#
########################################################################

dataStart = 1

GeneChipId = int( raw_input("Enter GeneChipId:") )
ProbeSetFreezeId = int( raw_input("Enter ProbeSetFreezeId:") )
input_file_name = raw_input("Enter file name with suffix:")

fp = open("%s" % input_file_name, 'rb')


try:
	passwd = getpass.getpass('Please enter mysql password here : ')
        con = MySQLdb.Connect(db='db_webqtl',host='localhost', user='username',passwd=passwd)

	db = con.cursor()
        print "You have successfully connected to mysql.\n"
except:
	print "You entered incorrect password.\n"
        sys.exit(0)
	
time0 = time.time()
########################################################################
#
#  Indicate Data Start Position, ProbeFreezeId, GeneChipId, DataFile
#
########################################################################

#GeneChipId = 4 
#dataStart = 1 	
#ProbeSetFreezeId = 359 #JAX Liver 6C Affy M430 2.0 (Jul11) MDP
#fp = open("GSE10493_AllSamples_6C_Z_AvgSE.txt", 'rb')


#########################################################################
#
#  Check if each line have same number of members
#  generate the gene list of expression data here
#
#########################################################################
print 'Checking if each line have same number of members'

GeneList = []
isCont = 1
header = fp.readline()
header = string.split(string.strip(header),'\t')
header = map(string.strip, header)
nfield = len(header)
line = fp.readline()

kj=0
while line:
	line2 = string.split(string.strip(line),'\t')
	line2 = map(string.strip, line2)
	if len(line2) != nfield:
		print "Error : " + line
		isCont = 0

	GeneList.append(line2[0])
	line = fp.readline()

	kj+=1
	if kj%100000 == 0:
		print 'checked ',kj,' lines'

GeneList = map(string.lower, GeneList)
GeneList.sort()
	
if isCont==0:
	sys.exit(0)


print 'used ',time.time()-time0,' seconds'
#########################################################################
#
#  Check if each strain exist in database
#  generate the string id list of expression data here
#
#########################################################################
print 'Checking if each strain exist in database'

isCont = 1
fp.seek(0)
header = fp.readline()
header = string.split(string.strip(header),'\t')
header = map(string.strip, header)
header = map(translateAlias, header)
header = header[dataStart:]
Ids = []
for item in header:
	try:
		db.execute('select Id from Strain where Name = "%s"' % item)
		Ids.append(db.fetchall()[0][0])
	except:
		print item,'does not exist, check the if the strain name is correct'
		isCont=0

if isCont==0:
	sys.exit(0)


print 'used ',time.time()-time0,' seconds'
########################################################################
#
# Check if each ProbeSet exist in database
#
########################################################################
print 'Check if each ProbeSet exist in database'

##---- find PID is name or target ----##
line = fp.readline()
line = fp.readline()
line2 = string.split(string.strip(line),'\t')
line2 = map(string.strip, line2)
PId = line2[0]

db.execute('select Id from ProbeSet where Name="%s" and ChipId=%d' % (PId, GeneChipId))
results = db.fetchall()
IdStr = 'TargetId'
if len(results)>0:
	IdStr = 'Name'


##---- get Name/TargetId list from database ----##
db.execute('select distinct(%s) from ProbeSet where ChipId=%d order by %s' % (IdStr, GeneChipId, IdStr))
results = db.fetchall()
	
Names = []
for item in results:
	Names.append(item[0])
Names = map(string.lower, Names)
Names.sort() # -- Fixed the lower case problem of ProbeSets affx-mur_b2_at  doesn't exist --#

##---- compare genelist with names ----##
x=y=0
x1=-1
GeneList2=[]
while x<len(GeneList) and y<len(Names):
	if GeneList[x]==Names[y]:
		x += 1
		y += 1
	elif GeneList[x]<Names[y]:
		if x!=x1:
			GeneList2.append(GeneList[x])
			x1 = x
		x += 1
	elif GeneList[x]>Names[y]:
		y += 1

	if x%100000==0:
		print 'check Name, checked %d lines'%x

while x<len(GeneList):
	GeneList2.append(GeneList[x])
	x += 1

isCont=1
ferror = open("ProbeSetError.txt", "wb")
for item in GeneList2:
	ferror.write(item + " doesn't exist \n")
	print item, " doesn't exist"
	isCont = 0
        
if isCont==0:
	sys.exit(0)


print 'used ',time.time()-time0,' seconds'
#############################
#Insert new Data into SE
############################
db.execute("""
	select ProbeSet.%s, ProbeSetXRef.DataId from ProbeSet, ProbeSetXRef 
	where ProbeSet.Id=ProbeSetXRef.ProbeSetId and ProbeSetXRef.ProbeSetFreezeId=%d"""
	 % (IdStr, ProbeSetFreezeId))
results = db.fetchall()

ProbeNameId = {}
for Name, Id in results:
	ProbeNameId[Name] = Id

ferror = open("ProbeError.txt", "wb")

DataValues = []

fp.seek(0) #XZ add this line
line = fp.readline() #XZ add this line
line = fp.readline()

kj = 0
while line:
	line2 = string.split(string.strip(line),'\t')
	line2 = map(string.strip, line2)

	CellId = line2[0]
	if not ProbeNameId.has_key(CellId):
		ferror.write(CellId + " doesn't exist\n")
		print CellId, " doesn't exist"
	else:
		DataId = ProbeNameId[CellId]
		datasorig = line2[dataStart:]

		i = 0
		for item in datasorig:
			if item != '':
				value = '('+str(DataId)+','+str(Ids[i])+','+str(item)+')'
				DataValues.append(value)
			i += 1

	kj += 1
	if kj % 100 == 0:
		Dataitems = ','.join(DataValues)
		cmd = 'insert ProbeSetSE values %s' % Dataitems
		db.execute(cmd)

		DataValues = []
		print 'inserted ',kj,' lines'
		print 'used ',time.time()-time0,' seconds'
	line = fp.readline()

if len(DataValues)>0:
	DataValues = ','.join(DataValues)
	cmd = 'insert ProbeSetSE values %s' % DataValues
	db.execute(cmd)

con.close()


