# pylmm is a python-based linear mixed-model solver with applications to GWAS

# Copyright (C) 2013  Nicholas A. Furlotte (nick.furlotte@gmail.com)
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

from __future__ import absolute_import, print_function, division

import sys
import time
import argparse
import uuid

import numpy as np
from scipy import linalg
from scipy import optimize
from scipy import stats
import pdb

import simplejson as json

import gzip
import zlib
import datetime
import cPickle as pickle
import simplejson as json

from pprint import pformat as pf

from redis import Redis
Redis = Redis()

import sys
sys.path.append("/home/zas1024/gene/wqflask/")
print("sys.path2:", sys.path)

has_gn2=True

from utility.benchmark import Bench
from utility import temp_data
from kinship import kinship, kinship_full, kvakve
import genotype
import phenotype
import gwas

# ---- A trick to decide on the environment:
try:
    from wqflask.my_pylmm.pyLMM import chunks
    from gn2 import uses
except ImportError:
    has_gn2=False
    from standalone import uses
    sys.stderr.write("WARNING: LMM standalone version missing the Genenetwork2 environment\n")
    pass

#np.seterr('raise')

#def run_human(pheno_vector,
#            covariate_matrix,
#            plink_input_file,
#            kinship_matrix,
#            refit=False,
#            loading_progress=None):

def run_human(pheno_vector,
            covariate_matrix,
            plink_input_file,
            kinship_matrix,
            refit=False,
            tempdata=None):

    v = np.isnan(pheno_vector)
    keep = True - v
    keep = keep.reshape((len(keep),))

    identifier = str(uuid.uuid4())
    
    #print("pheno_vector: ", pf(pheno_vector))
    #print("kinship_matrix: ", pf(kinship_matrix))
    #print("kinship_matrix.shape: ", pf(kinship_matrix.shape))

    #lmm_vars = pickle.dumps(dict(
    #    pheno_vector = pheno_vector,
    #    covariate_matrix = covariate_matrix,
    #    kinship_matrix = kinship_matrix
    #))
    #Redis.hset(identifier, "lmm_vars", lmm_vars)
    #Redis.expire(identifier, 60*60)

    if v.sum():
        pheno_vector = pheno_vector[keep]
        print("pheno_vector shape is now: ", pf(pheno_vector.shape))
        covariate_matrix = covariate_matrix[keep,:]
        print("kinship_matrix shape is: ", pf(kinship_matrix.shape))
        print("keep is: ", pf(keep.shape))
        kinship_matrix = kinship_matrix[keep,:][:,keep]

    print("kinship_matrix:", pf(kinship_matrix))

    n = kinship_matrix.shape[0]
    print("n is:", n)
    lmm_ob = LMM(pheno_vector,
                kinship_matrix,
                covariate_matrix)
    lmm_ob.fit()


    # Buffers for pvalues and t-stats
    p_values = []
    t_stats = []

    #print("input_file: ", plink_input_file)

    with Bench("Opening and loading pickle file"):
        with gzip.open(plink_input_file, "rb") as input_file:
            data = pickle.load(input_file)
            
    plink_input = data['plink_input']

    #plink_input.getSNPIterator()
    with Bench("Calculating numSNPs"):
        total_snps = data['numSNPs']

    with Bench("snp iterator loop"):
        count = 0

        with Bench("Create list of inputs"):
            inputs = list(plink_input)

        with Bench("Divide into chunks"):
            results = chunks.divide_into_chunks(inputs, 64)

        result_store = []

        key = "plink_inputs"
        
        # Todo: Delete below line when done testing
        Redis.delete(key)
        
        timestamp = datetime.datetime.utcnow().isoformat()

        # Pickle chunks of input SNPs (from Plink interator) and compress them
        #print("Starting adding loop")
        for part, result in enumerate(results):
            #data = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
            holder = pickle.dumps(dict(
                identifier = identifier,
                part = part,
                timestamp = timestamp,
                result = result
            ), pickle.HIGHEST_PROTOCOL)
            
            #print("Adding:", part)
            Redis.rpush(key, zlib.compress(holder))
        #print("End adding loop")
        #print("***** Added to {} queue *****".format(key))
        for snp, this_id in plink_input:
            #with Bench("part before association"):
            #if count > 1000:
            #    break
            count += 1

            percent_complete = (float(count) / total_snps) * 100
            #print("percent_complete: ", percent_complete)
            tempdata.store("percent_complete", percent_complete)

            #with Bench("actual association"):
            ps, ts = human_association(snp,
                                       n,
                                       keep,
                                       lmm_ob,
                                       pheno_vector,
                                       covariate_matrix,
                                       kinship_matrix,
                                       refit)

            #with Bench("after association"):
            p_values.append(ps)
            t_stats.append(ts)
        
    return p_values, t_stats


