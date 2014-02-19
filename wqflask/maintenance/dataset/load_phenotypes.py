import sys
import csv

import utilities

def main(argv):
    # config
    config = utilities.get_config(argv[1])
    print "config:"
    for item in config.items('config'):
        print "\t%s" % (str(item))
    #
    inbredsetid = config.get('config', 'inbredsetid')
    print "inbredsetid: %s" % inbredsetid
    # datafile
    datafile = open(config.get('config', 'datafile'), 'r')
    phenotypedata = csv.reader(datafile, delimiter='\t', quotechar='"')
    phenotypedata_head = phenotypedata.next()
    print "phenotypedata head:\n\t%s" % phenotypedata_head
    # metafile
    metafile = open(config.get('config', 'metafile'), 'r')
    phenotypemeta = csv.reader(metafile, delimiter='\t', quotechar='"')
    phenotypemeta_head = phenotypemeta.next()
    print "phenotypemeta head:\n\t%s" % phenotypemeta_head
    #
        
if __name__ == "__main__":
    print "command line arguments:\n\t%s" % sys.argv
    main(sys.argv)
    print "exit successfully"
