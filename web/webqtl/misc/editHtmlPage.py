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
import urlparse

from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil


#########################################
#      Edit HTML Page
#########################################

class editHtmlPage(templatePage):
	htmlPath = webqtlConfig.ChangableHtmlPath

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		self.templateInclude = 1
		self.dict['title'] = "Editing HTML"

		if not self.updMysql():
			return

		if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:
			pass
		else:
			heading = "Editing HTML"
			detail = ["You don't have the permission to modify this file"]
			self.error(heading=heading,detail=detail,error="Error")
			return

		path = fd.formdata.getvalue('path')
		preview = fd.formdata.getvalue('preview')
		newHtmlCode = fd.formdata.getvalue('htmlSrc')
		if newHtmlCode:
			#newHtmlCode = string.replace(newHtmlCode, "&amp;image", "&image")
			newHtmlCode = string.replace(newHtmlCode,"&amp;", "&")
		if path and preview:
			#preview
			self.templateInclude = 0
			#print newHtmlCode
			self.debug = newHtmlCode
		elif path:
			#edit result
			fileName = self.htmlPath + path
			newfileName = fileName +'.old'
			os.system("/bin/cp -f %s %s" % (fileName, newfileName))
			fp = open(fileName, 'wb')
			fp.write(newHtmlCode)
			fp.close()
			#print "chown qyh %s" % fileName
			TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#eeeeee", height=200)
			mainTitle = HT.Paragraph("Edit HTML", Class="title")
			url = HT.Href(text = "page", url =path, Class = "normal")
			intro = HT.Blockquote("This ",url, " has been succesfully modified. ")
			TD_LR.append(mainTitle, intro)
			self.dict['body'] = TD_LR
		#elif os.environ.has_key('HTTP_REFERER'):
		elif fd.refURL:
			#retrieve file to be edited
			#refURL = os.environ['HTTP_REFERER']
			addressing_scheme, network_location, path, parameters, query, fragment_identifier = urlparse.urlparse(fd.refURL)
			if path[-1] == "/":
				path += 'index.html'
				
			fileName = self.htmlPath + path
			try:
				fp = open(fileName,'rb')
			except:
				fp = open(os.path.join(self.htmlPath, 'temp.html'),'rb')
			htmlCode = fp.read()
			#htmlCode = string.replace(htmlCode, "&nbsp","&amp;nbsp")
			htmlCode = string.replace(htmlCode, "&","&amp;")
			fp.close()
			form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='editHtml',submit=HT.Input(type='hidden'))
			inputBox = HT.Textarea(name='htmlSrc', cols="100", rows=30,text=htmlCode)
			
			hddn = {'FormID':'editHtml', 'path':path, 'preview':''}
			for key in hddn.keys():
				form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
			previewButton = HT.Input(type='button',name='previewhtml', value='Preview',Class="button", onClick= "editHTML(this.form, 'preview');")
			submitButton = HT.Input(type='button',name='submitchange', value='Submit Change',Class="button", onClick= "editHTML(this.form, 'submit');")
			resetButton = HT.Input(type='reset',Class="button")
			form.append(HT.Center(inputBox, HT.P(), previewButton, submitButton, resetButton))
			
			TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#eeeeee")
			mainTitle = HT.Paragraph("Edit HTML", Class="title")
			intro = HT.Blockquote("You may edit the HTML source code in the editbox below, or you can copy the content of the editbox to your favorite HTML editor. ")
			imgUpload = HT.Href(url="javascript:openNewWin('/upload.html', 'menubar=0,toolbar=0,location=0,resizable=0,status=1,scrollbars=1,height=400, width=600');", text="here", Class="fs14")
			intro2 = HT.Blockquote("Click ", imgUpload, " to upload Images. ")
			TD_LR.append(mainTitle, intro, intro2, HT.Center(form))
			self.dict['body'] = TD_LR
		else:
			heading = "Editing HTML"
			detail = ["Error occured while trying to edit the html file."]
			self.error(heading=heading,detail=detail,error="Error")
			return

