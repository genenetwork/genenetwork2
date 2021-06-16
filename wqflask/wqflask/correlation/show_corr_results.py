# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Dr. Robert W. Williams at rwilliams@uthsc.edu
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)

import json

from base.trait import create_trait, jsonable
from base.data_set import create_dataset

from utility import hmac

def set_template_vars(start_vars, correlation_data):
    corr_type = start_vars['corr_type']
    corr_method = start_vars['corr_sample_method']

    this_dataset_ob = create_dataset(dataset_name=start_vars['dataset'])
    this_trait = create_trait(dataset=this_dataset_ob,
                              name=start_vars['trait_id'])

    correlation_data['this_trait'] = jsonable(this_trait, this_dataset_ob)
    correlation_data['this_dataset'] = this_dataset_ob.as_dict()

    target_dataset_ob = create_dataset(correlation_data['target_dataset'])
    correlation_data['target_dataset'] = target_dataset_ob.as_dict()

    table_json = correlation_json_for_table(correlation_data,
                                            correlation_data['this_trait'],
                                            correlation_data['this_dataset'],
                                            target_dataset_ob)

    correlation_data['table_json'] = table_json

    if target_dataset_ob.type == "ProbeSet":
        filter_cols = [7, 6]
    elif target_dataset_ob.type == "Publish":
        filter_cols = [6, 0]
    else:
        filter_cols = [4, 0]

    correlation_data['corr_method'] = corr_method
    correlation_data['filter_cols'] = filter_cols
    correlation_data['header_fields'] = get_header_fields(target_dataset_ob.type, correlation_data['corr_method'])
    correlation_data['formatted_corr_type'] = get_formatted_corr_type(corr_type, corr_method)

    return correlation_data

def correlation_json_for_table(correlation_data, this_trait, this_dataset, target_dataset_ob):
    """Return JSON data for use with the DataTable in the correlation result page

    Keyword arguments:
    correlation_data -- Correlation results
    this_trait -- Trait being correlated against a dataset, as a dict
    this_dataset -- Dataset of this_trait, as a dict
    target_dataset_ob - Target dataset, as a Dataset ob
    """
    this_trait = correlation_data['this_trait']
    this_dataset = correlation_data['this_dataset']
    target_dataset = target_dataset_ob.as_dict()

    corr_results = correlation_data['correlation_results']
    results_list = []
    for i, trait_dict in enumerate(corr_results):
        trait_name = list(trait_dict.keys())[0]
        trait = trait_dict[trait_name]
        target_trait_ob = create_trait(dataset=target_dataset_ob,
                                       name=trait_name,
                                       get_qtl_info=True)
        target_trait = jsonable(target_trait_ob, target_dataset_ob)
        if target_trait['view'] == False:
            continue
        results_dict = {}
        results_dict['index'] = i + 1
        results_dict['trait_id'] = target_trait['name']
        results_dict['dataset'] = target_dataset['name']
        results_dict['hmac'] = hmac.data_hmac(
            '{}:{}'.format(target_trait['name'], target_dataset['name']))
        results_dict['sample_r'] = f"{float(trait['corr_coeffient']):.3f}"
        results_dict['num_overlap'] = trait['num_overlap']
        results_dict['sample_p'] = f"{float(trait['p_value']):.3e}"
        if target_dataset['type'] == "ProbeSet":
            results_dict['symbol'] = target_trait['symbol']
            results_dict['description'] = "N/A"
            results_dict['location'] = target_trait['location']
            results_dict['mean'] = "N/A"
            results_dict['additive'] = "N/A"
            if bool(target_trait['description']):
                results_dict['description'] = target_trait['description']
            if bool(target_trait['mean']):
                results_dict['mean'] = f"{float(target_trait['mean']):.3f}"
            try:
                results_dict['lod_score'] = f"{float(target_trait['lrs_score']) / 4.61:.1f}"
            except:
                results_dict['lod_score'] = "N/A"
            results_dict['lrs_location'] = target_trait['lrs_location']
            if bool(target_trait['additive']):
                results_dict['additive'] = f"{float(target_trait['additive']):.3f}"
            results_dict['lit_corr'] = "--"
            results_dict['tissue_corr'] = "--"
            results_dict['tissue_pvalue'] = "--"
            if this_dataset['type'] == "ProbeSet":
                if 'lit_corr' in trait:
                    results_dict['lit_corr'] = f"{float(trait['lit_corr']):.3f}"
                if 'tissue_corr' in trait:
                    results_dict['tissue_corr'] = f"{float(trait['tissue_corr']):.3f}"
                    results_dict['tissue_pvalue'] = f"{float(trait['tissue_p_val']):.3e}"
        elif target_dataset['type'] == "Publish":
            results_dict['abbreviation_display'] = "N/A"
            results_dict['description'] = "N/A"
            results_dict['mean'] = "N/A"
            results_dict['authors_display'] = "N/A"
            results_dict['additive'] = "N/A"
            results_dict['pubmed_link'] = "N/A"
            results_dict['pubmed_text'] = "N/A"

            if bool(target_trait['abbreviation']):
                results_dict['abbreviation_display'] = target_trait['abbreviation']
            if bool(target_trait['description']):
                results_dict['description'] = target_trait['description']
            if bool(target_trait['mean']):
                results_dict['mean'] = f"{float(target_trait['mean']):.3f}"
            if bool(target_trait['authors']):
                authors_list = target_trait['authors'].split(',')
                if len(authors_list) > 6:
                    results_dict['authors_display'] = ", ".join(
                        authors_list[:6]) + ", et al."
                else:
                    results_dict['authors_display'] = target_trait['authors']
            if 'pubmed_id' in target_trait:
                results_dict['pubmed_link'] = target_trait['pubmed_link']
                results_dict['pubmed_text'] = target_trait['pubmed_text']
            try:
                results_dict['lod_score'] = f"{float(target_trait['lrs_score']) / 4.61:.1f}"
            except:
                results_dict['lod_score'] = "N/A"
            results_dict['lrs_location'] = target_trait['lrs_location']
            if bool(target_trait['additive']):
                results_dict['additive'] = f"{float(target_trait['additive']):.3f}"
        else:
            results_dict['location'] = target_trait['lrs_location']

        results_list.append(results_dict)

    return json.dumps(results_list)

