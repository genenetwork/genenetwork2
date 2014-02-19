import sys
import csv

import utilities

def main(argv):
    #
    config = utilities.get_config(argv[1])
    print "config:"
    for item in config.items('config'):
        print "\t%s" % (str(item))
    #
    datafile = open(config.get('config', 'datafile'), 'r')
    phenotypedata = csv.reader(datafile, delimiter='\t', quotechar='"')
    for row in phenotypedata:
        #print row
        pass
    #
    metafile = open(config.get('config', 'metafile'), 'r')
    phenotypemeta = csv.reader(metafile, delimiter='\t', quotechar='"')
    for row in phenotypemeta:
        print row[1]
        
if __name__ == "__main__":
    print "command line arguments:\n\t%s" % sys.argv
    main(sys.argv)
    print "exit successfully"