#class HumanAssociation(object):
#    def __init__(self):
#        

def human_association(snp,
                      n,
                      keep,
                      lmm_ob,
                      pheno_vector,
                      covariate_matrix,
                      kinship_matrix,
                      refit):

    x = snp[keep].reshape((n,1))
    #x[[1,50,100,200,3000],:] = np.nan
    v = np.isnan(x).reshape((-1,))

    # Check SNPs for missing values
    if v.sum():
        keeps = True - v
        xs = x[keeps,:]
        # If no variation at this snp or all genotypes missing 
        if keeps.sum() <= 1 or xs.var() <= 1e-6:
            return np.nan, np.nan
            #p_values.append(np.nan)
            #t_stats.append(np.nan)
            #continue

        # Its ok to center the genotype -  I used options.normalizeGenotype to
        # force the removal of missing genotypes as opposed to replacing them with MAF.

        #if not options.normalizeGenotype:
        #    xs = (xs - xs.mean()) / np.sqrt(xs.var())

        filtered_pheno = pheno_vector[keeps]
        filtered_covariate_matrix = covariate_matrix[keeps,:]
        
        print("kinship_matrix shape is: ", pf(kinship_matrix.shape))
        print("keeps is: ", pf(keeps.shape))
        filtered_kinship_matrix = kinship_matrix[keeps,:][:,keeps]
        filtered_lmm_ob = lmm.LMM(filtered_pheno,filtered_kinship_matrix,X0=filtered_covariate_matrix)
        if refit:
            filtered_lmm_ob.fit(X=xs)
        else:
            #try:
            filtered_lmm_ob.fit()
            #except: pdb.set_trace()
        ts,ps,beta,betaVar = Ls.association(xs,returnBeta=True)
    else:
        if x.var() == 0:
            return np.nan, np.nan
            #p_values.append(np.nan)
            #t_stats.append(np.nan)
            #continue
        if refit:
            lmm_ob.fit(X=x)
        ts, ps, beta, betaVar = lmm_ob.association(x)
    return ps, ts


#def run(pheno_vector,
#        genotype_matrix,
#        restricted_max_likelihood=True,
#        refit=False,
#        temp_data=None):
    
def run_other_old(pheno_vector,
        genotype_matrix,
        restricted_max_likelihood=True,
        refit=False,
        tempdata=None      # <---- can not be None
        ):
    
    """Takes the phenotype vector and genotype matrix and returns a set of p-values and t-statistics
    
    restricted_max_likelihood -- whether to use restricted max likelihood; True or False
    refit -- whether to refit the variance component for each marker
    temp_data -- TempData object that stores the progress for each major step of the
    calculations ("calculate_kinship" and "GWAS" take the majority of time) 
    
    """
    
    print("Running the original LMM engine in run_other (old)")
    print("REML=",restricted_max_likelihood," REFIT=",refit)
    with Bench("Calculate Kinship"):
        kinship_matrix,genotype_matrix = calculate_kinship(genotype_matrix, tempdata)
    
    print("kinship_matrix: ", pf(kinship_matrix))
    print("kinship_matrix.shape: ", pf(kinship_matrix.shape))
    
    # with Bench("Create LMM object"):
    #     lmm_ob = LMM(pheno_vector, kinship_matrix)
    
    # with Bench("LMM_ob fitting"):
    #     lmm_ob.fit()

    print("run_other_old genotype_matrix: ", genotype_matrix.shape)
    print(genotype_matrix)

    with Bench("Doing GWAS"):
        t_stats, p_values = GWAS(pheno_vector,
                                      genotype_matrix,
                                      kinship_matrix,
                                      restricted_max_likelihood=True,
                                      refit=False,
                                      temp_data=tempdata)
    Bench().report()
    return p_values, t_stats

