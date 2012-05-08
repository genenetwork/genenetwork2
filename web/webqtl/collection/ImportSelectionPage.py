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

#ImportSelectionPage.py

import string

from base.templatePage import templatePage
from AddToSelectionPage import AddToSelectionPage
				

#########################################
#     Import Selection Page
#########################################
class ImportSelectionPage(AddToSelectionPage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		if not self.openMysql():
			return

		if not fd.genotype:
			fd.readGenotype()
		
		self.importFile = fd.formdata.getvalue('importfile')
		if not self.importFile:
			templatePage.__init__(self, fd)
			heading = 'Import Collection'
			detail = ['The file you choose to import from doesn\'t exist.']
			self.error(heading=heading,detail=detail)
			return
		self.importFile = string.split(self.importFile, '\n')
		
		RISetLocate = 0
		self.searchResult = []
		for line in self.importFile:
			if line and line[0] != '#':
				if not RISetLocate:
					RISetLocate = line
					if RISetLocate != fd.RISet:
						templatePage.__init__(self, fd)
						heading = 'Import Collection'
						detail = ['The file you choose to import from doesn\'t contain %s selection.' % fd.RISet]
						self.error(heading=heading,detail=detail)
						return
				else:
					self.searchResult.append(line)
		
		if not self.searchResult:
			templatePage.__init__(self, fd)
			heading = 'Import Collection'
			detail = ['The file you choose to import from is empty.']
			self.error(heading=heading,detail=detail)
			return
				
		self.importMethod = fd.formdata.getvalue('importmethod')
		
		if self.importMethod == 'replace':
			checkPreSelection = 0
		else:
			checkPreSelection = 1
			
		if self.genSelection(fd=fd, checkPreSelection = checkPreSelection):
			self.writeHTML(fd)
	

		
