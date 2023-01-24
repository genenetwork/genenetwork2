from urllib.parse import urlparse
import pymysql as mdb
import os
import csv
import  lmdb
import os
import tempfile
import numpy as np 
from io import  BytesIO



def parse_db_url():
    """function to parse SQL_URI env variable note:there\
    is a default value for SQL_URI so a tuple result is\
    always expected"""
    parsed_db = urlparse(SQL_URI)


    return (
        parsed_db.hostname, parsed_db.username, parsed_db.password,
        parsed_db.path[1:], 3306)


# This function is deprecated. Use database_connection instead.
def database_connector():
    """function to create db connector"""
    host, user, passwd, db_name, db_port = parse_db_url()
    return mdb.connect(host=host,user=user,password=passwd,database=db_name)


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




def array_to_bytes(x:np.ndarray) -> bytes:
    np_bytes = BytesIO()

    np.save(np_bytes,x,allow_pickle =True)
    return (np_bytes.getvalue())




def bytes_to_array(b: bytes) -> np.ndarray:
    np_bytes = BytesIO(b)
    return np.load(np_bytes, allow_pickle=True)


def lmdb_file_generator(file_name,data:np.ndarray):

    #create unique filename

    # pass


def create_dataset(file_name, db_name, dataset: np.ndarray):

    # map size int(ie12)
    with lmdb.open(file_name, map_size=(dataset.nbytes*10)) as env:
        with env.begin(write=True) as txn:
            txn.put(db_name.encode(), array_to_bytes(dataset))

            return (file_name, db_name)


def read_dataset(file_name, db_name):
    with lmdb.open(file_name, readonly=True, create=False) as env:
        with env.begin() as txn:
            ndaray_bytes = txn.get(db_name.encode())
            # error handling
            return bytes_to_array(ndaray_bytes)


#simple lmdb file