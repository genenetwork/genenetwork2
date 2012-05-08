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
#      Mapping Class
#########################################
class cmdMap(cmdClass):

	def __init__(self,fd=None):

		cmdClass.__init__(self,fd)

		if not webqtlConfig.TEXTUI:
			self.contents.append("Please send your request to http://robot.genenetwork.org")
			return

		self.example = '###Example : <a href="%s%s?cmd=%s&probeset=100001_at&probe=136415&db=bra03-03Mas5&sort=lrs&return=20">%s%s?cmd=%s&probeset=100001_at&probe=136415&db=bra03-03Mas5&sort=lrs&return=20</a>' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID, webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID)
		if self.accessError:
			return
		try:
			self.returnnumber = int(self.data.getvalue('return'))
		except:
			self.returnnumber = None
		
		if self.error:
			self.contents.append(self.example)
			self.contents.append(self.accessCode)
		else:
			self.sort = self.data.getvalue('sort')
			self.readDB()
		
	def  readDB(self):
		prefix, dbId = self.getDBId(self.database)
		if not prefix or not dbId or (self.probe and string.lower(self.probe) in ("all","mm","pm")):
			self.contents.append("###Error: source trait doesn't exist or SELECT more than one trait.")
			self.contents.append(self.example)
			self.contents.append(self.accessCode)
			return
		RISet = self.getRISet(prefix, dbId)
		traitdata, heads = self.getTraitData(prefix, dbId, self.probeset, self.probe)
		if not traitdata:
			self.contents.append("###Error: source trait doesn't exist or SELECT more than one trait.")
			self.contents.append(self.example)
			self.contents.append(self.accessCode)
			return
			
		dataset = reaper.Dataset()
		dataset.read(os.path.join(webqtlConfig.GENODIR, RISet + '.geno'))
		strainList = list(dataset.prgy)
		
		strains = []
		trait = []
		_prgy = dataset.prgy
		for item in traitdata:
			if item[0] in _prgy:
				strains.append(item[0])	
				trait.append(item[1])
		
		qtlscan = dataset.regression(strains, trait)
		LRS = dataset.permutation(strains, trait)
		nperm = len(LRS)	
		if qtlscan:
			self.contents.append("Locus\tLRS\tChr\tAdditive\tp-value") 
			qtlresult = []
			if self.returnnumber:
				self.returnnumber = min(self.returnnumber,len(qtlscan))
				if self.sort == 'lrs':
					qtlscan.sort(self.cmpLRS)
					for item in qtlscan[:self.returnnumber]:
						p_value = reaper.pvalue(item.lrs,LRS)	
						qtlresult.append((item.locus.name,item.lrs,item.locus.chr,item.additive,p_value))
				else:#sort by position
					qtlscan2 = qtlscan[:]
					qtlscan2.sort(self.cmpLRS)
					LRSthresh = qtlscan2[self.returnnumber].lrs
					for item in qtlscan:
						if item.lrs >= LRSthresh:
							p_value = reaper.pvalue(item.lrs,LRS)	
							qtlresult.append((item.locus.name,item.lrs,item.locus.chr,item.additive,p_value))
			else:
				for item in qtlscan:
					p_value = reaper.pvalue(item.lrs,LRS)
					qtlresult.append((item.locus.name,item.lrs,item.locus.chr,item.additive,p_value))
				if self.sort == 'lrs':
					qtlresult.sort(self.cmpLRS2)
			for item in qtlresult:
				self.contents.append("%s\t%2.5f\t%s\t%2.5f\t%1.5f" % item)
		else:
			self.contents.append("###Error: Error occurs while regression.")
			return
			
	def cmpLRS(self,A,B):
		try:
			if A.lrs < B.lrs:
				return 1
			elif A.lrs == B.lrs:
				return 0
			else:
				return -1	
		except:
			return 0

	def cmpLRS2(self,A,B):
		try:
			if A[1] < B[1]:
				return 1
			elif A[1] == B[1]:
				return 0
			else:
				return -1	
		except:
			return 0
