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

from cmdClass import cmdClass
from search.TextSearchPage import TextSearchPage

######################################### 
#      Search Gene Symbol PAGE
#########################################
class cmdSearchGene(cmdClass):
	def __init__(self,fd):
		#example
		cmdClass.__init__(self,fd)
		self.page = None
		self.text = ""
		fd.geneName = fd.formdata.getvalue('gene')
		fd.returnFmt = fd.formdata.getvalue('format', 'html')
		if fd.geneName:
			fd.geneName = string.strip(fd.geneName)
		fd.refseq = fd.formdata.getvalue('refseq')
		if fd.refseq:
			fd.refseq = string.strip(fd.refseq)
		fd.genbankid = fd.formdata.getvalue('genbankid')
		if fd.genbankid:
			fd.genbankid = string.strip(fd.genbankid)
		fd.geneid = fd.formdata.getvalue('geneid')
		if fd.geneid:
			fd.geneid = string.strip(fd.geneid)
		if 1:
			if not (fd.geneName or fd.refseq or fd.genbankid or fd.geneid):
				raise "ValueError"
			fd.searchAlias = fd.formdata.getvalue('alias')
			if fd.searchAlias != '1':
				fd.searchAlias = None
			self.page = TextSearchPage(fd)
			if fd.returnFmt != 'text':
				pass
			else:
				self.text = self.page.output
				self.page = None
		elif "ValueError":
			self.text = "You need to submit a Gene name, a Refseq ID, or a GenBank ID"
		else:
			self.text = "Error occurs while searching the database"
			
