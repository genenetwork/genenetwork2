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

import sys
import string
import os
import MySQLdb
import cgi

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig


# XZ 08/14/2008: When I tried to replace 'from webqtlConfig import *' with 'import webqtlConfig'
# XZ 08/14/2008: I found some problems. I discussed with Hongqiang and the below is conclusion.
# XZ 08/14/2008: The program uses webqtlConfig.DB_NAME, webqtlConfig.MYSQL_SERVER and so on
# XZ 08/14/2008: without 'import webqtlConfig'. This program will not work.
# XZ 08/14/2008: CONFIG_htmlpath doesn't exist in webqtlConfig.py
# XZ 08/14/2008: Hongqian said this was done by Fan Zhang, and this program was not tested.
# XZ 08/14/2008: So nobody realize these bugs.

# XZ, 09/09/2008: This function is not called any where. 
# XZ, 09/09/2008: Actually, I don't think this function works.
def genHeaderFooter(i=1,title='',basehref='',js1='',js2='',layer='',body=''):
	"""
	generate footer and header HTML code
	default is header
	i = 0 is footer+header
	i = 1 is header
	i = 2 is footer	
	"""
	try:
                temp_file = CONFIG_htmlpath + 'beta-template.html'
		fp = open(temp_file, 'rb')
		template = fp.read()
		fp.close()
		template = template % (title,basehref,js1,js2,layer,body, "")
		header,footer = string.split(template,'<!-- split from Here -->')
		if i == 0:
			return header + footer
		elif i == 1:
			return header
		elif i == 2:
			return footer
		else:
			return ""
	except:
		if i == 0:
			return "header + footer"
		elif i == 1:
			return "header"
		elif i == 2:
			return "footer"
		else:
			return ""

# XZ, 09/09/2008: This function is only used in multitrait.py where it is called with value assigned to db.
# XZ, 09/09/2008: So the try-except block is not executed.
# XZ, 09/09/2008: This explains why no error was generated even without 'import webqtlConfig'
def genDatabaseMenu(db = None, public =1, RISetgp = 'BXD', selectname = 'database', selected = ""):
	"""
	generate database Menu
	public = 0 : search3.html databases Menu
	public = 1 : search.html databases Menu
	"""
	if not db:
		try:
			# import MySQLdb
			# con = MySQLdb.Connect(db='db_webqtl')
			# Modified by Fan Zhang
			con = MySQLdb.Connect(db=webqtlConfig.DB_NAME,host=webqtlConfig.MYSQL_SERVER, user=webqtlConfig.DB_USER,passwd=webqtlConfig.DB_PASSWD)
			db = con.cursor()
		except:
			return "Connect MySQL Server Error"
	else:
		pass
	
	databaseMenu = HT.Select(name=selectname)
	nmenu = 0

	# here's a hack: bxd and bxd300 can be correlated against each other
	# if either of those are the group, we put in special SQL that pulls both
	if RISetgp in ("BXD", "BXD300"):
		ibsNameQry = '(InbredSet.Name = "BXD" OR InbredSet.Name = "BXD300")'
	else:
		ibsNameQry = 'InbredSet.Name = "%s"' % RISetgp
	
	#Publish Database
	db.execute('''
		   SelecT
		     PublishFreeze.FullName,
		     PublishFreeze.Name
		   from
		     PublishFreeze,
		     InbredSet
		   where
		     PublishFreeze.InbredSetId = InbredSet.Id and
		     %s
		   ''' % ibsNameQry)
	for item in db.fetchall():
		databaseMenu.append(item)
		nmenu += 1
	
	#Genome Database
	db.execute('''
		   SelecT
		     GenoFreeze.FullName,
		     GenoFreeze.Name
		   from
		     GenoFreeze,InbredSet
		   where
		     GenoFreeze.InbredSetId = InbredSet.Id and
		     %s
		   ''' % ibsNameQry)
	for item in db.fetchall():
		databaseMenu.append(item)
		nmenu += 1
	
	#Microarray Database
	db.execute('SelecT Id, Name from Tissue')
	for item in db.fetchall():
		TId, TName = item
		databaseMenuSub = HT.Optgroup(label = '%s ------' % TName)
		db.execute('''
			   SelecT
			     ProbeSetFreeze.FullName,
			     ProbeSetFreeze.Name
			   from
			     ProbeSetFreeze,
			     ProbeFreeze,
			     InbredSet
			   where
			     ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
			     ProbeFreeze.TissueId = %d and
			     ProbeSetFreeze.public > %d and
			     ProbeFreeze.InbredSetId = InbredSet.Id and
			     %s
			   order by
			     ProbeSetFreeze.CreateTime desc,
			     ProbeSetFreeze.AvgId
			   '''  % (TId,public,ibsNameQry))
		for item2 in db.fetchall():
			databaseMenuSub.append(item2)
			nmenu += 1
		databaseMenu.append(databaseMenuSub)
	
	if nmenu:
		if selected:
			databaseMenu.selected.append(selected)
		return str(databaseMenu)
	else:
		return ''


