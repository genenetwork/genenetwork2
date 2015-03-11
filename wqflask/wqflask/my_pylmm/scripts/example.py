#!/usr/bin/python

from __future__ import absolute_import, print_function, division

import sys
import time

import numpy as np
from pyLMM import lmm

from pprint import pformat as pf


Y = np.genfromtxt('data/mdp.exprs.1.new')
print("exprs is:", pf(Y.shape))

# Loading npdump and first 1000 snps for speed
#K = np.load('data/hmdp.liver.K.npdump')
#snps = np.load('data/hmdp.liver.snps.1000.npdump').T

# These three lines will load all SNPs (from npdump or from txt) and 
# calculate the kinship
snps = np.genfromtxt('/home/zas1024/gene/web/new_genotypers/mdp.snps.1000.new').T
print("snps is:", pf(snps.shape))
#snps = snps[~np.isnan(snps).all(axis=1)]
#print ("snps is now:", pf(snps))
np.savetxt("/home/zas1024/gene/wqflask/wqflask/pylmm/data/mdp.snps.trimmed", snps, fmt='%s', delimiter=' ')
#snps = np.load('data/hmdp.liver.snps.npdump').T
K = lmm.calculateKinship(snps)
#print("K is:", pf(K))
#print("Y is:", pf(Y.shape))

# Instantiate a LMM object for the phentoype Y and fit the null model
L = lmm.LMM(Y,K)
L.fit()

# Manually calculate the association at one SNP
X = snps[:,0]
X[np.isnan(X)] = X[True - np.isnan(X)].mean() # Fill missing with MAF
X = X.reshape(len(X),1)
if X.var() == 0: ts,ps = (np.nan,np.nan)
else: ts,ps = L.association(X)

# If I want to refit the variance component
L.fit(X=X)
ts,ps = L.association(X)

# If I want to do a genome-wide scan over the 1000 SNPs.
# This call will use REML (REML = False means use ML).
# It will also refit the variance components for each SNP.
# Setting refit = False will cause the program to fit the model once
# and hold those variance component estimates for each SNP.
begin = time.time()
TS,PS = lmm.GWAS(Y,snps,K,REML=True,refit=False)
print("TS is:", pf(TS))
print("PS is:", pf(PS))
end = time.time()
sys.stderr.write("Total time for 1000 SNPs: %0.3f\n" % (end- begin))