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
    genofile = open(config.get('config', 'genofile'), 'r')
    metadic = {}
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
            strainnames = line.split()[4:]
            strains = datastructure.get_strains_bynames(inbredsetid=inbredsetid, strainnames=strainnames, updatestrainxref="yes")
            continue
        # geno line
        cells = line.split()
        chr = cells[0]
        locus = cells[1]
        cm = cells[2]
        mb = cells[3]
        values = cells[4:]
        print values
    return

            
    print "load %d samples from DB:" % (len(sample_names))
    for i in range(len(sample_names)):
        print "%s\t%s" % (sample_names[i], sample_ids[i])
    # parse geno file
    index = 0
    for line in file_geno:
        index += 1
        if index % 1000 == 0:
            print index
        items = line.split()
        chr = items[0]
        name = items[1]
        cm = items[2]
        mb = items[3]
        values = items[4:]
        # geno
        sql = """
            SELECT Id
            FROM Geno
            WHERE SpeciesId=%s
            AND Name like %s
            """
        cursor.execute(sql, (speciesid, name))
        results = cursor.fetchall()
        if results:
            genoid = results[0][0]
        else:
            print "insert geno %s" % (name)
            sql = """
                INSERT INTO Geno
                SET
                    SpeciesId=%s,
                    Name=%s,
                    Marker_Name=%s,
                    Chr=%s,
                    Mb=%s
                """
            cursor.execute(sql, (speciesid, name, name, chr, mb))
            genoid = con.insert_id()
        # genodata
        dataid += 1
        for i in range(len(values)):
            sample_id = sample_ids[i]
            try:
                value = int(values[i])
            except ValueError:
                continue
            if not value in [-1, 0, 1]:
                print sample_id, value
                continue
            sql = """
                INSERT INTO GenoData
                SET
                    Id=%s,
                    StrainId=%s,
                    value=%s
                """
            cursor.execute(sql, (dataid, sample_id, value))
        # genoxref
        sql = """
            INSERT INTO GenoXRef
            SET
                GenoFreezeId=%s,
                GenoId=%s,
                DataId=%s,
                cM=%s,
                Used_for_mapping=%s
            """
        cursor.execute(sql, (genofreezeid, genoid, dataid, cm, 'N'))
    print "Insert %d genoxref" % (index)
    # close
    file_geno.close()
    con.close()

if __name__ == "__main__":
    print "command line arguments:\n\t%s" % sys.argv
    main(sys.argv)
    print "exit successfully"
