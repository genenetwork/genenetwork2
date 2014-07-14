"""
Do whatever else is needed with the Marker object
Probably create Genofile object as well
Make sure rest of code works with params object (though
everything in the params object should probably just be the parameters of
the Genofile object)

Continue to rename variables in ways that make sense and to add underscores between words

Look at genofile_parser.py that I (Zach) wrote a while back and how much of it can just be reused

Get rid of/improve uninformative comments

"""


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
    with open(params['genofile']) as genofile:
        meta_data = {}
        print()
        # parse genofile
        for line in genofile:
            line = line.strip()
            if not line:
                pass
            elif line.startswith('#'):
                pass
            elif line.startswith('@'):
                line = line.strip('@')
                for item in line.split(';'):
                    kv = re.split(':|=', item)
                    meta_data[kv[0].strip()] = kv[1].strip()
            
            elif line.lower().startswith("chr"):
                print("geno file meta:")
                for key, value in meta_data.iteritems():
                    print("\t{}: {}".format(key, value))
                print("geno file head:\n\t{}\n".format(line))
                strain_names = line.split()[4:]
                strains = datastructure.get_strains_bynames(inbredsetid=inbredsetid,
                                                            strain_names=strain_names,
                                                            updatestrainxref="yes")
               
            else:
                # geno file line
                marker = Marker(line)
                #
                geno_id = check_or_insert_geno(params, marker)
    
                if check_genoxref(params): #Check if this can go earlier
                    continue
                
                insert_genodata(params)
                insert_genoxref(params)
                data_id += 1
    
    
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
    cursor.execute(sql, (speciesid, locus)) #This is correct
    result = cursor.fetchone()
    if result:
        geno_id = result[0]
        print("get geno record: ", geno_id)
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
        cursor.execute(sql, (species_id, locus, locus, chr, mb))
        row_count = cursor.rowcount
        geno_id = con.insert_id()
        print("INSERT INTO Geno: %d record: %d" % (row_count, geno_id))
    return geno_id

def check_GenoXRef():
    sql = """
        select GenoXRef.*
        from GenoXRef
        where GenoXRef.`GenoFreezeId`=%s
        AND GenoXRef.`GenoId`=%s
        """
    cursor.execute(sql, (geno_freeze_id, geno_id))
    row_count = cursor.rowcount
    return row_count
    
def insert_genodata():
    for index, strain in enumerate(strains):
        strain_id = strain[0]
        value = utilities.to_db_string(values[index], None)
        if not value:
            continue
        value = config.get('config', "genovalue_" + value)
        try:
            number = int(value)
        except ValueError:
            continue
        if number not in [-1, 0, 1]:
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
