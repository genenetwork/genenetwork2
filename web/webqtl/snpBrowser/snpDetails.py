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

#########################################
# A class for the information of SNPs ONLY. This is for the 'extra' page when you click on a SNP that doesn't have an RS#
# This is where the information populating
# The table is gathered. This is where you determine what variables you will display in the table
#########################################

import string
from htmlgen import HTMLgen2 as HT

import snpBrowserUtils
from base.templatePage import templatePage
from snpBrowserPage import snpBrowserPage

class snpDetails(templatePage):

	def __init__(self, fd, snpId):

		templatePage.__init__(self, fd)	
		
		snpCols = "snpname, chromosome, mb, domain, rs, function, type, majorAllele, majorCount, minorAllele, minorCount, class, flanking5, flanking3, blatScore, sourceId, gene, ncbi".split(", ")
		#get the details from the database if search the SNP variants by the "gene/snp" field
		if snpId:
			self.openMysql()

			mysqlField = ['snpname','rs', 'chromosome', 'mb',  'function', 'type', 'class', 'flanking5', 'flanking3', 'blatscore', 'domain', 'gene', 'ncbi']
			query = """
					SELECT
						%s, c.Name,b.* 
					from 
						SnpAll a, SnpPattern b, SnpSource c
					where 
						a.Id =%s AND a.Id = b.SnpId AND a.SourceId =c.Id 
				""" % (string.join(mysqlField, ", "), snpId)			
			
			self.cursor.execute(query)
			results = self.cursor.fetchone()
			result =results[:14]
			mysqlField.append('sourceName')
			snpDict = {}

			for i, item in enumerate(result):
				snpDict[mysqlField[i]] = item
			alleleList =results[15:]
			objSnpBrowserPage =snpBrowserPage(fd)
			flag =0
			majAllele,minAllele,majAlleleCount,minAlleleCount= objSnpBrowserPage.getMajMinAlleles(alleleList,flag)
			snpDict['majorAllele'] = majAllele
			snpDict['minorAllele'] = minAllele
			snpDict['majorCount'] = majAlleleCount
			snpDict['minorCount'] = minAlleleCount
		else:
			return
		
	# Creates the table for the SNP data
		snpTable = HT.TableLite(border=0, cellspacing=5, cellpadding=3, Class="collap")
		for item in snpCols:
			thisTR = HT.TR(HT.TD(snpBrowserUtils.columnNames[item], Class="fs14 fwb ffl b1 cw cbrb", NOWRAP = 1))
			if item in ('flanking5', 'flanking3'):
				seq0 = snpDict[item]
				seq = ""
				i = 0
				if seq0:
				  while i < len(seq0):
					seq += seq0[i:i+5] + " "
					i += 5
				thisTR.append(HT.TD(HT.Span(seq, Class="code", Id="green"), Class='fs13 b1 cbw c222'))
			elif item in snpDict.keys() and snpDict[item]:
				thisTR.append(HT.TD(snpDict[item], Class='fs13 b1 cbw c222'))
			else:
				thisTR.append(HT.TD("", Class='fs13 b1 cbw c222'))
			
			snpTable.append(thisTR)
			
		self.dict['body'] = HT.TD(HT.Paragraph("Details for %s" % snpDict['snpname'], Class="title"), HT.Blockquote(snpTable))
		self.dict['title'] = "Details for %s" % snpDict['snpname']