def run_other_new(pheno_vector,
        genotype_matrix,
        restricted_max_likelihood=True,
        refit=False,
        tempdata=None      # <---- can not be None
        ):
    
    """Takes the phenotype vector and genotype matrix and returns a set of p-values and t-statistics
    
    restricted_max_likelihood -- whether to use restricted max likelihood; True or False
    refit -- whether to refit the variance component for each marker
    temp_data -- TempData object that stores the progress for each major step of the
    calculations ("calculate_kinship" and "GWAS" take the majority of time) 
    
    """
    
    print("Running the new LMM2 engine in run_other_new")
    print("REML=",restricted_max_likelihood," REFIT=",refit)

    # Adjust phenotypes
    Y,G,keep = phenotype.remove_missing(pheno_vector,genotype_matrix,verbose=True)
    print("Removed missing phenotypes",Y.shape)

    # if options.maf_normalization:
    #     G = np.apply_along_axis( genotype.replace_missing_with_MAF, axis=0, arr=g )
    #     print "MAF replacements: \n",G
    # if not options.skip_genotype_normalization:
    # G = np.apply_along_axis( genotype.normalize, axis=1, arr=G)

    with Bench("Calculate Kinship"):
        K,G = calculate_kinship(G, tempdata)
    
    print("kinship_matrix: ", pf(K))
    print("kinship_matrix.shape: ", pf(K.shape))

    # with Bench("Create LMM object"):
    #     lmm_ob = lmm2.LMM2(Y,K)
    # with Bench("LMM_ob fitting"):
    #     lmm_ob.fit()

    print("run_other_new genotype_matrix: ", G.shape)
    print(G)

    with Bench("Doing GWAS"):
        t_stats, p_values = gwas.gwas(Y,
                                      G.T,
                                      K,
                                      restricted_max_likelihood=True,
                                      refit=False,verbose=True)
    Bench().report()
    return p_values, t_stats

# def matrixMult(A,B):
#     return np.dot(A,B)

def matrixMult(A,B):

    # If there is no fblas then we will revert to np.dot()

    try:
        linalg.fblas
    except AttributeError:
        return np.dot(A,B)

    #print("A is:", pf(A.shape))
    #print("B is:", pf(B.shape))

    # If the matrices are in Fortran order then the computations will be faster
    # when using dgemm.  Otherwise, the function will copy the matrix and that takes time.
    if not A.flags['F_CONTIGUOUS']:
       AA = A.T
       transA = True
    else:
       AA = A
       transA = False
    
    if not B.flags['F_CONTIGUOUS']:
       BB = B.T
       transB = True
    else:
       BB = B
       transB = False

    return linalg.fblas.dgemm(alpha=1.,a=AA,b=BB,trans_a=transA,trans_b=transB)


def calculate_kinship_new(genotype_matrix, temp_data=None):
    """ 
    Call the new kinship calculation where genotype_matrix contains
    inds (columns) by snps (rows).
    """
    print("call genotype.normalize")
    G = np.apply_along_axis( genotype.normalize, axis=0, arr=genotype_matrix)
    print("call calculate_kinship_new")
    return kinship(G.T,uses),G # G gets transposed, we'll turn this into an iterator (FIXME)

def calculate_kinship_old(genotype_matrix, temp_data=None):
    """
    genotype_matrix is an n x m matrix encoding SNP minor alleles.
    
    This function takes a matrix oF SNPs, imputes missing values with the maf,
    normalizes the resulting vectors and returns the RRM matrix.
    
    """
    print("call calculate_kinship_old")
    n = genotype_matrix.shape[0]
    m = genotype_matrix.shape[1]
    print("genotype 2D matrix n (inds) is:", n)
    print("genotype 2D matrix m (snps) is:", m)
    assert m>n, "n should be larger than m (snps>inds)"
    keep = []
    for counter in range(m):
        #print("type of genotype_matrix[:,counter]:", pf(genotype_matrix[:,counter]))
        #Checks if any values in column are not numbers
        not_number = np.isnan(genotype_matrix[:,counter])
        
        #Gets vector of values for column (no values in vector if not all values in col are numbers)
        marker_values = genotype_matrix[True - not_number, counter]
        #print("marker_values is:", pf(marker_values))
        
        #Gets mean of values in vector
        values_mean = marker_values.mean()

        genotype_matrix[not_number,counter] = values_mean
        vr = genotype_matrix[:,counter].var()
        if vr == 0:
            continue
        keep.append(counter)
        genotype_matrix[:,counter] = (genotype_matrix[:,counter] - values_mean) / np.sqrt(vr)
        
        percent_complete = int(round((counter/m)*45))
        if temp_data != None:
            temp_data.store("percent_complete", percent_complete)
        
    genotype_matrix = genotype_matrix[:,keep]
    print("After kinship (old) genotype_matrix: ", pf(genotype_matrix))
    kinship_matrix = np.dot(genotype_matrix, genotype_matrix.T) * 1.0/float(m)
    return kinship_matrix,genotype_matrix

