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

import os
import string
from math import *
import time

import reaper

from base import webqtlConfig
from utility import webqtlUtil
from cmdClass import cmdClass


#########################################
#      Correlation Class
#########################################
class cmdCorrelation(cmdClass):

	calFunction = 'webqtlUtil.calCorrelation'

	def __init__(self,fd=None):

		cmdClass.__init__(self,fd)

		if not webqtlConfig.TEXTUI:
			self.contents.append("Please send your request to http://robot.genenetwork.org")
			return


		self.example = '###Example : <a href="%s%s?cmd=%s&probeset=100001_at&probe=136415&db=bra03-03Mas5&searchdb=BXDPublish&return=500&sort=pvalue">%s%s?cmd=%s&probeset=100001_at&probe=136415&db=bra03-03Mas5&searchdb=BXDPublish&return=500&sort=pvalue</a>' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID, webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID)

		if self.accessError:
			return
			
		self.searchDB = self.data.getvalue('searchdb')
		if not self.searchDB or self.error:
			self.contents.append("###Error: source trait doesn't exist or no target database was given")
			self.contents.append(self.example)
			self.contents.append(self.accessCode)
			return
		
		try:
			self.returnNumber = int(self.data.getvalue('return'))
		except:
			self.returnNumber = None
		
		self.sort = self.data.getvalue('sort')

		prefix, dbId = self.getDBId(self.database)
		if not prefix or not dbId or (self.probe and string.lower(self.probe) in ("all","mm","pm")):
			self.contents.append("###Error: source trait doesn't exist or SELECT more than one trait.")
			self.contents.append(self.example)
			self.contents.append(self.accessCode)
			return
		RISet = self.getRISet(prefix, dbId)
		prefix2, dbId2 = self.getDBId(self.searchDB)
		if not prefix2 or not dbId2:
			self.contents.append("###Error: target database doesn't exist.")
			self.contents.append(self.example)
			self.contents.append(self.accessCode)
			return
		RISet2 = self.getRISet(prefix2, dbId2)
		if RISet2 != RISet:
			self.contents.append("###Error: target database has different Mouse InbredSet.")
			self.contents.append(self.example)
			self.contents.append(self.accessCode)
			return
		
		traitdata, heads = self.getTraitData(prefix, dbId, self.probeset, self.probe)
		if not traitdata:
			self.contents.append("###Error: source trait doesn't exist.")
			self.contents.append(self.example)
			self.contents.append(self.accessCode)
			return
			
		StrainNames = []
		sourceTrait = []
		StrainIds = []

		#XZ, Jan 27, 2011: Only the strains that are of the same inbredset are used to calculate correlation.
		for item in traitdata:
			one_strain_name = item[0]
			one_strain_value = item[1]

			self.cursor.execute('SELECT Strain.Id from Strain,StrainXRef, InbredSet WHERE Strain.Name="%s" and Strain.Id = StrainXRef.StrainId and StrainXRef.InbredSetId = InbredSet.Id and InbredSet.Name = "%s"' % (one_strain_name, RISet2))
			Results = self.cursor.fetchall()
			if Results:
				StrainIds.append('%d' % Results[0][0])
				StrainNames.append( one_strain_name )
				sourceTrait.append( one_strain_value )

		correlationArray = []

		useFastMethod = False
		if prefix2 == "ProbeSet":
			DatabaseFileName = self.getFileName( target_db_id=dbId2 )
			DirectoryList = os.listdir(webqtlConfig.TEXTDIR)  ### List of existing text files.  Used to check if a text file already exists
			if DatabaseFileName in DirectoryList:
				useFastMethod = True

		if useFastMethod:
			datasetFile = open(webqtlConfig.TEXTDIR+DatabaseFileName,'r')

			#XZ, 01/08/2009: read the first line
			line = datasetFile.readline()
			dataset_strains = webqtlUtil.readLineCSV(line)[1:]

			#XZ, 01/08/2009: This step is critical. It is necessary for this new method.
			_newvals = []
			for item in dataset_strains:
				if item in StrainNames:
					_newvals.append(sourceTrait[StrainNames.index(item)])
				else:
					_newvals.append('None')

			nnCorr = len(_newvals)

			
			for line in datasetFile:
				traitdata=webqtlUtil.readLineCSV(line)
				traitdataName = traitdata[0]
				traitvals = traitdata[1:]

				corr,nOverlap = webqtlUtil.calCorrelationText(traitvals,_newvals,nnCorr)
				traitinfo = [traitdataName,corr,nOverlap]
				correlationArray.append( traitinfo )

		#calculate correlation with slow method
		else:
			correlationArray = self.calCorrelation(sourceTrait, self.readDB(StrainIds, prefix2, dbId2) )

		correlationArray.sort(self.cmpCorr) #XZ: Do not forget the sort step

		if not self.returnNumber:
			correlationArray = correlationArray[:100]
		else:
			if self.returnNumber < len(correlationArray):
				correlationArray = correlationArray[:self.returnNumber]
		NN = len(correlationArray)
		for i in range(NN):
			nOverlap = correlationArray[i][-1]
			corr = correlationArray[i][-2]
			if nOverlap < 3:
				corrPValue = 1.0
			else:
				if abs(corr) >= 1.0:
					corrPValue = 0.0
				else:
					ZValue = 0.5*log((1.0+corr)/(1.0-corr))
					ZValue = ZValue*sqrt(nOverlap-3)
					corrPValue = 2.0*(1.0 - reaper.normp(abs(ZValue)))
			correlationArray[i].append(corrPValue)
		if self.sort == 'pvalue':
			correlationArray.sort(self.cmpPValue)
		
		if prefix2 == 'Publish':
			self.contents.append("RecordID\tCorrelation\t#Strains\tp-value")
		elif  prefix2 == 'Geno':
			self.contents.append("Locus\tCorrelation\t#Strains\tp-value")
		else:
			pass

		if prefix2 == 'Publish' or prefix2 == 'Geno':
			for item in correlationArray:
				self.contents.append("%s\t%2.6f\t%d\t%2.6f" % tuple(item))
		else:
			id = self.data.getvalue('id')
			if id == 'yes':					
				self.contents.append("ProbesetID\tCorrelation\t#Strains\tp-value\tGeneID")
				for item in correlationArray:
					query = """SELECT GeneID from %s WHERE Name = '%s'""" % (prefix2,item[0])
					self.cursor.execute(query)
					results = self.cursor.fetchall()
					if not results:
						item = item + [None]
					else:
						item = item + list(results[0])
					self.contents.append("%s\t%2.6f\t%d\t%2.6f\t%s" % tuple(item))
			elif id == 'only':					
				self.contents.append("GenID")
				for item in correlationArray:
					query = """SELECT GeneID from %s WHERE Name = '%s'""" % (prefix2,item[0])
					self.cursor.execute(query)
					results = self.cursor.fetchall()
					if not results:
						self.contents.append('None')
					else:
						self.contents.append(results[0][0])
			else:
				self.contents.append("ProbesetID\tCorrelation\t#Strains\tp-value")
				for item in correlationArray:
					self.contents.append("%s\t%2.6f\t%d\t%2.6f" % tuple(item))




	def getFileName(self, target_db_id):

		query = 'SELECT Id, FullName FROM ProbeSetFreeze WHERE Id = %s' %  target_db_id
		self.cursor.execute(query)
		result = self.cursor.fetchone()
		Id = result[0]
		FullName = result[1]
		FullName = FullName.replace(' ','_')
		FullName = FullName.replace('/','_')

		FileName = 'ProbeSetFreezeId_' + str(Id) + '_FullName_' + FullName + '.txt'

		return FileName


	
	def calCorrelation(self,source,target):
		allcorrelations = []
		NN = len(source)

		if len(source) != len(target[0]) - 1:
			return allcorrelations
		else:
			for traitData in target:
				corr,nOverlap = eval("%s(traitData[1:],source,NN)" % self.calFunction)
				traitinfo = [traitData[0],corr,nOverlap]				
				allcorrelations.append(traitinfo)

			return allcorrelations
	
	def cmpCorr(self,A,B):
		try:
			if abs(A[1]) < abs(B[1]):
				return 1
			elif abs(A[1]) == abs(B[1]):
				return 0
			else:
				return -1	
		except:
			return 0

	def cmpPValue(self,A,B):
		try:
			if A[-1] > B[-1]:
				return 1
			elif A[-1] ==  B[-1]:
				return 0
			else:
				return -1	
		except:
			return 0


        def  readDB(self, StrainIds=[], prefix2='', dbId2=''):

                #retrieve data from target database
                nnn = len(StrainIds) / 25
                if len(StrainIds) % 25:
                        nnn += 1
                oridata = []
                for step in range(nnn):
                        temp = []
                        StrainIdstep = StrainIds[step*25:min(len(StrainIds), (step+1)*25)]
                        for item in StrainIdstep:
                                temp.append('T%s.value' % item)
                        #XZ, 03/05/2009: test http://www.genenetwork.org/webqtl/WebQTL.py?cmd=cor&probeset=100001_at&probe=136415&db=bra08-03MAS5&searchdb=BXDPublish&return=500&sort=pvalue
                        if prefix2 == "Publish":
                                query = "SELECT PublishXRef.Id, "
                                dataStartPos = 1
                                query += string.join(temp,', ')
                                query += ' from (PublishXRef, PublishFreeze)\n'
                                #XZ, 03/05/2009: Xiaodong changed Data to PublishData
                                for item in StrainIdstep:
                                        query += 'left join PublishData as T%s on T%s.Id = PublishXRef.DataId and T%s.StrainId=%s\n' %(item,item,item,item)
                                query += "WHERE PublishXRef.InbredSetId = PublishFreeze.InbredSetId and PublishFreeze.Id = %d" % (dbId2, )
                        #XZ, 03/05/2009: test http://www.genenetwork.org/webqtl/WebQTL.py?cmd=cor&probeset=100001_at&probe=136415&db=bra08-03MAS5&searchdb=HC_M2_1005_M&return=500&sort=pvalue
                        #XZ, 03/05/2009: test http://www.genenetwork.org/webqtl/WebQTL.py?cmd=cor&probeset=100001_at&probe=136415&db=bra08-03MAS5&searchdb=BXDGeno&return=500&sort=pvalue
                        else:
                                query = "SELECT %s.Name," %  prefix2
                                query += string.join(temp,', ')
                                query += ' from (%s, %sXRef, %sFreeze) \n' % (prefix2,prefix2,prefix2)
                                #XZ, 03/05/2009: Xiaodong changed Data to %sData
                                for item in StrainIdstep:
                                        query += 'left join %sData as T%s on T%s.Id = %sXRef.DataId and T%s.StrainId=%s\n' %(prefix2,item,item,prefix2,item,item)
                                query += "WHERE %sXRef.%sFreezeId = %sFreeze.Id and %sFreeze.Id = %d  and %s.Id = %sXRef.%sId" % (prefix2, prefix2, prefix2, prefix2, dbId2, prefix2, prefix2, prefix2)
                        self.cursor.execute(query)
                        results = self.cursor.fetchall()
                        if not results:
                                self.contents.append("###Error: target database doesn't exist.")
                                self.contents.append(self.example)
                                self.contents.append(self.accessCode)
                                return
                        oridata.append(results)

                datasize = len(oridata[0])
                targetTrait = []
                for j in range(datasize):
                        traitdata = list(oridata[0][j])
                        for i in range(1,nnn):
                                traitdata += list(oridata[i][j][1:])
                        targetTrait.append(traitdata)

                return targetTrait
			
