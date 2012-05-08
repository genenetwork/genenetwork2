import sys
import os
import MySQLdb
import time

db='db_webqtl_leiyan'
author="megan memphis"

con = MySQLdb.Connect(db=db,user='webqtlupd',passwd='webqtl', host="localhost")
cursor = con.cursor()
cursor.execute('select PhenotypeId, Locus, DataId, Phenotype.Post_publication_description from PublishXRef, Phenotype where PublishXRef.PhenotypeId = Phenotype.Id and InbredSetId=%s'%InbredSetId)
PublishXRefInfos = cursor.fetchall()
