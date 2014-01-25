# Author:               Lei Yan

# import
import sys
import os
import re
import MySQLdb

def fetch():
    # parameters
    inbredsetid = 1
    # open db
    host = 'localhost'
    user = 'webqtl'
    passwd = 'webqtl'
    db = 'db_webqtl'
    con = MySQLdb.Connect(db=db, user=user, passwd=passwd, host=host)
    cursor = con.cursor()
    # get strain list
    strains = []
    sql = """
        SELECT Strain.`Name`
        FROM StrainXRef, Strain
        WHERE StrainXRef.`StrainId`=Strain.`Id`
        AND StrainXRef.`InbredSetId`=%s
        ORDER BY StrainXRef.`OrderId`
        """
    cursor.execute(sql, (inbredsetid))
    results = cursor.fetchall()
    for row in results:
        strain = row[0]
        strain = strain.lower()
        strains.append(strain)
    print "get %d strains: %s" % (len(strains), strains)
    #
    sql = """
        SELECT PublishXRef.`Id`, Phenotype.`Original_description`, Phenotype.`Pre_publication_description`, Phenotype.`Post_publication_description`
        FROM (PublishXRef, Phenotype)
        WHERE PublishXRef.`PhenotypeId`=Phenotype.`Id`
        AND PublishXRef.`InbredSetId`=%s
        """
    cursor.execute(sql, (inbredsetid))
    results = cursor.fetchall()
    print "get %d phenotypes" % (len(results))
    for phenotyperow in results:
        publishxrefid = phenotyperow[0]
        original_description = phenotyperow[1]
        pre_publication_description = phenotyperow[2]
        post_publication_description = phenotyperow[3]
        sql = """
            SELECT Strain.Name, PublishData.value
            FROM (PublishXRef, PublishData, Strain)
            WHERE PublishXRef.`InbredSetId`=%s
            AND PublishXRef.Id=%s
            AND PublishXRef.DataId=PublishData.Id
            AND PublishData.StrainId=Strain.Id
        """
        cursor.execute(sql, (inbredsetid, publishxrefid))
        results = cursor.fetchall()
        print "get %d values" % (len(results))
        for strainvalue in results:
            print strainvalue
        break
    
# main
if __name__ == "__main__":
    fetch()
    print "exit successfully"
