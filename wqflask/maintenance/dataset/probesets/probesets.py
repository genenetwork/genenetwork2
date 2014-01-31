import sys
sys.path.append('.')
sys.path.append('..')

from utilities import db

def fetch_probesetxref(probesetfreezeid):
    cursor = db.get_cursor()
    sql = """
        SELECT ProbeSetXRef.`ProbeSetId`, ProbeSetXRef.`DataId`
        FROM ProbeSetXRef
        WHERE ProbeSetXRef.`ProbeSetFreezeId`=%s
        """
    cursor.execute(sql, (probesetfreezeid))
    return cursor.fetchall()
    
def fetch_probeset(probesetid):
    cursor = db.get_cursor()
    sql = """
        SELECT *
        FROM ProbeSet
        WHERE ProbeSet.`Id`=%s
        """
    cursor.execute(sql, (probesetid))
    return cursor.fetchone()
    
def fetch_probesetdata(probesetdataid):
    cursor = db.get_cursor()
    sql = """
        SELECT Strain.`Id`, Strain.`Name`, ProbeSetData.`value`
        FROM ProbeSetData, Strain
        WHERE ProbeSetData.`Id`=%s
        AND ProbeSetData.`StrainId`=Strain.`Id`;
        """
    cursor.execute(sql, (probesetdataid))
    return cursor.fetchall()

results = fetch_probesetxref(112)
for row in results:
    print row
    probesetid = row[0]
    probesetdataid = row[1]
    print fetch_probeset(probesetid)
    print fetch_probesetdata(probesetdataid)
    break