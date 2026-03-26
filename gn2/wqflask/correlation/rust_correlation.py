"""module contains integration code for rust-gn3"""
import json
from functools import reduce

import requests
from flask import current_app

from gn_libs.mysqldb import database_connection

from gn2.utility.tools import SQL_URI
from gn2.utility.db_tools import mescape
from gn2.utility.db_tools import create_in_clause
from gn2.wqflask.correlation.correlation_functions\
    import get_trait_symbol_and_tissue_values
from gn2.wqflask.correlation.correlation_gn3_api import create_target_this_trait
from gn2.wqflask.correlation.correlation_gn3_api import lit_for_trait_list
from gn2.wqflask.correlation.correlation_gn3_api import do_lit_correlation
from gn2.wqflask.correlation.pre_computes import fetch_text_file
from gn2.wqflask.correlation.pre_computes import read_text_file
from gn2.wqflask.correlation.pre_computes import write_db_to_textfile
from gn2.wqflask.correlation.pre_computes import read_trait_metadata
from gn2.wqflask.correlation.pre_computes import cache_trait_metadata
from gn3.computations.correlations import compute_all_lit_correlation
from gn3.computations.rust_correlation import run_correlation
from gn3.computations.rust_correlation import get_sample_corr_data
from gn3.computations.rust_correlation import parse_tissue_corr_data

from gn2.wqflask.correlation.exceptions import WrongCorrelationType


def query_probes_metadata(dataset, trait_list):
    """query traits metadata in bulk for probeset"""

    if not bool(trait_list) or dataset.type != "ProbeSet":
        return []

    with database_connection(SQL_URI) as conn:
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
    cached_metadata = read_trait_metadata(dataset.name)
    to_fetch_metadata = list(
        set(traits).difference(list(cached_metadata.keys())))
    if to_fetch_metadata:
        results = {**({trait_name: {
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
            "lrs_location": f'Chr{chr_score}: {mb:{".6f" if mb  else ""}}',
            "lrs_chr": chr_score,
            "lrs_mb": mb

        } for trait_name, probe_chr, probe_mb, symbol, mean, description,
            additive, lrs, chr_score, mb
            in query_probes_metadata(dataset, to_fetch_metadata)}), **cached_metadata}
        cache_trait_metadata(dataset.name, results)
        return results
    return cached_metadata


def chunk_dataset(dataset, steps, name):

    results = []

    query = """
            SELECT ProbeSetXRef.DataId,ProbeSet.Name
            FROM ProbeSet, ProbeSetXRef, ProbeSetFreeze
            WHERE ProbeSetFreeze.Name = '{}' AND
                  ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                  ProbeSetXRef.ProbeSetId = ProbeSet.Id
    """.format(name)

    with database_connection(SQL_URI) as conn:
        with conn.cursor() as curr:
            curr.execute(query)
            traits_name_dict = dict(curr.fetchall())

    for i in range(0, len(dataset), steps):
        matrix = list(dataset[i:i + steps])
        results.append([traits_name_dict[matrix[0][0]]] + [str(value)
                                                           for (trait_name, strain, value) in matrix])
    return results


def compute_top_n_sample(start_vars, dataset, trait_list, tmpdir):
    """check if dataset is of type probeset"""

    if dataset.type.lower() != "probeset":
        return {}

    def __fetch_sample_ids__(samples_vals, samples_group):
        sample_data = get_sample_corr_data(
            sample_type=samples_group,
            sample_data=json.loads(samples_vals),
            dataset_samples=dataset.group.all_samples_ordered())

        with database_connection(SQL_URI) as conn:
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

    with database_connection(SQL_URI) as conn:
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
            corr_data, list(sample_data.values()), "pearson", ",", tmpdir)


def compute_top_n_lit(corr_results, target_dataset, this_trait, tmpdir) -> dict:
    if not __datasets_compatible_p__(this_trait.dataset, target_dataset, "lit"):
        return {}

    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, target_dataset)

    geneid_dict = {trait_name: geneid for (trait_name, geneid)
                   in geneid_dict.items() if
                   corr_results.get(trait_name)}
    with database_connection(SQL_URI) as conn:
        return reduce(
            lambda acc, corr: {**acc, **corr},
            compute_all_lit_correlation(
                conn=conn, trait_lists=list(geneid_dict.items()),
                species=species, gene_id=this_trait_geneid),
            {})

    return {}


def compute_top_n_tissue(target_dataset, this_trait, traits, method, tmpdir):
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
            data[1], data[0], method, ",", tmpdir, corr_type="tissue")

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


def __datasets_compatible_p__(trait_dataset, target_dataset, corr_method):
    return not (
        corr_method in ("tissue", "Tissue r", "Literature r", "lit")
        and (trait_dataset.type == "ProbeSet" and
             target_dataset.type in ("Publish", "Geno")))


# ============================================================================
# LMDB CORRELATION INTEGRATION (NEW)
# ============================================================================

