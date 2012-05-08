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
# created by Lei Yan 02/08/2011
import sys, os
import MySQLdb
import string



abs_path = os.path.abspath(os.path.dirname(__file__))
path1 = abs_path + "/.."
path2 = abs_path + "/../../javascript"
sys.path.insert(0, path1)

#must import GN python files after add path
from base import webqtlConfig

# build MySql database connection
con = MySQLdb.Connect(db=webqtlConfig.DB_NAME, host=webqtlConfig.MYSQL_SERVER, user=webqtlConfig.DB_USER, passwd=webqtlConfig.DB_PASSWD)
cursor = con.cursor()
cursor.execute("SELECT id,menuname FROM Species ORDER BY OrderId")
results = list(cursor.fetchall())
collectionsText = ""
for result in results:
	specieid = result[0]
	speciename = result[1]
	collectionsText += ("['" + speciename + "', ")
	collectionsText += ("null, ")
	collectionsText += ("null, ")
	collectionsText += "\n"
	cursor.execute("select name from InbredSet where speciesid=" + str(specieid))
	results2 = list(cursor.fetchall())
	for result2 in results2:
		inbredsetName = result2[0]
		if not cmp(inbredsetName, "BXD300"):
			continue
		collectionsText += "\t"
		collectionsText += ("['" + inbredsetName + "', ")
		collectionsText += ("'/webqtl/main.py?FormID=dispSelection&RISet=" + inbredsetName + "'], ")
		collectionsText += "\n"
	collectionsText += "],"
	collectionsText += "\n"
collectionsText = collectionsText.strip()

jstext = """/*
  --- menu items --- 
  note that this structure has changed its format since previous version.
  additional third parameter is added for item scope settings.
  Now this structure is compatible with Tigra Menu GOLD.
  Format description can be found in product documentation.
*/
var MENU_ITEMS = [
	['menu_grp1', null, null,
		['GeneNetwork Intro', '/home.html'],
		['Enter Trait Data', '/webqtl/main.py?FormID=submitSingleTrait'],
		['Batch Submission', '/webqtl/main.py?FormID=batSubmit'],
	],
	['menu_grp2', null, null,
		['Search Databases', '/'],
		['Tissue Correlation', '/webqtl/main.py?FormID=tissueCorrelation'],
		['SNP Browser', '/webqtl/main.py?FormID=snpBrowser'],
		['Gene Wiki', '/webqtl/main.py?FormID=geneWiki'],
		['Interval Analyst', '/webqtl/main.py?FormID=intervalAnalyst'],
		['QTLminer', '/webqtl/main.py?FormID=qtlminer'],
		['GenomeGraph', '/dbResults.html'],
		['Trait Collections',null,null,
%s
		],
		['Scriptable Interface', '/CGIDoc.html'],
		/* ['Simple Query Interface', '/GUI.html'], */
		['Database Information',null,null,
			['Database Schema', '/webqtl/main.py?FormID=schemaShowPage'],
		],
		['Data Sharing', '/webqtl/main.py?FormID=sharing'],
		['Microarray Annotations', '/webqtl/main.py?FormID=annotation'],
	],
	['menu_grp3', null, null,
		['Movies','http://www.genenetwork.org/tutorial/movies'],
		['Tutorials', null, null, 
                ['GN Barley Tutorial','/tutorial/pdf/GN_Barley_Tutorial.pdf'],
                ['GN Powerpoint', '/tutorial/ppt/index.html']],
		['HTML Tour','/tutorial/WebQTLTour/'],
		['FAQ','/faq.html'],
		['Glossary of Terms','/glossary.html'],
		['GN MediaWiki','http://wiki.genenetwork.org/'],
	],
	['menu_grp4', '/whats_new.html'
	],
	['menu_grp5', '/reference.html'
	],
	['menu_grp6', null, null,
		['Conditions and Limitation', '/conditionsofUse.html'],
		['Data Sharing Policy', '/dataSharing.html'],
		['Status and Contacts', '/statusandContact.html'],
		['Privacy Policy', '/privacy.html'],
	],
	['menu_grp8', '/links.html'
	],
];
"""

# create menu_items.js file
fileHandler = open(path2 + '/menu_items.js', 'w')
fileHandler.write(jstext % collectionsText)
fileHandler.close()
