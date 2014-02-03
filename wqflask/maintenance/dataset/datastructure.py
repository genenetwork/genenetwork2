import sys
sys.path.append('.')
sys.path.append('..')

from utilities import db

def get_probesetfreeze(inbredsetid):
    cursor = db.get_cursor()
    sql = """
        SELECT ProbeSetFreeze.`Id`, ProbeSetFreeze.`Name`, ProbeSetFreeze.`FullName`
        FROM ProbeSetFreeze, ProbeFreeze
        WHERE ProbeSetFreeze.`ProbeFreezeId`=ProbeFreeze.`Id`
        AND ProbeFreeze.`InbredSetId`=%s
        """
    cursor.execute(sql, (inbredsetid))
    return cursor.fetchall()
    