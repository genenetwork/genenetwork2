# Plink module
#
# Copyright (C) 2015  Pjotr Prins (pjotr.prins@thebird.nl)
# Some of the BED file parsing came from pylmm:
# Copyright (C) 2013  Nicholas A. Furlotte (nick.furlotte@gmail.com)

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

# According to the PLINK information

# Parse a textual BIM file and return the contents as a list of tuples
# 
# Extended variant information file accompanying a .bed binary genotype table.
# 
# A text file with no header line, and one line per variant with the following six fields:
# 
#     Chromosome code (either an integer, or 'X'/'Y'/'XY'/'MT'; '0' indicates unknown) or name
#     Variant identifier
#     Position in morgans or centimorgans (safe to use dummy value of '0')
#     Base-pair coordinate (normally 1-based, but 0 ok; limited to 231-2)
#     Allele 1 (corresponding to clear bits in .bed; usually minor)
#     Allele 2 (corresponding to set bits in .bed; usually major)
# 
# Allele codes can contain more than one character. Variants with negative bp coordinates are ignored by PLINK. Example
#
#     1 mm37-1-3125499  0 3125499 1 2
#     1 mm37-1-3125701  0 3125701 1 2
#     1 mm37-1-3187481  0 3187481 1 2

import struct
# import numpy as np

def readbim(fn):
    res = []
    for line in open(fn):
        list = line.split()
        if len([True for e in list if e == 'nan']) == 0:
          res.append( (list[0],list[1],int(list[2]),int(list[3]),int(list[4]),int(list[5])) )
    return res

# .bed (PLINK binary biallelic genotype table)
# 
# Primary representation of genotype calls at biallelic variants. Must
# be accompanied by .bim and .fam files. Basically contains num SNP
# blocks containing IND (compressed 4 IND into a byte)
#
# Since it is a biallelic format it supports for every individual
# whether the first allele is homozygous (b00), the second allele is
# homozygous (b11), it is heterozygous (b10) or that it is missing
# (b01).

# http://pngu.mgh.harvard.edu/~purcell/plink2/formats.html#bed
# http://pngu.mgh.harvard.edu/~purcell/plink2/formats.html#fam
# http://pngu.mgh.harvard.edu/~purcell/plink2/formats.html#bim

def readbed(fn,inds,func=None):

    # For every SNP block fetch the individual genotypes using values
    # 0.0 and 1.0 for homozygous and 0.5 for heterozygous alleles
    def fetchGenotypes(X):
        D = { \
              '00': 0.0, \
              '10': 0.5, \
              '11': 1.0, \
              '01': float('nan') \
           }
  
        G = []
        for x in X:
            if not len(x) == 10:
                xx = x[2:]
                x = '0b' + '0'*(8 - len(xx)) + xx
            a,b,c,d = (x[8:],x[6:8],x[4:6],x[2:4]) 
            L = [D[y] for y in [a,b,c,d]]
            G += L
        G = G[:inds]
        # G = np.array(G)
        return G

    bytes = inds / 4 + (inds % 4 and 1 or 0)
    format = 'c'*bytes
    count = 0
    with open(fn,'rb') as f:
        magic = f.read(3)
        assert( ":".join("{:02x}".format(ord(c)) for c in magic) == "6c:1b:01")
        while True:
            count += 1
            X = f.read(bytes)
            if not X:
                return(count-1)
            XX = [bin(ord(x)) for x in struct.unpack(format,X)]
            xs = fetchGenotypes(XX)
            func(count,xs)
