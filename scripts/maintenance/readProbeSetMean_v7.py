#!/usr/bin/python2
"""This script use the nearest marker to the transcript as control, increasing permutation rounds according to the p-value"""

########################################################################
# Last Updated Sep 27, 2011 by Xiaodong
########################################################################
import string
import sys
import MySQLdb
import getpass
import time


########################################################################

def translateAlias(str):
    if str == "B6":
        return "C57BL/6J"
    elif str == "D2":
        return "DBA/2J"
    else:
        return str

########################################################################
#
#  Indicate Data Start Position, ProbeFreezeId, GeneChipId, DataFile
#
########################################################################


dataStart = 1

GeneChipId = int(input("Enter GeneChipId:"))
ProbeSetFreezeId = int(input("Enter ProbeSetFreezeId:"))
input_file_name = input("Enter file name with suffix:")

fp = open("%s" % input_file_name, 'rb')

try:
    passwd = getpass.getpass('Please enter mysql password here : ')
    con = MySQLdb.Connect(db='db_webqtl', host='localhost',
                          user='username', passwd=passwd)

    db = con.cursor()
    print("You have successfully connected to mysql.\n")
except:
    print("You entered incorrect password.\n")
    sys.exit(0)

time0 = time.time()

#########################################################################
#
#  Check if each line have same number of members
#  generate the gene list of expression data here
#
#########################################################################
print('Checking if each line have same number of members')

GeneList = []
isCont = 1
header = fp.readline()
header = header.strip().split('\t')
header = [x.strip() for x in header]
nfield = len(header)
line = fp.readline()

kj = 0
while line:
    line2 = line.strip().split('\t')
    line2 = [x.strip() for x in line2]
    if len(line2) != nfield:
        print(("Error : " + line))
        isCont = 0

    GeneList.append(line2[0])
    line = fp.readline()

    kj += 1
    if kj % 100000 == 0:
        print(('checked ', kj, ' lines'))

GeneList = sorted(map(string.lower, GeneList))

if isCont == 0:
    sys.exit(0)


print(('used ', time.time()-time0, ' seconds'))
#########################################################################
#
#  Check if each strain exist in database
#  generate the string id list of expression data here
#
#########################################################################
print('Checking if each strain exist in database')

isCont = 1
fp.seek(0)
header = fp.readline()
header = header.strip().split('\t')
header = [x.strip() for x in header]
header = list(map(translateAlias, header))
header = header[dataStart:]
Ids = []
for item in header:
    try:
        db.execute('select Id from Strain where Name = "%s"' % item)
        Ids.append(db.fetchall()[0][0])
    except:
        print((item, 'does not exist, check the if the strain name is correct'))
        isCont = 0

if isCont == 0:
    sys.exit(0)


print(('used ', time.time()-time0, ' seconds'))
########################################################################
#
# Check if each ProbeSet exist in database
#
########################################################################
print('Check if each ProbeSet exist in database')

##---- find PID is name or target ----##
line = fp.readline()
line = fp.readline()
line2 = line.strip().split('\t')
line2 = [x.strip() for x in line2]
PId = line2[0]

db.execute('select Id from ProbeSet where Name="%s" and ChipId=%d' %
           (PId, GeneChipId))
results = db.fetchall()
IdStr = 'TargetId'
if len(results) > 0:
    IdStr = 'Name'


##---- get Name/TargetId list from database ----##
db.execute('select distinct(%s) from ProbeSet where ChipId=%d order by %s' % (
    IdStr, GeneChipId, IdStr))
results = db.fetchall()

Names = []
for item in results:
    Names.append(item[0])

print(Names)

Names = sorted(map(string.lower, Names))


##---- compare genelist with names ----##
x = y = 0
x1 = -1
GeneList2 = []
while x < len(GeneList) and y < len(Names):
    if GeneList[x] == Names[y]:
        x += 1
        y += 1
    elif GeneList[x] < Names[y]:
        if x != x1:
            GeneList2.append(GeneList[x])
            x1 = x
        x += 1
    elif GeneList[x] > Names[y]:
        y += 1

    if x % 100000 == 0:
        print(('check Name, checked %d lines' % x))

while x < len(GeneList):
    GeneList2.append(GeneList[x])
    x += 1

isCont = 1
ferror = open("ProbeSetError.txt", "wb")
for item in GeneList2:
    ferror.write(item + " doesn't exist \n")
    print((item, " doesn't exist, check if the ProbeSet name is correct"))
    isCont = 0

if isCont == 0:
    sys.exit(0)


print(('used ', time.time()-time0, ' seconds'))
#########################################################################
#
# Insert data into database
#
#########################################################################
print('getting ProbeSet/Id')


#---- get Name/Id map ----#
db.execute('select %s, Id from ProbeSet where ChipId=%d order by %s' %
           (IdStr, GeneChipId, IdStr))
results = db.fetchall()
NameIds = {}
for item in results:
    NameIds[item[0]] = item[1]
print(('used ', time.time()-time0, ' seconds'))


print('inserting data')

##---- get old max dataId ----##
db.execute('select max(Id) from ProbeSetData')
maxDataId = int(db.fetchall()[0][0])
bmax = maxDataId
print(("old_max = %d\n" % bmax))

##---- insert data ----##
fp.seek(0)
line = fp.readline()
line = fp.readline()
kj = 0

values1 = []
values2 = []
while line:
    line2 = line.strip().split('\t')
    line2 = [x.strip() for x in line2]
    PId = line2[0]
    recordId = NameIds[PId]

    maxDataId += 1
    datasorig = line2[dataStart:]

    ###### Data Table items ######
    i = 0
    for item in datasorig:
        try:
            values1.append('(%d,%d,%s)' % (maxDataId, Ids[i], float(item)))
        except:
            pass
        i += 1

    values2.append("(%d,%d,%d)" % (ProbeSetFreezeId, recordId, maxDataId))

    ##---- insert into table ----##
    kj += 1
    if kj % 100 == 0:
        cmd = ','.join(values1)
        cmd = 'insert into ProbeSetData values %s' % cmd
        db.execute(cmd)

        cmd = ','.join(values2)
        cmd = 'insert into ProbeSetXRef(ProbeSetFreezeId, ProbeSetId, DataId) values %s' % cmd
        db.execute(cmd)

        values1 = []
        values2 = []
        print(('Inserted ', kj, ' lines'))
        print(('used ', time.time()-time0, ' seconds'))

    line = fp.readline()


if len(values1) > 0:
    cmd = ','.join(values1)
    cmd = 'insert into ProbeSetData values %s' % cmd
    db.execute(cmd)

    cmd = ','.join(values2)
    cmd = 'insert into ProbeSetXRef(ProbeSetFreezeId, ProbeSetId, DataId) values %s' % cmd
    db.execute(cmd)

db.close()
con.close()
