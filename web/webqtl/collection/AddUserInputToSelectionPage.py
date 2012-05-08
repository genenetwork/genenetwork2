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

#AddUserInputToSelectionPage.py

import time

from base import webqtlConfig
from base.templatePage import templatePage
from utility import webqtlUtil
from AddToSelectionPage import AddToSelectionPage	
			
#########################################
#      Add UserInput to Selection Page
#########################################
class AddUserInputToSelectionPage(AddToSelectionPage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		if not self.openMysql():
			return

		if not fd.genotype:
			fd.readData(incf1 = 1)
			
		self.strainlist = []
		self.vals = []
		for i, strain in enumerate(fd.f1list + fd.strainlist):
			if fd.allTraitData.has_key(strain) and fd.allTraitData[strain].val != None:
				self.strainlist.append(strain)
				self.vals.append([fd.allTraitData[strain].val, fd.allTraitData[strain].var])
		
		if len(self.strainlist) > webqtlConfig.KMININFORMATIVE:
			pass
		else:
			templatePage.__init__(self, fd)
			heading = 'Add to Collection'
			detail = ['The number of informative strains in your trait is less than %d, this trait can not be added to the selection' % webqtlConfig.KMININFORMATIVE]
			self.error(heading=heading,detail=detail)
			return
		
		self.cursor.execute('delete Temp, TempData from Temp, TempData where Temp.DataId = TempData.Id and UNIX_TIMESTAMP()-UNIX_TIMESTAMP(CreateTime)>%d;' % webqtlConfig.MAXLIFE)
		ct0 = time.localtime(time.time())
		ct = time.strftime("%B/%d %H:%M:%S",ct0)
		if not fd.identification:
			fd.identification = "Unnamed Trait"
		user_ip = fd.remote_ip
		newDescription = '%s entered at %s from IP %s' % (fd.identification,ct,user_ip)
		newProbeSetID = webqtlUtil.genRandStr("USER_Tmp_")
		self.cursor.execute('SelecT max(id) from TempData')
		try:
			DataId = self.cursor.fetchall()[0][0] + 1
		except:
			DataId = 1
		self.cursor.execute('SelecT Id  from InbredSet where Name = "%s"' % fd.RISet)
		InbredSetId = self.cursor.fetchall()[0][0]
				
		self.cursor.execute('insert into Temp(Name,description, createtime,DataId,InbredSetId,IP) values(%s,%s,Now(),%s,%s,%s)' ,(newProbeSetID, newDescription, DataId,InbredSetId,user_ip))
		
		k = 0	
		for Strain in self.strainlist:
			self.cursor.execute('SelecT Strain.Id  from Strain,StrainXRef where Strain.Name = "%s" and Strain.Id = StrainXRef.StrainId and StrainXRef.InbredSetId=%d' % (Strain, InbredSetId))
			StrainId = self.cursor.fetchall()[0][0]
			self.cursor.execute('insert into TempData(Id, StrainId, value, SE) values(%s,%s,%s,%s)' , (DataId, StrainId, self.vals[k][0], self.vals[k][1]))
			k += 1

		self.searchResult = ['Temp::%s'	% newProbeSetID]

		if self.genSelection(fd=fd):
			self.writeHTML(fd)


