# This is the LMM runner that calls the possible methods using command line
# switches. It acts as a multiplexer where all the invocation complexity
# is kept outside the main LMM routines.
#
# Copyright (C) 2015  Pjotr Prins (pjotr.prins@thebird.nl)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from optparse import OptionParser
import sys
import tsvreader
import numpy as np
from lmm import gn2_load_redis, calculate_kinship_new
from kinship import kinship, kinship_full
import genotype
import phenotype
from standalone import uses

usage = """
python runlmm.py [options] command

  runlmm.py processing multiplexer reads standardised input formats
  and calls the different routines (writes to stdout)

  Current commands are:

    parse        : only parse input files
    redis        : use Redis to call into GN2
    kinship      : calculate (new) kinship matrix

  try --help for more information
"""


parser = OptionParser(usage=usage)
# parser.add_option("-f", "--file", dest="input file",
#                   help="In", metavar="FILE")
parser.add_option("--kinship",dest="kinship",
                  help="Kinship file format 1.0")
parser.add_option("--pheno",dest="pheno",
                  help="Phenotype file format 1.0")
parser.add_option("--geno",dest="geno",
                  help="Genotype file format 1.0")
parser.add_option("--maf-normalization",
                  action="store_true", dest="maf_normalization", default=False,
                  help="Apply MAF genotype normalization")
parser.add_option("--genotype-normalization",
                  action="store_true", dest="genotype_normalization", default=False,
                  help="Force genotype normalization")
parser.add_option("--remove-missing-phenotypes",
                  action="store_true", dest="remove_missing_phenotypes", default=False,
                  help="Remove missing phenotypes")
parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")
parser.add_option("--blas", action="store_true", default=False, dest="useBLAS", help="Use BLAS instead of numpy matrix multiplication")
parser.add_option("-t", "--threads",
                  type="int", dest="numThreads", 
                  help="Threads to use")
parser.add_option("--saveKvaKve",
                  action="store_true", dest="saveKvaKve", default=False,
                  help="Testing mode")
parser.add_option("--test",
                  action="store_true", dest="testing", default=False,
                  help="Testing mode")
parser.add_option("--test-kinship",
                  action="store_true", dest="test_kinship", default=False,
                  help="Testing mode for Kinship calculation")

(options, args) = parser.parse_args()

if len(args) != 1:
    print usage
    sys.exit(1)

cmd = args[0]
print "Command: ",cmd

k = None
y = None
g = None

if options.kinship:
    k = tsvreader.kinship(options.kinship)
    print k.shape

if options.pheno:
    y = tsvreader.pheno(options.pheno)
    print y.shape

if options.geno and cmd != 'iterator':
    g = tsvreader.geno(options.geno)
    print g.shape

if cmd == 'iterator':
    def snp_iterator(func):
        tsvreader.geno_iter(options.geno,func)
        
    if options.remove_missing_phenotypes:
        raise Exception('Can not use --remove-missing-phenotypes with LMM2')
    ps, ts = gn2_iter_redis('testrun_iter','other',k,y,snp_iterator)
    print np.array(ps)
    print len(ps),sum(ps)
    # Test results
    p1 = round(ps[0],4)
    p2 = round(ps[-1],4)
elif cmd == 'redis_new':
    # The main difference between redis_new and redis is that missing
    # phenotypes are handled by the first
    if options.remove_missing_phenotypes:
        raise Exception('Can not use --remove-missing-phenotypes with LMM2')
    Y = y
    G = g
    print "Original G",G.shape, "\n", G

    gt = G.T
    G = None
    ps, ts = gn2_load_redis('testrun','other',k,Y,gt,new_code=True)
    print np.array(ps)
    print len(ps),sum(ps)
    # Test results
    p1 = round(ps[0],4)
    p2 = round(ps[-1],4)
    sys.stderr.write(options.geno+"\n")
    if options.geno == 'data/small.geno':
        assert p1==0.0708, "p1=%f" % p1
        assert p2==0.1417, "p2=%f" % p2
    if options.geno == 'data/small_na.geno':
        assert p1==0.0897, "p1=%f" % p1
        assert p2==0.0405, "p2=%f" % p2
    if options.geno == 'data/test8000.geno':
        # assert p1==0.8984, "p1=%f" % p1
        # assert p2==0.9621, "p2=%f" % p2
        assert round(sum(ps)) == 4070
        assert len(ps) == 8000
