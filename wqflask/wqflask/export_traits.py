from __future__ import print_function, division

import csv
import xlsxwriter
import StringIO 
import datetime

import simplejson as json

from pprint import pformat as pf

def export_search_results_csv(targs):

    table_data = json.loads(targs['export_data'])
    table_headers = table_data['headers']
    table_rows = table_data['rows']
    
    buff = StringIO.StringIO()
    writer = csv.writer(buff)
    
    if 'file_name' in targs:
        file_name = targs['file_name']
    else:
        file_name = "table_export.csv"

    metadata = []

    if 'database_name' in targs:
        if targs['database_name'] != "None":
            metadata.append(["Data Set: " + targs['database_name']])
    if 'accession_id' in targs:
        if targs['accession_id'] != "None":
            metadata.append(["Metadata Link: http://genenetwork.org/webqtl/main.py?FormID=sharinginfo&GN_AccessionId=" + targs['accession_id']])
    metadata.append(["Export Date: " + datetime.datetime.now().strftime("%B %d, %Y")])
    metadata.append(["Export Time: " + datetime.datetime.now().strftime("%H:%M GMT")])
    if 'search_string' in targs:
        if targs['search_string'] != "None":
            metadata.append(["Search Query: " + targs['search_string']])
    if 'filter_term' in targs:
        if targs['filter_term'] != "None":
            metadata.append(["Search Filter Terms: " + targs['filter_term']])
    metadata.append(["Exported Row Number: " + str(len(table_rows))])

    for metadata_row in metadata:
        writer.writerow(metadata_row)

    writer.writerow([])

    writer.writerow(table_headers)
    for trait_info in table_rows:
        writer.writerow(trait_info)

    writer.writerow([])
    writer.writerow(["Funding for The GeneNetwork: NIAAA (U01AA13499, U24AA13513), NIDA, NIMH, and NIAAA (P20-DA21131), NCI MMHCC (U01CA105417), and NCRR (U01NR 105417)"])
    csv_data = buff.getvalue()
    buff.close()

    return csv_data, file_name