# def do_bicor(this_trait_vals, target_trait_vals):
#     r_library = ro.r["library"]             # Map the library function
#     r_options = ro.r["options"]             # Map the options function

#     r_library("WGCNA")
#     r_bicor = ro.r["bicorAndPvalue"]        # Map the bicorAndPvalue function

#     r_options(stringsAsFactors=False)

#     this_vals = ro.Vector(this_trait_vals)
#     target_vals = ro.Vector(target_trait_vals)

#     the_r, the_p, _fisher_transform, _the_t, _n_obs = [
#         numpy.asarray(x) for x in r_bicor(x=this_vals, y=target_vals)]

#     return the_r, the_p


def generate_corr_json(corr_results, this_trait, dataset, target_dataset, for_api=False):
    results_list = []
    for i, trait in enumerate(corr_results):
        if trait.view == False:
            continue
        results_dict = {}
        results_dict['index'] = i + 1
        results_dict['trait_id'] = trait.name
        results_dict['dataset'] = trait.dataset.name
        results_dict['hmac'] = hmac.data_hmac(
            '{}:{}'.format(trait.name, trait.dataset.name))
        if target_dataset.type == "ProbeSet":
            results_dict['symbol'] = trait.symbol
            results_dict['description'] = "N/A"
            results_dict['location'] = trait.location_repr
            results_dict['mean'] = "N/A"
            results_dict['additive'] = "N/A"
            if bool(trait.description_display):
                results_dict['description'] = trait.description_display
            if bool(trait.mean):
                results_dict['mean'] = f"{float(trait.mean):.3f}"
            try:
                results_dict['lod_score'] = f"{float(trait.LRS_score_repr) / 4.61:.1f}"
            except:
                results_dict['lod_score'] = "N/A"
            results_dict['lrs_location'] = trait.LRS_location_repr
            if bool(trait.additive):
                results_dict['additive'] = f"{float(trait.additive):.3f}"
            results_dict['sample_r'] = f"{float(trait.sample_r):.3f}"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = f"{float(trait.sample_p):.3e}"
            results_dict['lit_corr'] = "--"
            results_dict['tissue_corr'] = "--"
            results_dict['tissue_pvalue'] = "--"
            if bool(trait.lit_corr):
                results_dict['lit_corr'] = f"{float(trait.lit_corr):.3f}"
            if bool(trait.tissue_corr):
                results_dict['tissue_corr'] = f"{float(trait.tissue_corr):.3f}"
                results_dict['tissue_pvalue'] = f"{float(trait.tissue_pvalue):.3e}"
        elif target_dataset.type == "Publish":
            results_dict['abbreviation_display'] = "N/A"
            results_dict['description'] = "N/A"
            results_dict['mean'] = "N/A"
            results_dict['authors_display'] = "N/A"
            results_dict['additive'] = "N/A"
            if for_api:
                results_dict['pubmed_id'] = "N/A"
                results_dict['year'] = "N/A"
            else:
                results_dict['pubmed_link'] = "N/A"
                results_dict['pubmed_text'] = "N/A"

            if bool(trait.abbreviation):
                results_dict['abbreviation_display'] = trait.abbreviation
            if bool(trait.description_display):
                results_dict['description'] = trait.description_display
            if bool(trait.mean):
                results_dict['mean'] = f"{float(trait.mean):.3f}"
            if bool(trait.authors):
                authors_list = trait.authors.split(',')
                if len(authors_list) > 6:
                    results_dict['authors_display'] = ", ".join(
                        authors_list[:6]) + ", et al."
                else:
                    results_dict['authors_display'] = trait.authors
            if bool(trait.pubmed_id):
                if for_api:
                    results_dict['pubmed_id'] = trait.pubmed_id
                    results_dict['year'] = trait.pubmed_text
                else:
                    results_dict['pubmed_link'] = trait.pubmed_link
                    results_dict['pubmed_text'] = trait.pubmed_text
            try:
                results_dict['lod_score'] = f"{float(trait.LRS_score_repr) / 4.61:.1f}"
            except:
                results_dict['lod_score'] = "N/A"
            results_dict['lrs_location'] = trait.LRS_location_repr
            if bool(trait.additive):
                results_dict['additive'] = f"{float(trait.additive):.3f}"
            results_dict['sample_r'] = f"{float(trait.sample_r):.3f}"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = f"{float(trait.sample_p):.3e}"
        else:
            results_dict['location'] = trait.location_repr
            results_dict['sample_r'] = f"{float(trait.sample_r):.3f}"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = f"{float(trait.sample_p):.3e}"

        results_list.append(results_dict)

    return json.dumps(results_list)


