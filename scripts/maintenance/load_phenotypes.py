import sys
import csv

import utilities
import datastructure

def main(argv):
    # config
    config = utilities.get_config(argv[1])
    print "config:"
    for item in config.items('config'):
        print "\t%s" % (str(item))
    # var
    inbredsetid = config.get('config', 'inbredsetid')
    print "inbredsetid: %s" % inbredsetid
    species = datastructure.get_species(inbredsetid)
    speciesid = species[0]
    print "speciesid: %s" % speciesid
    dataid = datastructure.get_nextdataid_phenotype()
    print "next data id: %s" % dataid
    cursor, con = utilities.get_cursor()
    # datafile
    datafile = open(config.get('config', 'datafile'), 'r')
    phenotypedata = csv.reader(datafile, delimiter='\t', quotechar='"')
    phenotypedata_head = phenotypedata.next()
    print "phenotypedata head:\n\t%s" % phenotypedata_head
    strainnames = phenotypedata_head[1:]
    strains = datastructure.get_strains_bynames(inbredsetid=inbredsetid, strainnames=strainnames, updatestrainxref="yes")
    # metafile
    metafile = open(config.get('config', 'metafile'), 'r')
    phenotypemeta = csv.reader(metafile, delimiter='\t', quotechar='"')
    phenotypemeta_head = phenotypemeta.next()
    print "phenotypemeta head:\n\t%s" % phenotypemeta_head
    print
    # load
    for metarow in phenotypemeta:
        #
        datarow_value = phenotypedata.next()
        datarow_se = phenotypedata.next()
        datarow_n = phenotypedata.next()
        # Phenotype
        sql = """
            INSERT INTO Phenotype
            SET
            Phenotype.`Pre_publication_description`=%s,
            Phenotype.`Post_publication_description`=%s,
            Phenotype.`Original_description`=%s,
            Phenotype.`Pre_publication_abbreviation`=%s,
            Phenotype.`Post_publication_abbreviation`=%s,
            Phenotype.`Lab_code`=%s,
            Phenotype.`Submitter`=%s,
            Phenotype.`Owner`=%s,
            Phenotype.`Authorized_Users`=%s,
            Phenotype.`Units`=%s
            """
        cursor.execute(sql, (
            utilities.to_db_string(metarow[1], None),
            utilities.to_db_string(metarow[2], None),
            utilities.to_db_string(metarow[3], None),
            utilities.to_db_string(metarow[4], None),
            utilities.to_db_string(metarow[5], None),
            utilities.to_db_string(metarow[6], None),
            utilities.to_db_string(metarow[7], None),
            utilities.to_db_string(metarow[8], None),
            utilities.to_db_string(metarow[9], ""),
            utilities.to_db_string(metarow[18], ""),
            ))
        rowcount = cursor.rowcount
        phenotypeid = con.insert_id()
        print "INSERT INTO Phenotype: %d record: %d" % (rowcount, phenotypeid)
        # Publication
        publicationid = None # reset
        pubmed_id = utilities.to_db_string(metarow[0], None)
        if pubmed_id:
            sql = """
                SELECT Publication.`Id`
                FROM Publication
                WHERE Publication.`PubMed_ID`=%s
                """
            cursor.execute(sql, (pubmed_id))
            re = cursor.fetchone()
            if re:
                publicationid = re[0]
                print "get Publication record: %d" % publicationid
        if not publicationid:
            sql = """
                INSERT INTO Publication
                SET
                Publication.`PubMed_ID`=%s,
                Publication.`Abstract`=%s,
                Publication.`Authors`=%s,
                Publication.`Title`=%s,
                Publication.`Journal`=%s,
                Publication.`Volume`=%s,
                Publication.`Pages`=%s,
                Publication.`Month`=%s,
                Publication.`Year`=%s
                """
            cursor.execute(sql, (
                utilities.to_db_string(metarow[0], None),
                utilities.to_db_string(metarow[12], None),
                utilities.to_db_string(metarow[10], ""),
                utilities.to_db_string(metarow[11], None),
                utilities.to_db_string(metarow[13], None),
                utilities.to_db_string(metarow[14], None),
                utilities.to_db_string(metarow[15], None),
                utilities.to_db_string(metarow[16], None),
                utilities.to_db_string(metarow[17], ""),
                ))
            rowcount = cursor.rowcount
            publicationid = con.insert_id()
            print "INSERT INTO Publication: %d record: %d" % (rowcount, publicationid)
        # data
        for index, strain in enumerate(strains):
            #
            strainid = strain[0]
            value   = utilities.to_db_float(datarow_value[index+1], None)
            se      = utilities.to_db_float(datarow_se[index+1], None)
            n       = utilities.to_db_int(datarow_n[index+1], None)
            #
            if value is not None:
                sql = """
                    INSERT INTO PublishData
                    SET
                    PublishData.`Id`=%s,
                    PublishData.`StrainId`=%s,
                    PublishData.`value`=%s
                    """
                cursor.execute(sql, (dataid, strainid, value))
            if se is not None:
                sql = """
                    INSERT INTO PublishSE
                    SET
                    PublishSE.`DataId`=%s,
                    PublishSE.`StrainId`=%s,
                    PublishSE.`error`=%s
                    """
                cursor.execute(sql, (dataid, strainid, se))
            if n is not None:
                sql = """
                    INSERT INTO NStrain
                    SET
                    NStrain.`DataId`=%s,
                    NStrain.`StrainId`=%s,
                    NStrain.`count`=%s
                    """
                cursor.execute(sql, (dataid, strainid, n))
        # PublishXRef
        sql = """
            INSERT INTO PublishXRef
            SET
            PublishXRef.`InbredSetId`=%s,
            PublishXRef.`PhenotypeId`=%s,
            PublishXRef.`PublicationId`=%s,
            PublishXRef.`DataId`=%s,
            PublishXRef.`comments`=%s
            """
        cursor.execute(sql, (inbredsetid, phenotypeid, publicationid, dataid, ""))
        rowcount = cursor.rowcount
        publishxrefid = con.insert_id()
        print "INSERT INTO PublishXRef: %d record: %d" % (rowcount, publishxrefid)
        # for loop next
        dataid += 1
        print
    # release
    con.close()

if __name__ == "__main__":
    print "command line arguments:\n\t%s" % sys.argv
    main(sys.argv)
    print "exit successfully"
