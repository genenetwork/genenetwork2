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
    speciesid = config.get('config', 'speciesid')
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
            strains = datastructure.get_strains_bynames(speciesid, strainnames)
            continue
        cells = line.split()
        Chr = cells[0]
        Locus = cells[1]
        cM = cells[2]
        Mb = cells[3]
        print len(cells)
    return

    # open db
    host = 'localhost'
    user = 'webqtl'
    passwd = 'webqtl'
    db = 'db_webqtl'
    con = MySQLdb.Connect(db=db, user=user, passwd=passwd, host=host)
    cursor = con.cursor()
    # var
    speciesid = int(argv[2])
    inbredsetid = int(argv[3])
    genofreezeid = int(argv[4])
    sql = """
        SELECT Id
        FROM GenoData
        ORDER BY Id DESC
        LIMIT 1
        """
    cursor.execute(sql)
    results = cursor.fetchall()
    dataid = results[0][0]
    print "speciesid: %s"        % (speciesid)
    print "inbredsetid: %s"        % (inbredsetid)
    print "genofreezeid: %s"    % (genofreezeid)
    print "dataid start: %s"        % (dataid+1)
    # samples
    line = file_geno.readline()
    sample_names = line.split()[4:]
    sample_ids = []
    print "get %d samples from file:\n%s" % (len(sample_names), sample_names)
    for sample_name in sample_names:
        sql = """
            select Id
            from Strain
            where SpeciesId=%s
            and Name like %s
            """
        cursor.execute(sql, (speciesid, sample_name))
        results = cursor.fetchall()
        if results:
            sample_ids.append(results[0][0])
        else:
            print "insert sample %s" % (sample_name)
            sql = """
                INSERT INTO Strain
                SET
                    SpeciesId=%s,
                    Name=%s,
                    Name2=%s
                """
            cursor.execute(sql, (speciesid, sample_name, sample_name))
            sampleid = con.insert_id()
            sample_ids.append(sampleid)
            #
            sql = """
                SELECT OrderId
                FROM StrainXRef
                where InbredSetId=%s
                ORDER BY OrderId DESC
                LIMIT 1 
                """
            cursor.execute(sql, (inbredsetid))
            results = cursor.fetchall()
            orderid = results[0][0] + 1
            #
            sql = """
                INSERT INTO StrainXRef
                SET
                    InbredSetId=%s,
                    StrainId=%s,
                    OrderId=%s,
                    Used_for_mapping=%s
                """
            cursor.execute(sql, (inbredsetid, sampleid, orderid, "N"))
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
