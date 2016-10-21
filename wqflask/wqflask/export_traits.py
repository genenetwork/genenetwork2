from __future__ import print_function, division

import operator
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
    
    metadata = []

    metadata.append(["Citations: Please see www.genenetwork.org/reference.html"])
    if targs['database_name'] != "None":
        metadata.append(["Database: " + targs['database_name']])
    metadata.append(["Date: " + datetime.datetime.now().strftime("%B %d, %Y")])
    metadata.append(["Time: " + datetime.datetime.now().strftime("%H:%M GMT")])
    metadata.append(["Status of data ownership: Possibly unpublished data; please see www.genenetwork.org/statusandContact.html for details on sources, ownership, and usage of these data."])

    for metadata_row in metadata:
        writer.writerow(metadata_row)

    writer.writerow(table_headers)
    for trait_info in table_rows:
        writer.writerow(trait_info)

    csv_data = buff.getvalue()
    buff.close()

    return csv_data