from __future__ import absolute_import, print_function, division

import sys
sys.path.append("../../..")

print("sys.path: ", sys.path)

import numpy as np

import zlib
import cPickle as pickle
import redis
Redis = redis.Redis()

import lmm

class ProcessLmmChunk(object):
    
    def __init__(self):
        self.get_snp_data()
        self.get_lmm_vars()
        
        keep = self.trim_matrices()
        
        self.do_association(keep)
        
        print("p_values is: ", self.p_values)
        
    def get_snp_data(self):
        plink_pickled = zlib.decompress(Redis.lpop("plink_inputs"))
        plink_data = pickle.loads(plink_pickled)
        
        self.snps = np.array(plink_data['result'])
        self.identifier = plink_data['identifier']
        
    def get_lmm_vars(self):
        lmm_vars_pickled = Redis.hget(self.identifier, "lmm_vars")
        lmm_vars = pickle.loads(lmm_vars_pickled)
        
        self.pheno_vector = np.array(lmm_vars['pheno_vector'])
        self.covariate_matrix = np.array(lmm_vars['covariate_matrix'])
        self.kinship_matrix = np.array(lmm_vars['kinship_matrix'])
        
    def trim_matrices(self):
        v = np.isnan(self.pheno_vector)
        keep = True - v
        keep = keep.reshape((len(keep),))
        
        if v.sum():
            self.pheno_vector = self.pheno_vector[keep]
            self.covariate_matrix = self.covariate_matrix[keep,:]
            self.kinship_matrix = self.kinship_matrix[keep,:][:,keep]

        return keep
    
    def do_association(self, keep):
        n = self.kinship_matrix.shape[0]
        lmm_ob = lmm.LMM(self.pheno_vector,
                    self.kinship_matrix,
                    self.covariate_matrix)
        lmm_ob.fit()
    
        self.p_values = []
        
        for snp in self.snps:
            snp = snp[0]
            p_value, t_stat = lmm.human_association(snp,
                                        n,
                                        keep,
                                        lmm_ob,
                                        self.pheno_vector,
                                        self.covariate_matrix,
                                        self.kinship_matrix,
                                        False)
        
            self.p_values.append(p_value)
            

#plink_pickled = zlib.decompress(Redis.lpop("plink_inputs"))
#
#plink_data = pickle.loads(plink_pickled)
#result = np.array(plink_data['result'])
#print("snp size is: ", result.shape)
#identifier = plink_data['identifier']
#
#lmm_vars_pickled = Redis.hget(identifier, "lmm_vars")
#lmm_vars = pickle.loads(lmm_vars_pickled)
#
#pheno_vector = np.array(lmm_vars['pheno_vector'])
#covariate_matrix = np.array(lmm_vars['covariate_matrix'])
#kinship_matrix = np.array(lmm_vars['kinship_matrix'])
#
#v = np.isnan(pheno_vector)
#keep = True - v
#keep = keep.reshape((len(keep),))
#print("keep is: ", keep)
#
#if v.sum():
#    pheno_vector = pheno_vector[keep]
#    covariate_matrix = covariate_matrix[keep,:]
#    kinship_matrix = kinship_matrix[keep,:][:,keep]
#
#n = kinship_matrix.shape[0]
#print("n is: ", n)
#lmm_ob = lmm.LMM(pheno_vector,
#            kinship_matrix,
#            covariate_matrix)
#lmm_ob.fit()
#
#p_values = []
#
#for snp in result:
#    snp = snp[0]
#    p_value, t_stat = lmm.human_association(snp,
#                                n,
#                                keep,
#                                lmm_ob,
#                                pheno_vector,
#                                covariate_matrix,
#                                kinship_matrix,
#                                False)
#
#    p_values.append(p_value)
    



