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

from mod_python import apache, util, Cookie
import os
import time
import pyXLWriter as xl

from htmlgen import HTMLgen2 as HT

import GeneUtil
from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig


class IntervalAnalystPage(templatePage):
	filename = webqtlUtil.genRandStr("Itan_")

	_scriptfile = "main.py?FormID=intervalAnalyst"

	#A dictionary that lets us map the html form names "txStart_mm6" -> "Mb Start (mm8)"
	#the first item is the short name (column headers) and the second item is the long name (dropdown list)
	#   [short name, long name, category]
	columnNames = {"GeneSymbol" : ["Gene", "Gene Name", 'gene'],
			"GeneDescription" : ["Description", "Gene Description", 'species'],
			'GeneNeighborsCount' : ["Neighbors", "Gene Neighbors", 'gene'],
			'GeneNeighborsRange' : ["Neighborhood", "Gene Neighborhood (Mb)", 'gene'],
			'GeneNeighborsDensity' : ["Gene Density", "Gene Density (Neighbors/Mb)", 'gene'],
			"ProteinID" : ["Prot ID", "Protein ID", 'protein'],
			"Chromosome" : ["Chr", "Chromosome", 'species'],
			"TxStart" : ["Start", "Mb Start", 'species'],
			"TxEnd" : ["End", "Mb End", 'species'],
			"GeneLength" : ["Length", "Kb Length", 'species'],
			"cdsStart" : ["CDS Start", "Mb CDS Start", 'species'],
			"cdsEnd" : ["CDS End", "Mb CDS End", 'species'],
			"exonCount" : ["Num Exons", "Exon Count", 'species'],
			"exonStarts" : ["Exon Starts", "Exon Starts", 'species'],
			"exonEnds" : ["Exon Ends", "Exon Ends", 'species'],
			"Strand" : ["Strand", "Strand", 'species'],
			"GeneID" : ["Gene ID", "Gene ID", 'species'],
			"GenBankID" : ["GenBank", "GenBank ID", 'species'],
			"UnigenID" : ["Unigen", "Unigen ID", 'species'],
			"NM_ID" : ["NM ID", "NM ID", 'species'],
			"kgID" : ["kg ID", "kg ID", 'species'],
			"snpCount" : ["SNPs", "SNP Count", 'species'],
			"snpDensity" : ["SNP Density", "SNP Density", 'species'],
			"lrs" : ["LRS", "Likelihood Ratio Statistic", 'misc'],
			"lod" : ["LOD", "Likelihood Odds Ratio", 'misc'],
			"pearson" : ["Pearson", "Pearson Product Moment", 'misc'],
			"literature" : ["Lit Corr", "Literature Correlation", 'misc'],
			}

	###Species Freeze
	speciesFreeze = {'mouse':'mm9', 'rat':'rn3', 'human':'hg19'}
	for key in speciesFreeze.keys():
		speciesFreeze[speciesFreeze[key]] = key

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		fd.formdata['remote_ip'] = fd.remote_ip
		if not self.openMysql():
			return

		self.species = fd.formdata.getvalue("species", "mouse")
		try:
			self.startMb = float(fd.formdata.getvalue("startMb"))
		except:
			self.startMb = 10
		try:
			self.endMb = float(fd.formdata.getvalue("endMb"))
		except:
			self.endMb = self.startMb + 10

		self.Chr = fd.formdata.getvalue("chromosome", "1")
		self.xls = fd.formdata.getvalue("xls", "1")
		try:
			s1 = int(fd.formdata.getvalue("s1"))
			s2 = int(fd.formdata.getvalue("s2"))
			self.diffColDefault = self.diffCol = [s1, s2]
		except:
			self.diffColDefault = self.diffCol = []
			if self.species !=  'mouse':
				self.diffColDefault = [2, 3]#default is B6 and D2 for other species

		controlFrm, dispFields = self.genControlForm(fd)
		geneTable, filename = self.genGeneTable(fd, dispFields)

		infoTD = HT.TD(width=400, valign= "top")
		infoTD.append(HT.Paragraph("Interval Analyst : Chr %s" % self.Chr, Class="title"),
			HT.Strong("Species : "), self.species.title(), HT.BR(),
			HT.Strong("Database : "), "UCSC %s" % self.speciesFreeze[self.species], HT.BR(),
			HT.Strong("Range : "), "%2.6f Mb - %2.6f Mb" % (self.startMb, self.endMb), HT.BR(),
			)
		if filename:
			infoTD.append(HT.BR(), HT.BR(), HT.Href(text="Download", url = "/tmp/" + filename, Class="normalsize")
					, " output in MS excel format.")

		mainTable = HT.TableLite(HT.TR(infoTD, HT.TD(controlFrm, Class="doubleBorder", width=400), HT.TD("&nbsp;", width="")), cellpadding=10)
		mainTable.append(HT.TR(HT.TD(geneTable, colspan=3)))
		self.dict['body'] = HT.TD(mainTable)
		self.dict['title'] = "Interval Analyst"

	def genGeneTable(self, fd, dispFields):
		filename = ""
		if self.xls:
			#import pyXLWriter as xl
			filename = "IntAn_Chr%s_%2.6f-%2.6f" % (self.Chr, self.startMb, self.endMb)
			filename += ".xls"

			# Create a new Excel workbook
			workbook = xl.Writer(os.path.join(webqtlConfig.TMPDIR, filename))
			worksheet = workbook.add_worksheet()
			titleStyle = workbook.add_format(align = 'left', bold = 0, size=18, border = 1, border_color="gray")
			headingStyle = workbook.add_format(align = 'center', bold = 1, size=13, fg_color = 0x1E, color="white", border = 1, border_color="gray")

			##Write title Info
			worksheet.write([0, 0], "GeneNetwork Interval Analyst Table", titleStyle)
			worksheet.write([1, 0], "%s%s" % (webqtlConfig.PORTADDR, os.path.join(webqtlConfig.CGIDIR, self._scriptfile)))
			#
			worksheet.write([2, 0], "Date : %s" % time.strftime("%B %d, %Y", time.gmtime()))
			worksheet.write([3, 0], "Time : %s GMT" % time.strftime("%H:%M ", time.gmtime()))
			worksheet.write([4, 0], "Search by : %s" % fd.formdata['remote_ip'])
			worksheet.write([5, 0], "view region : Chr %s %2.6f - %2.6f Mb" % (self.Chr, self.startMb, self.endMb))
			nTitleRow = 7

		geneTable = HT.TableLite(Class="collap", cellpadding=5)
		headerRow = HT.TR(HT.TD(" ", Class="fs13 fwb ffl b1 cw cbrb", width="1"))
		if self.xls:
			worksheet.write([nTitleRow, 0], "Index", headingStyle)

		for ncol, column in enumerate(dispFields):
			if len(column) == 1:
				headerRow.append(HT.TD(self.columnNames[column[0]][0], Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = self.columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			else:
				headerRow.append(HT.TD(self.columnNames[column[0]][0], HT.BR(), " (%s)" % self.speciesFreeze[column[1]],
					Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1, align="Center"))
				if self.xls:
					colTitle = self.columnNames[column[0]][0] + " (%s)" % self.speciesFreeze[column[1]]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
				#headerRow.append(HT.TD(self.columnNames[column[0]][0], HT.BR(),
				#	"(%s %s)" % (column[1].title(), self.speciesFreeze[column[1]]),
				#	Class="colorBlue", NOWRAP=1, align="Center"))
		geneTable.append(headerRow)

		geneCol = GeneUtil.loadGenes(self.cursor, self.Chr, self.diffColDefault, self.startMb, self.endMb, species=self.species)
		for gIndex, theGO in enumerate(geneCol):
			geneRow = HT.TR(HT.TD(gIndex+1, Class="fs12 fwn b1", align="right"))
			if self.xls:
				nTitleRow += 1
				worksheet.write([nTitleRow, 0], gIndex + 1)

			for ncol, column in enumerate(dispFields):
				if len(column) == 1 or column[1]== self.species:
					keyValue = ""
					fieldName = column[0]
					curSpecies = self.species
					curGO = theGO
					if theGO.has_key(fieldName):
						keyValue = theGO[fieldName]
				else:
					fieldName , othSpec = column
					curSpecies = othSpec
					subGO = '%sGene' % othSpec
					keyValue = ""
					curGO = theGO[subGO]
					if theGO[subGO].has_key(fieldName):
						keyValue = theGO[subGO][fieldName]

				if self.xls:
					worksheet.write([nTitleRow, ncol+1], keyValue)
				geneRow.append(self.formatTD(keyValue, fieldName, curSpecies, curGO))

			geneTable.append(geneRow)

		if self.xls:
			workbook.close()
		return geneTable, filename

	def formatTD(self, keyValue, fieldName, Species, theGO):
		if keyValue is None:
			keyValue = ""
		if keyValue != "":
			if fieldName in ("exonStarts", "exonEnds"):
				keyValue = string.replace(keyValue, ',', ' ')
				return HT.TD(HT.Span(keyValue, Class="code", Id="green"), width=350, Class="fs12 fwn b1")
			elif fieldName in ("GeneDescription"):
				if keyValue == "---":
					keyValue = ""
				return HT.TD(keyValue, Class="fs12 fwn b1", width=300)
			elif fieldName in ("GeneSymbol"):
				webqtlLink = HT.Href("./%s?cmd=sch&gene=%s&alias=1&species=%s" % (webqtlConfig.SCRIPTFILE, keyValue, Species), 
					HT.Image("/images/webqtl_search.gif", border=0, valign="top"), target="_blank")
				if theGO['GeneID']:
					geneSymbolLink = HT.Href(webqtlConfig.NCBI_LOCUSID % theGO['GeneID'], keyValue, Class="normalsize", target="_blank")
				else:
					geneSymbolLink = keyValue
				return HT.TD(webqtlLink, geneSymbolLink, Class="fs12 fwn b1",NOWRAP=1)
			elif fieldName == 'UnigenID':
				try:
					gurl = HT.Href(webqtlConfig.UNIGEN_ID % tuple(string.split(keyValue,'.')[:2]), keyValue, Class="normalsize", target="_blank")
				except:
					gurl = keyValue
				return HT.TD(gurl, Class="fs12 fwn b1",NOWRAP=1)
			elif fieldName in ("exonCount", "Chromosome"):
				return HT.TD(keyValue, Class="fs12 fwn b1",align="right")
			elif fieldName in ("snpCount"):
				if keyValue:
					snpString = HT.Href(url="%s&chr=%s&start=%s&end=%s&geneName=%s&s1=%d&s2=%d" % (os.path.join(webqtlConfig.CGIDIR, 'main.py?FormID=snpBrowser'),
							theGO["Chromosome"], theGO["TxStart"], theGO["TxEnd"], theGO["GeneSymbol"], self.diffColDefault[0], self.diffColDefault[1]),
							text=theGO["snpCount"], target="_blank", Class="normalsize")
				else:
					snpString = keyValue
				return HT.TD(snpString, Class="fs12 fwn b1",align="right")
			elif fieldName in ("snpDensity", "GeneLength"):
				if keyValue: keyValue = "%2.3f" % keyValue
				else: keyValue = ""
				return HT.TD(keyValue, Class="fs12 fwn b1",align="right")
			elif fieldName in ("TxStart", "TxEnd"):
				return HT.TD("%2.6f" % keyValue, Class="fs12 fwn b1",align="right")
			else:
				return HT.TD(keyValue, Class="fs12 fwn b1",NOWRAP=1)
		else:
			return HT.TD(keyValue, Class="fs12 fwn b1",NOWRAP=1,align="right")

	def genControlForm(self, fd):
		##desc GeneList
		self.cursor.execute("Desc GeneList")
		GeneListFields = self.cursor.fetchall()
		GeneListFields = map(lambda X: X[0], GeneListFields)

		#group columns by category--used for creating the dropdown list of possible columns
		categories = {}
		for item in self.columnNames.keys():
			category = self.columnNames[item]
			if category[-1] not in categories.keys():
				categories[category[-1]] = [item ]
			else:
				categories[category[-1]] = categories[category[-1]]+[item]

		##List All Species in the Gene Table
		speciesDict = {}
		self.cursor.execute("select Species.Name, GeneList.SpeciesId from Species, GeneList where \
			GeneList.SpeciesId = Species.Id group by GeneList.SpeciesId order by Species.Id")
		results = self.cursor.fetchall()
		speciesField = categories.pop('species', [])
		categoriesOrder = ['gene', 'protein']
		for item in results:
			specName, specId = item
			categoriesOrder.append(specName)
			speciesDict[specName] = specId
			AppliedField = []
			for item2 in speciesField:
				if item2 in GeneListFields:
					self.cursor.execute("select %s from GeneList where SpeciesId = %d and %s is not NULL limit 1 " % (item2, specId, item2))
					columnApply = self.cursor.fetchone()
					if not columnApply:
						continue
				elif specName != 'mouse' and item2 in ('snpCount', 'snpDensity'):
					continue
				else:
					pass
				AppliedField.append(item2)
			categories[specName] = AppliedField

		categoriesOrder += ['misc']

		############################################################
		## Create the list of possible columns for the dropdown list
		############################################################
		allColumnsList = HT.Select(name="allColumns", Class="snpBrowserDropBox")

		for category in categoriesOrder:
			allFields = categories[category]
			if allFields:
				geneOpt = HT.Optgroup(label=category.title())
				for item in allFields:
					if category in self.speciesFreeze.keys():
						geneOpt.append(("%s (%s %s)" % (self.columnNames[item][1], category.title(), self.speciesFreeze[category]),
							"%s__%s" % (item, self.speciesFreeze[category])))
					else:
						geneOpt.append((self.columnNames[item][1], item))
				geneOpt.sort()
				allColumnsList.append(geneOpt)

		######################################
		## Create the list of selected columns
		######################################

		#cols contains the value of all the selected columns
		submitCols = cols = fd.formdata.getvalue("columns", "default")

		if cols == "default":
			if self.species=="mouse":  #these are the same columns that are shown on intervalPage.py
				cols = ['GeneSymbol', 'GeneDescription', 'Chromosome', 'TxStart', 'Strand', 'GeneLength', 'GeneID', 'NM_ID', 'snpCount', 'snpDensity']
			elif self.species=="rat":
				cols = ['GeneSymbol', 'GeneDescription', 'Chromosome', 'TxStart', 'GeneLength', 'Strand', 'GeneID', 'UnigenID']
			else:
				#should not happen
				cols = []
		else:
			if type(cols)==type(""):
				cols = [cols]

		colsLst = []
		dispFields = []
		for column in cols:
			if submitCols == "default" and column not in ('GeneSymbol') and (column in GeneListFields or column in speciesField):
				colsLst.append(("%s (%s %s)" % (self.columnNames[column][1], self.species.title(), self.speciesFreeze[self.species]),
							"%s__%s" % (column, self.speciesFreeze[self.species])))
				dispFields.append([column, self.species])
			else:
				column2 = column.split("__")
				if len(column2) == 1:
					colsLst.append((self.columnNames[column2[0]][1], column))
					dispFields.append([column])
				else:
					thisSpecies = self.speciesFreeze[column2[1]]
					colsLst.append(("%s (%s %s)" % (self.columnNames[column2[0]][1], thisSpecies.title(), column2[1]),
							column))
					dispFields.append((column2[0], thisSpecies))
		selectedColumnsList = HT.Select(name="columns", Class="snpBrowserSelectBox", multiple="true", data=colsLst, size=6)

		##########################
        ## Create the columns form
		##########################
		columnsForm = HT.Form(name="columnsForm", submit=HT.Input(type='hidden'), cgi=os.path.join(webqtlConfig.CGIDIR, self._scriptfile), enctype="multipart/form-data")
		columnsForm.append(HT.Input(type="hidden", name="fromdatabase", value= fd.formdata.getvalue("fromdatabase", "unknown")))
		columnsForm.append(HT.Input(type="hidden", name="species", value=self.species))
		if self.diffCol:
			columnsForm.append(HT.Input(type="hidden", name="s1", value=self.diffCol[0]))
			columnsForm.append(HT.Input(type="hidden", name="s2", value=self.diffCol[1]))
		startBox = HT.Input(type="text", name="startMb", value=self.startMb, size=10)
		endBox = HT.Input(type="text", name="endMb", value=self.endMb, size=10)
		addButton = HT.Input(type="button", name="add", value="Add", Class="button", onClick="addToList(this.form.allColumns.options[this.form.allColumns.selectedIndex].text, this.form.allColumns.options[this.form.allColumns.selectedIndex].value, this.form.columns)")
		removeButton = HT.Input(type="button", name="remove", value="Remove", Class="button", onClick="removeFromList(this.form.columns.selectedIndex, this.form.columns)")
		upButton = HT.Input(type="button", name="up", value="Up", Class="button", onClick="swapOptions(this.form.columns.selectedIndex, this.form.columns.selectedIndex-1, this.form.columns)")
		downButton = HT.Input(type="button", name="down", value="Down", Class="button", onClick="swapOptions(this.form.columns.selectedIndex, this.form.columns.selectedIndex+1, this.form.columns)")
		clearButton = HT.Input(type="button", name="clear", value="Clear", Class="button", onClick="deleteAllElements(this.form.columns)")
		submitButton = HT.Input(type="submit", value="Refresh", Class="button", onClick="selectAllElements(this.form.columns)")

		selectChrBox = HT.Select(name="chromosome")
		self.cursor.execute("""
			Select
				Chr_Length.Name, Length from Chr_Length, Species
			where
				Chr_Length.SpeciesId = Species.Id AND
				Species.Name = '%s'
			Order by
				Chr_Length.OrderId
			""" % self.species)

		results = self.cursor.fetchall()
		for chrInfo in results:
			selectChrBox.append((chrInfo[0], chrInfo[0]))
		selectChrBox.selected.append(self.Chr)

		innerColumnsTable = HT.TableLite(border=0, Class="collap", cellpadding = 2)
		innerColumnsTable.append(HT.TR(HT.TD(selectedColumnsList)),
					 HT.TR(HT.TD(clearButton, removeButton, upButton, downButton)))
		columnsTable = HT.TableLite(border=0, cellpadding=2, cellspacing=0)
		columnsTable.append(HT.TR(HT.TD(HT.Font("Chr: ", size=-1)),
					  HT.TD(selectChrBox, submitButton)),
				    HT.TR(HT.TD(HT.Font("View: ", size=-1)),
					  HT.TD(startBox, HT.Font("Mb to ", size=-1), endBox, HT.Font("Mb", size=-1))),
				    HT.TR(HT.TD(HT.Font("Show: ", size=-1)),
					  HT.TD(allColumnsList, addButton)),
				    HT.TR(HT.TD(""),
					  HT.TD(innerColumnsTable)))
		columnsForm.append(columnsTable)
		#columnsForm.append(HT.Input(type="hidden", name="sort", value=diffCol),
		#		   HT.Input(type="hidden", name="identification", value=identification),
		#		   HT.Input(type="hidden", name="traitInfo", value=traitInfo))

		return columnsForm, dispFields