def check_gn3_lmdb_status(dataset_name: str) -> tuple[bool, str | None]:
    """Check if LMDB dataset exists in GN3.
    
    Queries GN3 /lmdb_status endpoint to check availability.
    GN2 doesn't need to know about LMDB paths - just asks GN3.
    
    Args:
        dataset_name: Name of dataset (e.g., "HC_M2_0606_P")
    
    Returns:
        Tuple of (available: bool, lmdb_path: str|None)
    """
    gn3_url = current_app.config.get("GN3_API_URL", "http://localhost:8080")
    endpoint = f"{gn3_url}/api/correlation/lmdb_status/{dataset_name}"
    
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("available"):
            return True, data.get("lmdb_path")
        else:
            return False, None
            
    except requests.RequestException as e:
        current_app.logger.warning(
            f"Failed to check LMDB status for {dataset_name}: {e}"
        )
        return False, None


def call_gn3_lmdb_api(
    dataset_name: str,
    trait_vals: list[float],
    strains: list[str],
    method: str = "pearson",
    top_n: int = 500
) -> dict:
    """Call GN3 LMDB correlation API.
    
    Args:
        dataset_name: Name of target dataset (e.g., "HC_M2_0606_P")
        trait_vals: Input trait values
        strains: Strain names corresponding to values
        method: "pearson" or "spearman"
        top_n: Return top N results
    
    Returns:
        Correlation results from GN3
    
    Raises:
        requests.RequestException: If API call fails
    """
    gn3_url = current_app.config.get("GN3_API_URL", "http://localhost:8080")
    endpoint = f"{gn3_url}/api/correlation/lmdb_corr"
    
    payload = {
        "dataset_name": dataset_name,
        "trait_vals": trait_vals,
        "strains": strains,
        "method": method,
        "parallel": True,
        "top_n": top_n
    }
    
    response = requests.post(endpoint, json=payload, timeout=300)
    response.raise_for_status()
    
    result = response.json()
    
    if result.get("status") != "success":
        raise requests.RequestException(
            f"GN3 API error: {result.get('message', 'Unknown error')}"
        )
    
    return result["results"]


def __compute_sample_corr_lmdb__(
    start_vars: dict,
    corr_type: str,
    method: str,
    n_top: int,
    target_trait_info: tuple,
    tmpdir: str
) -> dict:
    """Compute sample correlation using LMDB (optimized path).
    
    This bypasses CSV generation and database queries by calling
    the GN3 LMDB endpoint.
    """
    (this_dataset, this_trait, target_dataset, _) = target_trait_info

    # Handle F1 and parental strains
    if this_dataset.group.f1list is not None:
        this_dataset.group.samplelist += this_dataset.group.f1list

    if this_dataset.group.parlist is not None:
        this_dataset.group.samplelist += this_dataset.group.parlist

    # Get sample data (filtered by user selection: primary/other/all)
    sample_data = get_sample_corr_data(
        sample_type=start_vars["corr_samples_group"],
        sample_data=json.loads(start_vars["sample_vals"]),
        dataset_samples=this_dataset.group.all_samples_ordered())

    if not sample_data:
        return {}

    # Extract values and strains
    trait_vals = list(sample_data.values())
    strains = list(sample_data.keys())

    try:
        # Call GN3 LMDB API
        results = call_gn3_lmdb_api(
            dataset_name=target_dataset.name,
            trait_vals=trait_vals,
            strains=strains,
            method=method,
            top_n=n_top
        )
        
        # Convert string values to floats for consistency
        formatted_results = {}
        for trait_name, data in results.items():
            formatted_results[trait_name] = {
                "corr_coefficient": float(data["corr_coefficient"]),
                "p_value": float(data["p_value"]),
                "num_overlap": int(data["num_overlap"])
            }
        
        return formatted_results
        
    except requests.RequestException as e:
        current_app.logger.warning(
            f"LMDB API failed for {target_dataset.name}: {e}. "
            f"Falling back to CSV method."
        )
        # Fall back to traditional method
        return __compute_sample_corr__(
            start_vars, corr_type, method, n_top, target_trait_info, tmpdir
        )


# ============================================================================
# EXISTING CORRELATION FUNCTIONS (UNCHANGED)
# ============================================================================