calculate_kinship = calculate_kinship_new  # alias

def GWAS(pheno_vector,
         genotype_matrix,
         kinship_matrix,
         kinship_eigen_vals=None,
         kinship_eigen_vectors=None,
         covariate_matrix=None,
         restricted_max_likelihood=True,
         refit=False,
         temp_data=None):
    """
    Performs a basic GWAS scan using the LMM.  This function
    uses the LMM module to assess association at each SNP and
    does some simple cleanup, such as removing missing individuals
    per SNP and re-computing the eigen-decomp

    pheno_vector - n x 1 phenotype vector
    genotype_matrix - n x m SNP matrix
    kinship_matrix - n x n kinship matrix
    kinship_eigen_vals, kinship_eigen_vectors = linalg.eigh(K) - or the eigen vectors and values for K
    covariate_matrix - n x q covariate matrix
    restricted_max_likelihood - use restricted maximum likelihood
    refit - refit the variance component for each SNP
    
    """
    if kinship_eigen_vals == None:
        kinship_eigen_vals = []
    if kinship_eigen_vectors == None:
        kinship_eigen_vectors = []
    
    n = genotype_matrix.shape[0]
    m = genotype_matrix.shape[1]

    if covariate_matrix == None:
        covariate_matrix = np.ones((n,1))

    # Remove missing values in pheno_vector and adjust associated parameters
    v = np.isnan(pheno_vector)
    if v.sum():
        keep = True - v
        print(pheno_vector.shape,pheno_vector)
        print(keep.shape,keep)
        pheno_vector = pheno_vector[keep]
        #genotype_matrix = genotype_matrix[keep,:]
        #covariate_matrix = covariate_matrix[keep,:]
        #kinship_matrix = kinship_matrix[keep,:][:,keep]
        kinship_eigen_vals = []
        kinship_eigen_vectors = []

    lmm_ob = LMM(pheno_vector,
                 kinship_matrix,
                 kinship_eigen_vals,
                 kinship_eigen_vectors,
                 covariate_matrix)
    if not refit:
        lmm_ob.fit()

    p_values = []
    t_statistics = []
    
    n = genotype_matrix.shape[0]
    m = genotype_matrix.shape[1]
    
    for counter in range(m):
        x = genotype_matrix[:,counter].reshape((n, 1))
        v = np.isnan(x).reshape((-1,))
        if v.sum():
            keep = True - v
            xs = x[keep,:]
            if xs.var() == 0:
                p_values.append(0)
                t_statistics.append(np.nan)
                continue
            
            print(genotype_matrix.shape,pheno_vector.shape,keep.shape)

            pheno_vector = pheno_vector[keep]
            covariate_matrix = covariate_matrix[keep,:]
            kinship_matrix = kinship_matrix[keep,:][:,keep]
            lmm_ob_2 = LMM(pheno_vector,
                           kinship_matrix,
                           X0=covariate_matrix)
            if refit:
                lmm_ob_2.fit(X=xs)
            else:
                lmm_ob_2.fit()
            ts, ps, beta, betaVar = lmm_ob_2.association(xs, REML=restricted_max_likelihood)
        else:
            if x.var() == 0:
                p_values.append(0)
                t_statistics.append(np.nan)
                continue

            if refit:
                lmm_ob.fit(X=x)
            ts, ps, beta, betaVar = lmm_ob.association(x, REML=restricted_max_likelihood)
            
        percent_complete = 45 + int(round((counter/m)*55))
        temp_data.store("percent_complete", percent_complete)

        p_values.append(ps)
        t_statistics.append(ts)

    return t_statistics, p_values


