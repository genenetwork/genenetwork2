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
import os

import reaper

from base import webqtlConfig
from cmdClass import cmdClass

#########################################
#      Geno Class
#########################################
class cmdGeno(cmdClass):

	def __init__(self,fd=None):

		cmdClass.__init__(self,fd)

		if not webqtlConfig.TEXTUI:
			self.contents.append("Please send your request to http://robot.genenetwork.org")
			return

		if self.accessError:
			return
		self.error = 0
		self.RISet = None
		self.chr = None
		self.dataset = None
		self.strainList = []
		try:
			self.RISet = self.data.getvalue('riset')
			if not self.RISet:
				raise ValueError
		except:
			self.error = 1
			self.contents.append('###Example : http://www.genenetwork.org%s%s?cmd=%s&riset=BXD&chr=1' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID))
			return
		try:
			self.format = self.data.getvalue('format')[:3]
		except:
			self.format = 'row'

		try:
			self.dataset = reaper.Dataset()
			try:
				self.dataset.read(os.path.join(webqtlConfig.GENODIR, self.RISet + '.geno'))
			except:
				self.dataset.read(os.path.join(webqtlConfig.GENODIR, self.RISet.upper() + '.geno'))
			self.strainList = list(self.dataset.prgy)
		except:
			self.error = 1
			#traceback.print_exc()	
			self.contents.append('###The name of RISet is incorrect')
			return

		try:
			self.chr = self.data.getvalue('chr')
			if self.chr:
				if self.chr == 'X' or self.chr == 'x':
					self.chr = '20'
				self.chr = int(self.chr)
		except:
			pass
		
		self.readGeno()

	def  readGeno(self):
		try:
			table = [['Chr'] + ['Locus'] + self.strainList]
			if self.chr:
				chr = self.dataset[self.chr-1]
				for locus in chr:
					items = string.split(string.join(locus.genotext, " "))
					items = [chr.name] + [locus.name] + items
					table += [items]
			else:
				for chr in self.dataset:
					for locus in chr:
						items = string.split(string.join(locus.genotext, " "))
						items = [chr.name] + [locus.name] + items
						table += [items]
			if self.format == 'col':
				table = [[r[col] for r in table] for col in range(1, len(table[0]))]
				table[0][0] = 'Line'
			lines = string.join(map(lambda x: string.join(x, '\t'), table), '\n')
			self.contents.append(lines)
		except:	
			self.contents =['###Error: Read file error or name of chromosome is incorrect']
			#traceback.print_exc()	
			return

		
			
