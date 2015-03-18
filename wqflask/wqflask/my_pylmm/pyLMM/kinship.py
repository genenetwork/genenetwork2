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
from scipy import linalg
import multiprocessing as mp # Multiprocessing is part of the Python stdlib
import Queue
import time

from optmatrix import matrix_initialize, matrixMultT

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

def compute_W(job,G,n,snps,compute_size):
   """
   Read 1000 SNPs at a time into matrix and return the result
   """
   m = compute_size
   W = np.ones((n,m)) * np.nan # W matrix has dimensions individuals x SNPs (initially all NaNs)
   for j in range(0,compute_size):
      pos = job*m + j # real position
      if pos >= snps:
         W = W[:,range(0,j)]
         break
      snp = G[job*compute_size+j]
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

# Calculate the kinship matrix from G (SNPs as rows!), returns K
#
def kinship(G,uses,computeSize=1000,numThreads=None,useBLAS=False):
   progress,debug,info,mprint = uses('progress','debug','info','mprint')

   matrix_initialize(useBLAS)

   mprint("G",G)
   n = G.shape[1] # inds
   inds = n
   m = G.shape[0] # snps
   snps = m
   info("%i SNPs" % (m))
   assert snps>inds, "snps should be larger than inds (%i snps, %i inds)" % (snps,inds)

   q = mp.Queue()
   p = mp.Pool(numThreads, f_init, [q])
   cpu_num = mp.cpu_count()
   info("CPU cores: %i" % cpu_num)
   iterations = snps/computeSize+1

   results = []
   K = np.zeros((n,n))  # The Kinship matrix has dimension individuals x individuals

   completed = 0
   for job in range(iterations):
      info("Processing job %d first %d SNPs" % (job, ((job+1)*computeSize)))
      W = compute_W(job,G,n,snps,computeSize)
      if numThreads == 1:
         # Single-core
         compute_matrixMult(job,W,q)
         j,x = q.get()
         debug("Job "+str(j)+" finished")
         progress("kinship",j,iterations)
         K_j = x
         K = K + K_j
      else:
         # Multi-core
         results.append(p.apply_async(compute_matrixMult, (job,W)))
         # Do we have a result?
         while (len(results)-completed>cpu_num*2):
            time.sleep(0.1)
            try: 
               j,x = q.get_nowait()
               debug("Job "+str(j)+" finished")
               K_j = x
               K = K + K_j
               completed += 1
               progress("kinship",completed,iterations)
            except Queue.Empty:
               pass
         
   if numThreads == None or numThreads > 1:
      for job in range(len(results)-completed):
         j,x = q.get(True,15)
         debug("Job "+str(j)+" finished")
         K_j = x
         K = K + K_j
         completed += 1
         progress("kinship",completed,iterations)

   K = K / float(snps)
   return K      

def kvakve(K,uses):
   """
   Obtain eigendecomposition for K and return Kva,Kve where Kva is cleaned
   of small values < 1e-6 (notably smaller than zero)
   """
   info,mprint = uses('info','mprint')

   info("Obtaining eigendecomposition for %dx%d matrix" % (K.shape[0],K.shape[1]) )
   Kva,Kve = linalg.eigh(K)
   mprint("Kva",Kva)
   mprint("Kve",Kve)

   if sum(Kva < 0):
      info("Cleaning %d eigen values (Kva<0)" % (sum(Kva < 0)))
      Kva[Kva < 1e-6] = 1e-6
   return Kva,Kve