class LMM:

    """
          This is a simple version of EMMA/fastLMM.  
          The main purpose of this module is to take a phenotype vector (Y), a set of covariates (X) and a kinship matrix (K)
          and to optimize this model by finding the maximum-likelihood estimates for the model parameters.
          There are three model parameters: heritability (h), covariate coefficients (beta) and the total
          phenotypic variance (sigma).
          Heritability as defined here is the proportion of the total variance (sigma) that is attributed to 
          the kinship matrix.
 
          For simplicity, we assume that everything being input is a numpy array.
          If this is not the case, the module may throw an error as conversion from list to numpy array
          is not done consistently.
 
    """
    def __init__(self,Y,K,Kva=[],Kve=[],X0=None,verbose=True):
 
       """
       The constructor takes a phenotype vector or array of size n.
       It takes a kinship matrix of size n x n.  Kva and Kve can be computed as Kva,Kve = linalg.eigh(K) and cached.
       If they are not provided, the constructor will calculate them.
       X0 is an optional covariate matrix of size n x q, where there are q covariates.
       When this parameter is not provided, the constructor will set X0 to an n x 1 matrix of all ones to represent a mean effect.
       """

       if X0 == None: X0 = np.ones(len(Y)).reshape(len(Y),1)
       self.verbose = verbose
 
       #x = Y != -9
       x = True - np.isnan(Y)
       #pdb.set_trace()
       if not x.sum() == len(Y):
          print("Removing %d missing values from Y\n" % ((True - x).sum()))
          if self.verbose: sys.stderr.write("Removing %d missing values from Y\n" % ((True - x).sum()))
          Y = Y[x]
          print("x: ", len(x))
          print("K: ", K.shape)
          #K = K[x,:][:,x]
          X0 = X0[x,:]
          Kva = []
          Kve = []
       self.nonmissing = x
 
       print("this K is:", K.shape, pf(K))
       
       if len(Kva) == 0 or len(Kve) == 0:
          # if self.verbose: sys.stderr.write("Obtaining eigendecomposition for %dx%d matrix\n" % (K.shape[0],K.shape[1]) )
          begin = time.time()
          # Kva,Kve = linalg.eigh(K)
          Kva,Kve = kvakve(K,uses)
          end = time.time()
          if self.verbose: sys.stderr.write("Total time: %0.3f\n" % (end - begin))
          print("sum(Kva),sum(Kve)=",sum(Kva),sum(Kve))

       self.K = K
       self.Kva = Kva
       self.Kve = Kve
       print("self.Kva is: ", self.Kva.shape, pf(self.Kva))
       print("self.Kve is: ", self.Kve.shape, pf(self.Kve))
       self.Y = Y
       self.X0 = X0
       self.N = self.K.shape[0]

       # ----> Below moved to kinship.kvakve(K)
       # if sum(self.Kva < 1e-6):
       #    if self.verbose: sys.stderr.write("Cleaning %d eigen values\n" % (sum(self.Kva < 0)))
       #    self.Kva[self.Kva < 1e-6] = 1e-6
 
       self.transform()

    def transform(self):
 
         """
            Computes a transformation on the phenotype vector and the covariate matrix.
            The transformation is obtained by left multiplying each parameter by the transpose of the 
            eigenvector matrix of K (the kinship).
         """
     
         self.Yt = matrixMult(self.Kve.T, self.Y)
         self.X0t = matrixMult(self.Kve.T, self.X0)
         self.X0t_stack = np.hstack([self.X0t, np.ones((self.N,1))])
         self.q = self.X0t.shape[1]

    def getMLSoln(self,h,X):
 
       """
          Obtains the maximum-likelihood estimates for the covariate coefficients (beta),
          the total variance of the trait (sigma) and also passes intermediates that can 
          be utilized in other functions. The input parameter h is a value between 0 and 1 and represents
          the heritability or the proportion of the total variance attributed to genetics.  The X is the 
          covariate matrix.
       """

       S = 1.0/(h*self.Kva + (1.0 - h))
       Xt = X.T*S
       XX = matrixMult(Xt,X)
       XX_i = linalg.inv(XX)
       beta =  matrixMult(matrixMult(XX_i,Xt),self.Yt)
       Yt = self.Yt - matrixMult(X,beta)
       Q = np.dot(Yt.T*S,Yt)
       sigma = Q * 1.0 / (float(self.N) - float(X.shape[1]))
       return beta,sigma,Q,XX_i,XX
 
    def LL_brent(self,h,X=None,REML=False): 
       #brent will not be bounded by the specified bracket.
       # I return a large number if we encounter h < 0 to avoid errors in LL computation during the search.
       if h < 0: return 1e6
       return -self.LL(h,X,stack=False,REML=REML)[0]
         
    def LL(self,h,X=None,stack=True,REML=False):
 
        """
           Computes the log-likelihood for a given heritability (h).  If X==None, then the 
           default X0t will be used.  If X is set and stack=True, then X0t will be matrix concatenated with
           the input X.  If stack is false, then X is used in place of X0t in the LL calculation.
           REML is computed by adding additional terms to the standard LL and can be computed by setting REML=True.
        """
 
        if X == None:
            X = self.X0t
        elif stack: 
            self.X0t_stack[:,(self.q)] = matrixMult(self.Kve.T,X)[:,0]
            X = self.X0t_stack
 
        n = float(self.N)
        q = float(X.shape[1])
        beta,sigma,Q,XX_i,XX = self.getMLSoln(h,X)
        LL = n*np.log(2*np.pi) + np.log(h*self.Kva + (1.0-h)).sum() + n + n*np.log(1.0/n * Q)
        LL = -0.5 * LL
 
        if REML:
            LL_REML_part = q*np.log(2.0*np.pi*sigma) + np.log(linalg.det(matrixMult(X.T,X))) - np.log(linalg.det(XX))
            LL = LL + 0.5*LL_REML_part

        return LL,beta,sigma,XX_i

    def getMax(self,H, X=None,REML=False):
 
        """
           Helper functions for .fit(...).  
           This function takes a set of LLs computed over a grid and finds possible regions 
           containing a maximum.  Within these regions, a Brent search is performed to find the 
           optimum.
  
        """
        n = len(self.LLs)
        HOpt = []
        for i in range(1,n-2):
            if self.LLs[i-1] < self.LLs[i] and self.LLs[i] > self.LLs[i+1]: 
                HOpt.append(optimize.brent(self.LL_brent,args=(X,REML),brack=(H[i-1],H[i+1])))
                if np.isnan(HOpt[-1][0]):
                    HOpt[-1][0] = [self.LLs[i-1]]

        if len(HOpt) > 1: 
            if self.verbose:
                sys.stderr.write("NOTE: Found multiple optima.  Returning first...\n")
            return HOpt[0]
        elif len(HOpt) == 1:
            return HOpt[0]
        elif self.LLs[0] > self.LLs[n-1]:
            return H[0]
        else:
            return H[n-1]

    def fit(self,X=None,ngrids=100,REML=True):
 
        """
            Finds the maximum-likelihood solution for the heritability (h) given the current parameters.
            X can be passed and will transformed and concatenated to X0t.  Otherwise, X0t is used as 
            the covariate matrix.
   
            This function calculates the LLs over a grid and then uses .getMax(...) to find the optimum.
            Given this optimum, the function computes the LL and associated ML solutions.
        """
     
        if X == None:
            X = self.X0t
        else: 
            #X = np.hstack([self.X0t,matrixMult(self.Kve.T, X)])
            self.X0t_stack[:,(self.q)] = matrixMult(self.Kve.T,X)[:,0]
            X = self.X0t_stack
  
        H = np.array(range(ngrids)) / float(ngrids)
        L = np.array([self.LL(h,X,stack=False,REML=REML)[0] for h in H])
        self.LLs = L
  
        hmax = self.getMax(H,X,REML)
        L,beta,sigma,betaSTDERR = self.LL(hmax,X,stack=False,REML=REML)
        
        self.H = H
        self.optH = hmax
        self.optLL = L
        self.optBeta = beta
        self.optSigma = sigma
  
        return hmax,beta,sigma,L

    def association(self,X, h = None, stack=True,REML=True, returnBeta=True):
 
        """
            Calculates association statitics for the SNPs encoded in the vector X of size n.
            If h == None, the optimal h stored in optH is used.
  
        """
        if stack: 
           #X = np.hstack([self.X0t,matrixMult(self.Kve.T, X)])
           self.X0t_stack[:,(self.q)] = matrixMult(self.Kve.T,X)[:,0]
           X = self.X0t_stack
           
        if h == None:
            h = self.optH
  
        L,beta,sigma,betaVAR = self.LL(h,X,stack=False,REML=REML)
        q  = len(beta)
        ts,ps = self.tstat(beta[q-1],betaVAR[q-1,q-1],sigma,q)
        
        if returnBeta:
            return ts,ps,beta[q-1].sum(),betaVAR[q-1,q-1].sum()*sigma
        return ts,ps

    def tstat(self,beta,var,sigma,q): 
 
          """
             Calculates a t-statistic and associated p-value given the estimate of beta and its standard error.
             This is actually an F-test, but when only one hypothesis is being performed, it reduces to a t-test.
          """
 
          ts = beta / np.sqrt(var * sigma)        
          ps = 2.0*(1.0 - stats.t.cdf(np.abs(ts), self.N-q))
          if not len(ts) == 1 or not len(ps) == 1:
              print("ts=",ts)
              print("ps=",ps)
              raise Exception("Something bad happened :(")
          return ts.sum(),ps.sum()

    def plotFit(self,color='b-',title=''):
 
       """
          Simple function to visualize the likelihood space.  It takes the LLs 
          calcualted over a grid and normalizes them by subtracting off the mean and exponentiating.
          The resulting "probabilities" are normalized to one and plotted against heritability.
          This can be seen as an approximation to the posterior distribuiton of heritability.
 
          For diagnostic purposes this lets you see if there is one distinct maximum or multiple 
          and what the variance of the parameter looks like.
       """
       import matplotlib.pyplot as pl
 
       mx = self.LLs.max()
       p = np.exp(self.LLs - mx)
       p = p/p.sum()
 
       pl.plot(self.H,p,color)
       pl.xlabel("Heritability")
       pl.ylabel("Probability of data")
       pl.title(title)