# XZ, 09/09/2008: This function is not called any where. 
# XZ, 09/09/2008: Actually, I don't think this function works.
# XZ, 09/09/2008: There is no 'DataForm' file now. It should be webqtlForm.py
def genRISample():
	import glob
	import reaper
	import random
	import math
	import webqtlUtil
	risets = filter(lambda X:X.find('F2')<0, map(os.path.basename, glob.glob(os.path.join(CONFIG_genodir, "*.geno"))))
	risets = map(lambda X:X.split('.')[0], risets)
	risets.remove("BayXSha")
	risets.sort()
	body = HT.Blockquote()
	NPerRow = 6
	for item in risets:
		values = []
		if item == 'AXBXA': item2='AXB/BXA'
		elif item == 'HXBBXH': item2='HXB/BXH'
		else: item2=item
		body.append(HT.Paragraph(item2, Class='subtitle'))
		tbl = HT.TableLite(Class="collap")
		dataset = reaper.Dataset()
		dataset.read(os.path.join(CONFIG_genodir, "%s.geno"%item))
		prgy = webqtlUtil.ParInfo[item] + list(dataset.prgy)
		
		mean = random.random()*100
		variance = random.random()*500
		variables = []
		while len(variables) < len(prgy):
			S = 2
			while (S>=1):
				U1= random.random()
				U2= random.random()
				V1= 2*U1-1.0
				V2= 2*U2-1.0
				S=V1*V1+V2*V2
			X= math.sqrt(-2 *  math.log(S) / S) * V1
			Y= math.sqrt(-2 *  math.log(S) / S) * V2	
			variables.append(mean + math.sqrt(variance) * X)
			variables.append(mean + math.sqrt(variance) * Y) 
		
		tempTR = HT.TR()
		for i, strain in enumerate(prgy):
			if i and i%NPerRow==0:
				tbl.append(tempTR)
				tempTR = HT.TR()
			if random.random() < 0.2:
				variable = 'X'
			else:
				variable = "%2.3f" % variables[i]
			
			tempTR.append(HT.TD(strain, Class="strains", width=80))
			tempTR.append(HT.TD(variable, Class="values", width=60))
			values.append(variable)
		
		for j in range(NPerRow-i%NPerRow-1):
			tempTR.append(HT.TD())
		tbl.append(tempTR)	
		body.append(tbl)
		body.append(HT.Paragraph("Copy the following line to paste into the GeneNetwork entry box:"))
		body.append(HT.Code(string.join(values, " ")))
		body.append(HT.HR(width="90%"))
	return body
		
if __name__ == "__main__":
	if os.environ.has_key('SCRIPT_FILENAME'):
		script_filename = os.environ['SCRIPT_FILENAME']
	else:
		script_filename = ''
	#Used as cgi script
	if script_filename and script_filename[-2:] == 'py':
		print 'Content-type: text/html\n'
		formdata = cgi.FieldStorage()
		sys.stderr = sys.stdout
		try:
			getID = string.lower(formdata.getvalue('get'))
		except:
			getID = ''
	#Used as command
	else:
		if len(sys.argv) >= 2:
			getID = string.lower(sys.argv[1])
		else:
			getID = ''
	
	if getID == 'headerfooter':
		print genHeaderFooter(0)
	elif getID == 'header':
		print genHeaderFooter(1)
	elif getID == 'footer':
		print genHeaderFooter(2)
	elif getID == 'databasemenu':
		print genDatabaseMenu(public=0)
	elif getID == 'datasample':
		print genRISample()
	else:
		print genHeaderFooter(0)
else:
	pass

