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
#      Interval Mapping Class
#########################################
class cmdInterval(cmdClass):

	def __init__(self,fd=None):

		cmdClass.__init__(self,fd)

		if not webqtlConfig.TEXTUI:
			self.contents.append("Please send your request to http://robot.genenetwork.org")
			return


		self.example = '###Example : <a href="%s%s?cmd=%s&probeset=100001_at&probe=136415&db=bra03-03Mas5&sort=pos&return=100&chr=12">%s%s?cmd=%s&probeset=100001_at&probe=136415&db=bra03-03Mas5&sort=pos&return=100&chr=12</a>' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID, webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, self.cmdID)
		if self.accessError:
			return
		self.sort = None
		self.step = 0.01
		self.peak = 1
		self.chr = None
		self.sort = None
		self.returnnumber = 20
		if self.error:
			self.error = 1
			self.contents.append(self.example)
			return
		else:
			try:
				self.sort = self.data.getvalue('sort')
				if string.lower(self.sort) == 'pos':
					self.sort = 'pos'
				else:
					self.sort = 'lrs'
			except:
				self.sort = None
			
			try:
				self.returnnumber = int(self.data.getvalue('return'))
			except:
				self.returnnumber = 20
			try:	
				self.chr = self.data.getvalue('chr')
			except:
				self.chr = None
				
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
			
		dataset0 = reaper.Dataset()
		dataset0.read(os.path.join(webqtlConfig.GENODIR, RISet + '.geno'))
		strainList = list(dataset0.prgy)
		dataset = dataset0.addinterval()
		if self.chr != None:
			for _chr in dataset:
				if string.lower(_chr.name) ==  string.lower(self.chr):
					dataset.chromosome = [_chr]
					break
		
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
		
		#print inter1[0]
		returnPeak = []
		nqtl = len(qtlscan)
		if self.peak:
			for i in range(nqtl):
				if i == 0 or qtlscan[i].locus.chr != qtlscan[i-1].locus.chr:
					if qtlscan[i].lrs < qtlscan[i+1].lrs:
						continue
				elif i == nqtl-1 or qtlscan[i].locus.chr != qtlscan[i+1].locus.chr:
					if qtlscan[i].lrs < qtlscan[i-1].lrs:
						continue
				else:
					if qtlscan[i].lrs < qtlscan[i+1].lrs or qtlscan[i].lrs < qtlscan[i-1].lrs:
						continue
				returnPeak.append(qtlscan[i])
		else:
			returnPeak = qtlscan[:]
			
		if returnPeak:
			self.contents.append("Locus\tLRS\tChr\tAdditive\tp-value\tcM") 
			qtlresult = []
			for item in returnPeak:
				p_value = reaper.pvalue(item.lrs,LRS)
				qtlresult.append((item.locus.name,item.lrs,item.locus.chr,item.additive,p_value, item.locus.cM))
			if self.sort == 'lrs':
				qtlresult.sort(self.cmpLRS2)
			for item in qtlresult:
				self.contents.append("%s\t%2.4f\t%s\t%2.4f\t%1.4f\t%s" % item)
		else:
			self.contents.append("###Error: Error occurs while regression.")
			return
	
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

			
