import sys
import re

import utilities
import datastructure

def main(argv):
    # config
    config = utilities.get_config(argv[1])
    print "config:"
    for item in config.items('config'):
        print "\t%s" % (str(item))
    # variables
    inbredsetid = config.get('config', 'inbredsetid')
    print "inbredsetid: %s" % inbredsetid
    species = datastructure.get_species(inbredsetid)
    speciesid = species[0]
    print "speciesid: %s" % speciesid
    genofreeze = datastructure.get_genofreeze_byinbredsetid(inbredsetid)
    genofreezeid = genofreeze[0]
    print "genofreezeid: %s" % genofreezeid
    dataid = datastructure.get_nextdataid_genotype()
    print "next data id: %s" % dataid
    cursor, con = utilities.get_cursor()
    # genofile
    genofile = open(config.get('config', 'genofile'), 'r')
    metadic = {}
    print
    # parse genofile
    for line in genofile:
        line = line.strip()
        if len(line) == 0:
            continue
        if line.startswith('#'):
            continue
        if line.startswith('@'):
            line = line.strip('@')
            items = line.split(';')
            for item in items:
                kv = re.split(':|=', item)
                metadic[kv[0].strip()] = kv[1].strip()
            continue
        if line.lower().startswith("chr"):
            #
            print "geno file meta:"
            for k, v in metadic.items():
                print "\t%s: %s" % (k, v)
            #
            print "geno file head:\n\t%s" % line
            print
            strainnames = line.split()[4:]
            strains = datastructure.get_strains_bynames(inbredsetid=inbredsetid, strainnames=strainnames, updatestrainxref="yes")
            continue
        # geno file line
        cells = line.split()
        chr = cells[0]
        locus = cells[1]
        cm = cells[2]
        mb = cells[3]
        values = cells[4:]
        # geno
        sql = """
            SELECT Geno.`Id`
            FROM Geno
            WHERE Geno.`SpeciesId`=%s
            AND Geno.`Name` like %s
            """
        cursor.execute(sql, (speciesid, locus))
        result = cursor.fetchone()
        if result:
            genoid = result[0]
            print "get geno record: %d" % genoid
        else:
            sql = """
                INSERT INTO Geno
                SET
                Geno.`SpeciesId`=%s,
                Geno.`Name`=%s,
                Geno.`Marker_Name`=%s,
                Geno.`Chr`=%s,
                Geno.`Mb`=%s
                """
            cursor.execute(sql, (speciesid, locus, locus, chr, mb))
            rowcount = cursor.rowcount
            genoid = con.insert_id()
            print "INSERT INTO Geno: %d record: %d" % (rowcount, genoid)
        # genodata
        for index, strain in enumerate(strains):
            strainid = strain[0]
            value = utilities.to_db_string(values[index], None)
            if not value:
                continue
            value = config.get('config', "genovalue_" + value)
            try:
                number = int(value)
            except:
                continue
            if not number in [-1, 0, 1]:
                continue
            sql = """
                INSERT INTO GenoData
                SET
                GenoData.`Id`=%s,
                GenoData.`StrainId`=%s,
                GenoData.`value`=%s
                """
            cursor.execute(sql, (dataid, strainid, number))
        # genoxref
        sql = """
            INSERT INTO GenoXRef
            SET
            GenoXRef.`GenoFreezeId`=%s,
            GenoXRef.`GenoId`=%s,
            GenoXRef.`DataId`=%s,
            GenoXRef.`cM`=%s,
            GenoXRef.`Used_for_mapping`=%s
            """
        cursor.execute(sql, (genofreezeid, genoid, dataid, cm, 'N'))
        rowcount = cursor.rowcount
        genoxrefid = con.insert_id()
        print "INSERT INTO GenoXRef: %d record: %d" % (rowcount, genoxrefid)
        # for loop next
        dataid += 1
        print
    # release
    genofile.close()
    con.close()

if __name__ == "__main__":
    print "command line arguments:\n\t%s" % sys.argv
    main(sys.argv)
    print "exit successfully"
