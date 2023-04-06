"""module contains integration code for rust-gn3"""
import json
from functools import reduce

from flask import current_app

from utility.db_tools import mescape
from utility.db_tools import create_in_clause
from wqflask.correlation.correlation_functions\
    import get_trait_symbol_and_tissue_values
from wqflask.correlation.correlation_gn3_api import create_target_this_trait
from wqflask.correlation.correlation_gn3_api import lit_for_trait_list
from wqflask.correlation.correlation_gn3_api import do_lit_correlation
from wqflask.correlation.pre_computes import fetch_text_file
from wqflask.correlation.pre_computes import read_text_file
from wqflask.correlation.pre_computes import write_db_to_textfile
from gn3.computations.correlations import compute_all_lit_correlation
from gn3.computations.rust_correlation import run_correlation
from gn3.computations.rust_correlation import get_sample_corr_data
from gn3.computations.rust_correlation import parse_tissue_corr_data
from gn3.db_utils import database_connection

from wqflask.correlation.exceptions import WrongCorrelationType


def query_probes_metadata(dataset, trait_list):
    """query traits metadata in bulk for probeset"""

    if not bool(trait_list) or dataset.type!="ProbeSet":
        return []

    with database_connection(current_app.config["SQL_URI"]) as conn:
        with conn.cursor() as cursor:

            query = """
                    SELECT ProbeSet.Name,ProbeSet.Chr,ProbeSet.Mb,
                    ProbeSet.Symbol,ProbeSetXRef.mean,
                    CONCAT_WS('; ', ProbeSet.description, ProbeSet.Probe_Target_Description) AS description,
                    ProbeSetXRef.additive,ProbeSetXRef.LRS,Geno.Chr, Geno.Mb
                    FROM ProbeSet INNER JOIN ProbeSetXRef
                    ON ProbeSet.Id=ProbeSetXRef.ProbeSetId
                    INNER JOIN Geno
                    ON ProbeSetXRef.Locus = Geno.Name
                    INNER JOIN Species
                    ON Geno.SpeciesId = Species.Id
                    WHERE ProbeSet.Name in ({}) AND
                    Species.Name = %s AND
                    ProbeSetXRef.ProbeSetFreezeId IN (
                      SELECT ProbeSetFreeze.Id
                      FROM ProbeSetFreeze WHERE ProbeSetFreeze.Name = %s)
                """.format(", ".join(["%s"] * len(trait_list)))

            cursor.execute(query,
                           (tuple(trait_list) +
                            (dataset.group.species,) + (dataset.name,))
                           )

            return cursor.fetchall()


def get_metadata(dataset, traits):
    """Retrieve the metadata"""
    def __location__(probe_chr, probe_mb):
        if probe_mb:
            return f"Chr{probe_chr}: {probe_mb:.6f}"
        return f"Chr{probe_chr}: ???"

    return {trait_name: {
            "name": trait_name,
            "view": True,
            "symbol": symbol,
            "dataset": dataset.name,
            "dataset_name": dataset.shortname,
            "mean": mean,
            "description": description,
            "additive": additive,
            "lrs_score": f"{lrs:3.1f}" if lrs else "",
            "location": __location__(probe_chr, probe_mb),
            "chr": probe_chr,
            "mb": probe_mb,
            "lrs_location":f'Chr{chr_score}: {mb:{".6f" if mb  else ""}}',
            "lrs_chr": chr_score,
            "lrs_mb": mb

            } for trait_name, probe_chr, probe_mb, symbol, mean, description,
            additive, lrs, chr_score, mb
            in query_probes_metadata(dataset, traits)}


