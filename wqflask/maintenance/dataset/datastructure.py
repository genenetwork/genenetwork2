import utilities

def get_probesetfreezes(inbredsetid):
    cursor, con = utilities.get_cursor()
    sql = """
        SELECT ProbeSetFreeze.`Id`, ProbeSetFreeze.`Name`, ProbeSetFreeze.`FullName`
        FROM ProbeSetFreeze, ProbeFreeze
        WHERE ProbeSetFreeze.`ProbeFreezeId`=ProbeFreeze.`Id`
        AND ProbeFreeze.`InbredSetId`=%s
        """
    cursor.execute(sql, (inbredsetid))
    return cursor.fetchall()

def get_probesetfreeze(probesetfreezeid):
    cursor, con = utilities.get_cursor()
    sql = """
        SELECT ProbeSetFreeze.`Id`, ProbeSetFreeze.`Name`, ProbeSetFreeze.`FullName`
        FROM ProbeSetFreeze
        WHERE ProbeSetFreeze.`Id`=%s
        """
    cursor.execute(sql, (probesetfreezeid))
    return cursor.fetchone()
    
def get_strains(inbredsetid):
    cursor, con = utilities.get_cursor()
    sql = """
        SELECT Strain.`Id`, Strain.`Name`
        FROM StrainXRef, Strain
        WHERE StrainXRef.`InbredSetId`=%s
        AND StrainXRef.`StrainId`=Strain.`Id`
        ORDER BY StrainXRef.`OrderId`
        """
    cursor.execute(sql, (inbredsetid))
    return cursor.fetchall()

def get_inbredset(probesetfreezeid):
    cursor, con = utilities.get_cursor()
    sql = """
        SELECT InbredSet.`Id`, InbredSet.`Name`, InbredSet.`FullName`
        FROM InbredSet, ProbeFreeze, ProbeSetFreeze
        WHERE InbredSet.`Id`=ProbeFreeze.`InbredSetId`
        AND ProbeFreeze.`Id`=ProbeSetFreeze.`ProbeFreezeId`
        AND ProbeSetFreeze.`Id`=%s
        """
    cursor.execute(sql, (probesetfreezeid))
    return cursor.fetchone()
    
def get_species(inbredsetid):
    cursor, con = utilities.get_cursor()
    sql = """
        SELECT Species.`Id`, Species.`Name`, Species.`MenuName`, Species.`FullName`
        FROM InbredSet, Species
        WHERE InbredSet.`Id`=%s
        AND InbredSet.`SpeciesId`=Species.`Id`
        """
    cursor.execute(sql, (inbredsetid))
    return cursor.fetchone()
    
def get_genofreeze_byinbredsetid(inbredsetid):
    cursor, con = utilities.get_cursor()
    sql = """
        SELECT GenoFreeze.`Id`, GenoFreeze.`Name`, GenoFreeze.`FullName`, GenoFreeze.`InbredSetId`
        FROM GenoFreeze
        WHERE GenoFreeze.`InbredSetId`=%s
        """
    cursor.execute(sql, (inbredsetid))
    return cursor.fetchone()

def get_nextdataid_phenotype():
    cursor, con = utilities.get_cursor()
    sql = """
        SELECT PublishData.`Id`
        FROM PublishData
        ORDER BY PublishData.`Id` DESC
        LIMIT 1
        """
    cursor.execute(sql)
    re = cursor.fetchone()
    dataid = re[0]
    dataid += 1
    return dataid

def insert_strain(speciesid, strainname):
    cursor, con = utilities.get_cursor()
    sql = """
        INSERT INTO Strain
        SET
        Strain.`Name`=%s,
        Strain.`Name2`=%s,
        Strain.`SpeciesId`=%s
        """
    cursor.execute(sql, (strainname, strainname, speciesid))

def get_strain(speciesid, strainname):
    cursor, con = utilities.get_cursor()
    sql = """
        SELECT Strain.`Id`, Strain.`Name`
        FROM Strain
        WHERE Strain.`SpeciesId`=%s
        AND Strain.`Name` LIKE %s
        """
    cursor.execute(sql, (speciesid, strainname))
    return cursor.fetchone()

def get_strain_sure(speciesid, strainname):
    strain = get_strain(speciesid, strainname)
    if not strain:
        insert_strain(speciesid, strainname)
        strain = get_strain(speciesid, strainname)
    return strain

def get_strains_bynames(speciesid, strainnames):
    strains = []
    for strainname in strainnames:
        strains.append(get_strain_sure(speciesid, strainname))
    return strains
