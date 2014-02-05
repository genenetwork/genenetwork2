import utilities

def get_geno(inbredsetid, name):
    cursor = utilities.get_cursor()
    sql = """
        SELECT Geno.`Id`, Geno.`Name`, Geno.`Chr`, Geno.`Mb`
        FROM (Geno, InbredSet)
        WHERE Geno.`SpeciesId`=InbredSet.`SpeciesId`
        AND InbredSet.`Id`=%s
        AND Geno.`Name` LIKE %s
        """
    cursor.execute(sql, (inbredsetid, name))
    return cursor.fetchone()

def load_genos(file):
    genotypes = []
    file_geno = open(file, 'r')
    for line in file_geno:
        line = line.strip()
        if line.startswith('#'):
            continue
        if line.startswith('@'):
            continue
        cells = line.split()
        if line.startswith("Chr"):
            strains = cells[4:]
            strains = [strain.lower() for strain in strains]
            continue
        genotype = {}
        genotype['chr'] = cells[0]
        genotype['locus'] = cells[1]
        genotype['cm'] = cells[2]
        genotype['mb'] = cells[3]
        values = cells[4:]
        values = [to_number(value) for value in values]
        genotype['values'] = values
        genotype['dicvalues'] = utilities.to_dic(strains, values)
        genotypes.append(genotype)
    return strains, genotypes
    
def to_number(char):
    dic = {
        'b': -1,
        'd': 1,
        'h': 0,
        'u': None,
        }
    return dic.get(char.lower(), None)