def chunk_dataset(dataset, steps, name):

    results = []

    query = """
            SELECT ProbeSetXRef.DataId,ProbeSet.Name
            FROM ProbeSet, ProbeSetXRef, ProbeSetFreeze
            WHERE ProbeSetFreeze.Name = '{}' AND
                  ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                  ProbeSetXRef.ProbeSetId = ProbeSet.Id
    """.format(name)

    with database_connection(current_app.config["SQL_URI"]) as conn:
        with conn.cursor() as curr:
            curr.execute(query)
            traits_name_dict = dict(curr.fetchall())

    for i in range(0, len(dataset), steps):
        matrix = list(dataset[i:i + steps])
        results.append([traits_name_dict[matrix[0][0]]] + [str(value)
                                                           for (trait_name, strain, value) in matrix])
    return results


def compute_top_n_sample(start_vars, dataset, trait_list):
    """check if dataset is of type probeset"""

    if dataset.type.lower() != "probeset":
        return {}

    def __fetch_sample_ids__(samples_vals, samples_group):
        sample_data = get_sample_corr_data(
            sample_type=samples_group,
            sample_data=json.loads(samples_vals),
            dataset_samples=dataset.group.all_samples_ordered())

        with database_connection(current_app.config["SQL_URI"]) as conn:
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

    if len(trait_list) == 0:
        return {}

    with database_connection(current_app.config["SQL_URI"]) as conn:
        with conn.cursor() as curr:
            # fetching strain data in bulk
            query = (
                "SELECT * from ProbeSetData "
                f"WHERE StrainID IN ({', '.join(['%s'] * len(sample_ids))}) "
                "AND Id IN ("
                "  SELECT ProbeSetXRef.DataId "
                "  FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze) "
                "  WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id "
                "  AND ProbeSetFreeze.Name = %s "
                "  AND ProbeSet.Name "
                f" IN ({', '.join(['%s'] * len(trait_list))}) "
                "  AND ProbeSet.Id = ProbeSetXRef.ProbeSetId"
                ")")
            curr.execute(
                query,
                tuple(sample_ids.values()) + (dataset.name,) + tuple(trait_list))

            corr_data = chunk_dataset(
                list(curr.fetchall()), len(sample_ids.values()), dataset.name)

        return run_correlation(
            corr_data, list(sample_data.values()), "pearson", ",")


def compute_top_n_lit(corr_results, target_dataset, this_trait) -> dict:
    if not __datasets_compatible_p__(this_trait.dataset, target_dataset, "lit"):
        return {}

    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, target_dataset)

    geneid_dict = {trait_name: geneid for (trait_name, geneid)
                   in geneid_dict.items() if
                   corr_results.get(trait_name)}
    with database_connection(current_app.config["SQL_URI"]) as conn:
        return reduce(
            lambda acc, corr: {**acc, **corr},
            compute_all_lit_correlation(
                conn=conn, trait_lists=list(geneid_dict.items()),
                species=species, gene_id=this_trait_geneid),
            {})

    return {}


