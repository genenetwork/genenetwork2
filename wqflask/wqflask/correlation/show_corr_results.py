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
from utility.type_checking import get_float, get_int, get_string

def set_template_vars(start_vars, correlation_data):
    corr_type = start_vars['corr_type']
    corr_method = start_vars['corr_sample_method']

    if start_vars['dataset'] == "Temp":
        this_dataset_ob = create_dataset(
            dataset_name="Temp", dataset_type="Temp", group_name=start_vars['group'])
    else:
        this_dataset_ob = create_dataset(dataset_name=start_vars['dataset'])
    this_trait = create_trait(dataset=this_dataset_ob,
                              name=start_vars['trait_id'])

    correlation_data['this_trait'] = jsonable(this_trait, this_dataset_ob)
    correlation_data['this_dataset'] = this_dataset_ob.as_monadic_dict().data

    target_dataset_ob = create_dataset(correlation_data['target_dataset'])
    correlation_data['target_dataset'] = target_dataset_ob.as_monadic_dict().data
    correlation_data['table_json'] = correlation_json_for_table(
        start_vars,
        correlation_data,
        target_dataset_ob)

    if target_dataset_ob.type == "ProbeSet":
        filter_cols = [7, 6]
    elif target_dataset_ob.type == "Publish":
        filter_cols = [6, 0]
    else:
        filter_cols = [4, 0]

    correlation_data['corr_method'] = corr_method
    correlation_data['filter_cols'] = filter_cols
    correlation_data['header_fields'] = get_header_fields(
        target_dataset_ob.type, correlation_data['corr_method'])
    correlation_data['formatted_corr_type'] = get_formatted_corr_type(
        corr_type, corr_method)

    return correlation_data


def apply_filters(trait, target_trait, target_dataset, **filters):
    def __p_val_filter__(p_lower, p_upper):

        return  not  (p_lower <= float(trait.get("corr_coefficient",0.0)) <= p_upper)

    def __min_filter__(min_expr):
        if (target_dataset['type'] in ["ProbeSet", "Publish"] and target_trait['mean']):
            return (min_expr != None) and (float(target_trait['mean']) < min_expr)

        return False

    def __location_filter__(location_type, location_chr,
                            min_location_mb, max_location_mb):

        if target_dataset["type"] in ["ProbeSet", "'Geno"] and location_type == "gene":

            return (
                ((location_chr!=None) and (target_trait["chr"]!=location_chr))
                     or
                ((min_location_mb!= None) and (
                    float(target_trait['mb']) < min_location_mb)
                    )

                     or
                    ((max_location_mb != None) and
                    (float(target_trait['mb']) > float(max_location_mb)
                     ))

                )
        elif target_dataset["type"] in ["ProbeSet", "Publish"]:

            return ((location_chr!=None) and (target_trait["lrs_chr"] != location_chr)
                  or 
                  ((min_location_mb != None) and (
                         float(target_trait['lrs_mb']) < float(min_location_mb)))
                  or
                ((max_location_mb != None) and (
                float(target_trait['lrs_mb']) > float(max_location_mb))
            )

                )
            
        return True

    if not target_trait:
        return True
    else:
        # check if one of the condition is not met i.e One is True
        return (__p_val_filter__(
            filters.get("p_range_lower"),
            filters.get("p_range_upper")
        )
            or
            (
                __min_filter__(
                    filters.get("min_expr")
                )
        )
            or
            __location_filter__(
                filters.get("location_type"),
                filters.get("location_chr"),
                filters.get("min_location_mb"),
                filters.get("max_location_mb")


        )
        )


def get_user_filters(start_vars):
    (min_expr, p_min, p_max) = (
        get_float(start_vars, 'min_expr'),
        get_float(start_vars, 'p_range_lower', -1.0),
        get_float(start_vars, 'p_range_upper', 1.0)
    )

    if all(keys in start_vars for keys in ["loc_chr",
                                           "min_loc_mb",
                                           "max_location_mb"]):

        location_chr = get_string(start_vars, "loc_chr")
        min_location_mb = get_int(start_vars, "min_loc_mb")
        max_location_mb = get_int(start_vars, "max_loc_mb")

    else:
        location_chr = min_location_mb = max_location_mb = None

    return {

        "min_expr": min_expr,
        "p_range_lower": p_min,
        "p_range_upper": p_max,
        "location_chr": location_chr,
        "location_type": start_vars['location_type'],
        "min_location_mb": min_location_mb,
        "max_location_mb": max_location_mb

    }


