import sys

import utilities
import genotypes

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
        SELECT ProbeSetXRef.`ProbeSetId`, ProbeSetXRef.`mean`, ProbeSetXRef.`LRS`, ProbeSetXRef.`Locus`
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
        normalized_probeset.append(probeset[1])
        normalized_probeset.append(probeset[2])
        normalized_probeset.append(probeset[3])
        normalized_probeset.append(probeset[4])
        normalized_probeset.append(probeset[5])
        normalized_probeset.append(probeset[6])
        normalized_probeset.append(probesetxref[1])
        normalized_probeset.append(probesetxref[2])
        locus = probesetxref[3]
        geno = genotypes.get_geno(inbredsetid=inbredsetid, name=locus)
        normalized_probeset.append(geno[2])
        normalized_probeset.append(geno[3])
        normalized_probesets.append(normalized_probeset)
    print normalized_probesets[:2]

get_normalized_probeset(locus="rs3663871", inbredsetid=1)
