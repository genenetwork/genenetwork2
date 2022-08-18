"""module contains integration code for rust-gn3"""
import json
from functools import reduce
from utility.db_tools import mescape
from utility.db_tools import create_in_clause
from wqflask.correlation.correlation_functions\
    import get_trait_symbol_and_tissue_values
from wqflask.correlation.correlation_gn3_api import create_target_this_trait
from wqflask.correlation.correlation_gn3_api import lit_for_trait_list
from wqflask.correlation.correlation_gn3_api import do_lit_correlation
from gn3.computations.correlations import compute_all_lit_correlation
from gn3.computations.rust_correlation import run_correlation
from gn3.computations.rust_correlation import get_sample_corr_data
from gn3.computations.rust_correlation import parse_tissue_corr_data
from gn3.db_utils import database_connector


def query_probes_metadata(dataset, results):

    """query traits metadata in bulk for probeset"""

    with database_connector() as conn:
        with conn.cursor() as cursor:

            query = """
                    SELECT ProbeSet.Name,ProbeSet.Chr,ProbeSet.Mb,
                    Symbol,mean,description,additive,LRS,Geno.Chr, Geno.Mb
                    from Geno, Species,ProbeSet,ProbeSetXRef,ProbeSetFreeze
                    where ProbeSet.Name in ({}) and
                    Species.Name = %s and
                    Geno.Name = ProbeSetXRef.Locus and
                    Geno.SpeciesId = Species.Id and
                    ProbeSet.Id=ProbeSetXRef.ProbeSetId and
                    ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId and
                    ProbeSetFreeze.Name = %s
                """.format(", ".join(["%s"] * len(trait_list)))

            cursor.execute(query,
                           (tuple(trait_list) +
                            (dataset.group.species,) + (dataset.name,))
                           )

            return cursor.fetchall()


def chunk_dataset(dataset, steps, name):

    results = []

    query = """
            SELECT ProbeSetXRef.DataId,ProbeSet.Name
            FROM ProbeSet, ProbeSetXRef, ProbeSetFreeze
            WHERE ProbeSetFreeze.Name = '{}' AND
                  ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                  ProbeSetXRef.ProbeSetId = ProbeSet.Id
    """.format(name)

    with database_connector() as conn:
        with conn.cursor() as curr:
            curr.execute(query)
            traits_name_dict = dict(curr.fetchall())

    for i in range(0, len(dataset), steps):
        matrix = list(dataset[i:i + steps])
        trait_name = traits_name_dict[matrix[0][0]]

        strains = [trait_name] + [str(value)
                                  for (trait_name, strain, value) in matrix]
        results.append(",".join(strains))

    return results


def compute_top_n_sample(start_vars, dataset, trait_list):
    """check if dataset is of type probeset"""

    if dataset.type.lower() != "probeset":
        return {}

    def __fetch_sample_ids__(samples_vals, samples_group):
        all_samples = json.loads(samples_vals)
        sample_data = get_sample_corr_data(
            sample_type=samples_group, all_samples=all_samples,
            dataset_samples=dataset.group.all_samples_ordered())

        with database_connector() as conn:
            with conn.cursor() as curr:
                curr.execute(
                    """
                    SELECT Strain.Name, Strain.Id FROM Strain, Species
                    WHERE Strain.Name IN {}
                    and Strain.SpeciesId=Species.Id
                    and Species.name = '{}'
                    """.format(create_in_clause(list(sample_data.keys())),
                               *mescape(dataset.group.species)))
                return (sample_data, dict(curr.fetchall()))

    (sample_data, sample_ids) = __fetch_sample_ids__(
        start_vars["sample_vals"], start_vars["corr_samples_group"])

    with database_connector() as conn:
        with conn.cursor() as curr:
            # fetching strain data in bulk
            curr.execute(
                """
                SELECT * from ProbeSetData
                where StrainID in {}
                and id in (SELECT ProbeSetXRef.DataId
                FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze)
                WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
                and ProbeSetFreeze.Name = '{}'
                and ProbeSet.Name in {}
                and ProbeSet.Id = ProbeSetXRef.ProbeSetId)
                """.format(
                    create_in_clause(list(sample_ids.values())),
                    dataset.name,
                    create_in_clause(trait_list)))

            corr_data = chunk_dataset(
                list(curr.fetchall()), len(sample_ids.values()), dataset.name)

        return run_correlation(
            corr_data, list(sample_data.values()), "pearson", ",")


def compute_top_n_lit(corr_results, this_dataset, this_trait) -> dict:
    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, this_dataset)

    geneid_dict = {trait_name: geneid for (trait_name, geneid)
                   in geneid_dict.items() if
                   corr_results.get(trait_name)}
    with database_connector() as conn:
        return reduce(
            lambda acc, corr: {**acc, **corr},
            compute_all_lit_correlation(
                conn=conn, trait_lists=list(geneid_dict.items()),
                species=species, gene_id=this_trait_geneid),
            {})

    return {}


