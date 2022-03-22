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

with MySQLdb.connect(
        host='localhost', user='username', passwd='', db='db_webqtl') as mydb:
    with mydb.cursor() as cursor:

        csv_data = csv.reader(file('GN711_pvalues.txt'), delimiter ="\t")
        for row in csv_data:
            cursor.execute(
                """UPDATE ProbeSetXRef SET pValue = %s WHERE ProbeSetFreezeId = %s AND ProbeSetId = %s """,
                (row))
print("Done")
