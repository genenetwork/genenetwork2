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

#BatchSubmitSelectionPage.py

import string
import time

from base import webqtlConfig
from base.templatePage import templatePage
from utility import webqtlUtil
from AddToSelectionPage import AddToSelectionPage
	

#########################################
#     batch submission result Page
#########################################
class BatchSubmitSelectionPage(AddToSelectionPage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		if not self.openMysql():
			return
		if not fd.genotype:
			fd.readGenotype()
		
		heading = 'Batch Submission'
		
		self.batchDataFile = fd.formdata.getvalue('batchdatafile')
		if not self.batchDataFile:
			templatePage.__init__(self, fd)
			detail = ['The file you choose to import from doesn\'t exist.']
			self.error(heading=heading,detail=detail)
			return
		self.batchDataFile = string.replace(self.batchDataFile, '\r', '\n')
		self.batchDataFile = string.replace(self.batchDataFile, '\n\n', '\n')
		self.batchDataFile = string.split(self.batchDataFile, '\n')
		self.batchDataFile = map(string.strip, self.batchDataFile)
		
		traitNames, strainNames, traitValues, SE, NStrain = self.parseDataFile()
		strainIds = []
		
		#print 'Content-type: text/html\n'
		#print len(traitNames), len(strainNames) , len(strainIds), len(traitValues) , len(SE), "<BR><BR>", len(NStrain)
		#return
		
		try:
			
			if not traitNames or not strainNames or not traitValues or len(traitNames) != len(traitValues) or len(traitNames) != len(SE) or len(traitNames) != len(NStrain):
				raise 'ValueError'
			for item in traitValues:
				if len(strainNames) != len(item):
					raise 'ValueError'
			for item in SE:
				if len(strainNames) != len(item):
					raise 'ValueError'
			for item in NStrain:
				if len(strainNames) != len(item):
					raise 'ValueError'
			for item in strainNames:
 				self.cursor.execute('''Select 
 								Strain.Id 
 							from Strain, StrainXRef,InbredSet 
 							where 
 								Strain.Name = "%s" AND
 								StrainXRef.StrainId = Strain.Id AND
 								StrainXRef.InbredSetId = InbredSet.Id AND
 								InbredSet.Name = "%s"
 							''' % (item, fd.RISet))
 				strainId = self.cursor.fetchone()[0]
 				strainIds.append(strainId)
 		except:
			templatePage.__init__(self, fd)
			detail = ['The format of the file is incorrect, or it contains unknown strains.']
			self.error(heading=heading,detail=detail)
			return
		
		self.searchResult = []	
		self.addToTable(traitNames, strainNames,strainIds, traitValues,SE, NStrain, fd)
		
		if self.genSelection(fd=fd):
			self.writeHTML(fd)
	
	def parseDataFile(self):
		rchSartPos = 0
		header = []
		traits = []
		data = []
		se = []
		nstrain = []
		strains = []
		
		if 1:
			for line in  self.batchDataFile:
				line = line.strip()
				if line == '' or line[0] == '#':
					continue
					
				columns = string.split(line, '\t')
				columns = map(string.strip, columns)
				
				if rchSartPos == 'column':
					strains.append(columns[0])
					tdata = map(webqtlUtil.StringAsFloat,columns[1:])
					for j, item in enumerate(tdata):
						if  posIdx[j][0] == 'data':
							data[posIdx[j][1]].append(item)
						elif  posIdx[j][0] == 'n':
							if item != None:
								nstrain[posIdx[j][1]].append(int(item))
							else:
								nstrain[posIdx[j][1]].append(item)
						else:
							se[posIdx[j][1]].append(item)
							
				elif rchSartPos == 'row':
					if columns[0].lower() == 'se':
						se.append(map(webqtlUtil.StringAsFloat,columns[1:]))
					elif columns[0].lower() == 'n':
						nstrain.append(map(webqtlUtil.IntAsFloat,columns[1:]))
					else:
						while (len(data) > len(se)):
							se.append([None] * len(data[-1]))
						while (len(data) > len(nstrain)):
							nstrain.append([None] * len(data[-1]))
						header.append(columns[0])
						data.append(map(webqtlUtil.StringAsFloat,columns[1:]))
 				elif columns[0] == '@format=column':
					rchSartPos = 'column'
					posIdx = []
					j = 0
					for item in columns[1:]:
						#assign column type
						if string.lower(item) == 'se':
							posIdx.append(('se',j-1))
						elif string.lower(item) == 'n':
							posIdx.append(('n',j-1))
						else:
							header.append(item)
							posIdx.append(('data',j))
							j += 1
					
					for i in range(len(header)):
						data.append([])
						se.append([])
						nstrain.append([])
 				elif columns[0] == '@format=row':
					rchSartPos = 'row'
					strains = columns[1:]
				else:
					pass
			#modify
			for i in range(len(se)):
				if se[i] == []:
					se[i] = [None] * len(data[-1])
			for i in range(len(nstrain)):
				if nstrain[i] == []:
					nstrain[i] = [None] * len(data[-1])
			if len(data) > len(se):
				se.append([None] * len(data[-1]))
			if len(data) > len(nstrain):
				nstrain.append([None] * len(data[-1]))
			
			return header,strains,data,se, nstrain
		else:
			return [],[],[],[], []


	#XZ, add items to self.searchResult	
	def addToTable(self, traitNames, strainNames,strainIds, traitValues, SE, NStrain, fd):
		self.cursor.execute('delete Temp, TempData from Temp, TempData where Temp.DataId = TempData.Id and UNIX_TIMESTAMP()-UNIX_TIMESTAMP(CreateTime)>%d;' % webqtlConfig.MAXLIFE)
		
		i = 0
		for trait in traitNames:
			ct0 = time.localtime(time.time())
			ct = time.strftime("%B/%d %H:%M:%S",ct0)
			if trait == '':
				trait = "Unnamed Trait"
			user_ip = fd.remote_ip
			newDescription = '%s entered at %s from IP %s' % (trait,ct,user_ip)
			newProbeSetID = webqtlUtil.genRandStr('Usr_TMP_')
			
			self.cursor.execute('SelecT max(id) from TempData')
			try:
				DataId = self.cursor.fetchall()[0][0] + 1
			except:
				DataId = 1
			
			self.cursor.execute('Select Id  from InbredSet where Name = "%s"' % fd.RISet)
			InbredSetId = self.cursor.fetchall()[0][0]
					
			self.cursor.execute('insert into Temp(Name,description, createtime,DataId,InbredSetId,IP) values(%s,%s,Now(),%s,%s,%s)' ,(newProbeSetID, newDescription, DataId,InbredSetId,user_ip))
			
			for k in range(len(traitValues[i])):
				if traitValues[i][k] != None:
					self.cursor.execute('insert into TempData(Id, StrainId, value, SE, NStrain) values(%s, %s, %s, %s, %s)' , (DataId, strainIds[k], traitValues[i][k],SE[i][k],NStrain[i][k]))
			
			self.searchResult.append('Temp::%s'	% newProbeSetID)
			i += 1
	
