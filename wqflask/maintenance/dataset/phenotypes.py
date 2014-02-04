# Author:               Lei Yan

# import

import utilities

def fetch():
    # parameters
    inbredsetid = 1
    phenotypesfile = open('bxdphenotypes.txt', 'w+')
    #
    phenotypesfile.write("id\tAuthors\tOriginal_description\tPre_publication_description\tPost_publication_description\t")
    # open db
    cursor = utilities.get_cursor()
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
    phenotypesfile.write('\t'.join([strain.upper() for strain in strains]))
    phenotypesfile.write('\n')
    phenotypesfile.flush()
    # phenotypes
    sql = """
        SELECT PublishXRef.`Id`, Publication.`Authors`, Phenotype.`Original_description`, Phenotype.`Pre_publication_description`, Phenotype.`Post_publication_description`
        FROM (PublishXRef, Phenotype, Publication)
        WHERE PublishXRef.`InbredSetId`=%s
        AND PublishXRef.`PhenotypeId`=Phenotype.`Id`
        AND PublishXRef.`PublicationId`=Publication.`Id`
        """
    cursor.execute(sql, (inbredsetid))
    results = cursor.fetchall()
    print "get %d phenotypes" % (len(results))
    for phenotyperow in results:
        publishxrefid = phenotyperow[0]
        authors = utilities.clearspaces(phenotyperow[1])
        original_description = utilities.clearspaces(phenotyperow[2])
        pre_publication_description = utilities.clearspaces(phenotyperow[3])
        post_publication_description = utilities.clearspaces(phenotyperow[4])
        phenotypesfile.write("%s\t%s\t%s\t%s\t%s\t" % (publishxrefid, authors, original_description, pre_publication_description, post_publication_description))
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
        strainvaluedic = {}
        for strainvalue in results:
            strainname = strainvalue[0]
            strainname = strainname.lower()
            value = strainvalue[1]
            strainvaluedic[strainname] = value
        for strain in strains:
            if strain in strainvaluedic:
                phenotypesfile.write(str(strainvaluedic[strain]))
            else:
                phenotypesfile.write('x')
            phenotypesfile.write('\t')
        phenotypesfile.write('\n')
        phenotypesfile.flush()
    # release
    phenotypesfile.close()
    
# main
if __name__ == "__main__":
    fetch()
    print "exit successfully"
