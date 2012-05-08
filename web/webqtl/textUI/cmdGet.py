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

from base import webqtlConfig
from cmdClass import cmdClass

#########################################
#      Get trait value Class
#########################################
class cmdGet(cmdClass):
	def __init__(self,fd=None):

		cmdClass.__init__(self,fd)

		if not webqtlConfig.TEXTUI:
			self.contents.append("Please send your request to http://robot.genenetwork.org")
			return

		self.example = '###Example : <a href="%s%s?cmd=%s&probeset=100001_at&db=bra03-03Mas5&probe=all">%s%s?cmd=%s&probeset=100001_at&db=bra03-03Mas5&probe=all</a>' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID, webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID)
		if self.accessError:
			return
		if not self.error:
			self.readDB()
		else:
			self.contents.append(self.example)
			self.contents.append(self.accessCode)

	def  readDB(self):
		prefix, dbId = self.getDBId(self.database)
		
		traitdata, heads = self.getTraitData(prefix, dbId, self.probeset, self.probe)
		try:	
			if not traitdata:
				raise ValueError
			traitdata = heads + list(traitdata)
			if self.format == 'col':
				self.formatCols(traitdata)
			else:
				self.formatRows(traitdata)
		except:
			self.contents.append('Error: no record was found')
			self.contents.append(self.accessCode)
			return

	def formatCols(self, traitdata):
		for item in traitdata:
			lines = []
			for item2 in item:
				lines.append(item2)
			lines = string.join(map(str,lines), '\t')
			self.contents.append(lines)
			
	def formatRows(self, traitdata):
		for i in range(len(traitdata[0])):
			lines = []
			for j in range(len(traitdata)):
				lines.append(traitdata[j][i])
			lines = string.join(map(str,lines), '\t')
			self.contents.append(lines)

			
