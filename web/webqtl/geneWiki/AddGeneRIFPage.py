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

#geneWikiPage.py
#
#This one's pretty self-evident from the title. If you use the GeneWiki module, this is what's behind it. -KA

# Xiaodong changed the dependancy structure

import glob
import re
import piddle as pid
from htmlgen import HTMLgen2 as HT
import os
import string

from utility import Plot
from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil

#########################################
#      Gene Wiki Page
#########################################

class AddGeneRIFPage(templatePage):

	fields = ['species', 'pubmedid', 'weburl', 'comment', 'email', 'initial', 'genecategory']
	spliter = "__split__"

	def __init__(self, fd):

		templatePage.__init__(self, fd)
		
		if not self.updMysql():
			return

		if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:
			self.privilege_to_delete_entry = 1
			self.additional_colspan = 1
		else:
			self.privilege_to_delete_entry = 0
			self.additional_colspan = 0

		#read input fields
		self.action = fd.formdata.getvalue("action", "disp").strip()
		self.symbol = fd.formdata.getvalue("symbol", "").strip()
		self.Id = fd.formdata.getvalue("Id")
		self.comment = fd.formdata.getvalue("comment", "").strip()
		self.email = fd.formdata.getvalue("email", "").strip()
		self.pubmedid = fd.formdata.getvalue("pubmedid", "").strip()
		self.species = fd.formdata.getvalue("species", "no specific species:0").strip()
		self.genecategory = fd.formdata.getvalue("genecategory")
		self.initial = fd.formdata.getvalue("initial", "").strip()
		self.weburl = fd.formdata.getvalue("weburl", "").strip()
		self.reason = fd.formdata.getvalue("reason", "").strip()
		
		#self.dict['title'] = 'Add GeneWiki Entries for %s' % self.symbol
		
		if not self.symbol:
			self.content_type = 'text/html'
			Heading = HT.Paragraph("GeneWiki Entries", Class="title")
			help1 = HT.Href(url="/GeneWikihelp.html", text=" help document", Class="fwn", target="_blank")
			Intro = HT.Blockquote("GeneWiki enables you to enrich the annotation of genes and transcripts. Please submit or edit a GeneWiki note (500 characters max) related to a gene, its transcripts, or proteins. When possible include PubMed identifiers or web resource links (URL addresses). Please ensure that the additions will have widespread use. For additional information, check the GeneWiki ", help1,  ".")
		
			Intro.append(HT.P(), "Please enter a gene symbol in the box below and then click submit.")
			form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='addgenerif',submit=HT.Input(type='hidden'))
			form.append(HT.Input(type="text", size = 45, maxlength=100, name="symbol"))	
			form.append(HT.Input(type="hidden", name="FormID", value="geneWiki"))
			form.append(HT.Input(type="submit", name="submit", value="submit", Class="button"))
			TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee',valign="top")
			TD_LR.append(Heading,Intro,HT.Center(form))
			self.dict['body'] = str(TD_LR)
			self.dict['title'] = "Gene Wiki"
		elif self.action == 'disp':
			self.content_type = 'text/html'
			self.dispWikiPage(fd)
		elif self.action in ('add', 'update'):
			if self.action == 'update':
				self.cursor.execute("Select Id from GeneRIF where symbol='%s' and Id = %s and versionId=0" % (self.symbol, self.Id))
				if not self.cursor.fetchall():
					print 'Content-type: text/html\n'
					heading = "Update Entry"
					detail = ["The Entry cannot be located."]
					self.error(heading=heading,detail=detail,error="Error")
					self.write()
					return
				else:
					pass
			else:
				pass
			status = fd.formdata.getvalue('curStatus')
			if status == 'insertResult':
				i = self.insertResultPage(fd)
				if i == 0:
					self.content_type = 'text/html'
					self.insertUpdateCheck(fd, "You entered wrong password, Please try again")
				elif i == 2:
					#prevent re-submit
					url = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + "?FormID=geneWiki&symbol=%s" % self.symbol
					self.redirection = url
					return
				else:
					self.content_type = 'text/html'
					pass
			elif status == 'insertCheck':
				self.content_type = 'text/html'
				self.insertUpdateCheck(fd)
			else:
				self.content_type = 'text/html'
				self.insertUpdateForm(fd)
		elif self.action == 'del':
			if self.Id:
				try:
					self.Id= int(self.Id)
					self.delRIF()
				except:
					pass
			self.redirection = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + "?FormID=geneWiki&symbol=%s" % self.symbol
			return
		elif self.action == 'history':
			self.content_type = 'text/html'
			self.cursor.execute("Select Id from GeneRIF where symbol='%s' and Id = %s and versionId=0" % (self.symbol, self.Id))
			if not self.cursor.fetchall():
				heading = "Update Entry"
				detail = ["The Entry cannot be located."]
				self.error(heading=heading,detail=detail,error="Error")
			else:
				pass
			self.historyPage(fd)
		else:
			self.content_type = 'text/html'
			pass
				
	def historyPage(self, fd):
		self.dict['title'] = "GeneWiki Entry History"
		title = HT.Paragraph(self.dict['title'], Class= "title")
		
		subtitle1 = HT.Blockquote("Most Recent Version:",  Class="subtitle")
		self.cursor.execute("select GeneRIF.Id, versionId, symbol, PubMed_ID, Species.Name, comment, createtime, weburl, reason from GeneRIF left Join Species on GeneRIF.SpeciesId = Species.Id Where GeneRIF.Id = %s and versionId = 0" % self.Id)
		results = self.cursor.fetchone()
		subtitle1.append(HT.Blockquote(self.genTable(results)))
		
		subtitle2 = HT.Blockquote("Previous Version:",  Class="subtitle")
		self.cursor.execute("select GeneRIF.Id, versionId, symbol, PubMed_ID, Species.Name, comment, createtime, weburl, reason from GeneRIF Left Join Species on GeneRIF.SpeciesId = Species.Id Where GeneRIF.Id = %s and versionId > 0 order by versionId desc" % self.Id)
		results = self.cursor.fetchall()
		if results:
			for item in results:
				subtitle2.append(HT.Blockquote(self.genTable(item), HT.P()))
		else:
			subtitle2.append(HT.Blockquote("No Previous History"))
			
		TD_LR = HT.TD(valign="top", bgcolor="#eeeeee")
		
		TD_LR.append(title, subtitle1, subtitle2)
		self.dict['body'] = TD_LR
	
	def genTable(self, results):
		if not results:
			return ""
		Id, versionId, symbol, PubMed_ID, Species_Name, comment, createtime, weburl, reason = results
		if not Species_Name:
			Species_Name="no specific species"
		tbl = HT.TableLite(border=0, cellpadding=5, Class="collap ffv")
		
		tbl.append(HT.TR(
			HT.TD("Gene Symbol: ", width = 200, Class="fs13 fwb b1 c222"), 
			HT.TD(self.symbol, width = 600, Class="fs13 b1 c222"),
		))
		
		tbl.append(HT.TR(
			HT.TD("Species: ", width = 200, Class="fs13 fwb b1 c222"), 
			HT.TD(Species_Name, width = 600, Class="fs13 b1 c222")
		))
		if PubMed_ID:
			PubMed_ID = PubMed_ID.split()
			pTD = HT.TD(Class="fs13 b1 c222")
			for item in PubMed_ID:
				pTD.append(HT.Href(text=item, target = "_blank", 
						url = webqtlConfig.PUBMEDLINK_URL % item, Class="fwn"), " ")
			tbl.append(HT.TR(
				HT.TD("PubMed IDs: ", Class="fs13 fwb b1 c222"), 
				pTD
			))
			
		if weburl:
			tbl.append(HT.TR(
				HT.TD("Web URL: ", Class="fs13 fwb b1 c222"), 
				HT.TD(HT.Href(text=weburl, url=weburl, Class='fwn'), Class="fs13 b1 c222")
			))
		
		tbl.append(HT.TR(
			HT.TD("Entry: ", Class="fs13 fwb b1 c222"), 
			HT.TD(comment, Class="fs13 b1 c222")
		))
		
		self.cursor.execute("select GeneCategory.Name from GeneCategory, GeneRIFXRef where GeneRIFXRef.GeneRIFId = %s and GeneRIFXRef.versionId=%s and GeneRIFXRef.GeneCategoryId = GeneCategory.Id" % (Id, versionId))
		results = self.cursor.fetchall()
		if results:
			tHD = HT.TD(Class="fs13 b1 c222")
			for i, item in enumerate(results):
				tHD.append(item[0])
				if i < len(results)-1:
					tHD.append("; ")
				if i%2 == 1:
					tHD.append(HT.BR())
				
			tbl.append(HT.TR(
				HT.TD("Category: ", Class="fs13 fwb b1 c222"), 
				tHD
			))
		
		tbl.append(HT.TR(
			HT.TD("Add Time: ", Class="fs13 fwb b1 c222"), 
			HT.TD(createtime, Class="fs13 b1 c222")
		))
		if reason:
			tbl.append(HT.TR(
				HT.TD("Reason for Modification: ", Class="fs13 fwb b1 c222"), 
				HT.TD(reason, Class="fs13 b1 c222")
			))
		return tbl
	
	def insertUpdateCheck(self, fd, warning= ""):
		self.dict['title'] = "%s GeneWiki Entry for %s" % (self.action.title(), self.symbol)
		#mailsrch = re.compile('([\w\-][\w\-\.]*@[\w\-][\w\-\.]+[a-zA-Z]{1,4})([\s,;])*')
		mailsrch = re.compile('([\w\-][\w\-\.]*)@([\w\-\.]+)\.([a-zA-Z]{1,4})([\s,;])*')
		httpsrch = re.compile('((?:http|ftp|gopher|file)://(?:[^ \n\r<\)]+))([\s,;])*')
		if not self.comment or not self.email:
			heading = self.dict['title']
			detail = ["Please don't leave text field or email field empty."]
			self.error(heading=heading,detail=detail,error="Error")
			return
		if self.action == 'update' and not self.reason:
			heading = self.dict['title']
			detail = ["Please submit your reason for this modification."]
			self.error(heading=heading,detail=detail,error="Error")
			return
		if len(self.comment) >500:
			heading = self.dict['title']
			detail = ["Your entry is more than 500 characters."]
			self.error(heading=heading,detail=detail,error="Error")
			return
		if self.email and re.sub(mailsrch, "", self.email) != "":
			heading = self.dict['title']
			detail = ["The format of your email address is incorrect."]
			self.error(heading=heading,detail=detail,error="Error")
			return
		
		if self.weburl == "http://":
			self.weburl = ""
		
		if self.weburl and re.sub(httpsrch, "", self.weburl) != "":
			heading = self.dict['title']
			detail = ["The format of web resource link is incorrect."]
			self.error(heading=heading,detail=detail,error="Error")
			return
		
		if self.pubmedid:
			try:
				test = map(int, string.split(self.pubmedid))
			except:
				heading = self.dict['title']
				detail = ["PubMed IDs can only be integers."]
				self.error(heading=heading,detail=detail,error="Error")
				return
		
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='addgenerif',submit=HT.Input(type='hidden'))
		recordInfoTable = HT.TableLite(border=0, cellspacing=1, cellpadding=5,align="center")
		
		addButton = HT.Input(type='submit',name='submit', value='%s GeneWiki Entry' % self.action.title(),Class="button")
		hddn = {'curStatus':'insertResult', 'FormID':'geneWiki', 'symbol':self.symbol, 
			'comment':self.comment, 'email':self.email, 'species':self.species, 
			'action':self.action, 'reason':self.reason}
		if self.Id:
			hddn['Id']=self.Id
		
		formBody = HT.TableLite()
		
		formBody.append(HT.TR(
			HT.TD(HT.Strong("Species: ")), 
			HT.TD(width=10), 
			HT.TD(string.split(self.species, ":")[0])
		))
		if self.pubmedid:
			try:
				formBody.append(HT.TR(
					HT.TD(HT.Strong("PubMed IDs: ")), 
					HT.TD(width=10), 
					HT.TD(self.pubmedid)
				))
				hddn['pubmedid'] = self.pubmedid
			except:
				pass
		if self.weburl:
			try:
				formBody.append(HT.TR(
					HT.TD(HT.Strong("Web URL: ")), 
					HT.TD(width=10), 
					HT.TD(HT.Href(text=self.weburl, url=self.weburl, Class='fwn'))
				))
				hddn['weburl'] = self.weburl
			except:
				pass
		formBody.append(HT.TR(
			HT.TD(HT.Strong("Gene Notes: ")), 
			HT.TD(width=10), 
			HT.TD(self.comment)
		))
		formBody.append(HT.TR(
			HT.TD(HT.Strong("Email: ")), 
			HT.TD(width=10), 
			HT.TD(self.email)
		))
		if self.initial:
			formBody.append(HT.TR(
				HT.TD(HT.Strong("Initial: ")), 
				HT.TD(width=10), 
				HT.TD(self.initial)
			))
			hddn['initial'] = self.initial
		
		if self.genecategory:
			cTD = HT.TD()
			if type(self.genecategory) == type(""):
				self.genecategory = string.split(self.genecategory)
			self.cursor.execute("Select Id, Name from GeneCategory where Id in (%s) order by Name " % string.join(self.genecategory, ', '))
			results = self.cursor.fetchall()
			for item in results:
				cTD.append(item[1], HT.BR())
				
			formBody.append(HT.TR(
				HT.TD(HT.Strong("Category: ")), 
				HT.TD(width=10), 
				cTD
			))
			hddn['genecategory'] = string.join(self.genecategory, " ")
			
		formBody.append(HT.TR(
			HT.TD(
				HT.BR(), HT.BR(), 
				HT.Div("For security reasons, enter the code (case insensitive) in the image below to finalize your submission"), HT.BR(), 
				addButton, HT.Input(type="password", size = 25, name="password"), 
			colspan=3)
		))
		
		
		code = webqtlUtil.genRandStr(length=5, chars="abcdefghkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789")
		filename= webqtlUtil.genRandStr("Sec_")
		hddn['filename'] = filename 
		securityCanvas = pid.PILCanvas(size=(300,100))
		Plot.plotSecurity(securityCanvas, text=code)
		
		os.system("touch %s_.%s" % (os.path.join(webqtlConfig.IMGDIR,filename), code))
		securityCanvas.save(os.path.join(webqtlConfig.IMGDIR,filename), format='png')
		
		formBody.append(HT.TR(
			HT.TD(HT.Image("/image/"+filename+".png"), colspan=3)
		))
		
		hddn['filename'] = filename 
		TD_LR = HT.TD(valign="top", bgcolor="#eeeeee")
		title = HT.Paragraph("%s GeneWiki Entry for %s" % (self.action.title(), self.symbol), Class="title")
		
		form.append(HT.P(), HT.Blockquote(formBody))
		
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
			
		TD_LR.append(title, HT.Blockquote(warning, Id="red"), form)
		
		self.dict['body'] = TD_LR		
	
	def insertUpdateForm(self, fd):
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='addgenerif',submit=HT.Input(type='hidden'))
		addButton = HT.Input(type='submit',name='submit', value='%s GeneWiki Entry' % self.action.title(),Class="button")
		resetButton = HT.Input(type='reset',Class="button")
		
		hddn = {'curStatus':'insertCheck', 'FormID':'geneWiki', 'symbol':self.symbol, 'action':self.action, 'reason':self.reason}
		if self.Id:
			hddn['Id']=self.Id
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
		
		if self.action == 'update':
			self.cursor.execute("Select Species.Name, PubMed_ID, weburl, comment, email, initial from GeneRIF left JOIN Species on Species.Id = GeneRIF.SpeciesId where symbol='%s' and GeneRIF.Id = %s and versionId=0" % (self.symbol, self.Id))
			oldSpeciesId, oldPubMed_ID, oldweburl, oldcomment, oldemail, oldinitial = self.cursor.fetchone()
			if not oldSpeciesId:
				oldSpeciesId="no specific species:0"
			oldemail =  ""
			self.cursor.execute("Select GeneCategoryId from GeneRIFXRef where GeneRIFId = %s and versionId=0" % self.Id)
			oldCategory = self.cursor.fetchall()
			if oldCategory:
				oldCategory = map(lambda X:X[0], oldCategory)
		else:
			oldSpeciesId = oldPubMed_ID = oldcomment = oldemail = oldinitial = oldweburl = ""
			oldCategory= ()
		
		if not oldweburl:
			oldweburl = "http://"
		#############################
		TD_LR = HT.TD(valign="top", bgcolor="#eeeeee")
		title = HT.Paragraph("%s GeneWiki Entry for %s" % (self.action.title(), self.symbol), Class="title")
		
		smenu = HT.Select(name="species")
		self.cursor.execute("select Id, Name from Species order by Name")
		for Id, Name in self.cursor.fetchall():
			smenu.append((Name, "%s:%s" % (Name, Id)))
		smenu.append(("no specific species", "no specific species:0"))
		if oldSpeciesId != "":
			smenu.selected.append(oldSpeciesId)
		else:
			smenu.selected.append("mouse")
		formBody = HT.TableLite()
		
		if self.action == 'update':
			formBody.append(HT.TR(
				HT.TD("Reason for Modification: "), 
				HT.TD(width=10), 
				HT.TD(HT.Input(type="text", size = 45, maxlength=100, name="reason"))
			))
		else:
			pass
			
		formBody.append(HT.TR(
			HT.TD("Species: "), 
			HT.TD("&nbsp;", width=10), 
			HT.TD(smenu)
		))
		formBody.append(HT.TR(
			HT.TD("PubMed IDs: "), 
			HT.TD("&nbsp;", width=10), 
			HT.TD(HT.Input(type="text", size = 25, maxlength=25, name="pubmedid", value=oldPubMed_ID), " (optional, separate by blank space only)")
		))
		formBody.append(HT.TR(
			HT.TD("Web resource URL: "), 
			HT.TD("&nbsp;", width=10), 
			HT.TD(HT.Input(type="text", size = 50, maxlength=100, name="weburl", value=oldweburl), " (optional)")
		))
		formBody.append(HT.TR(
			HT.TD("Text: "), 
			HT.TD("&nbsp;", width=10), 
			HT.TD(HT.Textarea(cols = 60, rows=5, name="comment", text=oldcomment))
		))
		formBody.append(HT.TR(
			HT.TD("Email: "), 
			HT.TD("&nbsp;", width=10), 
			HT.TD(HT.Input(type="text", size = 40, maxlength=40, name="email", value=oldemail))
		))
		formBody.append(HT.TR(
			HT.TD("User Code: "), 
			HT.TD("&nbsp;", width=10), 
			HT.TD(HT.Input(type="text", size =15, maxlength=10, name="initial", value=oldinitial), " (optional user or project code or your initials)")
		))
		
		self.cursor.execute("Select Id, Name from GeneCategory order by Name")
		results = self.cursor.fetchall()
		if results:
			tbl2 = HT.TableLite()
			tempTR = HT.TR()
			for i, item in enumerate(results):
				if item[0] in oldCategory:
					boxchecked = 1
				else:
					boxchecked = 0
				tempTR.append(HT.TD(HT.Input(type='checkbox', Class='checkbox', name='genecategory', value = item[0], checked=boxchecked), valign="top"), HT.TD(" ", item[1], valign="top"))
				if (i%2):
					tbl2.append(tempTR)
					tempTR = HT.TR()
			tbl2.append(tempTR)
			formBody.append(HT.TR(
				HT.TD("Category of Gene Note", HT.BR(), "(Please select one or", HT.BR(), "many categories):"), 
				HT.TD("&nbsp;", width=10), 
				HT.TD(tbl2)
			))
		formBody.append(HT.TR(
			HT.TD(addButton, "&nbsp;"*10, resetButton, colspan=3)
		))
		
		form.append(HT.P(), HT.Blockquote(formBody))
		
		TD_LR.append(title, form)
		self.dict['title'] = "%s GeneWiki Entry for %s" % (self.action.title(), self.symbol)	
		self.dict['body'] = TD_LR
	
	def dispWikiPage(self, fd):
		addButton = HT.Input(type="button",value="New GeneWiki Entry",onClick= \
					 "openNewWin('%s')" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + "?FormID=geneWiki&action=add&symbol=%s" % self.symbol), 
					 Class="button")
		geneRIFBody = HT.TableLite(cellpadding=3, width="100%")
		geneRIFBody.append(HT.TR(HT.TD(HT.Paragraph("GeneWiki for %s: " % self.symbol, addButton, Class="subtitle"), colspan=5+self.additional_colspan, height=40)))

		self.cursor.execute("select comment, PubMed_ID, weburl, Id from GeneRIF where symbol = '%s' and display > 0 and versionId=0" % self.symbol)
		results = self.cursor.fetchall()
		geneRIFBody.append(HT.TR(HT.TD(), HT.TD("GeneNetwork:", colspan=4+self.additional_colspan, Class="fwb")))
		if results:
			for i, item in enumerate(results):
				PubMedLink = WebLink = comma = ""
				if item[1]:
					PubMedLink = HT.Href(text="PubMed", target = "_blank", 
						url = webqtlConfig.PUBMEDLINK_URL % item[1], Class="fwn")
				if item[2]:
					if PubMedLink: comma = ", "
					WebLink = HT.Href(text="URL Link", target = "_blank", 
						url = item[2], Class="fwn")
				myTR = HT.TR(
					HT.TD("&nbsp", width=20),
					HT.TD(HT.Strong(i+1, ". "), valign="top"),
					HT.TD(HT.Paragraph(item[0], " ", PubMedLink, comma, WebLink), valign="top"),
					#HT.TD(, width=40, valign="top"),
					HT.TD(
						HT.Href(url=os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE)+ \
						"?FormID=geneWiki&action=update&Id=%d&symbol=%s" %(item[-1], self.symbol),
						onClick = "return confirm('Any user can edit any GeneWiki entry, with changes showing up immediately. The history of previous versions of this entry are stored and available for reference. Click OK to continue.');" ,
						text=HT.Image("/images/modify.gif", border=0), title="Modify Entry", Class="fwn")
						, width=20, valign="top"
					),
					HT.TD(
						HT.Href(url=os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE)+ \
						"?FormID=geneWiki&action=history&Id=%d&symbol=%s" %(item[-1], self.symbol),
						text=HT.Image("/images/history.gif", border=0), title="History of Entry", Class="fwn")
						, width=20, valign="top"
					)
				)
				if self.privilege_to_delete_entry:
					myTR.append(HT.TD(
						HT.Href(url=os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE)+ \
						"?FormID=geneWiki&action=del&Id=%d&symbol=%s" %(item[-1], self.symbol),
						onClick = "return confirm('Do you really want to delete this entry, click YES to continue.');" ,
						text=HT.Image("/images/trash.gif", border=0), title="Delete Entry", Class="fwn")
						, width=20, valign="top"
					))
				geneRIFBody.append(myTR)
		else:
			geneRIFBody.append(HT.TR(
					HT.TD("&nbsp", width=20),
					HT.TD(HT.U("There is no GeneWiki entry for this gene."), colspan=5+self.additional_colspan),
				))
				
		self.cursor.execute("select distinct Species.FullName, GeneRIF_BASIC.GeneId, GeneRIF_BASIC.comment, GeneRIF_BASIC.PubMed_ID from GeneRIF_BASIC, Species where GeneRIF_BASIC.symbol='%s' and GeneRIF_BASIC.SpeciesId = Species.Id order by Species.Id, GeneRIF_BASIC.createtime" % self.symbol)
		results = self.cursor.fetchall()
		if results:
			geneRIFBody.append(HT.TR(HT.TD(), HT.TD("GeneRIF from NCBI:", colspan=4+self.additional_colspan, Class="fwb")))
			for i, item in enumerate(results):
				PubMedLink = HT.Href(text="PubMed", target = "_blank", 
						url = webqtlConfig.PUBMEDLINK_URL % item[3], Class="fwn")
				GeneLink = HT.Href(text= item[0], target='_blank',\
						url=webqtlConfig.NCBI_LOCUSID % item[1], Class="fwn")
				myTR = HT.TR(
					HT.TD("&nbsp", width=20),
					HT.TD(HT.Strong(i+1, ". "), valign="top"),
					HT.TD(HT.Paragraph(item[2], " (", GeneLink,") ", PubMedLink), valign="top", colspan=3+self.additional_colspan))
				geneRIFBody.append(myTR)
				
		TD_LR = HT.TD(valign="top", bgcolor="#eeeeee")
		help1 = HT.Href(url="/GeneWikihelp.html", text=" help document", Class="fwn", target="_blank")
		title = HT.Paragraph("GeneWiki Entries", Class="title")
		intro = HT.Blockquote("GeneWiki enables you to enrich the annotation of genes and transcripts. Please submit or edit a GeneWiki note (500 characters max) related to a gene, its transcripts, or proteins. When possible include PubMed identifiers or web resource links (URL addresses). Please ensure that the additions will have widespread use. For additional information, check the GeneWiki ", help1,  ".")
		
		TD_LR.append(title, intro, HT.Blockquote(geneRIFBody))
		self.dict['title'] = "GeneWiki for %s" % self.symbol
		self.dict['body'] = TD_LR
			
			
	def delRIF(self):
		if self.privilege_to_delete_entry:
			self.cursor.execute("update GeneRIF set display= 0 where Id = %d" % self.Id)
		
	def insertResultPage(self, fd):
		try:
			password = fd.formdata.getvalue("password", "")
			filename = fd.formdata.getvalue("filename")
			code = glob.glob(os.path.join(webqtlConfig.IMGDIR,filename+"_.*"))
			code = string.split(code[0], '.')[-1]
			if string.lower(code) != string.lower(password):
				return 0 
			TD_LR = HT.TD(valign="top", bgcolor="#eeeeee")
			title = HT.Paragraph("Add GeneWiki Entry", Class="title")
			self.cursor.execute("Select max(Id) from GeneRIF")
			if self.action == 'update':
				#old record
				maxId = int(self.Id)
				self.cursor.execute("select max(versionId)+1 from GeneRIF where Id=%s" % maxId)
				newversionId = self.cursor.fetchone()[0]
				self.cursor.execute("update GeneRIF set versionId = %d where Id=%d and versionId = 0" % (newversionId, maxId))
				self.cursor.execute("update GeneRIFXRef set versionId = %d where GeneRIFId=%d and versionId = 0" % (newversionId, maxId))
			else:
				#new record
				try:
					maxId = self.cursor.fetchone()[0] +1
				except:
					maxId = 1
			
			for item in self.fields:
				if not getattr(self, item):
					setattr(self, item, None)
			self.cursor.execute("""insert into GeneRIF (id, symbol, PubMed_ID, SpeciesId, comment, email, createtime, user_ip, display, weburl, initial, reason)
				values (%s, %s, %s, %s, %s, %s, Now(), %s, 1, %s, %s, %s)""", 
				(maxId, self.symbol, self.pubmedid, string.split(self.species, ":")[-1], self.comment, 
				self.email, fd.remote_ip, self.weburl, self.initial, self.reason))
			if self.genecategory:
				Ids = string.split(self.genecategory)
				for item in Ids:
					self.cursor.execute("insert into GeneRIFXRef(GeneRIFId, GeneCategoryId) values(%s, %s)" % (maxId, item)) 
			return 2
		except:
			heading = self.dict['title']
			detail = ["Error occurred while adding your Gene RIFs."]
			self.error(heading=heading,detail=detail,error="Error")
			return 1
			
		
