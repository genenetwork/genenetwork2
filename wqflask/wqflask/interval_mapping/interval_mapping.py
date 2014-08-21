from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import string
import sys
import os
import collections

import numpy as np
from scipy import linalg
import rpy2.robjects

import simplejson as json

#from redis import Redis


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


class IntervalMapping(object):

    def __init__(self, start_vars, temp_uuid):

        #Currently only getting trait data for one trait, but will need
        #to change this to accept multiple traits once the collection page is implemented
        helper_functions.get_species_dataset_trait(self, start_vars)

        tempdata = temp_data.TempData(temp_uuid)
        
        self.samples = [] # Want only ones with values
        self.vals = []

        for sample in self.dataset.group.samplelist:
            value = start_vars['value:' + sample]
            self.samples.append(str(sample))
            self.vals.append(value)
 
        print("start_vars:", start_vars)
 
        self.set_options(start_vars)
 
        self.json_data = {}
 
        #if self.method == "qtl_reaper":
        self.json_data['lodnames'] = ['lod.hk']
        self.gen_reaper_results(tempdata)
        #else:
        #    self.gen_pylmm_results(tempdata)
        #self.gen_qtl_results(tempdata)

        #Get chromosome lengths for drawing the interval map plot
        chromosome_mb_lengths = {}
        self.json_data['chrnames'] = []
        for key in self.species.chromosomes.chromosomes.keys():
            self.json_data['chrnames'].append([self.species.chromosomes.chromosomes[key].name, self.species.chromosomes.chromosomes[key].mb_length])
            
            chromosome_mb_lengths[key] = self.species.chromosomes.chromosomes[key].mb_length
        
        #print("self.qtl_results:", self.qtl_results)
        
        print("JSON DATA:", self.json_data)
        
        #os.chdir(webqtlConfig.TMPDIR)
        json_filename = webqtlUtil.genRandStr(prefix="intmap_")
        json.dumps(self.json_data, webqtlConfig.TMPDIR + json_filename)
        
        self.js_data = dict(
            manhattan_plot = self.manhattan_plot,
            additive = self.additive,
            chromosomes = chromosome_mb_lengths,
            qtl_results = self.qtl_results,
            json_data = self.json_data
            #lrs_lod = self.lrs_lod,
        )

    def set_options(self, start_vars):
        """Sets various options (physical/genetic mapping, # permutations, which chromosome"""
        
        #self.plot_scale = start_vars['scale']
        #if self.plotScale == 'physic' and not fd.genotype.Mbmap:
        #    self.plotScale = 'morgan'
        #self.method = start_vars['mapping_method']
        self.num_permutations = int(start_vars['num_perm'])
        #self.do_bootstrap = start_vars['do_bootstrap']
        #self.selected_chr = start_vars['chromosome']
        if start_vars['manhattan_plot'] == "true":
            self.manhattan_plot = True
        else:
            self.manhattan_plot = False
        if start_vars['display_additive'] == "yes":
            self.additive = True
        else:
            self.additive = False
        if 'control_locus' in start_vars:
            self.control_locus = start_vars['control_locus']
        else:
            self.control_locus = None
        #self.weighted_regression = start_vars['weighted']
        #self.lrs_lod = start_vars['lrs_lod']


    def gen_qtl_results(self, tempdata):
        """Generates qtl results for plotting interval map"""

        self.dataset.group.get_markers()
        genotype = self.dataset.group.read_genotype_file()

        samples, values, variances = self.this_trait.export_informative()

        trimmed_samples = []
        trimmed_values = []
        for i in range(0, len(samples)):
            if samples[i] in self.dataset.group.samplelist:
                trimmed_samples.append(samples[i])
                trimmed_values.append(values[i])

        #if self.weighted_regression:
        #    self.lrs_array = self.genotype.permutation(strains = trimmed_samples,
        #                                                         trait = trimmed_values, 
        #                                                         variance = _vars,
        #                                                         nperm=self.num_permutations)
        #else:
        self.lrs_array = genotype.permutation(strains = trimmed_samples,
                                                   trait = trimmed_values, 
                                                   nperm= self.num_permutations)
        self.suggestive = self.lrs_array[int(self.num_permutations*0.37-1)]
        self.significant = self.lrs_array[int(self.num_permutations*0.95-1)]

        print("samples:", trimmed_samples)

        if self.control_locus:
            #if self.weighted_regression:
            #    self.qtl_results = self.dataset.genotype.regression(strains = samples,
            #                                                  trait = values,
            #                                                  variance = variances,
            #                                                  control = self.control_locus)
            #else:
            reaper_results = genotype.regression(strains = trimmed_samples,
                                                          trait = trimmed_values,
                                                          control = self.control_locus)
        else:
            #if self.weighted_regression:
            #    self.qtl_results = self.dataset.genotype.regression(strains = samples,
            #                                                  trait = values,
            #                                                  variance = variances)
            #else:
            print("strains:", trimmed_samples)
            print("trait:", trimmed_values)
            reaper_results = genotype.regression(strains = trimmed_samples,
                                                          trait = trimmed_values)

        #Need to convert the QTL objects that qtl reaper returns into a json serializable dictionary
        self.qtl_results = []
        self.json_data['chr'] = []
        self.json_data['pos'] = []
        self.json_data['lod.hk'] = []
        self.json_data['additive'] = []
        self.json_data['markernames'] = []
        for qtl in reaper_results:
            reaper_locus = qtl.locus
            #if reaper_locus.chr == "20":
            #    print("changing to X")
            #    self.json_data['chr'].append("X")
            #else:
            #    self.json_data['chr'].append(reaper_locus.chr)
            ##self.json_data['chr'].append(reaper_locus.chr)
            self.json_data['pos'].append(reaper_locus.Mb)
            self.json_data['lod.hk'].append(qtl.lrs)
            self.json_data['markernames'].append(reaper_locus.name)
            if self.additive:
                self.json_data['additive'].append(qtl.additive)
            locus = {"name":reaper_locus.name, "chr":reaper_locus.chr, "cM":reaper_locus.cM, "Mb":reaper_locus.Mb}
            qtl = {"lrs": qtl.lrs, "locus": locus, "additive": qtl.additive}
            self.qtl_results.append(qtl)


    def gen_reaper_results(self, tempdata):
        genotype = self.dataset.group.read_genotype_file()

        samples, values, variances = self.this_trait.export_informative()

        trimmed_samples = []
        trimmed_values = []
        for i in range(0, len(samples)):
            if samples[i] in self.dataset.group.samplelist:
                trimmed_samples.append(samples[i])
                trimmed_values.append(values[i])
                
        self.lrs_array = genotype.permutation(strains = trimmed_samples,
                                                   trait = trimmed_values, 
                                                   nperm= self.num_permutations)
        
        self.suggestive = self.lrs_array[int(self.num_permutations*0.37-1)]
        self.significant = self.lrs_array[int(self.num_permutations*0.95-1)]
        self.json_data['suggestive'] = self.suggestive
        self.json_data['significant'] = self.significant

        print("samples:", trimmed_samples)

        if self.control_locus:
            reaper_results = genotype.regression(strains = trimmed_samples,
                                                          trait = trimmed_values,
                                                          control = self.control_locus)
        else:
            reaper_results = genotype.regression(strains = trimmed_samples,
                                                          trait = trimmed_values)

        self.json_data['chr'] = []
        self.json_data['pos'] = []
        self.json_data['lod.hk'] = []
        self.json_data['additive'] = []
        self.json_data['markernames'] = []

        #Need to convert the QTL objects that qtl reaper returns into a json serializable dictionary
        self.qtl_results = []
        for qtl in reaper_results:
            reaper_locus = qtl.locus
            self.json_data['chr'].append(reaper_locus.chr)
            self.json_data['pos'].append(reaper_locus.Mb)
            self.json_data['lod.hk'].append(qtl.lrs)
            self.json_data['markernames'].append(reaper_locus.name)
            if self.additive:
                self.json_data['additive'].append(qtl.additive)
            locus = {"name":reaper_locus.name, "chr":reaper_locus.chr, "cM":reaper_locus.cM, "Mb":reaper_locus.Mb}
            qtl = {"lrs_value": qtl.lrs, "chr":reaper_locus.chr, "Mb":reaper_locus.Mb,
                   "cM":reaper_locus.cM, "name":reaper_locus.name, "additive":qtl.additive}
            self.qtl_results.append(qtl)
            
    def gen_pylmm_results(self, tempdata):
        print("USING PYLMM")
        self.dataset.group.get_markers()
        
        pheno_vector = np.array([val == "x" and np.nan or float(val) for val in self.vals])
        if self.dataset.group.species == "human":
            p_values, t_stats = self.gen_human_results(pheno_vector, tempdata)
        else:
            genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]

            no_val_samples = self.identify_empty_samples()
            trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)
            
            genotype_matrix = np.array(trimmed_genotype_data).T
            
            t_stats, p_values = lmm.run(
                pheno_vector,
                genotype_matrix,
                restricted_max_likelihood=True,
                refit=False,
                temp_data=tempdata
            )
            
            print("p_values:", p_values)
            self.dataset.group.markers.add_pvalues(p_values)
            self.qtl_results = self.dataset.group.markers.markers

    def gen_qtl_results_2(self, tempdata):
        """Generates qtl results for plotting interval map"""
    
        self.dataset.group.get_markers()
        self.dataset.read_genotype_file()
    
        pheno_vector = np.array([val == "x" and np.nan or float(val) for val in self.vals])
    
        #if self.dataset.group.species == "human":
        #    p_values, t_stats = self.gen_human_results(pheno_vector, tempdata)
        #else:
        genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]
        
        no_val_samples = self.identify_empty_samples()
        trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)
        
        genotype_matrix = np.array(trimmed_genotype_data).T
        
        t_stats, p_values = lmm.run(
            pheno_vector,
            genotype_matrix,
            restricted_max_likelihood=True,
            refit=False,
            temp_data=tempdata
        )
        
        self.dataset.group.markers.add_pvalues(p_values)
        
        self.qtl_results = self.dataset.group.markers.markers


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

    #def get_qtl_results(self):
    #    """Gets the LOD (or LRS) score at each marker in order do the qtl mapping"""
    #
    #    
    #    
    #    #self.genotype = self.genotype.addinterval()
    #    #resultSlice = []
    #    #controlGeno = []
    #    
    #    #if self.multipleInterval:
    #    #    self.suggestive = 0
    #    #    self.significance = 0
    #    #    if self.selectedChr > -1:
    #    #        self.genotype.chromosome = [self.genotype[self.selectedChr]]
    #    #else:
    #    #single interval mapping
    #    #try:
    #    #    self.suggestive = float(fd.formdata.getvalue('permSuggestive'))
    #    #    self.significance = float(fd.formdata.getvalue('permSignificance'))
    #    #except:
    #    #    self.suggestive = None
    #    #    self.significance = None
    #    
    #    #NOT DOING MULTIPLE TRAITS YET, BUT WILL NEED TO LATER
    #    #_strains, _vals, _vars = self.traitList[0].exportInformative(weightedRegression)
    #    
    #    #if webqtlUtil.ListNotNull(_vars):
    #    #    pass
    #    #else:
    #    #    weightedRegression = 0
    #    #    _strains, _vals, _vars = self.traitList[0].exportInformative()
    #        
    #    ##locate genotype of control Locus
    #    #if self.controlLocus:
    #    #    controlGeno2 = []
    #    #    _FIND = 0
    #    #    for _chr in self.genotype:
    #    #        for _locus in _chr:
    #    #            if _locus.name == self.controlLocus:
    #    #                controlGeno2 = _locus.genotype
    #    #                _FIND = 1
    #    #                break
    #    #        if _FIND:
    #    #            break
    #    #    if controlGeno2:
    #    #        _prgy = list(self.genotype.prgy)
    #    #        for _strain in _strains:
    #    #            _idx = _prgy.index(_strain)
    #    #            controlGeno.append(controlGeno2[_idx])
    #    #    else:
    #    #        return "The control marker you selected is not in the genofile."
    #    #
    #    #    
    #    #    if self.significance and self.suggestive:
    #    #        pass
    #    #    else:
    #    #        if self.permChecked:
    #    #            if weightedRegression:
    #    #                self.LRSArray = self.genotype.permutation(strains = _strains, trait = _vals, 
    #    #                    variance = _vars, nperm=fd.nperm)
    #    #            else:
    #    #                self.LRSArray = self.genotype.permutation(strains = _strains, trait = _vals, 
    #    #                    nperm=fd.nperm)
    #    #            self.suggestive = self.LRSArray[int(fd.nperm*0.37-1)]
    #    #            self.significance = self.LRSArray[int(fd.nperm*0.95-1)]
    #    #
    #    #        else:
    #    #            self.suggestive = 9.2
    #    #            self.significance = 16.1
    #    #
    #    #    #calculating bootstrap
    #    #    #from now on, genotype could only contain a single chromosome 
    #    #    #permutation need to be performed genome wide, this is not the case for bootstrap
    #    #    
    #    #    #due to the design of qtlreaper, composite regression need to be performed genome wide
    #    #    if not self.controlLocus and self.selectedChr > -1:
    #    #        self.genotype.chromosome = [self.genotype[self.selectedChr]]
    #    #    elif self.selectedChr > -1: #self.controlLocus and self.selectedChr > -1
    #    #        lociPerChr = map(len, self.genotype)
    #    #        resultSlice = reduce(lambda X, Y: X+Y, lociPerChr[:self.selectedChr], 0)
    #    #        resultSlice = [resultSlice,resultSlice+lociPerChr[self.selectedChr]]
    #    #    else:
    #    #        pass
    #        
    #    #calculate QTL for each trait
    #    self.qtl_results = []
    #
    #    #for thisTrait in self.traitList:
    #    _strains, _vals, _vars = thisTrait.exportInformative(weightedRegression)
    #    if self.controlLocus:
    #        if weightedRegression:
    #            qtlresult = self.genotype.regression(strains = _strains, trait = _vals, 
    #                    variance = _vars, control = self.controlLocus)
    #        else:
    #            qtlresult = self.genotype.regression(strains = _strains, trait = _vals,
    #                control = self.controlLocus)
    #        if resultSlice:
    #            qtlresult = qtlresult[resultSlice[0]:resultSlice[1]]
    #    else:
    #        if weightedRegression:
    #            qtlresult = self.genotype.regression(strains = _strains, trait = _vals, 
    #                    variance = _vars)
    #        else:
    #            qtlresult = self.genotype.regression(strains = _strains, trait = _vals)
    #
    #    self.qtlresults.append(qtlresult)
    #    
    #    if not self.multipleInterval:
    #        if self.controlLocus and self.selectedChr > -1:
    #            self.genotype.chromosome = [self.genotype[self.selectedChr]]
    #            
    #        if self.bootChecked:
    #            if controlGeno:
    #                self.bootResult = self.genotype.bootstrap(strains = _strains, trait = _vals,
    #                    control = controlGeno, nboot=fd.nboot)
    #            elif weightedRegression:
    #                self.bootResult = self.genotype.bootstrap(strains = _strains, trait = _vals, 
    #                    variance = _vars, nboot=fd.nboot)
    #            else:
    #                self.bootResult = self.genotype.bootstrap(strains = _strains, trait = _vals, 
    #                    nboot=fd.nboot)
    #        else:
    #            self.bootResult = []