def gn2_redis(key,species,new_code=True):
    """
    Invoke pylmm using Redis as a container. new_code runs the new
    version
    """
    json_params = Redis.get(key)
    
    params = json.loads(json_params)
    
    tempdata = temp_data.TempData(params['temp_uuid'])

    print('kinship', np.array(params['kinship_matrix']))
    print('pheno', np.array(params['pheno_vector']))
    geno = np.array(params['genotype_matrix'])
    print('geno', geno.shape, geno)
    
    if species == "human" :
        ps, ts = run_human(pheno_vector = np.array(params['pheno_vector']),
                  covariate_matrix = np.array(params['covariate_matrix']),
                  plink_input_file = params['input_file_name'],
                  kinship_matrix = np.array(params['kinship_matrix']),
                  refit = params['refit'],
                  tempdata = tempdata)
    else:
        if new_code:
            ps, ts = run_other_new(pheno_vector = np.array(params['pheno_vector']),
                               genotype_matrix = geno,
                               restricted_max_likelihood = params['restricted_max_likelihood'],
                               refit = params['refit'],
                               tempdata = tempdata)
        else:
            ps, ts = run_other_old(pheno_vector = np.array(params['pheno_vector']),
                               genotype_matrix = geno,
                               restricted_max_likelihood = params['restricted_max_likelihood'],
                               refit = params['refit'],
                               tempdata = tempdata)
        
    results_key = "pylmm:results:" + params['temp_uuid']

    json_results = json.dumps(dict(p_values = ps,
                                   t_stats = ts))
    
    #Pushing json_results into a list where it is the only item because blpop needs a list
    Redis.rpush(results_key, json_results)
    Redis.expire(results_key, 60*60)
    return ps, ts

# This is the main function used by Genenetwork2 (with environment)
def gn2_main():
    parser = argparse.ArgumentParser(description='Run pyLMM')
    parser.add_argument('-k', '--key')
    parser.add_argument('-s', '--species')
    
    opts = parser.parse_args()
    
    key = opts.key
    species = opts.species

    gn2_redis(key,species)

def gn2_load_redis(key,species,kinship,pheno,geno,new_code=True):
    print("Loading Redis from parsed data")
    if kinship == None:
        k = None
    else:
        k = kinship.tolist()
    params = dict(pheno_vector = pheno.tolist(),
                  genotype_matrix = geno.tolist(),
                  kinship_matrix= k,
                  restricted_max_likelihood = True,
                  refit = False,
                  temp_uuid = "testrun_temp_uuid",
                        
                  # meta data
                  timestamp = datetime.datetime.now().isoformat(),
    )
            
    json_params = json.dumps(params)
    Redis.set(key, json_params)
    Redis.expire(key, 60*60)

    return gn2_redis(key,species,new_code)
    
if __name__ == '__main__':
    print("WARNING: Calling pylmm from lmm.py will become OBSOLETE, use runlmm.py instead!")
    if has_gn2:
        gn2_main()
    else:
        print("Run from runlmm.py instead")