def compute_top_n_tissue(this_dataset, this_trait, traits, method):

    # refactor lots of rpt

    trait_symbol_dict = dict({
        trait_name: symbol
        for (trait_name, symbol)
        in this_dataset.retrieve_genes("Symbol").items()
        if traits.get(trait_name)})

    corr_result_tissue_vals_dict = get_trait_symbol_and_tissue_values(
        symbol_list=list(trait_symbol_dict.values()))

    data = parse_tissue_corr_data(symbol_name=this_trait.symbol,
                                  symbol_dict=get_trait_symbol_and_tissue_values(
                                      symbol_list=[this_trait.symbol]),
                                  dataset_symbols=trait_symbol_dict,
                                  dataset_vals=corr_result_tissue_vals_dict)

    if data:
        return run_correlation(
            data[1], data[0], method, ",", "tissue")

    return {}


def merge_results(dict_a: dict, dict_b: dict, dict_c: dict) -> list[dict]:
    """code to merge diff corr  into individual dicts
    a"""

    def __merge__(trait_name, trait_corrs):
        return {
            trait_name: {
                **trait_corrs,
                **dict_b.get(trait_name, {}),
                **dict_c.get(trait_name, {})
            }
        }
    return [__merge__(tname, tcorrs) for tname, tcorrs in dict_a.items()]


def __compute_sample_corr__(
        start_vars: dict, corr_type: str, method: str, n_top: int,
        target_trait_info: tuple):
    """Compute the sample correlations"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info
    all_samples = json.loads(start_vars["sample_vals"])
    sample_data = get_sample_corr_data(
        sample_type=start_vars["corr_samples_group"], all_samples=all_samples,
        dataset_samples=this_dataset.group.all_samples_ordered())
    target_dataset.get_trait_data(list(sample_data.keys()))

    target_data = []
    for (key, val) in target_dataset.trait_data.items():
        lts = [key] + [str(x) for x in val]
        r = ",".join(lts)
        target_data.append(r)

    return run_correlation(
        target_data, list(sample_data.values()), method, ",", corr_type,
        n_top)


def __compute_tissue_corr__(
        start_vars: dict, corr_type: str, method: str, n_top: int,
        target_trait_info: tuple):
    """Compute the tissue correlations"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info
    trait_symbol_dict = this_dataset.retrieve_genes("Symbol")
    corr_result_tissue_vals_dict = get_trait_symbol_and_tissue_values(
        symbol_list=list(trait_symbol_dict.values()))

    data = parse_tissue_corr_data(
        symbol_name=this_trait.symbol,
        symbol_dict=get_trait_symbol_and_tissue_values(
            symbol_list=[this_trait.symbol]),
        dataset_symbols=trait_symbol_dict,
        dataset_vals=corr_result_tissue_vals_dict)

    if data:
        return run_correlation(data[1], data[0], method, ",", "tissue")
    return {}


def __compute_lit_corr__(
        start_vars: dict, corr_type: str, method: str, n_top: int,
        target_trait_info: tuple):
    """Compute the literature correlations"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info
    target_dataset_type = target_dataset.type
    this_dataset_type = this_dataset.type
    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, this_dataset)

    with database_connector() as conn:
        return reduce(
            lambda acc, lit: {**acc, **lit},
            compute_all_lit_correlation(
                conn=conn, trait_lists=list(geneid_dict.items()),
                species=species, gene_id=this_trait_geneid),
            {})
    return {}


def compute_correlation_rust(
        start_vars: dict, corr_type: str, method: str = "pearson",
        n_top: int = 500, should_compute_all: bool = False):
    """function to compute correlation"""
    target_trait_info = create_target_this_trait(start_vars)
    (this_dataset, this_trait, target_dataset, sample_data) = (
        target_trait_info)

    # Replace this with `match ...` once we hit Python 3.10
    corr_type_fns = {
        "sample": __compute_sample_corr__,
        "tissue": __compute_tissue_corr__,
        "lit": __compute_lit_corr__
    }
    results = corr_type_fns[corr_type](
        start_vars, corr_type, method, n_top, target_trait_info)

    # END: Replace this with `match ...` once we hit Python 3.10

    top_a = top_b = {}

    if should_compute_all:

        if corr_type == "sample":

            top_a = compute_top_n_tissue(
                this_dataset, this_trait, results, method)

            top_b = compute_top_n_lit(results, this_dataset, this_trait)

        elif corr_type == "lit":

            # currently fails for lit

            top_a = compute_top_n_sample(
                start_vars, target_dataset, list(results.keys()))
            top_b = compute_top_n_tissue(
                this_dataset, this_trait, results, method)

        else:

            top_a = compute_top_n_sample(
                start_vars, target_dataset, list(results.keys()))

            top_b = compute_top_n_lit(results, this_dataset, this_trait)

    return {
        "correlation_results": merge_results(
            results, top_a, top_b),
        "this_trait": this_trait.name,
        "target_dataset": start_vars['corr_dataset'],
        "return_results": n_top
    }
