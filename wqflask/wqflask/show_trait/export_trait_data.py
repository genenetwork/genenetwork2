from __future__ import print_function, division

import simplejson as json

#import xlwt
from pprint import pformat as pf

def export_sample_table(targs):
    #print("* keys0 args is:", targs[0].keys())
    
    
    test_export_file = open("/home/zas1024/gene/wqflask/wqflask/show_trait/export_test.txt", "w")
    
    for key, item in targs.iteritems():
        print("[arrow] key is:", key)
    
    sample_data = json.loads(targs['json_data'])
    
    print("primary_samples is:", pf(sample_data['primary_samples']))
     
    for key in sample_data['primary_samples'][0]:
        test_export_file.write(key + ",")
    test_export_file.write("\n")