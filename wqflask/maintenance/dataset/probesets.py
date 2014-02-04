import sys

import utilities

def get_probesetxref(probesetfreezeid):
    cursor = utilities.get_cursor()
    sql = """
        SELECT ProbeSetXRef.`ProbeSetId`, ProbeSetXRef.`DataId`
        FROM ProbeSetXRef
        WHERE ProbeSetXRef.`ProbeSetFreezeId`=%s
        """
    cursor.execute(sql, (probesetfreezeid))
    return cursor.fetchall()
    
def get_probeset(probesetid):
    cursor = utilities.get_cursor()
    sql = """
        SELECT *
        FROM ProbeSet
        WHERE ProbeSet.`Id`=%s
        """
    cursor.execute(sql, (probesetid))
    return cursor.fetchone()
    
def get_probesetdata(probesetdataid):
    cursor = utilities.get_cursor()
    sql = """
        SELECT Strain.`Id`, Strain.`Name`, ProbeSetData.`value`
        FROM ProbeSetData, Strain
        WHERE ProbeSetData.`Id`=%s
        AND ProbeSetData.`StrainId`=Strain.`Id`;
        """
    cursor.execute(sql, (probesetdataid))
    return cursor.fetchall()

def get_probesetxref_probesetfreezeid(locus, probesetfreezeid):
    cursor = utilities.get_cursor()
    sql = """
        SELECT ProbeSetXRef.`ProbeSetId`
        FROM ProbeSetXRef
        WHERE ProbeSetXRef.`ProbeSetFreezeId`=%s
        AND ProbeSetXRef.`Locus` LIKE %s
        """
    cursor.execute(sql, (probesetfreezeid, locus))
    return cursor.fetchall()
    
def get_probesetxref_inbredsetid(locus, inbredsetid):
    cursor = utilities.get_cursor()
    sql = """
        SELECT ProbeSetXRef.`ProbeSetId`
        FROM (ProbeSetXRef, ProbeSetFreeze, ProbeFreeze)
        WHERE ProbeSetXRef.`ProbeSetFreezeId`=ProbeSetFreeze.`Id`
        AND ProbeSetFreeze.`ProbeFreezeId`=ProbeFreeze.`Id`
        AND ProbeFreeze.`InbredSetId`=%s
        AND ProbeSetXRef.`Locus` LIKE %s
        """
    cursor.execute(sql, (inbredsetid, locus))
    return cursor.fetchall()

print get_probesetxref_inbredsetid(locus="rs3663871", inbredsetid=1)