elif cmd == 'redis':
    # Emulating the redis setup of GN2
    G = g
    print "Original G",G.shape, "\n", G
    if y is not None and options.remove_missing_phenotypes:
        gnt = np.array(g).T
        Y,g,keep = phenotype.remove_missing(y,g.T,options.verbose)
        G = g.T
        print "Removed missing phenotypes",G.shape, "\n", G
    else:
        Y = y
    if options.maf_normalization:
        G = np.apply_along_axis( genotype.replace_missing_with_MAF, axis=0, arr=g )
        print "MAF replacements: \n",G
    if options.genotype_normalization:
        G = np.apply_along_axis( genotype.normalize, axis=1, arr=G)
    g = None
    gnt = None

    gt = G.T
    G = None
    ps, ts = gn2_load_redis('testrun','other',k,Y,gt, new_code=False)
    print np.array(ps)
    print len(ps),sum(ps)
    # Test results 4070.02346579
    p1 = round(ps[0],4)
    p2 = round(ps[-1],4)
    sys.stderr.write(options.geno+"\n")
    if options.geno == 'data/small.geno':
        assert p1==0.0708, "p1=%f" % p1
        assert p2==0.1417, "p2=%f" % p2
    if options.geno == 'data/small_na.geno':
        assert p1==0.0897, "p1=%f" % p1
        assert p2==0.0405, "p2=%f" % p2
    if options.geno == 'data/test8000.geno':
        assert int(sum(ps)) == 4070
        assert len(ps) == 8000
elif cmd == 'kinship':
    G = g
    print "Original G",G.shape, "\n", G
    if y != None and options.remove_missing_phenotypes:
        gnt = np.array(g).T
        Y,g = phenotype.remove_missing(y,g.T,options.verbose)
        G = g.T
        print "Removed missing phenotypes",G.shape, "\n", G
    if options.maf_normalization:
        G = np.apply_along_axis( genotype.replace_missing_with_MAF, axis=0, arr=g )
        print "MAF replacements: \n",G
    if options.genotype_normalization:
        G = np.apply_along_axis( genotype.normalize, axis=1, arr=G)
    g = None
    gnt = None

    if options.test_kinship:
        K = kinship_full(np.copy(G),uses)
        print "Genotype",G.shape, "\n", G
        print "first Kinship method",K.shape,"\n",K
        k1 = round(K[0][0],4)
        K2,G = calculate_kinship_new(np.copy(G).T,temp_data=None)
        print "Genotype",G.shape, "\n", G
        print "GN2 Kinship method",K2.shape,"\n",K2
        k2 = round(K2[0][0],4)
    
    print "Genotype",G.shape, "\n", G
    K3 = kinship(G.T,uses)
    print "third Kinship method",K3.shape,"\n",K3
    sys.stderr.write(options.geno+"\n")
    k3 = round(K3[0][0],4)
    if options.geno == 'data/small.geno':
        assert k1==0.8, "k1=%f" % k1
        assert k2==0.7939, "k2=%f" % k2
        assert k3==0.7939, "k3=%f" % k3
    if options.geno == 'data/small_na.geno':
        assert k1==0.8333, "k1=%f" % k1
        assert k2==0.7172, "k2=%f" % k2
        assert k3==0.7172, "k3=%f" % k3
    if options.geno == 'data/test8000.geno':
        assert k3==1.4352, "k3=%f" % k3

else:
    print "Doing nothing"
