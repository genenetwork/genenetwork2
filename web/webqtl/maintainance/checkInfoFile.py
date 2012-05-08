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
# Last updated by NL 2011/01/28

# created by Ning Liu 2011/01/27
# This script is to check whether dataset related Info file exist or not; if not, the tempate Info file will be generated
# This script should be only run at GeneNetwork production server

import sys, os
import MySQLdb

current_file_name = __file__
pathname = os.path.dirname( current_file_name )
abs_path = os.path.abspath(pathname)
sys.path.insert(0, abs_path + '/..')

from base import template
from base import webqtlConfig
from base import header
from base import footer

# build MySql database connection
con = MySQLdb.Connect(db=webqtlConfig.DB_NAME,host=webqtlConfig.MYSQL_SERVER, user=webqtlConfig.DB_USER,passwd=webqtlConfig.DB_PASSWD)
cursor = con.cursor()

InfoFilePath =webqtlConfig.HTMLPATH+'dbdoc/'
		
# create template for Info file
def createTemplateForInfoFile(datasetId=None,datasetFullName=None,InfoFileURL=None):
	#template.py has been changed with dynamic header and footer
	userInfo=""
	headerInfo=header.header_string % userInfo
	serverInfo=""
	footerInfo=footer.footer_string % serverInfo
	
	title =datasetFullName
	contentTitle = '''
	<P class="title">%s<A HREF="/webqtl/main.py?FormID=editHtml"><img src="/images/modify.gif" alt="modify this page" border= 0 valign="middle"></A><BR><BR>
	''' % datasetFullName	
	content ='''
	Accession number: <A HREF="/webqtl/main.py?FormID=sharinginfo&GN_AccessionId=%s">GN%s</A></P>
	<br><br>
	This page will be updated soon. 
	<br><br>
	''' % (datasetId,datasetId)	
	
	body=contentTitle+content
	# Note: 'templateParameters' includes parameters required for template.py
	# templateParameters = ['title','basehref','js1','js2','layer','header','body', 'footer']
	templateParameters =[title,'','','','',headerInfo,body,footerInfo]
	
	# build template file
	templateFile=template.template % tuple(templateParameters)		
	InfoFileHandler = open(InfoFileURL, 'w')
	# write template file into Info .html file
	InfoFileHandler.write(templateFile)
	InfoFileHandler.close()
	
	
# select all ProbeSet names from datatable 'ProbeSetFreeze'
cursor.execute("select Id, Name, FullName from  ProbeSetFreeze ")		
results = cursor.fetchall()
for item in results:
	datasetId = item[0]
	datasetName =item[1]
	datasetFullName =item[2]
	InfoFileURL = InfoFilePath+datasetName+".html"
	# check Info html file exist or not
	if not os.path.exists(InfoFileURL):
		createTemplateForInfoFile(datasetId=datasetId,datasetFullName=datasetFullName,InfoFileURL=InfoFileURL)

		







 
