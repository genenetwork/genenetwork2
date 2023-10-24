import os
from typing import Tuple
from urllib.parse import urlparse
import MySQLdb as mdb
from MySQLdb.cursors import DictCursor

def parse_db_url(sql_uri: str) -> Tuple:
    """function to parse SQL_URI"""
    parsed_db = urlparse(sql_uri)
    return (
        parsed_db.hostname, parsed_db.username, parsed_db.password,
        parsed_db.path[1:], parsed_db.port)

sql_uri = os.environ.get("SQL_URI")
host, user, passwd, db_name, port = parse_db_url(sql_uri)
conn = mdb.connect(db=db_name,
                   user=user,
                   passwd=passwd,
                   host=host,
                   port=port)

query = (
    "SELECT psf.Id, psf.FullName "
    "FROM ProbeSetXRef AS psx "
    "INNER JOIN ProbeSetFreeze AS psf ON psx.ProbeSetFreezeId = psf.Id "
    "INNER JOIN ProbeFreeze AS pf ON psf.ProbeFreezeId = pf.Id "
    "INNER JOIN InbredSet AS ibs ON pf.InbredSetId = ibs.Id "
    "WHERE psx.Locus IS NULL AND "
    "ibs.MappingMethodId = 1"
)

dataset_NAs_counts = {}
dataset_name_dict = {} # Mapping of IDs to names
with conn.cursor(cursorclass=DictCursor) as cursor:
    cursor.execute(query)
    for row in cursor.fetchall():
        dset_id = str(row['Id'])
        if dset_id in dataset_NAs_counts:
            dataset_NAs_counts[dset_id] += 1
        else:
            dataset_NAs_counts[dset_id] = 1
        if dset_id not in dataset_name_dict:
            dataset_name_dict[dset_id] = str(row['FullName'])

sorted_NAs_counts = {k: v for k, v in sorted(dataset_NAs_counts.items(), key=lambda item: item[1], reverse=True)}

output_path = os.path.join(os.environ.get("TMPDIR"), "filtered_NAs_list.csv")
with open(output_path, "w") as out_file:
    out_file.write("ID\tFullName\tCount\n")
    for dset_id in sorted_NAs_counts:
        out_file.write("\t".join([str(dset_id), str(dataset_name_dict[dset_id]), str(sorted_NAs_counts[dset_id])]) + "\n")


        