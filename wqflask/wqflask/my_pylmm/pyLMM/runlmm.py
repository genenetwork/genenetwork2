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

usage = """
python runlmm.py [options] command

  runlmm.py processing multiplexer reads standardised input formats
  and calls the different routines

  Current commands are:

    parse        : only parse input files
    redis        : use Redis to call into GN2

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

(options, args) = parser.parse_args()

if len(args) != 1:
    print usage
    sys.exit(1)

cmd = args[0]
print "Command: ",cmd

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
    x = True - np.isnan(G)
    m = G[x].mean()
    s = np.sqrt(G[x].var())
    G[np.isnan(G)] = m
    if s == 0: G = G - m
    else: G = (G - m) / s
    return G

gT = normalizeGenotype(g.T)

# Remove individuals with missing phenotypes
v = np.isnan(y)
keep = True - v
if v.sum():
   if options.verbose: sys.stderr.write("Cleaning the phenotype vector by removing %d individuals...\n" % (v.sum()))
   y  = y[keep]
   gT = gT[keep,:]
   k = k[keep,:][:,keep]

if cmd == 'redis':
    ps, ts = gn2_load_redis('testrun','other',k,y,gT)
    print ps[0:10],ps[-10:]
