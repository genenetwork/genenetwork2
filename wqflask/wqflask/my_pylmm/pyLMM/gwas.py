# pylmm-based GWAS calculation
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
#!/usr/bin/python

import pdb
import time
import sys
# from utility import temp_data
import lmm


import os
import numpy as np
import input
from optmatrix import matrix_initialize
# from lmm import LMM

import multiprocessing as mp # Multiprocessing is part of the Python stdlib
import Queue 

def compute_snp(j,snp_ids,q = None):
   # print(j,len(snp_ids),"\n")
   result = []
   for snp_id in snp_ids:
      # j,snp_id = collect
      snp,id = snp_id
      # id = collect[1]
      # result = []
      # Check SNPs for missing values
      x = snp[keep].reshape((n,1))  # all the SNPs
      v = np.isnan(x).reshape((-1,))
      if v.sum():
         # NOTE: this code appears to be unreachable!
         if verbose:
            sys.stderr.write("Found missing values in "+str(x))
         keeps = True - v
         xs = x[keeps,:]
         if keeps.sum() <= 1 or xs.var() <= 1e-6: 
            # PS.append(np.nan)
            # TS.append(np.nan)
            # result.append(formatResult(id,np.nan,np.nan,np.nan,np.nan))
            # continue
            result.append(formatResult(id,np.nan,np.nan,np.nan,np.nan))
            continue

         # Its ok to center the genotype -  I used normalizeGenotype to 
         # force the removal of missing genotypes as opposed to replacing them with MAF.
         if not normalizeGenotype:
            xs = (xs - xs.mean()) / np.sqrt(xs.var())
         Ys = Y[keeps]
         X0s = X0[keeps,:]
         Ks = K[keeps,:][:,keeps]
         if kfile2:
            K2s = K2[keeps,:][:,keeps]
            Ls = LMM_withK2(Ys,Ks,X0=X0s,verbose=verbose,K2=K2s)
         else:
            Ls = LMM(Ys,Ks,X0=X0s,verbose=verbose)
         if refit:
           Ls.fit(X=xs,REML=REML)
         else:
            #try:
            Ls.fit(REML=REML)
            #except: pdb.set_trace()
         ts,ps,beta,betaVar = Ls.association(xs,REML=REML,returnBeta=True)
      else:
         if x.var() == 0:
            # Note: this code appears to be unreachable!

            # PS.append(np.nan)
            # TS.append(np.nan)
            # result.append(formatResult(id,np.nan,np.nan,np.nan,np.nan)) # writes nan values
            result.append(formatResult(id,np.nan,np.nan,np.nan,np.nan))
            continue

         if refit:
            L.fit(X=x,REML=REML)
         # This is where it happens
         ts,ps,beta,betaVar = L.association(x,REML=REML,returnBeta=True)
      result.append(formatResult(id,beta,np.sqrt(betaVar).sum(),ts,ps))
      # compute_snp.q.put([j,formatResult(id,beta,np.sqrt(betaVar).sum(),ts,ps)])
   # print [j,result[0]]," in result queue\n"
   if not q:
      q = compute_snp.q
   q.put([j,result])
   return j
      # PS.append(ps)
      # TS.append(ts)
      # return len(result)
      # compute.q.put(result)
      # return None

def f_init(q):
   compute_snp.q = q

def gwas(Y,G,K,restricted_max_likelihood=True,refit=False,verbose=True):
   """
   Execute a GWAS. The G matrix should be n inds (cols) x m snps (rows)
   """
   matrix_initialize()
   cpu_num = mp.cpu_count()
   numThreads = 1
   kfile2 = False

   sys.stderr.write(str(G.shape)+"\n")
   n = G.shape[1] # inds
   inds = n
   m = G.shape[0] # snps
   snps = m
   sys.stderr.write(str(m)+" SNPs\n")
   # print "***** GWAS: G",G.shape,G
   assert m>n, "n should be larger than m (snps>inds)"

   # CREATE LMM object for association
   # if not kfile2:  L = LMM(Y,K,Kva,Kve,X0,verbose=verbose)
   # else:  L = LMM_withK2(Y,K,Kva,Kve,X0,verbose=verbose,K2=K2)

   runlmm = lmm.LMM(Y,K) # ,Kva,Kve,X0,verbose=verbose)
   if not refit:
      if verbose: sys.stderr.write("Computing fit for null model\n")
      runlmm.fit()  # follow GN model in run_other
      if verbose: sys.stderr.write("\t heritability=%0.3f, sigma=%0.3f\n" % (runlmm.optH,runlmm.optSigma))
      
   # outFile = "test.out"
   # out = open(outFile,'w')
   out = sys.stderr

   def outputResult(id,beta,betaSD,ts,ps):
      out.write(formatResult(id,beta,betaSD,ts,ps))
   def printOutHead(): out.write("\t".join(["SNP_ID","BETA","BETA_SD","F_STAT","P_VALUE"]) + "\n")
   def formatResult(id,beta,betaSD,ts,ps):
      return "\t".join([str(x) for x in [id,beta,betaSD,ts,ps]]) + "\n"

   printOutHead()

   # Set up the pool
   # mp.set_start_method('spawn')
   q = mp.Queue()
   p = mp.Pool(numThreads, f_init, [q])
   collect = []

   # Buffers for pvalues and t-stats
   # PS = []
   # TS = []
   count = 0

   completed = 0
   last_j = 0
   # for snp_id in G:
   for snp in G:
      print snp.shape,snp
      snp_id = ('SNPID',snp)
      count += 1
      if count % 1000 == 0:
         job = count/1000
         if verbose:
            sys.stderr.write("Job %d At SNP %d\n" % (job,count))
         if numThreads == 1:
            compute_snp(job,collect,q)
            collect = []
            j,lines = q.get()
            if verbose:
               sys.stderr.write("Job "+str(j)+" finished\n")
            for line in lines:
               out.write(line)
         else:
            p.apply_async(compute_snp,(job,collect))
            collect = []
            while job > completed:
               try:
                  j,lines = q.get_nowait()
                  if verbose:
                     sys.stderr.write("Job "+str(j)+" finished\n")
                  for line in lines:
                     out.write(line)
                  completed += 1
               except Queue.Empty:
                  pass
               if job > completed + cpu_num + 5:
                  time.sleep(1)
               else:
                  if job >= completed:
                    break

      collect.append(snp_id)

   if not numThreads or numThreads > 1:
      for job in range(int(count/1000)-completed):
         j,lines = q.get(True,15) # time out
         if verbose:
            sys.stderr.write("Job "+str(j)+" finished\n")
         for line in lines:
            out.write(line)

   # print collect
   ps = [item[1][3] for item in collect]
   ts = [item[1][2] for item in collect]
   print ps
   return ts,ps
