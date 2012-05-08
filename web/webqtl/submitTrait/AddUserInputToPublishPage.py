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

#AddUserInputToPublishPage.py
#
#Classes:
#AddUserInputToPublishPage
#-KA

import string
from htmlgen import HTMLgen2 as HT
import os
import time

from base.webqtlTrait import webqtlTrait
from base.webqtlDataset import webqtlDataset
from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil


#########################################
#      AddUserInputToPublishPage
#########################################

class AddUserInputToPublishPage(templatePage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)
		
		if not self.updMysql():
			return
		fd.incparentsf1 = 1
		if not fd.genotype:
			fd.readGenotype()
			fd.strainlist = fd.f1list + fd.strainlist
		fd.readData()

		if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:
			pass
		else:
			heading = "Add to Published Database"
			detail = ["You don't have the permission to modify this database"]
			self.error(heading=heading,detail=detail,error="Error")
			return
			
		self.cursor.execute("""
				SelecT 
					PublishFreeze.Name 
				from 
					PublishFreeze, InbredSet 
				where 
					PublishFreeze.InbredSetId = InbredSet.Id AND 
					InbredSet.Name = '%s'""" % fd.RISet)
		
		try:
			self.db = webqtlDataset(self.cursor.fetchone()[0], self.cursor)
		except:
			heading = "Add to Published Database"
			detail = ["The published database you requested has not been established"]
			self.error(heading=heading,detail=detail,error="Error")
			return
		
		status = fd.formdata.getvalue('curStatus')
		if status == 'insertResult':
			newRecord = self.readForm(fd)
			if not newRecord:
				return
			else:
				self.insertResultPage(fd, newRecord)
		elif status == 'insertCheck':
			newRecord = self.readForm(fd)
			if not newRecord:
				return
			else:
				self.insertCheckPage(fd, newRecord)
		else:
			self.dispFormPage(fd)
	
	def readForm(self, fd):
		newRecord = {}
		for field in self.db.disfield:
			fieldValue = fd.formdata.getvalue(field)
			if field == 'name' or field == 'sequence':
				fieldValue = None
			elif (not fieldValue) and (field == 'post_publication_description' or field == 'authors' or field == 'title' or field=='year'):
				heading = "Add to Published Database"
				detail = ["You did not enter information for %s." % webqtlUtil.formatField(field)]
				self.error(heading=heading,detail=detail,error="Error")
				return {}
			elif fieldValue and field == 'pubmed_id':
				try:
					fieldValue = int(fieldValue)
				except:
					fieldValue = None
			else:
				pass
			newRecord[field] = fieldValue
		return newRecord
		
	def insertResultPage(self, fd, newRecord):
		#generate html
		if 1:

			#XZ: Create new publication record if necessary
			PublicationId = None
			if newRecord['pubmed_id']:
				self.cursor.execute('SelecT Id from Publication where PubMed_ID = %d' % newRecord['pubmed_id'])
				results = self.cursor.fetchall()
				if not results:
					pass
				else:
					PublicationId = results[0][0]

			if not PublicationId:
				insertFields = ['Id']
				self.cursor.execute('SelecT max(Id) from Publication')
				maxId = self.cursor.fetchall()[0][0] + 1
				insertValues = [maxId]
				for field in self.db.disfield:
					if field in ('authors', 'title', 'abstract', 'journal','volume','pages','month','year') and newRecord[field]:
						insertFields.append(field)
						insertValues.append(newRecord[field])
				NFields = ['%s'] * len(insertFields)
				query = "insert into Publication (%s) Values (%s)" % (string.join(insertFields, ','), string.join(NFields, ','))

				self.cursor.execute(query, tuple(insertValues))
				PublicationId = maxId


			#XZ: Create new phenotype
			self.cursor.execute('SelecT max(Id) from Phenotype')
			maxId = self.cursor.fetchall()[0][0] + 1
			PhenotypeId = maxId
			if not newRecord['units']:
				newRecord['units'] = "Unknown"

			insertFields = ['Id']
			insertValues = [PhenotypeId]
			insertFields.append( 'Post_publication_description' )
			insertValues.append( newRecord['post_publication_description'] )
			insertFields.append( 'Units' )
			insertValues.append( newRecord['units'] )
			insertFields.append( 'Post_publication_abbreviation' )
                        insertValues.append( newRecord['post_publication_abbreviation'] )

			insertFields.append( 'Submitter' )
                        insertValues.append( self.userName )
			insertFields.append( 'Authorized_Users' )
			insertValues.append( self.userName )

			if newRecord['pre_publication_description']:
				insertFields.append( 'Pre_publication_description' )
				insertValues.append( newRecord['pre_publication_description'] )

			insertFields.append( 'Original_description' )
			original_desc_string = 'Original post publication description: ' + newRecord['post_publication_description']
			if newRecord['pre_publication_description']:
				original_desc_string = original_desc_string + '\n\nOriginal pre publication description: ' + newRecord['pre_publication_description']
			insertValues.append( original_desc_string )

			if newRecord['pre_publication_abbreviation']:
				insertFields.append( 'Pre_publication_abbreviation' )
				insertValues.append( newRecord['pre_publication_abbreviation'] )

			if newRecord['lab_code']:
				insertFields.append( 'Lab_code' )
				insertValues.append( newRecord['lab_code'] )

			if newRecord['owner']:
				insertFields.append( 'Owner' )
				insertValues.append( newRecord['owner'] )


			NFields = ['%s'] * len(insertFields)
			query = "insert into Phenotype (%s) Values (%s)" % (string.join(insertFields, ','), string.join(NFields, ','))
			self.cursor.execute(query, tuple(insertValues))

			


			#XZ: Insert data into PublishData, PublishSE and NStrain tables.
			self.cursor.execute('SelecT max(Id) from PublishData')
			DataId = self.cursor.fetchall()[0][0] + 1

			self.db.getRISet()
			InbredSetId = self.db.risetid

			self.cursor.execute('Select SpeciesId from InbredSet where Id=%s' % InbredSetId)
			SpeciesId = self.cursor.fetchone()[0]

			StrainIds = []
			for item in fd.strainlist:
				self.cursor.execute('Select Id from Strain where SpeciesId=%s and Name = "%s"' % (SpeciesId, item) )
				StrainId = self.cursor.fetchall()
				if not StrainId:
					raise ValueError
				else:
					StrainIds.append(StrainId[0][0])
			
			for i, strainName in enumerate(fd.strainlist):
				if fd.allTraitData.has_key(strainName):
					tdata = fd.allTraitData[strainName]
					traitVal, traitVar, traitNP = tdata.val, tdata.var, tdata.N
				else:
					continue
					
				if traitVal != None:
					#print 'insert into Data values(%d, %d, %s)' % (DataId, StrainIds[i], traitVal), "<BR>"
					#XZ, 03/05/2009: Xiaodong changed Data to PublishData
					self.cursor.execute('insert into PublishData values(%d, %d, %s)' % (DataId, StrainIds[i], traitVal))
				if traitVar != None:
					#print 'insert into SE values(%d, %d, %s)' % (DataId, StrainIds[i], traitVar), "<BR>"
					#XZ, 03/13/2009: Xiaodong changed SE to PublishSE
					self.cursor.execute('insert into PublishSE values(%d, %d, %s)' % (DataId, StrainIds[i], traitVar))
				if traitNP != None:
					#print 'insert into NStrain values(%d, %d, %s)' % (DataId, StrainIds[i], traitNP), "<BR>"
					self.cursor.execute('insert into NStrain values(%d, %d, %d)' % (DataId, StrainIds[i], traitNP))


			self.cursor.execute('SelecT max(Sequence) from PublishXRef where InbredSetId = %d and PhenotypeId = %d and PublicationId = %d' % (InbredSetId,PhenotypeId,PublicationId))
			Sequence = self.cursor.fetchall()
			if not Sequence or not Sequence[0][0]:
				Sequence = 1
			else:
				Sequence = Sequence[0][0] + 1
			
			self.cursor.execute('SelecT max(Id) from PublishXRef where InbredSetId = %d' % InbredSetId)
			try:
				InsertId = self.cursor.fetchall()[0][0] + 1
			except:
				InsertId = 10001
			
			ctime = time.ctime()
			comments = "Inserted by %s at %s\n" % (self.userName, ctime)
			#print 'insert into PublishXRef(Id, PublicationId, InbredSetId, PhenotypeId, DataId, Sequence, comments) values(%s, %s, %s, %s, %s, %s, %s)' % (InsertId , PublicationId, InbredSetId, PhenotypeId, DataId, Sequence, comments)
			self.cursor.execute('insert into PublishXRef(Id, PublicationId, InbredSetId, PhenotypeId, DataId, Sequence, comments) values(%s, %s, %s, %s, %s, %s, %s)', (InsertId , PublicationId, InbredSetId, PhenotypeId, DataId, Sequence, comments))
			
			TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#ffffff", height=200)
			form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))
			hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':'_','CellID':'_','RISet':fd.RISet, 'incparentsf1':'on'}
			for key in hddn.keys():
				form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
			
			mainTitle = HT.Paragraph("Add Trait to Published Database", Class="title")
			
			info = HT.Paragraph("Your Trait has been succesfully added to ", self.db.genHTML(), ".")
			
			thisTrait = webqtlTrait(db=self.db, cursor=self.cursor, name=InsertId)
			thisTrait.retrieveInfo()
			
			tbl = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0)
			
			checkBox = HT.Input(type="checkbox",name="searchResult",value="%s" % thisTrait)
			tbl.append(HT.TR(HT.TD(width=30), HT.TD(thisTrait.genHTML(dispFromDatabase=1, privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users))))
			form.append(info, HT.P(), tbl)
			TD_LR.append(mainTitle, HT.Blockquote(form))
			
			self.dict['body'] = TD_LR
		else:
			heading = "Add to Published Database"
			detail = ["Error occured while adding the data."]
			self.error(heading=heading,detail=detail,error="Error")
			return
	
	def insertCheckPage(self, fd, newRecord):
		#generate html
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='dataInput',submit=HT.Input(type='hidden'))
		hddn = {'database':self.db.name, 'curStatus':'insertResult', 'FormID':'dataEditing', 'submitID':'addPublish', 'RISet':fd.RISet}
		
		recordTable = HT.TableLite(border=0, align="left")
		title1 = HT.Paragraph("Trait Information:", Class="subtitle")
		title2 = HT.Paragraph("Trait Data:", Class="subtitle")
		recordInfoContainer = HT.Div(align="left")
		recordDataContainer = HT.Div(align="left")
		addButton = HT.Input(type='submit',name='submit', value='Add to Publish',Class="button")
		resetButton = HT.Input(type='reset',Class="button")

		recordInfoTable = HT.TableLite(border=0, cellspacing=1, cellpadding=5, align="left")
		for field in self.db.disfield:
			if newRecord[field]:
				recordInfoTable.append(HT.TR(
					HT.TD("%s :" % webqtlUtil.formatField(field), Class="fs12 fwb ff1", valign="top",align="right"),
					HT.TD(width=20),HT.TD(newRecord[field])))
				hddn[field] = newRecord[field]

		recordInfoContainer.append(addButton, resetButton, HT.P(), title1, HT.BR(), recordInfoTable)
		
		recordDataTable = HT.TableLite(border=0, width = "80%",cellspacing=3, cellpadding=2)	
		recordDataTable.append(HT.TR(HT.TD('Strain Name',Class="fs12 ffl fwb",align="left"), 
			HT.TD('TraitData',Class="fs12 ffl fwb",align="right"), 
			HT.TD('SE',Class="fs12 ffl fwb",align="right"),
			HT.TD('N Per Strain',Class="fs12 ffl fwb",align="right"),
			HT.TD('&nbsp'*8,Class="fs12 ffl fwb",align="center"),
			HT.TD('Strain Name',Class="fs12 ffl fwb",align="left"), 
			HT.TD('TraitData',Class="fs12 ffl fwb",align="right"), 
			HT.TD('SE',Class="fs12 ffl fwb",align="right"),
			HT.TD('N Per Strain',Class="fs12 ffl fwb",align="right")))
		
		tempTR = HT.TR(align="Center")
		for i, strainName in enumerate(fd.strainlist):
			if fd.allTraitData.has_key(strainName):
				tdata = fd.allTraitData[strainName]
				traitVal, traitVar, traitNP = tdata.val, tdata.var, tdata.N
			else:
				traitVal, traitVar, traitNP = None, None, None
			
			if traitVal != None:	
				traitVal = "%2.3f" % traitVal
			else:
				traitVal = 'x'
			if traitVar != None:	
				traitVar = "%2.3f" % traitVar
			else:
				traitVar = 'x'
			if traitNP != None:	
				traitNP = "%d" % traitNP
			else:
				traitNP = 'x'
					
			tempTR.append(HT.TD(HT.Paragraph(strainName),align='left'), 
				HT.TD(traitVal,align='right'), 
				HT.TD(traitVar,align='right'),
				HT.TD(traitNP,align='right'),
				HT.TD('',align='center'))
			if i % 2:
				recordDataTable.append(tempTR)
				tempTR = HT.TR(align="Center")
				
		if (i+1) % 2:
			tempTR.append(HT.TD(''))
			tempTR.append(HT.TD(''))
			recordDataTable.append(tempTR)

		info = HT.Paragraph("Please review the trait information and data in the text below. Check the values for errors. If no error is found, please click the \"Add to Publish\" button to submit it.")
		recordDataContainer.append(title2, HT.BR(), info, HT.P(), recordDataTable, HT.P(), addButton, resetButton, HT.P())

		recordTable.append(HT.TR(HT.TD(recordInfoContainer)), HT.TR(HT.TD(recordDataContainer)))			

		webqtlUtil.exportData(hddn, fd.allTraitData, 1)
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))

		
		#############################
		TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#ffffff")
		
		mainTitle = HT.Paragraph("Add Trait to Published Database", Class="title")

		form.append(recordTable)
		
		TD_LR.append(mainTitle, HT.Blockquote(form))
		
		self.dict['body'] = TD_LR

	def dispFormPage(self, fd):
		###specical care, temporary trait data
		fullname =  fd.formdata.getvalue('fullname')
		if fullname:
			thisTrait = webqtlTrait(fullname=fullname, data= fd.allTraitData, cursor=self.cursor)
			thisTrait.retrieveInfo()
			PhenotypeValue = thisTrait.description
		else:
			thisTrait = webqtlTrait(data= fd.allTraitData)
			PhenotypeValue = thisTrait.identification
			
		self.dict['title'] = 'Add to Published Database'
		
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='dataInput',submit=HT.Input(type='hidden'))

		recordTable = HT.TableLite(border=0, align="left")
		recordInfoContainer = HT.Div(align="left")
		recordDataContainer = HT.Div(align="left")
		title1 = HT.Paragraph("&nbsp;Trait Information:", align="left", Class="subtitle")
		title2 = HT.Paragraph("&nbsp;Trait Data:", align="left", Class="subtitle")
		addButton = HT.Input(type='submit',name='submit', value='Submit Trait',Class="button")
		resetButton = HT.Input(type='reset',Class="button")

		recordInfoTable = HT.TableLite(border=0, cellspacing=1, cellpadding=5,align="left")
		for field in self.db.disfield:
			fieldValue = ""

			if field == 'comments':
				continue
			elif field == 'name' or field == 'sequence' or field == 'original_description' or field == 'submitter' or field == 'authorized_users':
				form.append(HT.Input(type="hidden",name=field,value=fieldValue))
				continue
			elif field == 'post_publication_description':
				inputBox = HT.Textarea(name=field, cols=60, rows=6,text=PhenotypeValue)
			elif field == 'abstract' or field == 'pre_publication_description' or field == 'owner':
				inputBox = HT.Textarea(name=field, cols=60, rows=6,text=fieldValue)
			elif field == 'post_publication_abbreviation' or field == 'pre_publication_abbreviation':
				inputBox = HT.Input(type="text",name=field,size=60, maxlength=30,value=fieldValue)
			else:
				inputBox = HT.Input(type="text",name=field,size=60, maxlength=255,value=fieldValue)
			if field in ('post_publication_description', 'authors', 'title', 'year'):
				requiredSign = HT.Span('*', Class="cr")
			else:
				requiredSign = ''
				
			recordInfoTable.append(HT.TR(
				HT.TD(requiredSign, "%s :" % webqtlUtil.formatField(field), Class="fs12 fwb ff1", valign="top",align="right"),
				HT.TD(width=20),HT.TD(inputBox)))

			if field == 'pubmed_id':
				recordInfoTable.append(HT.TR(
				HT.TD(), HT.TD(width=20), 
				HT.TD("Do not enter PubMed_ID if this trait has not been Published.", 
					HT.BR(), "If the PubMed_ID you entered is alreday stored in our database, ",
					HT.BR(), "all the following fields except Post Publication Description will be ignored.",
					HT.BR(), "Do not enter any non-digit character in this field.", Class="fs11 cr")
				))
			if field == 'pre_publication_description':
				recordInfoTable.append(HT.TR(
				HT.TD(), HT.TD(width=20),
				HT.TD("If the PubMed ID is entered, the Post Publication Description will be shown to all",
					HT.BR(), " users. If there is no PubMed ID, and the Pre Publication Description is entered,",
					HT.BR(), "only you and authorized users can see the Post Publication Description.", Class="fs11 cr")
				))
			if field == 'owner':
				recordInfoTable.append(HT.TR(
				HT.TD(), HT.TD(width=20),
				HT.TD("Please provide detailed owner contact information including full name, title,",
                                        HT.BR(), " institution, address, email etc", Class="fs11 cr")
				))

		recordInfoTable.append(HT.TR(HT.TD(HT.Span('*', Class="cr"), " Required field", align="center", colspan=3)))
		recordInfoContainer.append(addButton, resetButton, HT.P(), title1, HT.BR(), recordInfoTable)

		recordDataTable = HT.TableLite(border=0, width = "90%",cellspacing=2, cellpadding=2)
		recordDataTable.append(HT.TR(HT.TD('Strain Name',Class="fs12 ffl fwb",align="left"), 
			HT.TD('Trait Data',Class="fs12 ffl fwb",align="right"), 
			HT.TD('SE',Class="fs12 ffl fwb",align="right"),
			HT.TD('N Per Strain',Class="fs12 ffl fwb",align="right"),
			HT.TD('&nbsp'*8,Class="fs12 ffl fwb",align="center"),
			HT.TD('Strain Name',Class="fs12 ffl fwb",align="left"), 
			HT.TD('Trait Data',Class="fs12 ffl fwb",align="right"), 
			HT.TD('SE',Class="fs12 ffl fwb",align="right"),
			HT.TD('N Per Strain',Class="fs12 ffl fwb",align="right")))
		
		tempTR = HT.TR(align="right")
		for i, strainName in enumerate(fd.strainlist):
			if thisTrait.data.has_key(strainName):
				tdata = thisTrait.data[strainName]
				traitVal, traitVar, traitNP = tdata.val, tdata.var, tdata.N
			else:
				traitVal, traitVar, traitNP = None, None, None
			
			if traitVal != None:	
				traitVal = "%2.3f" % traitVal
			else:
				traitVal = 'x'
			if traitVar != None:	
				traitVar = "%2.3f" % traitVar
			else:
				traitVar = 'x'
			if traitNP != None:	
				traitNP = "%d" % traitNP
			else:
				traitNP = 'x'

			tempTR.append(HT.TD(HT.Paragraph(strainName), width="120px", align='left'), \
				HT.TD(HT.Input(name=fd.strainlist[i], size=8, maxlength=8, value=traitVal, align="right"), width="100px", align='right'),
				HT.TD(HT.Input(name='V'+fd.strainlist[i], size=8, maxlength=8, value=traitVar, align="right"), width="100px", align='right'),
				HT.TD(HT.Input(name='N'+fd.strainlist[i], size=8, maxlength=8, value=traitNP, align="right"), width="120px", align='right'),
				HT.TD('', align='center'))
			if i % 2:
				recordDataTable.append(tempTR)
				tempTR = HT.TR(align="Center")
		
		if (i+1) % 2:
			tempTR.append(HT.TD(''))
			tempTR.append(HT.TD(''))
			tempTR.append(HT.TD(''))
			recordDataTable.append(tempTR)

		recordDataContainer.append(title2, HT.BR(), recordDataTable, HT.P(), addButton, resetButton, HT.P())

		recordTable.append(HT.TR(HT.TD(recordInfoContainer)), HT.TR(HT.TD(recordDataContainer)))

		"""
		"""
		
		hddn = {'database':self.db.name, 'curStatus':'insertCheck', 'FormID':'dataEditing', 'submitID':'addPublish', 'RISet':fd.RISet}
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))

		
		#############################
		TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#ffffff")
		
		mainTitle = HT.Paragraph("Add Trait to Published Database", Class="title")
		
		form.append(recordTable)
		
		TD_LR.append(mainTitle, form)
		
		self.dict['body'] = TD_LR
			
