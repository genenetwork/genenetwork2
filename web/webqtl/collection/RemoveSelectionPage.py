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

from base.templatePage import templatePage
from base.webqtlTrait import webqtlTrait	
from AddToSelectionPage import AddToSelectionPage

#########################################
#      Remove Selection Page
#########################################
class RemoveSelectionPage(AddToSelectionPage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		if not self.openMysql():
			return

		if not fd.genotype:
			fd.readGenotype()
		
		self.searchResult = fd.formdata.getvalue('searchResult')
		if self.searchResult:
			pass
		else:
			templatePage.__init__(self, fd)
			heading = 'Remove Selections'
			detail = ['You need to select at least one trait to remove from your selection.']
			self.error(heading=heading,detail=detail)
			return

		self.genSelection(fd=fd)
		self.writeHTML(fd)



	def genSelection(self, fd=None):
		collectionName = '%s_Select' % fd.RISet

		try:
			preSelection = fd.input_session_data[collectionName]
			preSelection = list(string.split(preSelection,','))
		except:
			preSelection = []
		
		if type("1") == type(self.searchResult):
			self.searchResult = [self.searchResult]
		
		if preSelection:
			for item in self.searchResult:
				try:
					preSelection.remove(item)
				except:
					pass
		self.searchResult = preSelection[:]
		
		if not self.searchResult:
			self.session_data_changed[collectionName] = ""
			return
		
		#self.searchResult.sort()
		for item in self.searchResult:
			if not item:
				self.searchResult.remove(item)
				
		searchResult2 = []
		self.theseTraits = []
		for item in self.searchResult:
			try:
				thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
				thisTrait.retrieveInfo(QTL=1)
				self.theseTraits.append(thisTrait)
				searchResult2.append(item)
			except:
				pass

		allTraitStr = string.join(searchResult2,',')

		self.session_data_changed[collectionName] = allTraitStr

