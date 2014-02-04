import utilities

def get_geno(inbredsetid, name):
    cursor = utilities.get_cursor()
    sql = """
        SELECT Geno.`Id`, Geno.`Name`, Geno.`Chr`, Geno.`Mb`
        FROM (Geno, InbredSet)
        WHERE Geno.`SpeciesId`=InbredSet.`SpeciesId`
        AND InbredSet.`Id`=%s
        AND Geno.`Name` LIKE %s
        """
    cursor.execute(sql, (inbredsetid, name))
    return cursor.fetchone()
