#!/usr/bin/python
import sys
import os
import string
import reaper
import MySQLdb
"""
def swap(A, B):
	temp = A
	A = B
	B = A

fp = open('ColXCvi.txt')
fout = open('ColXCvi2.txt', "wb")
line = fp.readline()
i = 0
while line:
	line2 = map(string.strip, string.split(line.strip()))
	print len(line2)
	if i == 0:
		line2 = line2[:7] + map(lambda X:'ColXCvi' + X, line2[7:])
	X = line2[1]
	line2[1] = line2[2]
	line2[2] = X
	line2 = line2[:5] + line2[7:]
	fout.write(string.join(line2[1:], "\t") + "\n")
	line = fp.readline()
	i += 1
	
fout.close()
fp.close()
"""
"""
try:
	#import getpass
	#passwd = getpass.getpass('Please enter mysql password here : ')
	con = MySQLdb.Connect(db='db_webqtl',user='webqtlupd',passwd='webqtl', host="opteron")
	cursor = con.cursor()
	print "You have successfully connected to mysql.\n"
except:
	print "You entered incorrect password.\n"
	sys.exit(0)

for geno in ("ColXBur.geno", "ColXCvi.geno"):
	a = reaper.Dataset()
	a.read(geno)
	#print a.prgy, len(a.prgy)
	for item in a.prgy:
		cursor.execute("insert into Strain(Name, SpeciesId) values(%s, 3)", item)
		
cursor.close()

try:
	#import getpass
	#passwd = getpass.getpass('Please enter mysql password here : ')
	con = MySQLdb.Connect(db='db_webqtl',user='webqtlupd',passwd='webqtl', host="opteron")
	cursor = con.cursor()
	print "You have successfully connected to mysql.\n"
except:
	print "You entered incorrect password.\n"
	sys.exit(0)
cursor.execute("select max(Id)+1 from Geno")
maxId = cursor.fetchone()[0]

for geno in ("ColXBur.geno", "ColXCvi.geno"):
	a = reaper.Dataset()
	a.read(geno)
	#print a.prgy, len(a.prgy)
	for chr in a:
		for locus in chr:
			print geno, locus.name, chr.name, locus.Mb
			try:
				cursor.execute("insert into Geno(Id, Name, Chr, MB_UCSC, chr_num, Source, Source2) values(%s, %s, %s, %s, %s, %s, %s)", (maxId, locus.name, chr.name, locus.Mb, chr.name, "Institute for Agronomical Research", "Institute for Agronomical Research"))
				maxId += 1
			except:
				pass
cursor.close()
mysql> select max(Id) from Data;
+----------+
| max(Id)  |
+----------+
| 22163234 |
+----------+
1 row in set (0.00 sec)

mysql> select max(DataId) from GenoXRef;
+-------------+
| max(DataId) |
+-------------+
|    16098047 |
+-------------+
1 row in set (0.04 sec)

mysql> select * from Strain order by Id desc limit 5;
+------+------------+-----------+--------+
| Id   | Name       | SpeciesId | Symbol |
+------+------------+-----------+--------+
| 1828 | ColXCvi499 |         3 | NULL   |
| 1827 | ColXCvi497 |         3 | NULL   |
| 1826 | ColXCvi496 |         3 | NULL   |
| 1825 | ColXCvi495 |         3 | NULL   |
| 1824 | ColXCvi494 |         3 | NULL   |
+------+------------+-----------+--------+

"""

"""
try:
	#import getpass
	#passwd = getpass.getpass('Please enter mysql password here : ')
	con = MySQLdb.Connect(db='db_webqtl',user='webqtlupd',passwd='webqtl', host="opteron")
	cursor = con.cursor()
	print "You have successfully connected to mysql.\n"
except:
	print "You entered incorrect password.\n"
	sys.exit(0)

freezeId = 14
for geno in ("ColXBur.geno", "ColXCvi.geno"):
	a = reaper.Dataset()
	a.read(geno)
	strainIds = []
	for strain in a.prgy:
		cursor.execute("select Id from Strain where Name = '%s' and SpeciesId=3" % strain)
		strainIds.append(cursor.fetchone()[0])
	for chr in a:
		for locus in chr:
			cursor.execute("select max(Id)+1 from Data")
			dataId = cursor.fetchone()[0]
			cursor.execute("select Id from Geno where Name = '%s'" % locus.name)
			GenoId = cursor.fetchone()[0]
			#print geno, locus.name, chr.name, locus.Mb, dataId, GenoId
			for i, item in enumerate(locus.genotype):
				cursor.execute("insert into Data values(%s, %s, %s)" ,(dataId, strainIds[i], item))
			cursor.execute("insert into GenoXRef values(%s, %s, %s)" , (freezeId, GenoId, dataId))
	freezeId -= 1
cursor.close()
"""

try:
	#import getpass
	#passwd = getpass.getpass('Please enter mysql password here : ')
	con = MySQLdb.Connect(db='db_webqtl',user='webqtlupd',passwd='webqtl', host="opteron")
	cursor = con.cursor()
	print "You have successfully connected to mysql.\n"
except:
	print "You entered incorrect password.\n"
	sys.exit(0)

freezeId = 14
for geno in ("ColXBur.geno", "ColXCvi.geno"):
	values = [-1, 1, 0, 0]
	if geno == "ColXBur.geno":
		strains = ["Col-0", "Bur-0", "ColXBurF1", "BurXColF1"]
	else:
		strains = ["Col-0", "Cvi", "ColXCviF1", "CviXColF1"]
	strainIds = []
	for strain in strains:
		cursor.execute("select Id from Strain where Name = '%s' and SpeciesId=3" % strain)
		strainIds.append(cursor.fetchone()[0])
	print strainIds
	cursor.execute("select DataId from GenoXRef where GenoFreezeId = %d" % freezeId)
	results = cursor.fetchall()
	for dataId in results:
		for i, strainId in enumerate(strainIds):
			#print "insert into Data values(%s, %s, %s)" % (dataId[0], strainId, values[i])
			cursor.execute("insert into Data values(%s, %s, %s)" ,(dataId[0], strainId, values[i]))
	freezeId -= 1
cursor.close()

