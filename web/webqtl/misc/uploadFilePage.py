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

import os
import string

from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil

#########################################
#      Upload File Page 
#########################################

class uploadFilePage(templatePage):

	uploadPath = webqtlConfig.UPLOADPATH

	def __init__(self, fd, formdata, cookies):

		templatePage.__init__(self, fd)

		if not self.openMysql():
			return

                if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:
                        pass
                else:
                        heading = "Upload File"
                        detail = ["You don't have the permission to upload file to the server."]
                        self.error(heading=heading,detail=detail)
                        return
		
		self.cursor.close()

		file1 = self.save_uploaded_file (formdata, 'imgName1')
		file2 = self.save_uploaded_file (formdata, 'imgName2')
		file3 = self.save_uploaded_file (formdata, 'imgName3')
		file4 = self.save_uploaded_file (formdata, 'imgName4')
		file5 = self.save_uploaded_file (formdata, 'imgName5')
		
		i = 0
		uploaded = []

		for filename in (file1, file2, file3, file4, file5):
			if filename: 
				i += 1
				uploaded.append(filename)
				
		if i == 0:
			heading = "Upload File"
			detail = ["No file was selected, no file uploaded."]
			self.error(heading=heading,detail=detail)
			return
		else:
			TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

			imgTbl = HT.TableLite(border=0, width = "90%",cellspacing=2, cellpadding=2, align="Center")
			imgTbl.append(HT.TR(HT.TD("Thumbnail", width="%30", align='center',Class="colorBlue"), 
					HT.TD("URL", width="%60",Class="colorBlue", align='center')))
			for item in uploaded:
				img = HT.Image("/images/upload/" + item, border = 0, width=80)

				#url = "%s/images/upload/" % webqtlConfig.PORTADDR + item
				#url = HT.Href(text=url, url = url, Class='normalsize', target="_blank")
				url2 = "/images/upload/" + item
				url2 = HT.Href(text=url2, url = url2, Class='normalsize', target="_blank")
				imgTbl.append(HT.TR(HT.TD(img, width="%30", align='center',Class="colorWhite"), 
					#HT.TD(url, HT.BR(), 'OR', HT.BR(), url2,  width="%60",Class="colorWhite", align='center')))
					HT.TD(url2,  width="%60",Class="colorWhite", align='center')))

			intro = HT.Paragraph('A total of %d files are uploaded' % i)
			TD_LR.append( HT.Center(intro) )

			TD_LR.append( imgTbl )
		
			self.dict['body'] = str(TD_LR)	
		
	def save_uploaded_file(self, form, form_field, upload_dir=""):
		if not upload_dir:
			upload_dir = self.uploadPath
		if not form.has_key(form_field):
			return None
		fileitem = form[form_field]
		
		if not fileitem.filename or not fileitem.file:
			return None
		
		seqs = [""] + range(200)
		try:
			newfileName =  string.split(fileitem.filename, ".")
			for seq in seqs:
				newfileName2 = newfileName[:]
				if seq != "":
					newfileName2[-2] = "%s-%s" % (newfileName2[-2], seq)
				fileExist = glob.glob(os.path.join(upload_dir, string.join(newfileName2, ".")))
				if not fileExist:
					break
		except:
			pass
		
		newfileName = string.join(newfileName2, ".")
		#print [newfileName, os.path.join(upload_dir, newfileName)]
		#return
		
		fout = file (os.path.join(upload_dir, newfileName), 'wb')
		while 1:
			chunk = fileitem.file.read(100000)
			if not chunk: break
			fout.write (chunk)
		fout.close()
		return newfileName