def generate_table_metadata(all_traits, dataset_metadata, dataset_obj):

    def __fetch_trait_data__(trait, dataset_obj):
        target_trait_ob = create_trait(dataset=dataset_obj,
                                       name=trait,
                                       get_qtl_info=True)
        return jsonable(target_trait_ob, dataset_obj)

    metadata = [__fetch_trait_data__(trait, dataset_obj) for
                trait in (all_traits ^ dataset_metadata.keys())]
    return (dataset_metadata | ({trait["name"]: trait for trait in metadata}))


def populate_table(dataset_metadata, target_dataset, this_dataset, corr_results, filters):

    def __populate_trait__(idx, trait):

        trait_name = list(trait.keys())[0]
        target_trait = dataset_metadata.get(trait_name)
        trait = trait[trait_name]
        if not apply_filters(trait, target_trait, target_dataset, **filters):
            results_dict = {}
            results_dict['index'] = idx + 1  #
            results_dict['trait_id'] = target_trait['name']
            results_dict['dataset'] = target_dataset['name']
            results_dict['hmac'] = hmac.data_hmac(
                '{}:{}'.format(target_trait['name'], target_dataset['name']))
            results_dict['sample_r'] = f"{float(trait.get('corr_coefficient',0.0)):.3f}"
            results_dict['num_overlap'] = trait.get('num_overlap', 0)
            results_dict['sample_p'] = f"{float(trait.get('p_value',0)):.3e}"
            if target_dataset['type'] == "ProbeSet":
                results_dict['symbol'] = target_trait['symbol']
                results_dict['description'] = "N/A"
                results_dict['location'] = target_trait['location']
                results_dict['mean'] = "N/A"
                results_dict['additive'] = "N/A"
                if target_trait['description']:
                    results_dict['description'] = target_trait['description']
                if target_trait['mean']:
                    results_dict['mean'] = f"{float(target_trait['mean']):.3f}"
                try:
                    results_dict['lod_score'] = f"{float(target_trait['lrs_score']) / 4.61:.1f}"
                except:
                    results_dict['lod_score'] = "N/A"
                results_dict['lrs_location'] = target_trait['lrs_location']
                if target_trait['additive']:
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
                results_dict['pubmed_text'] = target_trait["pubmed_text"]

                if target_trait["abbreviation"]:
                    results_dict = target_trait['abbreviation']

                if target_trait["description"] == target_trait['description']:
                    results_dict['description'] = target_trait['description']

                if target_trait["mean"]:
                    results_dict['mean'] = f"{float(target_trait['mean']):.3f}"

                if target_trait["authors"]:
                    authors_list = target_trait['authors'].split(',')
                    results_dict['authors_display'] = ", ".join(
                        authors_list[:6]) + ", et al." if len(authors_list) > 6 else target_trait['authors']

                if "pubmed_id" in target_trait:
                    results_dict['pubmed_link'] = target_trait['pubmed_link']
                    results_dict['pubmed_text'] = target_trait['pubmed_text']
                try:
                    results_dict["lod_score"] = f"{float(target_trait['lrs_score']) / 4.61:.1f}"
                except ValueError:
                    results_dict['lod_score'] = "N/A"
            else:
                results_dict['lrs_location'] = target_trait['lrs_location']

            return results_dict

    return [__populate_trait__(idx, trait)
            for (idx, trait) in enumerate(corr_results)]


def correlation_json_for_table(start_vars, correlation_data, target_dataset_ob):
    """Return JSON data for use with the DataTable in the correlation result page

    Keyword arguments:
    correlation_data -- Correlation results
    this_trait -- Trait being correlated against a dataset, as a dict
    this_dataset -- Dataset of this_trait, as a monadic dict
    target_dataset_ob - Target dataset, as a Dataset ob
    """
    this_dataset = correlation_data['this_dataset']

    traits = set()
    for trait in correlation_data["correlation_results"]:
        traits.add(list(trait)[0])

    dataset_metadata = generate_table_metadata(traits,
                                               correlation_data["traits_metadata"],
                                               target_dataset_ob)
    return json.dumps([result for result in (
        populate_table(dataset_metadata=dataset_metadata,
                       target_dataset=target_dataset_ob.as_monadic_dict().data,
                       this_dataset=correlation_data['this_dataset'],
                       corr_results=correlation_data['correlation_results'],
                       filters=get_user_filters(start_vars))) if result])


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
