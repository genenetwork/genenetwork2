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
import lmm2

import os
import numpy as np
import input
from optmatrix import matrix_initialize
from lmm2 import LMM2

import multiprocessing as mp # Multiprocessing is part of the Python stdlib
import Queue 

def formatResult(id,beta,betaSD,ts,ps):
   return "\t".join([str(x) for x in [id,beta,betaSD,ts,ps]]) + "\n"

def compute_snp(j,n,snp_ids,lmm2,REML,q = None):
   # print("COMPUTE SNP",j,snp_ids,"\n")
   result = []
   for snp_id in snp_ids:
      snp,id = snp_id
      x = snp.reshape((n,1))  # all the SNPs
      # print "X=",x
      # if refit:
      #    L.fit(X=snp,REML=REML)
      ts,ps,beta,betaVar = lmm2.association(x,REML=REML,returnBeta=True)
      # result.append(formatResult(id,beta,np.sqrt(betaVar).sum(),ts,ps))
      result.append( (ts,ps) )
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
   numThreads = None
   kfile2 = False
   reml = restricted_max_likelihood

   sys.stderr.write(str(G.shape)+"\n")
   n = G.shape[1] # inds
   inds = n
   m = G.shape[0] # snps
   snps = m
   sys.stderr.write(str(m)+" SNPs\n")
   # print "***** GWAS: G",G.shape,G
   assert snps>inds, "snps should be larger than inds (snps=%d,inds=%d)" % (snps,inds)

   # CREATE LMM object for association
   # if not kfile2:  L = LMM(Y,K,Kva,Kve,X0,verbose=verbose)
   # else:  L = LMM_withK2(Y,K,Kva,Kve,X0,verbose=verbose,K2=K2)

   lmm2 = LMM2(Y,K) # ,Kva,Kve,X0,verbose=verbose)
   if not refit:
      if verbose: sys.stderr.write("Computing fit for null model\n")
      lmm2.fit()  # follow GN model in run_other
      if verbose: sys.stderr.write("\t heritability=%0.3f, sigma=%0.3f\n" % (lmm2.optH,lmm2.optSigma))
      
   # outFile = "test.out"
   # out = open(outFile,'w')
   out = sys.stderr

   def outputResult(id,beta,betaSD,ts,ps):
      out.write(formatResult(id,beta,betaSD,ts,ps))
   def printOutHead(): out.write("\t".join(["SNP_ID","BETA","BETA_SD","F_STAT","P_VALUE"]) + "\n")

   # printOutHead()
   res = []

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
      snp_id = (snp,'SNPID')
      count += 1
      # print count,snp_id
      if count % 1000 == 0:
         job = count/1000
         if verbose:
            sys.stderr.write("Job %d At SNP %d\n" % (job,count))
         if numThreads == 1:
            print "Running on 1 THREAD"
            compute_snp(job,n,collect,lmm2,reml,q)
            collect = []
            j,lst = q.get()
            if verbose:
               sys.stderr.write("Job "+str(j)+" finished\n")
            # for line in lines:
            #    out.write(line)
            res.append(lst)
         else:
            p.apply_async(compute_snp,(job,n,collect,lmm2,reml))
            collect = []
            while job > completed:
               try:
                  j,lst = q.get_nowait()
                  if verbose:
                     sys.stderr.write("Job "+str(j)+" finished\n")
                  # for line in lines:
                  #    out.write(line)
                  res.append(lst)
                  completed += 1
               except Queue.Empty:
                  pass
               if job > completed + cpu_num + 5:
                  time.sleep(1)
               else:
                  if job >= completed:
                    break

      collect.append(snp_id)

   if numThreads==1:
      print "Running on 1 THREAD"
      compute_snp(count/1000,n,collect,lmm2,reml,q)
      j,lst = q.get()
      # for line in lines:
      #    out.write(line)
      res.append(lst)
   else:
      for job in range(int(count/1000)-completed):
         j,lst = q.get(True,15) # time out
         if verbose:
            sys.stderr.write("Job "+str(j)+" finished\n")
         res.append(lst)

   # print res
   ts = [item[0] for res1 in res for item in res1]
   ps = [item[1] for res1 in res for item in res1]
   # ts = [item[1] for item in res]
   # print ps
   return ts,ps
