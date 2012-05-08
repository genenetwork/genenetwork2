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

from cmdClass import cmdClass
from showTrait.ShowTraitPage import ShowTraitPage


######################################### 
#      SHOW DATA-EDITING PAGE
#########################################
class cmdShowEditing(cmdClass):
	def __init__(self,fd):
		###example = http://www.webqtl.org/cgi-bin/beta/WebQTL?cmd=snp&chr=1&start=0&end=21345677
		cmdClass.__init__(self,fd)
		self.page = None
		prefix, dbId = self.getDBId(self.database)
		try:
			if not prefix or not dbId:
				raise ValueError
			self.cursor.execute('SELECT Name from %sFreeze WHERE Id=%d' % (prefix, dbId))
			database = self.cursor.fetchall()[0][0]
			traitInfos = (database,self.probeset,self.probe)
			self.page = ShowTraitPage(fd,traitInfos)
			#self = page
		except:
			print "Database Name Incorrect"

