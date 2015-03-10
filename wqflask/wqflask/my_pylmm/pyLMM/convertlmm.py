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

from __future__ import print_function
from optparse import OptionParser
import sys
import os
import numpy as np
# from lmm import LMM, run_other
# import input
import plink

usage = """
python convertlmm.py [--plink] [--prefix out_basename] [--kinship kfile] [--pheno pname] [--geno gname]

  Convert files for runlmm.py processing. Writes to stdout by default.

  try --help for more information
"""

# if len(args) == 0:
#     print usage
#     sys.exit(1)

option_parser = OptionParser(usage=usage)
option_parser.add_option("--kinship", dest="kinship",
                  help="Parse a kinship file. This is an nxn plain text file and can be computed with the pylmmKinship program")
option_parser.add_option("--pheno", dest="pheno",
                         help="Parse a phenotype file (use with --plink only)")
option_parser.add_option("--geno", dest="geno",
                         help="Parse a genotype file (use with --plink only)")
option_parser.add_option("--plink", dest="plink", action="store_true", default=False,
                  help="Parse PLINK style")
# option_parser.add_option("--kinship",action="store_false", dest="kinship", default=True,
#                   help="Parse a kinship file. This is an nxn plain text file and can be computed with the pylmmKinship program.")
option_parser.add_option("--prefix", dest="prefix",
                  help="Output prefix for output file(s)")
option_parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")
option_parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="Print extra info")

(options, args) = option_parser.parse_args()

writer = None
num_inds = None
snp_names = []
ind_names = []

def msg(s):
    sys.stderr.write("INFO: ")
    sys.stderr.write(s)
    sys.stderr.write("\n")
    
def wr(s):
    if writer:
        writer.write(s)
    else:
        sys.stdout.write(s)

def wrln(s):
    wr(s)
    wr("\n")
            

if options.pheno:
    if not options.plink:
        raise Exception("Use --plink switch")
    # Because plink does not track size we need to read the whole thing first
    msg("Converting pheno "+options.pheno)
    phenos = []
    count = 0
    count_pheno = None
    for line in open(options.pheno,'r'):
        count += 1
        list = line.split()
        pcount = len(list)-2
        assert(pcount > 0)
        if count_pheno == None:
            count_pheno = pcount
        assert(count_pheno == pcount)
        row = [list[0]]+list[2:]
        phenos.append(row)

    writer = None
    if options.prefix:
        writer = open(options.prefix+".pheno","w")
    wrln("# Phenotype format version 1.0")
    wrln("# Individuals = "+str(count))
    wrln("# Phenotypes = "+str(count_pheno))
    for i in range(count_pheno):
        wr("\t"+str(i+1))
        wr("\n")
    for i in range(count):
        wr("\t".join(phenos[i]))
        wr("\n")
    num_inds = count
    msg(str(count)+" pheno lines written")

if options.kinship:
    is_header = True
    count = 0
    msg("Converting kinship "+options.kinship)
    writer = None
    if options.prefix:
        writer = open(options.prefix+".kin","w")
    for line in open(options.kinship,'r'):
        count += 1
        if is_header:
            size = len(line.split())
            wrln("# Kinship format version 1.0")
            wrln("# Size="+str(size))
            for i in range(size):
                wr("\t"+str(i+1))
            wr("\n")
            is_header = False
        wr(str(count))
        wr("\t")
        wr("\t".join(line.split()))
        wr("\n")
    num_inds = count
    msg(str(count)+" kinship lines written")
    
if options.geno:
    msg("Converting geno "+options.geno+'.bed')
    if not options.plink:
        raise Exception("Use --plink switch")
    if not num_inds:
        raise Exception("Can not figure out the number of individuals, use --pheno or --kinship")    
    bim_snps = plink.readbim(options.geno+'.bim')
    num_snps = len(bim_snps)
    writer = None
    if options.prefix:
        writer = open(options.prefix+".geno","w")
    wrln("# Genotype format version 1.0")
    wrln("# Individuals = "+str(num_inds))
    wrln("# SNPs = "+str(num_snps))
    wrln("# Encoding = HAB")
    for i in range(num_inds):
        wr("\t"+str(i+1))
    wr("\n")

    m = []
    def out(i,x):
        # wr(str(i)+"\t")
        # wr("\t".join(x))
        # wr("\n")
        m.append(x)
        
    snps = plink.readbed(options.geno+'.bed',num_inds, ('A','H','B','-'), out)

    msg("Write transposed genotype matrix")
    for g in range(num_snps):
        wr(bim_snps[g][1]+"\t")
        for i in range(num_inds):
            wr(m[g][i])
        wr("\n")
            
    msg(str(count)+" geno lines written (with "+str(snps)+" snps)")
   
msg("Converting done")
