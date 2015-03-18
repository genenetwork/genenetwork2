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
   result = []
   for snp_id in snp_ids:
      snp,id = snp_id
      x = snp.reshape((n,1))  # all the SNPs
      # if refit:
      #    L.fit(X=snp,REML=REML)
      ts,ps,beta,betaVar = lmm2.association(x,REML=REML,returnBeta=True)
      # result.append(formatResult(id,beta,np.sqrt(betaVar).sum(),ts,ps))
      result.append( (ts,ps) )
   if not q:
      q = compute_snp.q
   q.put([j,result])
   return j

def f_init(q):
   compute_snp.q = q

def gwas(Y,G,K,uses,restricted_max_likelihood=True,refit=False,verbose=True):
   """
   GWAS. The G matrix should be n inds (cols) x m snps (rows)
   """
   progress,debug,info,mprint = uses('progress','debug','info','mprint')

   matrix_initialize()
   cpu_num = mp.cpu_count()
   numThreads = None # for now use all available threads
   kfile2 = False
   reml = restricted_max_likelihood

   mprint("G",G)
   n = G.shape[1] # inds
   inds = n
   m = G.shape[0] # snps
   snps = m
   info("%s SNPs",snps)
   assert snps>inds, "snps should be larger than inds (snps=%d,inds=%d)" % (snps,inds)

   # CREATE LMM object for association
   # if not kfile2:  L = LMM(Y,K,Kva,Kve,X0,verbose=verbose)
   # else:  L = LMM_withK2(Y,K,Kva,Kve,X0,verbose=verbose,K2=K2)

   lmm2 = LMM2(Y,K) # ,Kva,Kve,X0,verbose=verbose)
   if not refit:
      info("Computing fit for null model")
      lmm2.fit()  # follow GN model in run_other
      info("heritability=%0.3f, sigma=%0.3f" % (lmm2.optH,lmm2.optSigma))
            
   res = []

   # Set up the pool
   # mp.set_start_method('spawn')
   q = mp.Queue()
   p = mp.Pool(numThreads, f_init, [q])
   collect = []

   count = 0
   job = 0
   jobs_running = 0
   jobs_completed = 0
   for snp in G:
      snp_id = (snp,'SNPID')
      count += 1
      if count % 1000 == 0:
         job += 1
         debug("Job %d At SNP %d" % (job,count))
         if numThreads == 1:
            debug("Running on 1 THREAD")
            compute_snp(job,n,collect,lmm2,reml,q)
            collect = []
            j,lst = q.get()
            debug("Job "+str(j)+" finished")
            jobs_completed += 1
            progress("GWAS2",jobs_completed,snps/1000)
            res.append((j,lst))
         else:
            p.apply_async(compute_snp,(job,n,collect,lmm2,reml))
            jobs_running += 1
            collect = []
            while jobs_running > cpu_num:
               try:
                  j,lst = q.get_nowait()
                  debug("Job "+str(j)+" finished")
                  jobs_completed += 1
                  progress("GWAS2",jobs_completed,snps/1000)
                  res.append((j,lst))
                  jobs_running -= 1
               except Queue.Empty:
                  time.sleep(0.1)
                  pass
               if jobs_running > cpu_num*2:
                  time.sleep(1.0)
               else:
                  break

      collect.append(snp_id)

   if numThreads==1 or count<1000 or len(collect)>0:
      job += 1
      debug("Collect final batch size %i job %i @%i: " % (len(collect), job, count))
      compute_snp(job,n,collect,lmm2,reml,q)
      collect = []
      j,lst = q.get()
      res.append((j,lst))
   debug("count=%i running=%i collect=%i" % (count,jobs_running,len(collect)))
   for job in range(jobs_running):
      j,lst = q.get(True,15) # time out
      debug("Job "+str(j)+" finished")
      jobs_completed += 1
      progress("GWAS2",jobs_completed,snps/1000)
      res.append((j,lst))

   mprint("Before sort",[res1[0] for res1 in res])
   res = sorted(res,key=lambda x: x[0])
   mprint("After sort",[res1[0] for res1 in res])
   info([len(res1[1]) for res1 in res])
   ts = [item[0] for j,res1 in res for item in res1]
   ps = [item[1] for j,res1 in res for item in res1]
   return ts,ps