def __compute_sample_corr__(
        start_vars: dict,
        corr_type: str,
        method: str,
        n_top: int,
        target_trait_info: tuple,
        tmpdir
):
    """Compute the sample correlations (traditional CSV method)"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info

    if this_dataset.group.f1list is not None:
        this_dataset.group.samplelist += this_dataset.group.f1list

    if this_dataset.group.parlist is not None:
        this_dataset.group.samplelist += this_dataset.group.parlist

    sample_data = get_sample_corr_data(
        sample_type=start_vars["corr_samples_group"],
        sample_data=json.loads(start_vars["sample_vals"]),
        dataset_samples=this_dataset.group.all_samples_ordered())

    if not bool(sample_data):
        return {}

    if target_dataset.type == "ProbeSet" and start_vars.get("use_cache") == "true":
        with database_connection(SQL_URI) as conn:
            file_path = fetch_text_file(target_dataset.name, conn)
            if file_path:
                (sample_vals, target_data) = read_text_file(
                    sample_data, file_path)

                return run_correlation(target_data,
                                       sample_vals,
                                       method,
                                       ",",
                                       tmpdir,
                                       corr_type=corr_type,
                                       top_n=n_top)

            write_db_to_textfile(target_dataset.name, this_dataset.group.samplelist, conn)
            file_path = fetch_text_file(target_dataset.name, conn)
            if file_path:
                (sample_vals, target_data) = read_text_file(
                    sample_data, file_path)

                return run_correlation(
                    target_data,
                    sample_vals,
                    method,
                    ",",
                    tmpdir,
                    corr_type=corr_type,
                    top_n=n_top)

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
        target_data,
        list(sample_data.values()),
        method,
        ",",
        tmpdir,
        corr_type=corr_type,
        top_n=n_top)


def __compute_tissue_corr__(
        start_vars: dict,
        corr_type: str,
        method: str,
        n_top: int,
        target_trait_info: tuple,
        tmpdir: str
):
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

    if data is not None:
        return run_correlation(
            data[1], data[0], method, ",", tmpdir, corr_type="tissue")
    return {}


def __compute_lit_corr__(
        start_vars: dict,
        corr_type: str,
        method: str,
        n_top: int,
        target_trait_info: tuple,
        tmpdir: str
):
    """Compute the literature correlations"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info
    if not __datasets_compatible_p__(this_dataset, target_dataset, corr_type):
        raise WrongCorrelationType(this_trait, target_dataset, corr_type)

    target_dataset_type = target_dataset.type
    this_dataset_type = this_dataset.type
    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, target_dataset)

    with database_connection(SQL_URI) as conn:
        return reduce(
            lambda acc, lit: {**acc, **lit},
            compute_all_lit_correlation(
                conn=conn, trait_lists=list(geneid_dict.items()),
                species=species, gene_id=this_trait_geneid)[:n_top],
            {})
    return {}


def compute_correlation_rust(
        start_vars: dict,
        corr_type: str,
        tmpdir: str,
        method: str = "pearson",
        n_top: int = 500,
        should_compute_all: bool = False):
    """function to compute correlation with LMDB optimization.
    
    For sample correlation on ProbeSet datasets, tries LMDB first
    for performance, falls back to CSV if LMDB unavailable.
    """
    target_trait_info = create_target_this_trait(start_vars)
    (this_dataset, this_trait, target_dataset, sample_data) = (
        target_trait_info)
    if not __datasets_compatible_p__(this_dataset, target_dataset, corr_type):
        raise WrongCorrelationType(this_trait, target_dataset, corr_type)

    # Route to appropriate correlation method
    if corr_type == "sample":
        # Try LMDB first for ProbeSet sample correlations
        if target_dataset.type == "ProbeSet":
            # Ask GN3 if LMDB is available (GN2 doesn't need to know paths)
            lmdb_available, _ = check_gn3_lmdb_status(target_dataset.name)
            if lmdb_available:
                results = __compute_sample_corr_lmdb__(
                    start_vars, corr_type, method, n_top, target_trait_info, tmpdir
                )
            else:
                # Fall back to CSV method
                results = __compute_sample_corr__(
                    start_vars, corr_type, method, n_top, target_trait_info, tmpdir
                )
        else:
            # Non-ProbeSet datasets use CSV
            results = __compute_sample_corr__(
                start_vars, corr_type, method, n_top, target_trait_info, tmpdir
            )
    elif corr_type == "tissue":
        results = __compute_tissue_corr__(
            start_vars, corr_type, method, n_top, target_trait_info, tmpdir
        )
    elif corr_type == "lit":
        results = __compute_lit_corr__(
            start_vars, corr_type, method, n_top, target_trait_info, tmpdir
        )
    else:
        raise ValueError(f"Unknown correlation type: {corr_type}")

    # Compute additional correlations if requested
    top_a = top_b = {}

    if should_compute_all:

        if corr_type == "sample":
            if this_dataset.type == "ProbeSet":
                top_a = compute_top_n_tissue(
                    target_dataset, this_trait, results, method, tmpdir)

                top_b = compute_top_n_lit(results, target_dataset, this_trait, tmpdir)
            else:
                pass

        elif corr_type == "lit":
            top_a = compute_top_n_sample(
                start_vars, target_dataset, list(results.keys()), tmpdir)
            top_b = compute_top_n_tissue(
                target_dataset, this_trait, results, method, tmpdir)

        else:
            top_a = compute_top_n_sample(
                start_vars, target_dataset, list(results.keys()), tmpdir)

    return {
        "correlation_results": merge_results(
            results, top_a, top_b),
        "this_trait": this_trait.name,
        "target_dataset": start_vars['corr_dataset'],
        "traits_metadata": get_metadata(target_dataset, list(results.keys())),
        "return_results": n_top
    }
