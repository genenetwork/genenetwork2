"""module that calls the gn3 api's to do the correlation """
import json

from wqflask.correlation import correlation_functions

from base import data_set

from base.trait import create_trait
from base.trait import retrieve_sample_data

from gn3.computations.correlations import compute_all_sample_correlation
from gn3.computations.correlations import map_shared_keys_to_values
from gn3.computations.correlations import compute_all_lit_correlation
from gn3.computations.correlations import compute_tissue_correlation
from gn3.db_utils import database_connector


def create_target_this_trait(start_vars):
    """this function creates the required trait and target dataset for correlation"""

    this_dataset = data_set.create_dataset(dataset_name=start_vars['dataset'])
    target_dataset = data_set.create_dataset(
        dataset_name=start_vars['corr_dataset'])
    this_trait = create_trait(dataset=this_dataset,
                              name=start_vars['trait_id'])
    sample_data = ()
    return (this_dataset, this_trait, target_dataset, sample_data)


def process_samples(start_vars, sample_names, excluded_samples=None):
    """process samples"""
    sample_data = {}
    if not excluded_samples:
        excluded_samples = ()
        sample_vals_dict = json.loads(start_vars["sample_vals"])
        for sample in sample_names:
            if sample not in excluded_samples:
                val = sample_vals_dict[sample]
                if not val.strip().lower() == "x":
                    sample_data[str(sample)] = float(val)
    return sample_data


def sample_for_trait_lists(corr_results, target_dataset,
                           this_trait, this_dataset, start_vars):
    """interface function for correlation on top results"""

    sample_data = process_samples(
        start_vars, this_dataset.group.samplelist)
    target_dataset.get_trait_data(list(sample_data.keys()))
    # should filter target traits from here
    _corr_results = corr_results

    this_trait = retrieve_sample_data(this_trait, this_dataset)

    this_trait_data = {
        "trait_sample_data": sample_data,
        "trait_id": start_vars["trait_id"]
    }
    results = map_shared_keys_to_values(
        target_dataset.samplelist, target_dataset.trait_data)
    correlation_results = compute_all_sample_correlation(corr_method="pearson",
                                                         this_trait=this_trait_data,
                                                         target_dataset=results)

    return correlation_results


def tissue_for_trait_lists(corr_results, this_dataset, this_trait):
    """interface function for doing tissue corr_results on trait_list"""
    trait_lists = dict([(list(corr_result)[0], True)
                        for corr_result in corr_results])
    # trait_lists = {list(corr_results)[0]: 1 for corr_result in corr_results}
    traits_symbol_dict = this_dataset.retrieve_genes("Symbol")
    traits_symbol_dict = dict({trait_name: symbol for (
        trait_name, symbol) in traits_symbol_dict.items() if trait_lists.get(trait_name)})
    primary_tissue_data, target_tissue_data = get_tissue_correlation_input(
        this_trait, traits_symbol_dict)
    corr_results = compute_tissue_correlation(
        primary_tissue_dict=primary_tissue_data,
        target_tissues_data=target_tissue_data,
        corr_method="pearson")
    return corr_results


def lit_for_trait_list(corr_results, this_dataset, this_trait):
    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, this_dataset)

    # trait_lists = {list(corr_results)[0]: 1 for corr_result in corr_results}
    trait_lists = dict([(list(corr_result)[0], True)
                        for corr_result in corr_results])

    geneid_dict = {trait_name: geneid for (trait_name, geneid) in geneid_dict.items() if
                   trait_lists.get(trait_name)}

    conn, _cursor_object = database_connector()

    with conn:

        correlation_results = compute_all_lit_correlation(
            conn=conn, trait_lists=list(geneid_dict.items()),
            species=species, gene_id=this_trait_geneid)

    return correlation_results


def compute_correlation(start_vars, method="pearson"):
    """compute correlation for to call gn3  api"""
    # pylint: disable-msg=too-many-locals

    corr_type = start_vars['corr_type']

    (this_dataset, this_trait, target_dataset,
     sample_data) = create_target_this_trait(start_vars)

    method = start_vars['corr_sample_method']
    corr_return_results = int(start_vars.get("corr_return_results", 100))
    corr_input_data = {}

    if corr_type == "sample":

        sample_data = process_samples(
            start_vars, this_dataset.group.samplelist)
        target_dataset.get_trait_data(list(sample_data.keys()))
        this_trait = retrieve_sample_data(this_trait, this_dataset)
        this_trait_data = {
            "trait_sample_data": sample_data,
            "trait_id": start_vars["trait_id"]
        }
        results = map_shared_keys_to_values(
            target_dataset.samplelist, target_dataset.trait_data)
        correlation_results = compute_all_sample_correlation(corr_method=method,
                                                             this_trait=this_trait_data,
                                                             target_dataset=results)

        # do tissue correaltion

        # code to be use later

        # tissue_result = tissue_for_trait_lists(
        #     correlation_results, this_dataset, this_trait)
        # # lit spoils the party so slow
        # lit_result = lit_for_trait_list(
        #     correlation_results, this_dataset, this_trait)


    elif corr_type == "tissue":
        trait_symbol_dict = this_dataset.retrieve_genes("Symbol")
        primary_tissue_data, target_tissue_data = get_tissue_correlation_input(
            this_trait, trait_symbol_dict)

        corr_input_data = {
            "primary_tissue": primary_tissue_data,
            "target_tissues_dict": target_tissue_data
        }
        correlation_results = compute_tissue_correlation(
            primary_tissue_dict=corr_input_data["primary_tissue"],
            target_tissues_data=corr_input_data[
                "target_tissues_dict"],
            corr_method=method

        )

    elif corr_type == "lit":
        (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
            this_trait, this_dataset)

        conn, _cursor_object = database_connector()
        with conn:
            correlation_results = compute_all_lit_correlation(
                conn=conn, trait_lists=list(geneid_dict.items()),
                species=species, gene_id=this_trait_geneid)

    return correlation_results[0:corr_return_results]


def do_lit_correlation(this_trait, this_dataset):
    """function for fetching lit inputs"""
    geneid_dict = this_dataset.retrieve_genes("GeneId")
    species = this_dataset.group.species.lower()
    trait_geneid = this_trait.geneid
    return (trait_geneid, geneid_dict, species)


def get_tissue_correlation_input(this_trait, trait_symbol_dict):
    """Gets tissue expression values for the primary trait and target tissues values"""
    primary_trait_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
        symbol_list=[this_trait.symbol])
    if this_trait.symbol.lower() in primary_trait_tissue_vals_dict:
        primary_trait_tissue_values = primary_trait_tissue_vals_dict[this_trait.symbol.lower(
        )]
        corr_result_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
            symbol_list=list(trait_symbol_dict.values()))
        primary_tissue_data = {
            "this_id": this_trait.name,
            "tissue_values": primary_trait_tissue_values

        }
        target_tissue_data = {
            "trait_symbol_dict": trait_symbol_dict,
            "symbol_tissue_vals_dict": corr_result_tissue_vals_dict
        }
        return (primary_tissue_data, target_tissue_data)
    return None
