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
        SELECT ProbeSet.`Id`, ProbeSet.`Name`, ProbeSet.`Symbol`, ProbeSet.`description`, ProbeSet.`Probe_Target_Description`, ProbeSet.`Chr`, ProbeSet.`Mb`
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

def get_normalized_probeset(locus, inbredsetid):
    normalized_probesets = []
    probesetxrefs = get_probesetxref_inbredsetid(locus, inbredsetid)
    for probesetxref in probesetxrefs:
        normalized_probeset = []
        probesetid = probesetxref[0]
        probeset = get_probeset(probesetid)
        normalized_probeset.append(probeset)
        normalized_probesets.append(normalized_probeset)
    print normalized_probesets

get_normalized_probeset(locus="rs3663871", inbredsetid=1)
