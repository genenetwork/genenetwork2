import sys
import csv

import utilities
import datastructure
import genotypes

def main(argv):
    # config
    config = utilities.get_config(argv[1])
    print "config:"
    for item in config.items('config'):
        print "\t%s" % (str(item))
    # var
    print "variable:"
    inbredsetid = config.get('config', 'inbredsetid')
    print "\tinbredsetid: %s" % inbredsetid
    # datafile
    datafile = open(config.get('config', 'datafile'), 'r')
    datafile = csv.reader(datafile, delimiter='\t', quotechar='"')
    datafile.next()
    delrowcount = 0
    for row in datafile:
        if len(row) == 0:
            continue
        genoname = row[0]
        delrowcount += genotypes.delete(genoname, inbredsetid)
    print "deleted %d genotypes" % (delrowcount)

if __name__ == "__main__":
    print "command line arguments:\n\t%s" % sys.argv
    main(sys.argv)
    print "exit successfully"
