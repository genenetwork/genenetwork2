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
# Last updated by Lei Yan 2011/02/08

# created by Lei Yan 02/08/2011

import string
import MySQLdb
import time
import os
import sys

path1 = os.path.abspath(os.path.dirname(__file__))
path2 = path1 + "/.."
path3 = path1 + "/../../tmp"
sys.path.insert(0, path2)
from base import webqtlConfig

try:
        con = MySQLdb.Connect(db=webqtlConfig.DB_NAME,host=webqtlConfig.MYSQL_SERVER, user=webqtlConfig.DB_USER,passwd=webqtlConfig.DB_PASSWD)
        cursor = con.cursor()
        print "You have successfully connected to mysql.\n"
except:
        print "You entered incorrect password.\n"
        sys.exit(0)

taxIds = {'10090':1, '9606':4, '10116':2, '3702':3}
taxIdKeys = taxIds.keys()

os.chdir(path3)
cdict = {}

os.system("rm -f gene_info")
os.system("wget ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz")
os.system("gunzip gene_info.gz")
try:
	fp = open("gene_info")
except:
	print "gene_info doesn't exit"
	sys.exit(1)

i=0
line = fp.readline()
while line:
	line2 = map(string.strip, string.split(line.strip(), "\t"))
	if line2[0] in taxIdKeys:
		cdict[line2[1]] = line2[2]
	line = fp.readline()
	i += 1
	if i%1000 == 0:
		print "finished ",  i
fp.close()

os.system("rm -f generifs_basic")
os.system("wget ftp://ftp.ncbi.nlm.nih.gov/gene/GeneRIF/generifs_basic.gz")
os.system("gunzip generifs_basic.gz")
try:
	fp = open("generifs_basic")
except:
	print "generifs_basic doesn't exist"
	sys.exit(1)

cursor.execute("delete from GeneRIF_BASIC")
count = 0
line = fp.readline()
while line:
	line2 = map(string.strip, string.split(line.strip(), "\t"))
	if line2[0] in taxIdKeys:
		count += 1
		line2[0] = taxIds[line2[0]]
		if len(line2) !=5:
			print line
		else:
			try:
				symbol=cdict[line2[1]]
			except:
				symbol= ""
			
			line2 = line2[:2] + [symbol] + line2[2:]
			cursor.execute("insert into GeneRIF_BASIC(SpeciesId, GeneId, Symbol, PubMed_ID, createtime, comment) values(%s, %s, %s, %s, %s, %s)", tuple(line2))
	line = fp.readline()

fp.close()
print count, "\n"
cursor.close()
