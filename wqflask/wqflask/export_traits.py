from __future__ import print_function, division

import operator
import csv
import xlsxwriter
import StringIO 

import simplejson as json

from pprint import pformat as pf

def export_search_results_csv(targs):

    table_data = json.loads(targs['export_data'])
    table_headers = table_data['headers']
    table_rows = table_data['rows']
    
    buff = StringIO.StringIO()
    writer = csv.writer(buff)
    
    writer.writerow(table_headers)
    for trait_info in table_rows:
        writer.writerow(trait_info)
        
    csv_data = buff.getvalue()
    buff.close()

    return csv_data