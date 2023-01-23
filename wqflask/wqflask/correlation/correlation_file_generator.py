def get_probesetfreezes(conn,inbredsetid=1):


	with conn.cursor() as cursor:
		cursor.execute(
			"SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.FullName "
    		"FROM ProbeSetFreeze, ProbeFreeze "
    		"WHERE ProbeSetFreeze.ProbeFreezeId=ProbeFreeze.Id "
    		"AND ProbeFreeze.InbredSetId=%s",
    		(inbredsetid,)
			)

		return  cursor.fetchall() 
