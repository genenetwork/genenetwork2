# This is a converter for common LMM formats, so as to keep complexity
# outside the main routines. 

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
import input


usage = """
python convertlmm.py [--kinship] infile 

  Convert files for runlmm.py processing. Writes to stdout.

  try --help for more information
"""

parser = OptionParser(usage=usage)
# parser.add_option("-f", "--file", dest="input file",
#                   help="In", metavar="FILE")
parser.add_option("--kinship",action="store_false", dest="kinship", default=True,
                  help="Parse a kinship file. This is an nxn plain text file and can be computed with the pylmmKinship program.")
parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")

(options, args) = parser.parse_args()

if len(args) == 0:
    print usage
    sys.exit(1)

if options.kinship:
    is_header = True
    assert(len(args)==1)
    count = 0
    for line in open(args[0],'r'):
        count += 1
        if is_header:
            size = len(line.split())
            print "# Kinship format version 1.0"
            print "# Size=",size
            for i in range(size):
                sys.stdout.write("\t"+str(i+1))
            sys.stdout.write("\n")
            is_header = False
        sys.stdout.write(str(count))
        sys.stdout.write("\t")
        sys.stdout.write("\t".join(line.split()))
        sys.stdout.write("\n")
