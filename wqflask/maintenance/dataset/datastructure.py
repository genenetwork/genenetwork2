import utilities

def get_probesetfreeze(inbredsetid):
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
    