def get_formatted_corr_type(corr_type, corr_method):
    formatted_corr_type = ""
    if corr_type == "lit":
        formatted_corr_type += "Literature Correlation "
    elif corr_type == "tissue":
        formatted_corr_type += "Tissue Correlation "
    elif corr_type == "sample":
        formatted_corr_type += "Genetic Correlation "

    if corr_method == "pearson":
        formatted_corr_type += "(Pearson's r)"
    elif corr_method == "spearman":
        formatted_corr_type += "(Spearman's rho)"
    elif corr_method == "bicor":
        formatted_corr_type += "(Biweight r)"

    return formatted_corr_type


def get_header_fields(data_type, corr_method):
    if data_type == "ProbeSet":
        if corr_method == "spearman":
            header_fields = ['Index',
                             'Record',
                             'Symbol',
                             'Description',
                             'Location',
                             'Mean',
                             'Sample rho',
                             'N',
                             'Sample p(rho)',
                             'Lit rho',
                             'Tissue rho',
                             'Tissue p(rho)',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']
        else:
            header_fields = ['Index',
                             'Record',
                             'Symbol',
                             'Description',
                             'Location',
                             'Mean',
                             'Sample r',
                             'N',
                             'Sample p(r)',
                             'Lit r',
                             'Tissue r',
                             'Tissue p(r)',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']
    elif data_type == "Publish":
        if corr_method == "spearman":
            header_fields = ['Index',
                             'Record',
                             'Abbreviation',
                             'Description',
                             'Mean',
                             'Authors',
                             'Year',
                             'Sample rho',
                             'N',
                             'Sample p(rho)',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']
        else:
            header_fields = ['Index',
                             'Record',
                             'Abbreviation',
                             'Description',
                             'Mean',
                             'Authors',
                             'Year',
                             'Sample r',
                             'N',
                             'Sample p(r)',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']

    else:
        if corr_method == "spearman":
            header_fields = ['Index',
                             'ID',
                             'Location',
                             'Sample rho',
                             'N',
                             'Sample p(rho)']
        else:
            header_fields = ['Index',
                             'ID',
                             'Location',
                             'Sample r',
                             'N',
                             'Sample p(r)']

    return header_fields
