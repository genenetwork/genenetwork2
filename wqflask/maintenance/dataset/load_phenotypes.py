import sys
import csv

import utilities

def main(argv):
    # config
    config = utilities.get_config(argv[1])
    print "config:"
    for item in config.items('config'):
        print "\t%s" % (str(item))
    # var
    inbredsetid = config.get('config', 'inbredsetid')
    cursor, con = utilities.get_cursor()
    print "inbredsetid: %s" % inbredsetid
    # datafile
    datafile = open(config.get('config', 'datafile'), 'r')
    phenotypedata = csv.reader(datafile, delimiter='\t', quotechar='"')
    phenotypedata_head = phenotypedata.next()
    print "phenotypedata head:\n\t%s" % phenotypedata_head
    # metafile
    metafile = open(config.get('config', 'metafile'), 'r')
    phenotypemeta = csv.reader(metafile, delimiter='\t', quotechar='"')
    phenotypemeta_head = phenotypemeta.next()
    print "phenotypemeta head:\n\t%s" % phenotypemeta_head
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
            utilities.to_db_string_null(metarow[1]),
            utilities.to_db_string_null(metarow[2]),
            utilities.to_db_string_null(metarow[3]),
            utilities.to_db_string_null(metarow[4]),
            utilities.to_db_string_null(metarow[5]),
            utilities.to_db_string_null(metarow[6]),
            utilities.to_db_string_null(metarow[7]),
            utilities.to_db_string_null(metarow[8]),
            utilities.to_db_string_null(metarow[9]),
            utilities.to_db_string_null(metarow[18])
            ))
        rowcount = cursor.rowcount
        phenotypeid = con.insert_id()
        print "INSERT INTO Phenotype: %d record: %d" % (rowcount, phenotypeid)

if __name__ == "__main__":
    print "command line arguments:\n\t%s" % sys.argv
    main(sys.argv)
    print "exit successfully"
