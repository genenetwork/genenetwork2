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
# Last updated by GeneNetwork Core Team 2011/04/20



#DataUpdatePage.py
#
#Classes:
#DataUpagePage
#-KA


import string
from htmlgen import HTMLgen2 as HT
import os
import time

from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil
from dbFunction import webqtlDatabaseFunction

#########################################
#      Update Trait
#########################################

class DataUpdatePage(templatePage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		if not self.updMysql():
			return

		if not fd.genotype:
			fd.readGenotype()
			fd.strainlist = fd.f1list + fd.strainlist
		
		fd.readData()
		
		self.formdata = fd.formdata
		self.dict['title'] = 'Data Updating'
		
		try:
			thisTrait = webqtlTrait(fullname=self.formdata.getvalue('fullname'), cursor=self.cursor)
			thisTrait.retrieveInfo()
		except:
			heading = "Updating Database"
			detail = ["The trait doesn't exist."]
			self.error(heading=heading,detail=detail,error="Error")
			return

		if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:
				pass
		else:
			heading = "Updating Database"
			detail = ["You don't have the permission to modify this trait"]
			self.error(heading=heading,detail=detail,error="Error")
			return

			
		status = self.formdata.getvalue('curStatus')
		if status == 'updateCheck': #XZhou: Check the change
			self.updateCheckPage(fd, thisTrait)
		elif status == 'updateResult': #XZhou: make the changes to database
			self.updateResultPage(fd, thisTrait)
		else: #XZhou: show info retrieved from database
			self.dispTraitPage(fd, thisTrait)


	def dispTraitPage(self, fd, thisTrait):	
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='dataInput',submit=HT.Input(type='hidden'))

		#XZhou: This is to show trait info.
		recordInfoTable = HT.TableLite(border=0, cellspacing=1, cellpadding=5,align="left")

		for field in thisTrait.db.disfield:
			fieldValue = getattr(thisTrait, field)
			if not fieldValue:
				fieldValue = ""
			#fields to be ignored
			if field in ("chipid", "genbankid"):
				continue
			elif field == "comments":
				if fieldValue:
					comments = string.split(fieldValue, '\n')
					title0 = HT.Paragraph("Update History: ", Class="subtitle")
					form.append(title0)
					history = HT.Blockquote()
					for item in comments:
						if item:
							history.append(item, HT.BR())
					form.append(history)
				continue
			else:
				pass
				
			if field == 'name' or field == 'units':
				form.append(HT.Input(type="hidden",name=field,value=fieldValue))
				if field == 'name':
					inputBox = HT.Strong(fieldValue)
				else:
					continue
			elif field == 'pubmed_id':
				inputBox = HT.Span(HT.Input(type="text",name=field,size=60, maxlength=255,value=fieldValue))
				warning = HT.Paragraph(Class="fs11 cr")
				warning.append('1. Please enter only the PubMed ID integer value into the field above.', HT.BR(), '&nbsp;&nbsp;&nbsp;&nbsp;Don\'t enter',
							' other characters.', HT.BR()) 
				warning.append('2. If you modify an existing PubMed ID, changes will affect other records with', HT.BR(), \
							'&nbsp;&nbsp;&nbsp;&nbsp;the same ID but will NOT affect the phenotype description or trait data.', HT.BR()) 
				warning.append('3. If your delete an existing PubMed ID, this will not affect any other traits,', HT.BR(), \
							'&nbsp;&nbsp;&nbsp;&nbsp;including those with the same PubMed ID.', HT.BR()) 
				warning.append('4. If you enter publication data for a PubMed ID that is already in the database,', HT.BR(), \
							'&nbsp;&nbsp;&nbsp;&nbsp;then all fields except Phenotype and Trait Data will be ignored.') 
				inputBox.append(warning)
			elif field == 'pre_publication_description' or field == 'post_publication_description' or field == 'original_description' or field == 'owner' or field == 'abstract' or field == 'blatseq' or field == 'targetseq' or field == 'description' or field == 'authors' or field == 'sequence' or field == 'alias' or field == 'probe_target_description':
				inputBox = HT.Textarea(name=field, cols=60, rows=4,text=fieldValue)
			elif field == 'post_publication_abbreviation' or field == 'pre_publication_abbreviation':
				inputBox = HT.Input(type="text",name=field,size=60, maxlength=30,value=fieldValue)
			elif field == 'geneid':
				inputBox = HT.Input(type="text",name=field,size=60, maxlength=255,value=fieldValue)
				recordInfoTable.append(HT.TR(
                                HT.TD("%s :" % webqtlUtil.formatField(field), Class="fs12 fwb ff1", align="right"),
                                HT.TD(width=20),HT.TD(inputBox)))
				#XZ: homologene is not in thisTrait.db.disfield, so have to do in this way
				field = 'homologeneid'
				inputBox = HT.Input(type="text",name=field,size=60, maxlength=255,value=thisTrait.homologeneid)
			else:
				inputBox = HT.Input(type="text",name=field,size=60, maxlength=255,value=fieldValue)

			#XZ: For existing non-confidential phenotype trait, pre_publication_description and pre_publication_abbreviation are not shown to anybody except submitter or admistrator to prevent the trait being set to confidential one.
			if thisTrait.db.type == 'Publish' and field == 'pre_publication_description' or field == 'pre_publication_abbreviation':
				if not thisTrait.confidential and webqtlConfig.USERDICT[self.privilege] < webqtlConfig.USERDICT['admin'] and self.userName != thisTrait.submitter:
					continue

			#XZ and Rob, April 20, 2011: This is to add field and inputBox to table. Note that the change of format to each field(Capitalize) by webqtlUtil.formatField function.
			recordInfoTable.append(HT.TR(
				HT.TD("%s :" % webqtlUtil.formatField(field), Class="fs12 fwb ff1", align="right", valign="top"),
				HT.TD(width=5),HT.TD(inputBox)))

		#XZhou: This is to show trait data.
		recordDataTable = HT.Text('Trait data updating is disabled')
		
		if thisTrait.db.type == 'Publish':
			thisTrait.retrieveData()
			recordDataTable = HT.TableLite(border=0, width = "90%",cellspacing=2, cellpadding=2)
			recordDataTable.append(HT.TR(HT.TD('Strain Name',Class="fs12 ffl fwb",align="Center"), 
				HT.TD('TraitData',Class="fs12 ffl fwb",align="Center"), 
				HT.TD('SE',Class="fs12 ffl fwb",align="Center"),
				HT.TD('N Per Strain',Class="fs12 ffl fwb",align="Center"),
				HT.TD('Strain Name',Class="fs12 ffl fwb",align="Center"), 
				HT.TD('TraitData',Class="fs12 ffl fwb",align="Center"), 
				HT.TD('SE',Class="fs12 ffl fwb",align="Center"),
				HT.TD('N Per Strain',Class="fs12 ffl fwb",align="Center")))
			tempTR = HT.TR(align="Center")
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
						
				tempTR.append(HT.TD(HT.Paragraph(strainName),align='CENTER'), 
					HT.TD(HT.Input(name=strainName, size=8, maxlength=8, value=traitVal),align='CENTER'),
					HT.TD(HT.Input(name='V'+strainName, size=8, maxlength=8, value=traitVar),align='CENTER'),
					HT.TD(HT.Input(name='N'+strainName, size=8, maxlength=8, value=traitNP),align='CENTER'))
				if i % 2:
					recordDataTable.append(tempTR)
					tempTR = HT.TR(align="Center")
			
			if (i+1) % 2:
				tempTR.append(HT.TD(''))
				tempTR.append(HT.TD(''))
				tempTR.append(HT.TD(''))
				recordDataTable.append(tempTR)
					
		updateButton = HT.Input(type='submit',name='submit', value='Submit Change',Class="button")
		resetButton = HT.Input(type='reset',Class="button")
		
		hddn = {'fullname':str(thisTrait), 'FormID':'updateRecord', 'curStatus':'updateCheck', 'RISet':fd.RISet, "incparentsf1":1}
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))

		
		#############################
		TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#eeeeee")

		containerTable = HT.TableLite(border=0, width = "90%",cellspacing=0, cellpadding=0)
		
		mainTitle = HT.Paragraph("Update Info and Data", Class="title")
		
		title1 = HT.Paragraph("Trait Information: ", Class="subtitle")

		title2 = HT.Paragraph("Trait Data:", Class="subtitle")

		containerTable.append(HT.TR(HT.TD(title1)), HT.TR(HT.TD(HT.BR(),updateButton,resetButton,HT.BR(),HT.BR())), 
					 HT.TR(HT.TD(recordInfoTable)), HT.TR(HT.TD(title2)), HT.TR(HT.TD(HT.BR(),recordDataTable, HT.BR(), HT.BR())),
					 HT.TR(HT.TD(updateButton,resetButton)))
		
		form.append(containerTable)
		
		TD_LR.append(mainTitle, form)
		
		self.dict['body'] = TD_LR
		
	def updateCheckPage(self, fd, thisTrait):
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='updateCheck',submit=HT.Input(type='hidden'))
		hddn = {'fullname':str(thisTrait), 'FormID':'updateRecord', 'curStatus':'updateResult', 'RISet':fd.RISet, "incparentsf1":1}
		
		recordInfoTable = HT.TableLite(border=0, cellspacing=1, cellpadding=5,align="left",width="90%")
		infoChanges = []
		for field in thisTrait.db.disfield:
			#fields to be ignored
			#XZ: The stupid htmlgen can not set readonly for input and textarea. This is the only way I can prevent displayed items such as 'original_description', 'submitter' being changed.
			if field in ("chipid", "genbankid", "comments", "original_description", "submitter"):
				continue
			oldValue = getattr(thisTrait, field)
			if not oldValue:
				oldValue = ''
			oldValue = str(oldValue)
			modifiedValue = self.formdata.getvalue(field)
			if not modifiedValue:
				modifiedValue = ""
			modifiedValue.strip()
			oldValue.strip()
			if oldValue == modifiedValue:
				form.append(HT.Input(type="hidden",name=field,value=oldValue))
				continue
				
			oldValue = HT.Paragraph(oldValue, Class="cr")
			warning = ''
			if field == 'PubMed_ID':
				if modifiedValue != "":
					try:
						modifiedValue = int(modifiedValue)
					except:
						continue
					
				#whether new PMID already exists
				newPMIDExist = None
				if modifiedValue:
					self.cursor.execute("SelecT Id from Publication where PubMed_ID = %d" % modifiedValue)
					results = self.cursor.fetchall()
					if results:
						newPMIDExist = results[0][0]
				if newPMIDExist:
					warning = HT.Paragraph(Class="fs11 cr")
					warning.append('This new PubMed_ID already exists in our database. If you still want to change to this very PubMed_ID, the publication information (title, author, journal, etc.) will be replaced by those linked to this new PubMed_ID. That means, all the fields below (if any, except phenotype info and trait value) will be ignored.')

			infoChanges.append(field)
			inputBox = HT.Textarea(name=field, cols=50, rows=3,text=modifiedValue, onChange = "Javascript:this.form.curStatus.value='updateCheck';")
			recordInfoTable.append(
				HT.TR(HT.TD("%s :" % webqtlUtil.formatField(field), Class="fs12 fwb ff1", colspan = 3, valign="top")), 
				HT.TR(HT.TD(oldValue, valign="top"),HT.TD(width=20),HT.TD( inputBox, warning)))

		#XZ: homologeneid is not in thisTrait.db.disfield
		if thisTrait.db.type == "ProbeSet":
			field = 'homologeneid'
			oldValue = getattr(thisTrait, field)
                        if not oldValue:
                                oldValue = ''
                        oldValue = str(oldValue)
                        modifiedValue = self.formdata.getvalue(field)
                        if not modifiedValue:
                                modifiedValue = ""
                        modifiedValue.strip()
                        oldValue.strip()

                        if oldValue == modifiedValue:
                                form.append(HT.Input(type="hidden",name=field,value=oldValue))
                        else:
				oldValue = HT.Paragraph(oldValue, Class="cr")
				warning = ''
				infoChanges.append(field)
				inputBox = HT.Textarea(name=field, cols=50, rows=3,text=modifiedValue, onChange = "Javascript:this.form.curStatus.value='updateCheck';")
	                        recordInfoTable.append(
        			                        HT.TR(HT.TD("%s :" % webqtlUtil.formatField(field), Class="fs12 fwb ff1", colspan = 3, valign="top")),
                                			HT.TR(HT.TD(oldValue, valign="top"),HT.TD(width=20),HT.TD( inputBox, warning)))
				

		if infoChanges == []:
			recordInfoTable = ""
			recordInfoChange = HT.Blockquote('No change has been made.')
		else:
			hddn['modifiedField'] = string.join(infoChanges, '::')
			recordInfoChange = ''
			
		recordDataChange = HT.Blockquote('Trait data updating is disabled')
		recordDataTable = ""
		
		modifiedVals = []
		modifiedVars = []
		modifiedNps = []
		numDataChanges = 0
		if thisTrait.db.type == 'Publish':
			thisTrait.retrieveData()
			recordDataTable = HT.TableLite(border=0, width = "90%",cellspacing=2, cellpadding=2)
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
					
				try:	
					modifiedVal =  "%2.3f" % fd.allTraitData[strainName].val
				except:
					modifiedVal = 'x'
				try:	
					modifiedVar = "%2.3f" % fd.allTraitData[strainName].var
				except:
					modifiedVar = 'x'
				try:	
					modifiedNp = "%d" % fd.allTraitData[strainName].N
				except:
					modifiedNp = 'x'
				
				if modifiedVal != traitVal:
					recordDataTable.append(HT.TR(HT.TD(HT.Paragraph(strainName + " Value")),
						HT.TD(HT.Paragraph(traitVal, Class="cr")), 
						HT.TD(HT.Input(name=strainName, size=8, maxlength=8, value=modifiedVal, onChange = "Javascript:this.form.curStatus.value='updateCheck';"))))
					numDataChanges += 1
					modifiedVals.append(modifiedVal)
				else:
					form.append(HT.Input(type="hidden",name=strainName,value=traitVal))
					modifiedVals.append(traitVal)
					
				if modifiedVar != traitVar:
					recordDataTable.append(HT.TR(HT.TD(HT.Paragraph(strainName + " SE")),
						HT.TD(HT.Paragraph(traitVar, Class="cr")), 
						HT.TD(HT.Input(name='V'+strainName, size=8, maxlength=8, value=modifiedVar, onChange = "Javascript:this.form.curStatus.value='updateCheck';"))))
					numDataChanges += 1
					modifiedVars.append(modifiedVar)
				else:
					form.append(HT.Input(type="hidden",name='V'+strainName,value=traitVar))
					modifiedVars.append(traitVar)
					
				if modifiedNp != traitNP:
					recordDataTable.append(HT.TR(HT.TD(HT.Paragraph(strainName + " N Per Strain")),
						HT.TD(HT.Paragraph(traitNP, Class="cr")), 
						HT.TD(HT.Input(name='N'+strainName, size=8, maxlength=8, value=modifiedNp, onChange = "Javascript:this.form.curStatus.value='updateCheck';"))))
					numDataChanges += 1
					modifiedNps.append(modifiedNp)
				else:
					form.append(HT.Input(type="hidden",name='N'+strainName,value=traitNP))
					modifiedNps.append(traitNP)
					
					
			if numDataChanges == 0:
				recordDataChange = HT.Blockquote('No change has been made.')
				recordDataTable = ""
			else:
				hddn['modifiedDataField'] = 1
				recordDataChange = ""
				
		#if numDataChanges:
		#	hddn['val'] = string.join(modifiedVals, ',')
		#	hddn['var'] = string.join(modifiedVars, ',')
		#	hddn['np'] = string.join(modifiedNps, ',')
			
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))

		#############################
		TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#eeeeee", height=200)
		
		mainTitle = HT.Paragraph("Update Info and Data", Class="title")
		
		title1 = HT.Paragraph("Trait Information:", Class="subtitle")

		title2 = HT.Paragraph("Trait Data:", Class="subtitle")
		
		if numDataChanges or infoChanges:
			recordChange = HT.Blockquote('The table below lists all the changes made. The texts in red are the original information stored on the server, the texts to the right are the modified version. ')
			updateButton = HT.Input(type='submit',name='submit', value='Update Data',Class="button")
			resetButton = HT.Input(type='reset',Class="button")
			form.append(title1, HT.Center(updateButton,resetButton), recordInfoChange, recordInfoTable,title2, recordDataChange, HT.Center(recordDataTable,HT.P(),updateButton,resetButton),HT.P())
			TD_LR.append(mainTitle, recordChange, HT.Blockquote(form))
		else:
			recordInfoChange = HT.Blockquote("No change has been made")
			TD_LR.append(mainTitle, recordInfoChange)
			
		self.dict['body'] = TD_LR
		#self.dict['js1'] = webqtlConfig.resetFieldScript
		return

	def updateResultPage(self, fd, thisTrait):
	
		comments = []
		ctime = time.ctime()
		##Start Updating
		dataID = -1
		if thisTrait.db.type == 'Publish':
			self.cursor.execute("SelecT PublishXRef.InbredSetId, PublishXRef.DataId, PublishXRef.PublicationId, PublishXRef.PhenotypeId, PublishXRef.Sequence from PublishXRef, PublishFreeze where PublishXRef.InbredSetId= PublishFreeze.InbredSetId and  PublishFreeze.Name = '%s' and PublishXRef.Id = %s" % (thisTrait.db.name, thisTrait.name))
			PInbredSetId, dataID, PublicationId, PhenotypeId, Sequence = self.cursor.fetchall()[0]
			
		modifyField = self.formdata.getvalue('modifiedField')
		###Modify Trait Informations
		if modifyField:
			modifyField = string.split(modifyField, '::')
			comments += modifyField
			updateHomologeneid = False

			if thisTrait.db.type == 'Publish':
				PhenotypeItemUpdate = []
				PhenotypeItemValues = []
				PublicationItemUpdate = []
				PublicationItemValues = []

				for item in modifyField:
					itemvalue = self.formdata.getvalue(item)

					#XZ: identify Phenotype items
					if item in ['pre_publication_description', 'post_publication_description', 'original_description', 'pre_publication_abbreviation', 'post_publication_abbreviation', 'lab_code', 'submitter', 'owner', 'authorized_users', 'units']:
						if itemvalue != None: #XZ: the problem is that the item value can not be deleted
							PhenotypeItemUpdate.append('%s=%%s' % item)
							PhenotypeItemValues.append(itemvalue)

							continue #XZ: this is important to distinguish Phenotype item and Publication item

					elif item == "pubmed_id":
						#Only integer allowed in this field
						try:
							itemvalue = int(itemvalue)
						except:
							itemvalue = None
							
						#whether old PMID exists
						self.cursor.execute("SelecT PubMed_ID from Publication where Id = %d" % PublicationId)
						oldPMID = self.cursor.fetchone()
						if oldPMID:
							oldPMID = oldPMID[0]
						
						#whether new PMID already exists
						newPMID = None
						self.cursor.execute("SelecT Id from Publication where PubMed_ID = %d" % itemvalue)
						newPMID = self.cursor.fetchone()
						if newPMID:
							newPMID = newPMID[0]
						
						##the logic is still not very clear here
						if newPMID:
							#new PMID in record
							self.cursor.execute("Update PublishXRef set PublicationId = %d where InbredSetId=%d and PhenotypeId=%d and PublicationId=%d and Sequence=%d" % (newPMID, PInbredSetId, PhenotypeId, PublicationId, Sequence))
							#no need to update other fields
							PublicationItemUpdate = []
							break
						elif itemvalue:
							#have new PMID, but not in record or need to change
							self.cursor.execute("Update Publication set pubmed_id=%d where Id = %s" % (itemvalue,PublicationId))
						else:
							#no new PMID
							if oldPMID:
								#remove a pubmed_id, don't know if this ever gonna happen
								self.cursor.execute("SelecT max(Id) from Publication")
								maxId = self.cursor.fetchone()[0] + 1
								self.cursor.execute("SelecT * from Publication where Id = %d" % PublicationId)
								oldRecs = list(self.cursor.fetchone())
								oldRecs[0] = maxId
								oldRecs[1] = None
								NFields = ['%s'] * len(oldRecs)
								query = "insert into Publication Values (%s)" % string.join(NFields, ',')
								self.cursor.execute(query, tuple(oldRecs))
								self.cursor.execute("Update PublishXRef set PublicationId = %d where InbredSetId=%d and PhenotypeId=%d and PublicationId=%d and Sequence=%d" % (maxId, PInbredSetId, PhenotypeId, PublicationId, Sequence))
								PublicationId = maxId
								pass
							else:
								pass
						continue
					else:
						pass

					if itemvalue:						
						PublicationItemUpdate.append('%s=%%s' % item)
						PublicationItemValues.append(itemvalue)

				if PhenotypeItemUpdate:
                                        updateStr= string.join(PhenotypeItemUpdate,',')
                                        query = "Update Phenotype set %s where Id = %s" % (updateStr, PhenotypeId)
                                        self.cursor.execute(query,tuple(PhenotypeItemValues))

				if PublicationItemUpdate:
					updateStr= string.join(PublicationItemUpdate,',')
					query = "Update Publication set %s where Id = %s" % (updateStr, PublicationId)
					self.cursor.execute(query,tuple(PublicationItemValues))

			else: #ProbeSet or Genotype Data
				itemValues = []
	                        itemUpdate = []

				for item in modifyField:
					itemvalue = self.formdata.getvalue(item)
					if itemvalue != None:
						itemvalue = string.strip(itemvalue)
					else:
						pass
					if item == 'homologeneid':
						updateHomologeneid = True
						new_homologeneid = 0

						if itemvalue and len(itemvalue) > 0:
							try:
								new_homologeneid = int(itemvalue)
							except:
								heading = "Record Updating Result"
								detail = ["Can't update database. Homologeneid must be integer!"]
								self.error(heading=heading,detail=detail,error="Error")
								return
					else:
						itemUpdate.append('%s=%%s' % item) #XZ: Use %% to put a % in the output string
						itemValues.append(itemvalue)

				if itemUpdate:
					updateStr= string.join(itemUpdate,', ')
					comments = "%s modified %s at %s\n" % (self.userName, string.join(comments, ', '), ctime)
					if thisTrait.db.type == "ProbeSet":#XZ, June 29, 2010: The algorithm is not good. Need to fix it later.
					 	if thisTrait.chipid in (2,4):
					 		if thisTrait.name[-2:] == '_A':
								thisTrait.name = string.replace(thisTrait.name, '_A', '')
					 		elif thisTrait.name[-2:] == '_B':
								thisTrait.name = string.replace(thisTrait.name, '_B', '')
							else:
								pass
							query = "Update %s set %s where Name like '%s%%%%'" % (thisTrait.db.type,updateStr,thisTrait.name)
							self.cursor.execute(query,tuple(itemValues))
							self.cursor.execute("Update %s set comments = CONCAT(comments,'%s') where Name like '%s%%%%'" % (thisTrait.db.type, comments, thisTrait.name))
						elif thisTrait.sequence:
							query = "Update %s set %s where BlatSeq='%s'" % (thisTrait.db.type,updateStr,thisTrait.sequence)
							self.cursor.execute(query,tuple(itemValues))
							self.cursor.execute("Update %s set comments = CONCAT(comments,'%s') where BlatSeq='%s'" % (thisTrait.db.type, comments, thisTrait.sequence))
						else:
							query = "Update %s set %s where Name='%s'" % (thisTrait.db.type,updateStr,thisTrait.name)
							self.cursor.execute(query,tuple(itemValues))
							self.cursor.execute("Update %s set comments = CONCAT(comments,'%s') where Name='%s'" % (thisTrait.db.type, comments, thisTrait.name))
					else: #XZ: Genotype
						query = "Update %s set %s where SpeciesId=%s and Name='%s'" % (thisTrait.db.type,updateStr, webqtlDatabaseFunction.retrieveSpeciesId(self.cursor, thisTrait.db.riset), thisTrait.name)
						self.cursor.execute(query,tuple(itemValues))

				if updateHomologeneid: #XZ: to update homologene id must be after updating geneid.
				#XZ: In one species, one homologeneid can have multiple geneid. One geneid only can have one homologeneid.
				#XZ: In Homologene table, GeneId is unique.
                                #XZ: Geneid might just being updated.
                                        thisTrait = webqtlTrait(fullname=self.formdata.getvalue('fullname'), cursor=self.cursor)
                                        thisTrait.retrieveInfo()

					if not thisTrait.geneid:
                                        	heading = "Record Updating Result"
						detail = ["There is no geneid associated with this trait. Can't update homologeneid info"]
						self.error(heading=heading,detail=detail,error="Error")
						return
					else:
						query = """
							SELECT Species.TaxonomyId
							FROM Species, InbredSet
							WHERE InbredSet.Name = '%s' and InbredSet.SpeciesId = Species.Id
							""" % thisTrait.db.riset
						self.cursor.execute(query)
	                                        taxonomyId = self.cursor.fetchone()[0]

						if not new_homologeneid:
							query = """DELETE FROM Homologene WHERE GeneId=%s""" % thisTrait.geneid
                                                        self.cursor.execute(query)
						else:
							query = """SELECT GeneId FROM Homologene WHERE GeneId=%s""" % thisTrait.geneid
							self.cursor.execute(query)
							result = self.cursor.fetchone()

							if not result:
	                                                        query = """INSERT into Homologene (HomologeneId, GeneId, TaxonomyId) VALUES (%s, %s, %s)""" % (new_homologeneid, thisTrait.geneid, taxonomyId)
        	                                                self.cursor.execute(query)
							else:
								query = """UPDATE Homologene SET HomologeneId=%s WHERE GeneId=%s""" % (new_homologeneid, thisTrait.geneid)
								self.cursor.execute(query)


                                #XZ: It's critical to get lasted info first, then update gene level info across traits by geneid.
				#XZ: Need to build index on GeneId. Otherwise, it's too slow.
                                if thisTrait.db.type == 'ProbeSet':
                                        thisTrait = webqtlTrait(fullname=self.formdata.getvalue('fullname'), cursor=self.cursor)
                                        thisTrait.retrieveInfo()

					if thisTrait.geneid:
						if 'symbol' in modifyField:
							if thisTrait.symbol:
								query = """UPDATE ProbeSet SET Symbol='%s' WHERE GeneId=%s""" % (thisTrait.symbol, thisTrait.geneid)
							else:
                        	                                query = """UPDATE ProbeSet SET Symbol=NULL WHERE GeneId=%s""" % (thisTrait.geneid)
							self.cursor.execute(query)

						if 'alias' in modifyField:
							if thisTrait.alias:
								query = """UPDATE ProbeSet SET alias='%s' WHERE GeneId=%s""" % (thisTrait.alias, thisTrait.geneid)
							else:
								query = """UPDATE ProbeSet SET alias=NULL WHERE GeneId=%s""" % (thisTrait.geneid)
							self.cursor.execute(query)

						if 'description' in modifyField:
							if thisTrait.description: #XZ: Attention, we must use "%s" instead of '%s'. Otherwise, to insert 3'UTR will generate error.
								query = """UPDATE ProbeSet SET description="%s" WHERE GeneId=%s""" % (thisTrait.description, thisTrait.geneid)
							else:
								query = """UPDATE ProbeSet SET description=NULL WHERE GeneId=%s""" % (thisTrait.geneid)
							self.cursor.execute(query)

						if 'strand_gene' in modifyField:
							if thisTrait.strand_gene:
								query = """UPDATE ProbeSet SET Strand_Gene='%s' WHERE GeneId=%s""" % (thisTrait.strand_gene, thisTrait.geneid)
							else:
								query = """UPDATE ProbeSet SET Strand_Gene=NULL WHERE GeneId=%s""" % (thisTrait.geneid)
							self.cursor.execute(query)

						if 'unigeneid' in modifyField:
							if thisTrait.unigeneid:
								query = """UPDATE ProbeSet SET UniGeneId='%s' WHERE GeneId=%s""" % (thisTrait.unigeneid, thisTrait.geneid)
							else:
								query = """UPDATE ProbeSet SET UniGeneId=NULL WHERE GeneId=%s""" % (thisTrait.geneid)
							self.cursor.execute(query)

						if 'refseq_transcriptid' in modifyField:
							if thisTrait.refseq_transcriptid:
								query = """UPDATE ProbeSet SET RefSeq_TranscriptId='%s' WHERE GeneId=%s""" % (thisTrait.refseq_transcriptid, thisTrait.geneid)
							else:
								query = """UPDATE ProbeSet SET RefSeq_TranscriptId=NULL WHERE GeneId=%s""" % (thisTrait.geneid)
							self.cursor.execute(query)

						if 'genbankid' in modifyField:
							if thisTrait.genbankid:
								query = """UPDATE ProbeSet SET GenbankId='%s' WHERE GeneId=%s""" % (thisTrait.genbankid, thisTrait.geneid)
							else:
								query = """UPDATE ProbeSet SET GenbankId=NULL WHERE GeneId=%s""" % (thisTrait.geneid)
							self.cursor.execute(query)

						if 'omim' in modifyField:
							if thisTrait.omim:
								query = """UPDATE ProbeSet SET OMIM='%s' WHERE GeneId=%s""" % (thisTrait.omim, thisTrait.geneid)
							else:
								query = """UPDATE ProbeSet SET OMIM=NULL WHERE GeneId=%s""" % (thisTrait.geneid)
							self.cursor.execute(query)


		###Modify Trait Data
		if thisTrait.db.type == 'Publish' and dataID > 0 and fd.formdata.getvalue("modifiedDataField"):
			StrainIds = []
			for item in fd.strainlist:
				self.cursor.execute('SelecT Id from Strain where Name = "%s"' % item)
				StrainId = self.cursor.fetchone()
				if not StrainId:
					raise ValueError
				else:
					StrainIds.append(StrainId[0])
			comments.append('Trait Value')
			#XZ, 03/05/2009: Xiaodong changed Data to PublishData, SE to PublishSE
			self.cursor.execute('delete from PublishData where Id = %d' % dataID)
			self.cursor.execute('delete from PublishSE where DataId = %d' % dataID)
			self.cursor.execute('delete from NStrain where DataId = %d' % dataID)
				
			for i, strain in enumerate(fd.strainlist):
				sId = StrainIds[i]
				if fd.allTraitData.has_key(strain):
					tdata = fd.allTraitData[strain]
					_val, _var, _N = tdata.val, tdata.var, tdata.N
					if _val != None:
						#XZ, 03/05/2009: Xiaodong changed Data to PublishData, SE to PublishSE
						self.cursor.execute('insert into PublishData values(%d, %d, %s)' % (dataID, sId, _val))
					if _var != None:
						self.cursor.execute('insert into PublishSE values(%d, %d, %s)' % (dataID, sId, _var))
					if _N != None:
						self.cursor.execute('insert into NStrain values(%d, %d, %s)' % (dataID, sId, _N))
				else:
					pass
			#end for
		else:
			pass
		TD_LR = HT.TD(valign="top", bgcolor="#eeeeee",height=200,width="100%")
		main_title = HT.Paragraph(" Record Updating Result", Class="title")

		TD_LR.append(main_title,HT.Blockquote('Successfully updated record %s in database ' % thisTrait.name, thisTrait.db.genHTML(), '.'))
		if thisTrait.db.type == 'Publish':
			comments = "%s modified %s at %s\n" % (self.userName, string.join(comments, ', '), ctime)
			self.cursor.execute("Update PublishXRef set comments = CONCAT(comments,'%s') where InbredSetId=%d and PhenotypeId=%d and PublicationId=%d and Sequence=%d" % (comments,  PInbredSetId, PhenotypeId, PublicationId, Sequence))
			
		if 0:
			heading = "Record Updating Result"
			detail = ["Can't update database. The server may be down at this time or you don't have the permission"]
			self.error(heading=heading,detail=detail,error="Error")
			return
		self.dict['body'] = str(TD_LR)

