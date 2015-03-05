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
import os
import numpy as np
# from lmm import LMM, run_other
import csv


usage = """
python runlmm.py [options] command

  runlmm.py processing multiplexer reads standard input types and calls the routines

  Current commands are:

    parse        : only parse input files

  try --help for more information
"""

parser = OptionParser(usage=usage)
# parser.add_option("-f", "--file", dest="input file",
#                   help="In", metavar="FILE")
parser.add_option("--kinship",dest="kinship",
                  help="Kinship file format")
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
    K1 = []
    print options.kinship
    with open(options.kinship,'r') as tsvin:
        assert(tsvin.readline().strip() == "# Kinship format version 1.0")
        tsvin.readline()
        tsvin.readline()
        tsv = csv.reader(tsvin, delimiter='\t')
        for row in tsv:
            ns = np.genfromtxt(row[1:])
            K1.append(ns) # <--- slow
    K = np.array(K1)
