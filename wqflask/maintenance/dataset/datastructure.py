import utilities

def get_probesetfreezes(inbredsetid):
    cursor = utilities.get_cursor()
    sql = """
        SELECT ProbeSetFreeze.`Id`, ProbeSetFreeze.`Name`, ProbeSetFreeze.`FullName`
        FROM ProbeSetFreeze, ProbeFreeze
        WHERE ProbeSetFreeze.`ProbeFreezeId`=ProbeFreeze.`Id`
        AND ProbeFreeze.`InbredSetId`=%s
        """
    cursor.execute(sql, (inbredsetid))
    return cursor.fetchall()

def get_probesetfreeze(probesetfreezeid):
    cursor = utilities.get_cursor()
    sql = """
        SELECT ProbeSetFreeze.`Id`, ProbeSetFreeze.`Name`, ProbeSetFreeze.`FullName`
        FROM ProbeSetFreeze
        WHERE ProbeSetFreeze.`Id`=%s
        """
    cursor.execute(sql, (probesetfreezeid))
    return cursor.fetchone()
    
def get_strains(inbredsetid):
    cursor = utilities.get_cursor()
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
    cursor = utilities.get_cursor()
    sql = """
        SELECT InbredSet.`Id`, InbredSet.`Name`, InbredSet.`FullName`
        FROM InbredSet, ProbeFreeze, ProbeSetFreeze
        WHERE InbredSet.`Id`=ProbeFreeze.`InbredSetId`
        AND ProbeFreeze.`Id`=ProbeSetFreeze.`ProbeFreezeId`
        AND ProbeSetFreeze.`Id`=%s
        """
    cursor.execute(sql, (probesetfreezeid))
    return cursor.fetchone()
