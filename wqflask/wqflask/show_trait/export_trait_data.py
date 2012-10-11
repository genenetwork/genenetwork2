from __future__ import print_function, division

import simplejson as json

#import xlwt
from pprint import pformat as pf

def export_sample_table(targs):
    #print("* keys0 args is:", targs[0].keys())
    
    for key, item in targs.iteritems():
        print("[arrow] key is:", key)
    
    sample_data = json.loads(targs['json_data'])
    print("sample_data is:", pf(sample_data))