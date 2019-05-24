from __future__ import absolute_import, division, print_function

import string

from base import data_set
from base import webqtlConfig
from base.trait import GeneralTrait, retrieve_sample_data

from utility import helper_functions
from wqflask.marker_regression import gemma_mapping, rqtl_mapping, qtlreaper_mapping, plink_mapping

import utility.logger
logger = utility.logger.getLogger(__name__ )

def do_mapping_for_api(start_vars):
    assert('db' in start_vars)
    assert('trait_id' in start_vars)

    dataset = data_set.create_dataset(dataset_name = start_vars['db'])
    dataset.group.get_markers()
    this_trait = GeneralTrait(dataset = dataset, name = start_vars['trait_id'])
    this_trait = retrieve_sample_data(this_trait, dataset)

    samples = []
    vals = []

    for sample in dataset.group.samplelist:
        in_trait_data = False
        for item in this_trait.data:
            if this_trait.data[item].name == sample:
                value = str(this_trait.data[item].value)
                samples.append(item)
                vals.append(value)
                in_trait_data = True
                break
        if not in_trait_data:
            vals.append("x")

    mapping_params = initialize_parameters(start_vars, dataset, this_trait)

    covariates = "" #ZS: It seems to take an empty string as default. This should probably be changed.

    if mapping_params['mapping_method'] == "gemma":
        header_row = ["name", "chr", "Mb", "lod_score", "p_value"]
        if mapping_params['use_loco'] == "True": #ZS: gemma_mapping returns both results and the filename for LOCO, so need to only grab the former for api
            result_markers = gemma_mapping.run_gemma(this_trait, dataset, samples, vals, covariates, mapping_params['use_loco'], mapping_params['maf'])[0]
        else:
            result_markers = gemma_mapping.run_gemma(this_trait, dataset, samples, vals, covariates, mapping_params['use_loco'], mapping_params['maf'])
    elif mapping_params['mapping_method'] == "rqtl":
        header_row = ["name", "chr", "Mb", "lod_score"]
        if mapping_params['num_perm'] > 0:
            _sperm_output, _suggestive, _significant, result_markers = rqtl_mapping.run_rqtl_geno(vals, dataset, mapping_params['rqtl_method'], mapping_params['rqtl_model'], 
                                                                                        mapping_params['perm_check'], mapping_params['num_perm'], 
                                                                                        mapping_params['do_control'], mapping_params['control_marker'], 
                                                                                        mapping_params['manhattan_plot'], mapping_params['pair_scan'])
        else:
            result_markers = rqtl_mapping.run_rqtl_geno(vals, dataset, mapping_params['rqtl_method'], mapping_params['rqtl_model'], 
                                                 mapping_params['perm_check'], mapping_params['num_perm'], 
                                                 mapping_params['do_control'], mapping_params['control_marker'], 
                                                 mapping_params['manhattan_plot'], mapping_params['pair_scan'])

    output_rows = []
    output_rows.append(header_row)
    for marker in result_markers:
        this_row = [marker[header] for header in header_row]
        output_rows.append(this_row)

    return output_rows


def initialize_parameters(start_vars, dataset, this_trait):
    mapping_params = {}
    mapping_params['mapping_method'] = "gemma"
    if 'method' in start_vars:
        mapping_params['mapping_method'] = start_vars['method']

    if mapping_params['mapping_method'] == "rqtl":
        mapping_params['rqtl_method'] = "hk"
        mapping_params['rqtl_model'] = "normal"
        mapping_params['do_control'] = False
        mapping_params['control_marker'] = ""
        mapping_params['manhattan_plot'] = True
        mapping_params['pair_scan'] = False
        if 'rqtl_method' in start_vars:
            mapping_params['rqtl_method'] = start_vars['rqtl_method']
        if 'rqtl_model' in start_vars:
            mapping_params['rqtl_model'] = start_vars['rqtl_model']
        if 'control_marker' in start_vars:
            mapping_params['control_marker'] = start_vars['control_marker']
            mapping_params['do_control'] = True
        if 'pair_scan' in start_vars:
            if start_vars['pair_scan'].lower() == "true":
                mapping_params['pair_scan'] = True

        if 'interval_mapping' in start_vars:
            if start_vars['interval_mapping'].lower() == "true":
                mapping_params['manhattan_plot'] = False
        elif 'manhattan_plot' in start_vars:
            if start_vars['manhattan_plot'].lower() != "true":
                mapping_params['manhattan_plot'] = False

    mapping_params['maf'] = 0.01
    if 'maf' in start_vars:
        mapping_params['maf'] = start_vars['maf'] # Minor allele frequency

    mapping_params['use_loco'] = False
    if 'use_loco' in start_vars:
        if start_vars['use_loco'].lower() != "false":
            mapping_params['use_loco'] = start_vars['use_loco']

    mapping_params['num_perm'] = 0
    mapping_params['perm_check'] = False
    if 'num_perm' in start_vars:
        try:
            mapping_params['num_perm'] = int(start_vars['num_perm'])
            mapping_params['perm_check'] = "ON"
        except:
            mapping_params['perm_check'] = False

    return mapping_params
    

