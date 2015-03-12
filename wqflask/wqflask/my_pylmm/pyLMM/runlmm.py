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
from lmm import gn2_load_redis
from kinship import kinship

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

if options.geno:
    g = tsvreader.geno(options.geno)
    print g.shape
    
def normalizeGenotype(G):
    # Run for every SNP list (num individuals)
    x = True - np.isnan(G)  # Matrix of True/False
    m = G[x].mean()         # Global mean value
    # print m
    s = np.sqrt(G[x].var()) # Global stddev
    # print s
    G[np.isnan(G)] = m      # Plug-in mean values for missing
    if s == 0:
        G = G - m           # Subtract the mean
    else:
        G = (G - m) / s     # Normalize the deviation
    return G

gn = []
for snp in g:
    gn.append( normalizeGenotype(snp) )

gn = g

print("Before",g)

gT = g.T
print("After",gT)
G = np.array(gT)
print "G shape",G.shape

# Remove individuals with missing phenotypes
if y != None:
    v = np.isnan(y)
    keep = True - v
    if v.sum():
       if options.verbose: sys.stderr.write("runlmm.py: Cleaning the phenotype vector by removing %d individuals...\n" % (v.sum()))
       y = y[keep]
       G = G[keep,:]
       if k != None: k = k[keep,:][:,keep]

if cmd == 'redis':
    print G
    ps, ts = gn2_load_redis('testrun','other',np.array(k),y,G,options.testing)
    print np.array(ps)
elif cmd == 'kinship':
    gn = []
    for snp in G.T:
        gn.append( normalizeGenotype(snp) )
    G2 = np.array(gn)
    print G2.shape,G2
    K = kinship(G2,options)
else:
    print "Doing nothing"
