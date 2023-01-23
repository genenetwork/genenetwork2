from urllib.parse import urlparse
import pymysql as mdb
import os
import csv


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

    # fi parents included?????
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


def get_probesetfreeze(conn, probes):

    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.FullName "
            "FROM ProbeSetFreeze "
            "WHERE ProbeSetFreeze.Id=%s",
            (probes,)
        )
        return cursor.fetchone()


 def query_for_last_modification():

 	pass
 	"""

SELECT database_name,table_name,last_update FROM
  mysql.innodb_table_stats a,
  (SELECT database_name AS db_last_update_name,
       max(last_update) AS db_last_update 
   FROM mysql.innodb_table_stats 
   WHERE database_name  in ( "db_webqtl")
   GROUP BY database_name )  AS b 
WHERE a.database_name = b.db_last_update_name

  AND a.last_update = b.db_last_update ;

"""
 

 # todo file_storage lmdb  file_parsing file_run




def parse_dataset(results):
	ids = ["ID"]
	data = {}
	for (trait, strain,val) in results:
		if strain  not in ids:
			ids.append(strain)

		if trait in data:
			data[trait].append(val)
		else:
			data[trait] = [trait,val]

	return (data,ids)

# above refactor the code

def generate_csv_file(conn,db_name,txt_dir,file_name):

    # write to file

     # file name ,file expiry,type of storage  

     # I want to use lmdb to store the files
     # file name already done  #import that

     # file expiry to be done lt
  
    try:
        (data,col_ids) = parse_dataset(fetch_probeset_data(conn,db_name))
        with open( os.path.join(txt_dir,file_name),"w+" ,encoding='UTF8') as file_handler:
            writer = csv.writer(file_handler)
            writer.writerow(col_ids) # write header s
            writer.writerows(val for val in data.values() )
            return "success"

    except Exception as e:
        raise e



def lmdb_file_generator():
	pass 



""""
import  lmdb
import os
import tempfile
with tempfile.TemporaryDirectory() as tmpdirname:

    tmp_file_path = os.path.join(tmpdirname,"img_lmdb")
    breakpoint()
    db = lmdb.open(tmp_file_path, map_size=int(1e12))

    with db.begin(write=True) as in_txn:
       

    db.close()

"""
