from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import string
import sys
import datetime
import os
import collections
import uuid

import numpy as np
from scipy import linalg

import cPickle as pickle

import simplejson as json

from redis import Redis
Redis = Redis()

from base.trait import GeneralTrait
from base import data_set
from base import species
from base import webqtlConfig
from utility import webqtlUtil
from wqflask.my_pylmm.data import prep_data
from wqflask.my_pylmm.pyLMM import lmm
from wqflask.my_pylmm.pyLMM import input
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data

from utility.benchmark import Bench


class MarkerRegression(object):

    def __init__(self, start_vars, temp_uuid):

        helper_functions.get_species_dataset_trait(self, start_vars)

        #tempdata = temp_data.TempData(temp_uuid)
        
        self.samples = [] # Want only ones with values
        self.vals = []

        for sample in self.dataset.group.samplelist:
            value = start_vars['value:' + sample]
            self.samples.append(str(sample))
            self.vals.append(value)
 
        self.mapping_method = start_vars['method']
        print("self.mapping_method:", self.mapping_method)
 
        if self.mapping_method == "gemma":
            qtl_results = self.run_gemma()
        elif self.mapping_method == "pylmm":
            #self.qtl_results = self.gen_data(tempdata)
            qtl_results = self.gen_data(str(temp_uuid))
        
        self.lod_cutoff = self.get_lod_score_cutoff()
        self.filtered_markers = []
        for marker in qtl_results:
            #if marker['lod_score'] > self.lod_cutoff:
            if marker['lod_score'] > 1:
                self.filtered_markers.append(marker)
                
        print("filtered_markers:", self.filtered_markers)

        #Get chromosome lengths for drawing the manhattan plot
        chromosome_mb_lengths = {}
        for key in self.species.chromosomes.chromosomes.keys():
            chromosome_mb_lengths[key] = self.species.chromosomes.chromosomes[key].mb_length
        
        self.js_data = dict(
            chromosomes = chromosome_mb_lengths,
            qtl_results = self.filtered_markers,
        )

    def run_gemma(self):
        """Generates p-values for each marker using GEMMA"""
        
        #filename = webqtlUtil.genRandStr("{}_{}_".format(self.dataset.group.name, self.this_trait.name))
        self.gen_pheno_txt_file()

        os.chdir("/home/zas1024/gene/web/gemma")

        gemma_command = './gemma -bfile %s -k output_%s.cXX.txt -lmm 1 -o %s_output' % (
                                                                                                 self.dataset.group.name,
                                                                                                 self.dataset.group.name,
                                                                                                 self.dataset.group.name)
        print("gemma_command:" + gemma_command)
        
        os.system(gemma_command)
        
        included_markers, p_values = self.parse_gemma_output()
        
        self.dataset.group.get_specified_markers(markers = included_markers)
        
        #for marker in self.dataset.group.markers.markers:
        #    if marker['name'] not in included_markers:
        #        print("marker:", marker)
        #        self.dataset.group.markers.markers.remove(marker)
        #        #del self.dataset.group.markers.markers[marker]
        
        self.dataset.group.markers.add_pvalues(p_values)

        return self.dataset.group.markers.markers


    def parse_gemma_output(self):
        included_markers = []
        p_values = []
        with open("/home/zas1024/gene/web/gemma/output/{}_output.assoc.txt".format(self.dataset.group.name)) as output_file:
            for line in output_file:
                if line.startswith("chr"):
                    continue
                else:
                    included_markers.append(line.split("\t")[1])
                    p_values.append(float(line.split("\t")[10]))
                    #p_values[line.split("\t")[1]] = float(line.split("\t")[10])
        print("p_values: ", p_values)
        return included_markers, p_values

    def gen_pheno_txt_file(self):
        """Generates phenotype file for GEMMA"""
        
        #with open("/home/zas1024/gene/web/gemma/tmp_pheno/{}.txt".format(filename), "w") as outfile:
        #    for sample, i in enumerate(self.samples):
        #        print("sample:" + str(i))
        #        print("self.vals[i]:" + str(self.vals[sample]))
        #        outfile.write(str(i) + "\t" + str(self.vals[sample]) + "\n")
                
        with open("/home/zas1024/gene/web/gemma/{}.fam".format(self.dataset.group.name), "w") as outfile:
            for i, sample in enumerate(self.samples):
                outfile.write(str(sample) + " " + str(sample) + " 0 0 0 " + str(self.vals[i]) + "\n")

    #def gen_plink_for_gemma(self, filename):
    #    
    #    make_bed = "/home/zas1024/plink/plink --file /home/zas1024/plink/%s --noweb --no-fid --no-parents --no-sex --no-pheno --pheno %s%s.txt --out %s%s --make-bed" % (webqtlConfig.HTMLPATH,
    #                                                                                                                                             webqtlConfig.HTMLPATH,
    #                                                                                                                                             self.dataset.group.name,
    #                                                                                                                                             webqtlConfig.TMPDIR,
    #                                                                                                                                             filename,
    #                                                                                                                                             webqtlConfig.TMPDIR,
    #                                                                                                                                             filename)
    #
    #
    
    #def gen_data(self, tempdata):
    def gen_data(self, temp_uuid):
        """Generates p-values for each marker"""

        self.dataset.group.get_markers()

        pheno_vector = np.array([val == "x" and np.nan or float(val) for val in self.vals])

        #lmm_uuid = str(uuid.uuid4())

        key = "pylmm:input:" + temp_uuid
        print("key is:", pf(key))
        #with Bench("Loading cache"):
        #    result = Redis.get(key)

        if self.dataset.group.species == "human":
            p_values, t_stats = self.gen_human_results(pheno_vector, key, temp_uuid)
            #p_values = self.trim_results(p_values)
            
        else:
            genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]
            
            no_val_samples = self.identify_empty_samples()
            trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)
            
            genotype_matrix = np.array(trimmed_genotype_data).T

            #print("pheno_vector: ", pf(pheno_vector))
            #print("genotype_matrix: ", pf(genotype_matrix))
            #print("genotype_matrix.shape: ", pf(genotype_matrix.shape))

            #params = {"pheno_vector": pheno_vector,
            #            "genotype_matrix": genotype_matrix,
            #            "restricted_max_likelihood": True,
            #            "refit": False,
            #            "temp_data": tempdata}
            
            params = dict(pheno_vector = pheno_vector.tolist(),
                        genotype_matrix = genotype_matrix.tolist(),
                        restricted_max_likelihood = True,
                        refit = False,
                        temp_uuid = temp_uuid,
                        
                        # meta data
                        timestamp = datetime.datetime.now().isoformat(),
                        )
            
            json_params = json.dumps(params)
            print("json_params:", json_params)
            Redis.set(key, json_params)
            Redis.expire(key, 60*60)
            print("before printing command")

            command = 'python /home/zas1024/gene/wqflask/wqflask/my_pylmm/pyLMM/lmm.py --key {} --species {}'.format(key,
                                                                                                                    "other")
            print("command is:", command)
            print("after printing command")

            os.system(command)

            #t_stats, p_values = lmm.run(key)
            #lmm.run(key)
            
            json_results = Redis.blpop("pylmm:results:" + temp_uuid, 45*60)
            results = json.loads(json_results[1])
            p_values = [float(result) for result in results['p_values']]
            print("p_values:", p_values)
            #p_values = self.trim_results(p_values)
            t_stats = results['t_stats']
            
            #t_stats, p_values = lmm.run(
            #    pheno_vector,
            #    genotype_matrix,
            #    restricted_max_likelihood=True,
            #    refit=False,
            #    temp_data=tempdata
            #)
            #print("p_values:", p_values)

        self.dataset.group.markers.add_pvalues(p_values)
        
        self.get_lod_score_cutoff()
        
        return self.dataset.group.markers.markers

    def trim_results(self, p_values):
        print("len_p_values:", len(p_values))
        if len(p_values) > 500:
            p_values.sort(reverse=True)
            trimmed_values = p_values[:500]
        
        return trimmed_values

    #def gen_human_results(self, pheno_vector, tempdata):
    def gen_human_results(self, pheno_vector, key, temp_uuid):
        file_base = os.path.join(webqtlConfig.PYLMM_PATH, self.dataset.group.name)

        plink_input = input.plink(file_base, type='b')
        input_file_name = os.path.join(webqtlConfig.SNP_PATH, self.dataset.group.name + ".snps.gz")

        pheno_vector = pheno_vector.reshape((len(pheno_vector), 1))
        covariate_matrix = np.ones((pheno_vector.shape[0],1))
        kinship_matrix = np.fromfile(open(file_base + '.kin','r'),sep=" ")
        kinship_matrix.resize((len(plink_input.indivs),len(plink_input.indivs)))

        print("Before creating params")

        params = dict(pheno_vector = pheno_vector.tolist(),
                    covariate_matrix = covariate_matrix.tolist(),
                    input_file_name = input_file_name,
                    kinship_matrix = kinship_matrix.tolist(),
                    refit = False,
                    temp_uuid = temp_uuid,
                        
                    # meta data
                    timestamp = datetime.datetime.now().isoformat(),
                    )
        
        print("After creating params")
        
        json_params = json.dumps(params)
        Redis.set(key, json_params)
        Redis.expire(key, 60*60)

        print("Before creating the command")

        command = 'python /home/zas1024/gene/wqflask/wqflask/my_pylmm/pyLMM/lmm.py --key {} --species {}'.format(key,
                                                                                                                "human")
        
        print("command is:", command)
        
        os.system(command)
        
        json_results = Redis.blpop("pylmm:results:" + temp_uuid, 45*60)
        results = json.loads(json_results[1])
        t_stats = results['t_stats']
        p_values = results['p_values']
        

        #p_values, t_stats = lmm.run_human(key)

        #p_values, t_stats = lmm.run_human(
        #        pheno_vector,
        #        covariate_matrix,
        #        input_file_name,
        #        kinship_matrix,
        #        loading_progress=tempdata
        #    )

        return p_values, t_stats

    def get_lod_score_cutoff(self):
        high_qtl_count = 0
        for marker in self.dataset.group.markers.markers:
            if marker['lod_score'] > 1:
                high_qtl_count += 1

        if high_qtl_count > 1000:
            return 1
        else:
            return 0

    def identify_empty_samples(self):
        no_val_samples = []
        for sample_count, val in enumerate(self.vals):
            if val == "x":
                no_val_samples.append(sample_count)
        return no_val_samples
        
    def trim_genotypes(self, genotype_data, no_value_samples):
        trimmed_genotype_data = []
        for marker in genotype_data:
            new_genotypes = []
            for item_count, genotype in enumerate(marker):
                if item_count in no_value_samples:
                    continue
                try:
                    genotype = float(genotype)
                except ValueError:
                    genotype = np.nan
                    pass
                new_genotypes.append(genotype)
            trimmed_genotype_data.append(new_genotypes)
        return trimmed_genotype_data
    
def create_snp_iterator_file(group):
    plink_file_base = os.path.join(webqtlConfig.PYLMM_PATH, group)
    plink_input = input.plink(plink_file_base, type='b')
    
    data = dict(plink_input = list(plink_input),
                numSNPs = plink_input.numSNPs)
    
    #input_dict = {}
    #
    #input_dict['plink_input'] = list(plink_input)
    #input_dict['numSNPs'] = plink_input.numSNPs
    #
    
    snp_file_base = os.path.join(webqtlConfig.SNP_PATH, group + ".snps.gz")
    
    with gzip.open(snp_file_base, "wb") as fh:
        pickle.dump(data, fh, pickle.HIGHEST_PROTOCOL)

#if __name__ == '__main__':
#    import cPickle as pickle
#    import gzip
#    create_snp_iterator_file("HLC")
    
if __name__ == '__main__':
    import cPickle as pickle
    import gzip
    create_snp_iterator_file("HLC")
