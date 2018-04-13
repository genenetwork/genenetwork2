#!/usr/bin/python2
########################################################################
# Last Updated Apr 11, 2016 By Arthur and Zach
########################################################################
import string
import sys
import MySQLdb
import getpass
import time
import csv
########################################################################

mydb = MySQLdb.connect(host='localhost',
    user='username',
    passwd='',
    db='db_webqtl')
cursor = mydb.cursor()

csv_data = csv.reader(file('GN711_pvalues.txt'), delimiter ="\t")
for row in csv_data:

    cursor.execute("""UPDATE ProbeSetXRef SET pValue = %s WHERE ProbeSetFreezeId = %s AND ProbeSetId = %s """,
          (row))
#close the connection to the database.
mydb.commit()
cursor.close()
print "Done"