# pylmm kinship calculation
#
# Copyright (C) 2013  Nicholas A. Furlotte (nick.furlotte@gmail.com)
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

# env PYTHONPATH=$pylmm_lib_path:./lib python $pylmm_lib_path/runlmm.py --pheno test.pheno --geno test9000.geno kinship --test

import sys
import os
import numpy as np
import multiprocessing as mp # Multiprocessing is part of the Python stdlib
import Queue 

from optmatrix import matrix_initialize, matrixMultT


def compute_W(job,G,n,snps,compute_size):
   """
   Read 1000 SNPs at a time into matrix and return the result
   """
   W = np.ones((n,compute_size)) * np.nan # W matrix has dimensions individuals x SNPs (initially all NaNs)
   for j in range(0,compute_size):
      row = job*compute_size + j
      if row >= compute_size or row>=snps:
         W = W[:,range(0,j)]
         break
      # print job,compute_size,j
      snp = G[job*compute_size+j]
      # print snp.shape,snp
      if snp.var() == 0:
         continue
      W[:,j] = snp  # set row to list of SNPs
   return W

def compute_matrixMult(job,W,q = None):
   """
   Compute Kinship(W)*j

   For every set of SNPs matrixMult is used to multiply matrices T(W)*W
   """
   res = matrixMultT(W)
   if not q: q=compute_matrixMult.q
   q.put([job,res])
   return job

def f_init(q):
   compute_matrixMult.q = q

def kinship_full(G):
   """
   Calculate the Kinship matrix using a full dot multiplication
   """
   print G.shape
   m = G.shape[0] # snps
   n = G.shape[1] # inds
   sys.stderr.write(str(m)+" SNPs\n")
   assert m>n, "n should be larger than m (snps>inds)"
   m = np.dot(G.T,G)
   m = m/G.shape[0]
   return m

# Calculate the kinship matrix from G (SNPs as rows!), returns K
#
def kinship(G,options):
   numThreads = None
   if options.numThreads:
      numThreads = int(options.numThreads)
   options.computeSize = 1000
   matrix_initialize(options.useBLAS)
   
   sys.stderr.write(str(G.shape)+"\n")
   n = G.shape[1] # inds
   inds = n
   m = G.shape[0] # snps
   snps = m
   sys.stderr.write(str(m)+" SNPs\n")
   assert m>n, "n should be larger than m (snps>inds)"

   q = mp.Queue()
   p = mp.Pool(numThreads, f_init, [q])
   iterations = snps/options.computeSize+1
   if options.testing:
      iterations = 8
   # jobs = range(0,8) # range(0,iterations)

   results = []

   K = np.zeros((n,n))  # The Kinship matrix has dimension individuals x individuals

   completed = 0
   for job in range(iterations):
      if options.verbose:
         sys.stderr.write("Processing job %d first %d SNPs\n" % (job, ((job+1)*options.computeSize)))
      W = compute_W(job,G,n,snps,options.computeSize)
      if numThreads == 1:
         compute_matrixMult(job,W,q)
         j,x = q.get()
         if options.verbose: sys.stderr.write("Job "+str(j)+" finished\n")
         K_j = x
         # print j,K_j[:,0]
         K = K + K_j
      else:
         results.append(p.apply_async(compute_matrixMult, (job,W)))
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

   if numThreads == None or numThreads > 1:
      for job in range(len(results)-completed):
         j,x = q.get(True,15)
         if options.verbose: sys.stderr.write("Job "+str(j)+" finished\n")
         K_j = x
         # print j,K_j[:,0]
         K = K + K_j

   K = K / float(snps)
   outFile = 'runtest.kin'
   if options.verbose: sys.stderr.write("Saving Kinship file to %s\n" % outFile)
   np.savetxt(outFile,K)

   if options.saveKvaKve:
      if options.verbose: sys.stderr.write("Obtaining Eigendecomposition\n")
      Kva,Kve = linalg.eigh(K)
      if options.verbose: sys.stderr.write("Saving eigendecomposition to %s.[kva | kve]\n" % outFile)
      np.savetxt(outFile+".kva",Kva)
      np.savetxt(outFile+".kve",Kve)
   return K      