def compute_top_n_tissue(target_dataset, this_trait, traits, method):
    # refactor lots of rpt
    if not __datasets_compatible_p__(this_trait.dataset, target_dataset, "tissue"):
        return {}

    trait_symbol_dict = dict({
        trait_name: symbol
        for (trait_name, symbol)
        in target_dataset.retrieve_genes("Symbol").items()
        if traits.get(trait_name)})

    corr_result_tissue_vals_dict = get_trait_symbol_and_tissue_values(
        symbol_list=list(trait_symbol_dict.values()))

    data = parse_tissue_corr_data(symbol_name=this_trait.symbol,
                                  symbol_dict=get_trait_symbol_and_tissue_values(
                                      symbol_list=[this_trait.symbol]),
                                  dataset_symbols=trait_symbol_dict,
                                  dataset_vals=corr_result_tissue_vals_dict)

    if data and data[0]:
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

    if this_dataset.group.f1list !=None:
        this_dataset.group.samplelist+= this_dataset.group.f1list

    if this_dataset.group.parlist!= None:
        this_dataset.group.samplelist+= this_dataset.group.parlist

    sample_data = get_sample_corr_data(
        sample_type=start_vars["corr_samples_group"],
        sample_data= json.loads(start_vars["sample_vals"]),
        dataset_samples=this_dataset.group.all_samples_ordered())

    if not bool(sample_data):
        return {}


    if target_dataset.type == "ProbeSet" and start_vars.get("use_cache") == "true":
        with database_connection(current_app.config["SQL_URI"]) as conn:
            file_path = fetch_text_file(target_dataset.name, conn)
            if file_path:
                (sample_vals, target_data) = read_text_file(
                    sample_data, file_path)

        
                return run_correlation(target_data, sample_vals,
                                       method, ",", corr_type, n_top)


            write_db_to_textfile(target_dataset.name, conn)
            file_path = fetch_text_file(target_dataset.name, conn)
            if file_path:
                (sample_vals, target_data) = read_text_file(
                    sample_data, file_path)


                return run_correlation(target_data, sample_vals,
                                       method, ",", corr_type, n_top)



    target_dataset.get_trait_data(list(sample_data.keys()))

    def __merge_key_and_values__(rows, current):
        wo_nones = [value for value in current[1]]
        if len(wo_nones) > 0:
            return rows + [[current[0]] + wo_nones]
        return rows

    target_data = reduce(
        __merge_key_and_values__, target_dataset.trait_data.items(), [])

    if len(target_data) == 0:
        return {}


    return run_correlation(
        target_data, list(sample_data.values()), method, ",", corr_type,
        n_top)


def __datasets_compatible_p__(trait_dataset, target_dataset, corr_method):
    return not (
        corr_method in ("tissue", "Tissue r", "Literature r", "lit")
        and (trait_dataset.type == "ProbeSet" and
             target_dataset.type in ("Publish", "Geno")))


def __compute_tissue_corr__(
        start_vars: dict, corr_type: str, method: str, n_top: int,
        target_trait_info: tuple):
    """Compute the tissue correlations"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info
    if not __datasets_compatible_p__(this_dataset, target_dataset, corr_type):
        raise WrongCorrelationType(this_trait, target_dataset, corr_type)

    trait_symbol_dict = target_dataset.retrieve_genes("Symbol")
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
    if not __datasets_compatible_p__(this_dataset, target_dataset, corr_type):
        raise WrongCorrelationType(this_trait, target_dataset, corr_type)

    target_dataset_type = target_dataset.type
    this_dataset_type = this_dataset.type
    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, target_dataset)

    with database_connection(current_app.config["SQL_URI"]) as conn:
        return reduce(
            lambda acc, lit: {**acc, **lit},
            compute_all_lit_correlation(
                conn=conn, trait_lists=list(geneid_dict.items()),
                species=species, gene_id=this_trait_geneid)[:n_top],
            {})
    return {}


def compute_correlation_rust(
        start_vars: dict, corr_type: str, method: str = "pearson",
        n_top: int = 500, should_compute_all: bool = False):
    """function to compute correlation"""
    target_trait_info = create_target_this_trait(start_vars)
    (this_dataset, this_trait, target_dataset, sample_data) = (
        target_trait_info)
    if not __datasets_compatible_p__(this_dataset, target_dataset, corr_type):
        raise WrongCorrelationType(this_trait, target_dataset, corr_type)

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
            if this_dataset.type == "ProbeSet":
                top_a = compute_top_n_tissue(
                    target_dataset, this_trait, results, method)

                top_b = compute_top_n_lit(results, target_dataset, this_trait)
            else:
                pass

        elif corr_type == "lit":

            # currently fails for lit

            top_a = compute_top_n_sample(
                start_vars, target_dataset, list(results.keys()))
            top_b = compute_top_n_tissue(
                target_dataset, this_trait, results, method)

        else:

            top_a = compute_top_n_sample(
                start_vars, target_dataset, list(results.keys()))

    return {
        "correlation_results": merge_results(
            results, top_a, top_b),
        "this_trait": this_trait.name,
        "target_dataset": start_vars['corr_dataset'],
        "traits_metadata": get_metadata(target_dataset, list(results.keys())),
        "return_results": n_top
    }
