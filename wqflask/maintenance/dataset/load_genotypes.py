#Do whatever else is needed with the Marker object
#Probably create Genofile object as well
#Make sure rest of code works with params object (though
#everything in the params object should probably just be the parameters of
#the Genofile object)


from __future__ import absolute_import, print_function, division

import sys
import re
import argparse

import utilities
import datastructure

def main():
    parser = argparse.ArgumentParser(description='Load Genotypes')
    parser.add_argument('-c', '--config')
    opts = parser.parse_args()
    config = opts.config
    # config
    config = utilities.get_config(config)
    print("config:")
    for item in config.items('config'):
        print("\t", str(item))
    parse_genofile(fetch_parameters(config))

def fetch_parameters(config):
    # variables
    params = {}
    params['inbredsetid'] = config.get('config', 'inbredsetid')
    species = datastructure.get_species(params['inbredsetid'])
    params["speciesid"] = species[0]
    genofreeze = datastructure.get_genofreeze_byinbredsetid(params['inbredsetid'])
    params['genofreezeid'] = genofreeze[0]
    params['dataid'] = datastructure.get_nextdataid_genotype()
    params['genofile'] = config.get('config', 'genofile')
    return params
    
def parse_genofile(params):
    # genofile
    genofile = open(params['genofile'], 'r')
    metadic = {}
    print()
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
            print("geno file meta:")
            for k, v in metadic.items():
                print("\t{}: {}".format(k, v))
            #
            print("geno file head:\n\t{}\n".format(line))
            strainnames = line.split()[4:]
            strains = datastructure.get_strains_bynames(inbredsetid=inbredsetid, strainnames=strainnames, updatestrainxref="yes")
            continue
        # geno file line
        marker = Marker(line)
        #
        genoid = check_or_insert_geno(params, marker)
        if check_genoxref(params):
            continue
        insert_genodata(params)
        insert_genoxref(params)
        dataid += 1
    genofile.close()
    
    
class Marker(object):
    def __init__(self, line):
        self.cells = line.split()
        self.chromosome = cells[0]
        self.locus = cells[1]
        self.cm = cells[2]
        self.mb = cells[3]
        self.values = cells[4:]
        
def check_or_insert_geno(params, marker):
    cursor, con = utilities.get_cursor()
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
        print("get geno record: %d" % genoid)
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
        print("INSERT INTO Geno: %d record: %d" % (rowcount, genoid))
    return genoid

def check_GenoXRef():
    sql = """
        select GenoXRef.*
        from GenoXRef
        where GenoXRef.`GenoFreezeId`=%s
        AND GenoXRef.`GenoId`=%s
        """
    cursor.execute(sql, (genofreezeid, genoid))
    rowcount = cursor.rowcount
    return rowcount
    
def insert_genodata():
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

def insert_genoxref():
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
    print("INSERT INTO GenoXRef: %d record" % (rowcount))

if __name__ == "__main__":
    print("command line arguments:\n\t%s" % sys.argv)
    main()
    print("exit successfully")
