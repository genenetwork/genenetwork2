# Author:               Lei Yan
# Create Date:          2014-01-21
# Last Update Date:     2014-01-24

# import
import sys
import os
import re
import MySQLdb
import ConfigParser

def main(argv):

    # load configuration from configuration file
    config = ConfigParser.ConfigParser()
    config.read(argv[1])
    genofile = config.get('configuration', 'genofile')

    # parse genofile
    genotypes = []
    file_geno = open(genofile, 'r')
    for line in file_geno:
        line = line.strip()
        if line.startswith('#'):
            continue
        if line.startswith('@'):
            continue
        cells = line.split()
        if line.startswith("Chr"):
            strains = cells[4:]
            continue
        genotype = {}
        genotype['chr'] = cells[0]
        genotype['locus'] = cells[1]
        genotype['cm'] = cells[2]
        genotype['mb'] = cells[3]
        genotype['values'] = cells[4:]
        genotypes.append(genotype)
    print "get %d strains:\t%s" % (len(strains), strains)
    print "load %d genotypes" % len(genotypes)

    # phenotypes

# main
if __name__ == "__main__":
    main(sys.argv)
    print "exit successfully"
