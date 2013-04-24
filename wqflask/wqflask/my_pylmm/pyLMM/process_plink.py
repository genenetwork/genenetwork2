from __future__ import absolute_import, print_function, division

import cPickle as pickle
import redis
Redis = redis.Redis()

from wqflask.my_pylmm.pyLMM import lmm

lmm_vars_pickled = Redis.get("lmm_vars")


plink_pickled = Redis.lpop("plink_inputs")

plink_data = pickle.loads(plink_pickled)


ps, ts = lmm.human_association(snp,
                                n,
                                keep,
                                lmm_ob,
                                pheno_vector,
                                covariate_matrix,
                                kinship_matrix,
                                refit)