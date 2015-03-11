#!/usr/bin/python

# pylmm is a python-based linear mixed-model solver with applications to GWAS

# Copyright (C) 2013  Nicholas A. Furlotte (nick.furlotte@gmail.com)

#The program is free for academic use. Please contact Nick Furlotte
#<nick.furlotte@gmail.com> if you are interested in using the software for
#commercial purposes.

#The software must not be modified and distributed without prior
#permission of the author.

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import pdb

from optparse import OptionParser,OptionGroup
usage = """usage: %prog [options] --[tfile | bfile] plinkFileBase outfile

"""

parser = OptionParser(usage=usage)

basicGroup = OptionGroup(parser, "Basic Options")
#advancedGroup = OptionGroup(parser, "Advanced Options")

#basicGroup.add_option("--pfile", dest="pfile",
#                  help="The base for a PLINK ped file")
basicGroup.add_option("--tfile", dest="tfile",
                  help="The base for a PLINK tped file")
basicGroup.add_option("--bfile", dest="bfile",
                  help="The base for a PLINK binary ped file")
basicGroup.add_option("--emmaSNP", dest="emmaFile", default=None,
                  help="For backwards compatibility with emma, we allow for \"EMMA\" file formats.  This is just a text file with individuals on the rows and snps on the columns.")
basicGroup.add_option("--emmaNumSNPs", dest="numSNPs", type="int", default=0,
		     help="When providing the emmaSNP file you need to specify how many snps are in the file")

basicGroup.add_option("-e", "--efile", dest="saveEig", help="Save eigendecomposition to this file.")
basicGroup.add_option("-n", default=1000,dest="computeSize", type="int", help="The maximum number of SNPs to read into memory at once (default 1000).  This is important when there is a large number of SNPs, because memory could be an issue.")
basicGroup.add_option("-t", "--nthreads", dest="numThreads", help="maximum number of threads to use")

basicGroup.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="Print extra info")

parser.add_option_group(basicGroup)
#parser.add_option_group(advancedGroup)

(options, args) = parser.parse_args()
if len(args) != 1: 
   parser.print_help()
   sys.exit()

outFile = args[0]

import sys
import os
import numpy as np
from scipy import linalg
from pylmm.lmm import calculateKinship
from pylmm import input
import multiprocessing as mp # Multiprocessing is part of the Python stdlib
import Queue 

if not options.tfile and not options.bfile and not options.emmaFile: 
   parser.error("You must provide at least one PLINK input file base (--tfile or --bfile) or an emma formatted file (--emmaSNP).")

numThreads = None
if options.numThreads:
   numThreads = int(options.numThreads)
   
if options.verbose: sys.stderr.write("Reading PLINK input...\n")
if options.bfile: IN = input.plink(options.bfile,type='b')
elif options.tfile: IN = input.plink(options.tfile,type='t')
#elif options.pfile: IN = input.plink(options.pfile,type='p')
elif options.emmaFile: 
   if not options.numSNPs: parser.error("You must provide the number of SNPs when specifying an emma formatted file.")
   IN = input.plink(options.emmaFile,type='emma')
else: parser.error("You must provide at least one PLINK input file base (--tfile or --bfile) or an emma formatted file (--emmaSNP).")

def compute_W(job):
   """
   Read 1000 SNPs at a time into matrix and return the result
   """
   n = len(IN.indivs)
   m = options.computeSize
   W = np.ones((n,m)) * np.nan # W matrix has dimensions individuals x SNPs (initially all NaNs)
   for j in range(0,options.computeSize):
      row = job*m + j
      if row >= IN.numSNPs:
         W = W[:,range(0,j)]
         break
      snp,id = IN.next()
      if snp.var() == 0:
         continue
      W[:,j] = snp  # set row to list of SNPs
   return W

def compute_dgemm(job,W):
   """
   Compute Kinship(W)*j

   For every set of SNPs dgemm is used to multiply matrices T(W)*W
   """
   res = None
   try:
      res = linalg.fblas.dgemm(alpha=1.,a=W.T,b=W.T,trans_a=True,trans_b=False)
   except AttributeError:
      res = np.dot(W,W.T) 
   compute_dgemm.q.put([job,res])
   return job

def f_init(q):
    compute_dgemm.q = q

n = len(IN.indivs)
# m = options.computeSize
# jobsize=m

IN.getSNPIterator()
# Annoying hack to get around the fact that it is expensive to determine the number of SNPs in an emma file
if options.emmaFile: IN.numSNPs = options.numSNPs
# i = 0

# mp.set_start_method('spawn')
q = mp.Queue()
p = mp.Pool(numThreads, f_init, [q])
iterations = IN.numSNPs/options.computeSize+1
# jobs = range(0,8) # range(0,iterations)

results = []

K = np.zeros((n,n))  # The Kinship matrix has dimension individuals x individuals

completed = 0

# for job in range(8):
for job in range(iterations):
   if options.verbose:
      sys.stderr.write("Processing job %d first %d SNPs\n" % (job, ((job+1)*options.computeSize)))
   W = compute_W(job)
   results.append(p.apply_async(compute_dgemm, (job,W)))   
   # Do we have a result?
   try: 
     j,x = q.get_nowait()
     if options.verbose: sys.stderr.write("Job "+str(j)+" finished\n")
     K_j = x
     # print j,K_j[:,0]
     K = K + K_j
     completed += 1
   except Queue.Empty:
     pass

for job in range(len(results)-completed):
   j,x = q.get()
   if options.verbose: sys.stderr.write("Job "+str(j)+" finished\n")
   K_j = x
   # print j,K_j[:,0]
   K = K + K_j
        
K = K / float(IN.numSNPs)
if options.verbose: sys.stderr.write("Saving Kinship file to %s\n" % outFile)
np.savetxt(outFile,K)

if options.saveEig:
   if options.verbose: sys.stderr.write("Obtaining Eigendecomposition\n")
   Kva,Kve = linalg.eigh(K)
   if options.verbose: sys.stderr.write("Saving eigendecomposition to %s.[kva | kve]\n" % outFile)
   np.savetxt(outFile+".kva",Kva)
   np.savetxt(outFile+".kve",Kve)
      



