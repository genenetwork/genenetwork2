# !/usr/bin/python3
"""This script use the nearest marker to the transcript as control, increasing permutation rounds according to the p-value"""

########################################################################
# Last Updated 3/11/2022 by Zach
########################################################################
import csv
import string
import sys
import MySQLdb
import getpass
import time

########################################################################

def translate_alias(str):
    if str == "B6":
        return "C57BL/6J"
    elif str == "D2":
        return "DBA/2J"
    else:
        return str


########################################################################
#
#  Indicate Data Start Position, ProbeFreezeId, gene_chip_id, DataFile
#
########################################################################

data_start = 1

gene_chip_id = int(input("Enter GeneChipId:"))
probeset_freeze_id = int(input("Enter ProbeSetFreezeId:"))
input_file_name = input("Enter file name with suffix:")

try:
    passwd = getpass.getpass('Please enter mysql password here : ')
    conn = MySQLdb.Connect(db='db_webqtl', host='localhost', user='webqtlout', passwd=passwd)

    db = conn.cursor()

    print
    "You have successfully connected to mysql.\n"
except:
    print
    "You entered incorrect password.\n"
    sys.exit(0)

time0 = time.time()

#########################################################################
#
#  Check if each line have same number of members
#  generate the gene list of expression data here
#
#########################################################################
print
'Checking if each line have same number of members'

gene_list = []
strain_list = []
trait_data = []

with open(input_file_name, "r") as csvfile:
    reader = csv.DictReader(csvfile, delimiter="\t")
    
    kj = 0
    for line in reader:
        trait_data.append(line)

        # Get the strain list; only need to get it once
        if kj == 0:
            strain_list = [item for item in line.keys() if item != "ProbeSetID"]
            print("STRAIN LIST:", strain_list)

        gene_list.append(line['ProbeSetID'])

        if kj % 100000 == 0:
            print(f"checked {kj} lines")
        kj += 1

gene_list.sort()

print(f"used {time.time() - time0} seconds")
#########################################################################
#
#  Check if each strain exist in database
#  generate the string id list of expression data here
#
#########################################################################
print('Checking if each strain exists in database')

strain_list = map(translate_alias, strain_list)

strain_ids = {}
for item in strain_list:
    try:
        db.execute(f'select Id from Strain where Name = "{item}" AND SpeciesId=1')
        strain_ids[item] = db.fetchone()[0]
    except:
        print(f"{item} does not exist, check the if the strain name is correct")
        sys.exit(0)

print(f"Used {time.time() - time0} seconds")

########################################################################
#
# Check if each ProbeSet exist in database
#
########################################################################
print("Check if each ProbeSet exists in database")


# Check whether ProbeSetIDs are Name or TargetId (if not Name, assume to be TargetId)
id_type = "TargetId"
db.execute(f"select Id from ProbeSet where Name='{gene_list[0]}' and ChipId={gene_chip_id}")
if len(db.fetchall()):
    id_type = "Name"

## Get Name/TargetId + ID list from database
db.execute(f"select {id_type}, Id from ProbeSet where ChipId={gene_chip_id} order by {id_type}")
records_from_db = db.fetchall()

record_names = [item[0] for item in records_from_db]
record_names.sort()

# Compare gene_list with gene_names
invalid_records = []
lowercase_records = [name2.lower() for name2 in record_names]
for name in gene_list:
    if name.lower() not in lowercase_records:
        invalid_records.append(name)

if len(invalid_records):
    with open("ProbeSetError.txt", "wb") as error_fh:
        for item in invalid_records:
            error_fh.write(f"{item} doesn't exist, cheeck if the ProbeSet name is correct \n")
    sys.exit(0)

print(f"used {time.time() - time0} seconds")
#########################################################################
#
# Insert data into database
#
#########################################################################
print("getting ProbeSet Name + Id")
record_ids = {}
for record in records_from_db:
    record_ids[record[0]] = record[1]

print(f"used {time.time() - time0} seconds")

print("inserting data")

# Get old max dataId
db.execute('select max(Id) from ProbeSetData')
latest_data_id = int(db.fetchone()[0])
print(f"Latest DataId = {latest_data_id}")

# Insert data
probeset_data_values = []
probeset_xref_values = []
for i, item in enumerate(trait_data):
    latest_data_id += 1


    probeset_id = item['ProbeSetID']
    item.pop('ProbeSetID')
    sample_data = item
    for strain in sample_data:
        probeset_data_values.append(f"({latest_data_id},{strain_ids[strain]},{float(sample_data[strain])})")

    probeset_xref_values.append(f"({probeset_freeze_id},{record_ids[probeset_id]},{latest_data_id})")

    # Insert into tables for every 100 traits
    if i % 100 == 0:
        data_query = f"INSERT INTO ProbeSetData VALUES {','.join(probeset_data_values)}"
        db.execute(data_query)

        xref_query = (
            "INSERT INTO ProbeSetXRef(ProbeSetFreezeId, ProbeSetId, DataId) "
            f"VALUES {','.join(probeset_xref_values)}")
        db.execute(xref_query)

        probeset_data_values = []
        probeset_xref_values = []

        print(f"Inserted {i} lines")
        print(f"Used {time.time() - time0} seconds")

# Insert the remainder (since the loop above only inserts every 100 traits)
if len(probeset_data_values):
    data_query = f"INSERT INTO ProbeSetData VALUES {','.join(probeset_data_values)}"
    db.execute(data_query)

    xref_query = (
        "INSERT INTO ProbeSetXRef(ProbeSetFreezeId, ProbeSetId, DataId) "
        f"VALUES {','.join(probeset_xref_values)}")
    db.execute(xref_query)

conn.commit()
conn.close()
