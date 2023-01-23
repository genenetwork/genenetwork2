def get_probesetfreezes(conn, inbredsetid=1):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.FullName "
            "FROM ProbeSetFreeze, ProbeFreeze "
            "WHERE ProbeSetFreeze.ProbeFreezeId=ProbeFreeze.Id "
            "AND ProbeFreeze.InbredSetId=%s",
            (inbredsetid,)
        )

        return cursor.fetchall()


def get_strains(conn, inbredsetid=1):

    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT Strain.Id, Strain.Name "
            "FROM StrainXRef, Strain "
            "WHERE StrainXRef.InbredSetId=%s "
            "AND StrainXRef.StrainId=Strain.Id "
            "ORDER BY StrainXRef.OrderId",
            (inbredsetid)
        )

        return cursor.fetchall()

def fetch_datasets(conn):

	#fi parents included?????
	with conn.cursor() as cursor:
	    cursor.execute(
	        "SELECT ProbeSet.Name, Strain.Name, ProbeSetData.value "
	        "FROM Strain LEFT JOIN ProbeSetData "
	        "ON Strain.Id = ProbeSetData.StrainId "
	        "LEFT JOIN ProbeSetXRef ON ProbeSetData.Id = ProbeSetXRef.DataId "
	        "LEFT JOIN ProbeSet ON ProbeSetXRef.ProbeSetId = ProbeSet.Id "
	        "WHERE ProbeSetXRef.ProbeSetFreezeId IN "
	        "(SELECT Id FROM ProbeSetFreeze WHERE Name = %s) "
	        "ORDER BY Strain.Name",
	        (db_name,))
	    return cursor.fetchall()
