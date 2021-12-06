from typing import Union, Tuple

import MySQLdb
from gn3.db.traits import retrieve_trait_info
from flask import flash, request, current_app, render_template
from gn3.computations.partial_correlations import partial_correlations_entry

from wqflask import app

def parse_trait(trait_str: str) -> Union[dict, None]:
    keys = ("name", "dataset", "symbol", "description", "data_hmac")
    parts = tuple(part.strip() for part in trait_str.split(":::"))
    if len(parts) == len(keys):
        return dict(zip(keys, parts))
    return None

def process_step_select_primary(
        primary_trait: dict, control_traits: Tuple[dict, ...],
        target_traits: Tuple[dict, ...],
        traits_list: Tuple[dict, ...], corr_method: str) -> Tuple[
            str, dict, Tuple[dict, ...], Tuple[dict, ...], Tuple[dict, ...],
            str]:
    if primary_trait is None:
        flash("You must select a primary trait", "alert-danger")
        return (
            "select-primary", primary_trait, control_traits, target_traits,
            traits_list, corr_method)

    return (
        "select-controls", primary_trait, control_traits, target_traits,
        tuple(
            trait for trait in traits_list
            if trait["data_hmac"] != primary_trait["data_hmac"]),
        corr_method)

def process_step_select_controls(
        primary_trait: dict, control_traits: Tuple[dict, ...],
        target_traits: Tuple[dict, ...],
        traits_list: Tuple[dict, ...], corr_method: str) -> Tuple[
            str, dict, Tuple[dict, ...], Tuple[dict, ...], Tuple[dict, ...],
            str]:
    if len(control_traits) == 0 or len(control_traits) > 3:
        flash(
            ("You must select a minimum of one control trait, up to a maximum "
             "of three control traits."),
            "alert-danger")
        return (
            "select-controls", primary_trait, control_traits, target_traits,
            traits_list, corr_method)

    hmacs =(primary_trait["data_hmac"],) + tuple(
        trait["data_hmac"] for trait in control_traits)
    return (
        "select-targets", primary_trait, control_traits, target_traits,
        tuple(
            trait for trait in traits_list if trait["data_hmac"] not in hmacs),
        corr_method)

def process_step_select_targets(
        primary_trait: dict, control_traits: Tuple[dict, ...],
        target_traits: Tuple[dict, ...],
        traits_list: Tuple[dict, ...], corr_method: str) -> Tuple[
            str, dict, Tuple[dict, ...], Tuple[dict, ...], Tuple[dict, ...],
            str]:
    if len(target_traits) == 0:
        flash(
            "You must select at least one target trait.", "alert-danger")
        return (
            "select-targets", primary_trait, control_traits, target_traits,
            traits_list, corr_method)

    hmacs =(primary_trait["data_hmac"],) + tuple(
        trait["data_hmac"] for trait in (control_traits + target_traits))
    return (
        "select-corr-method", primary_trait, control_traits, target_traits,
        tuple(
            trait for trait in traits_list if trait["data_hmac"] not in hmacs),
        corr_method)

def process_step_select_corr_method(
        primary_trait: dict, control_traits: Tuple[dict, ...],
        target_traits: Tuple[dict, ...],
        traits_list: Tuple[dict, ...], corr_method: str) -> Tuple[
            str, dict, Tuple[dict, ...], Tuple[dict, ...], Tuple[dict, ...],
            str]:
    methods = (
        "genetic correlation, pearson's r",
        "genetic correlation, spearman's rho",
        "sgo literature correlation",
        "tissue correlation, pearson's r",
        "tissue correlation, spearman's rho")
    if corr_method.lower() not in methods:
        flash(
            "Selected method is unknown.", "alert-danger")
        return (
            "select-corr-method", primary_trait, control_traits, target_traits,
            traits_list, corr_method)

    hmacs =(primary_trait["data_hmac"],) + tuple(
        trait["data_hmac"] for trait in (control_traits + target_traits))
    return (
        "run-correlation", primary_trait, control_traits, target_traits,
        tuple(
            trait for trait in traits_list if trait["data_hmac"] not in hmacs),
        corr_method)

def process_step(
        step: str, primary_trait: dict, control_traits: Tuple[dict, ...],
        target_traits: Tuple[dict, ...], traits_list: Tuple[dict, ...],
        corr_method: str) -> Tuple[
            str, dict, Tuple[dict, ...], Tuple[dict, ...], Tuple[dict, ...],
            str]:
    processor_functions = {
        # "select-traits": lambda arg: arg,
        "select-primary": process_step_select_primary,
        "select-controls": process_step_select_controls,
        "select-targets": process_step_select_targets,
        "select-corr-method": process_step_select_corr_method
    }
    return processor_functions[(step or "select-primary")](
        primary_trait, control_traits, target_traits, traits_list, corr_method)

def sequence_of_traits(trait_strs) -> Tuple[dict, ...]:
    return tuple(filter(
        lambda trt: trt is not None,
        (parse_trait(tstr.strip()) for tstr in trait_strs)))

def publish_target_dabases(conn, group, threshold):
    query = (
        "SELECT PublishFreeze.FullName,PublishFreeze.Name "
        "FROM PublishFreeze, InbredSet "
        "WHERE PublishFreeze.InbredSetId = InbredSet.Id "
        "AND InbredSet.Name = %(group)s "
        "AND PublishFreeze.public > %(threshold)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"group": group, "threshold": threshold})
        res = cursor.fetchall()
        if res:
            return tuple(
                dict(zip(("description", "value"), row)) for row in res)

    return tuple()

def geno_target_databases(conn, group, threshold):
    query = (
        "SELECT GenoFreeze.FullName,GenoFreeze.Name "
        "FROM GenoFreeze, InbredSet "
        "WHERE GenoFreeze.InbredSetId = InbredSet.Id "
        "AND InbredSet.Name = %(group)s "
        "AND GenoFreeze.public > %(threshold)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"group": group, "threshold": threshold})
        res = cursor.fetchall()
        if res:
            return tuple(
                dict(zip(("description", "value"), row)) for row in res)

    return tuple()

def probeset_target_databases(conn, group, threshold):
    query1 = "SELECT Id, Name FROM Tissue order by Name"
    query2 = (
        "SELECT ProbeFreeze.TissueId, ProbeSetFreeze.FullName, ProbeSetFreeze.Name "
        "FROM ProbeSetFreeze, ProbeFreeze, InbredSet "
        "WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
        "AND ProbeFreeze.TissueId IN %(tissue_ids)s "
        "AND ProbeSetFreeze.public > %(threshold)s "
        "AND ProbeFreeze.InbredSetId = InbredSet.Id "
        "AND InbredSet.Name like %(group)s "
        "ORDER BY ProbeSetFreeze.CreateTime desc, ProbeSetFreeze.AvgId")
    with conn.cursor() as cursor:
        cursor.execute(query1)
        tissue_res = cursor.fetchall()
        if tissue_res:
            tissue_ids = tuple(row[0] for row in tissue_res)
            cursor.execute(
                query2,{
                    "tissue_ids": tissue_ids, "group": f"{group}%%",
                    "threshold": threshold
                })
            db_res = cursor.fetchall()
            if db_res:
                databases = tuple(
                    dict(zip(("tissue_id", "description", "value"), row))
                    for row in db_res)
                return tuple(
                    {tissue_name: tuple(
                        {
                            "value": item["value"],
                            "description": item["description"]
                         } for item in databases
                        if item["tissue_id"] == tissue_id)}
                    for tissue_id, tissue_name in tissue_res)

    return tuple()

def target_databases(conn, step, trait, threshold):
    """
    Retrieves the names of possible target databases from the database.
    """
    if step != "select-corr-method":
        return None

    trait_info = retrieve_trait_info(
        threshold, f"{trait['dataset']}::{trait['name']}", conn)
    group = trait_info["group"]
    return (
        publish_target_dabases(conn, group, threshold) +
        geno_target_databases(conn, group, threshold) +
        probeset_target_databases(conn, group, threshold))

def pcorrelations(conn, values):
    if values["step"] != "run-correlation":
        return None

    def trait_fullname(trait):
        return f"{trait['dataset']}::{trait['name']}"

    return partial_correlations_entry(
        conn, trait_fullname(values["primary_trait"]),
        tuple(trait_fullname(trait) for trait in values["control_traits"]),
        values["method"], values["criteria"], values["target_db"])

@app.route("/partial_correlations", methods=("POST",))
def partial_correlations():
    form = request.form
    traits_list = tuple(filter(
        lambda trt: trt is not None,
        (parse_trait(tstr) for tstr in form.get("traits_list", "").split("|||"))))

    args_dict = dict(zip(
        ("step", "primary_trait", "control_traits", "target_traits",
         "traits_list", "method"),
        process_step(
            form.get("step", None),
            parse_trait(form.get("primary_trait", "")),
            sequence_of_traits(
                form.getlist("control_traits[]") or
                form.get("control_traits", "").split("|||")),
            sequence_of_traits(
                form.getlist("target_traits[]") or
                form.get("target_traits", "").split("|||")),
            sequence_of_traits(form.get("traits_list", "").split("|||")),
            form.get("method"))))

    conn = MySQLdb.Connect(
        db=current_app.config.get("DB_NAME"),
        user=current_app.config.get("DB_USER"),
        passwd=current_app.config.get("DB_PASS"),
        host=current_app.config.get("DB_HOST"))
    target_dbs = target_databases(
        conn, args_dict["step"], args_dict["primary_trait"], 0)

    if args_dict["step"] == "run-correlation":
        args_dict = {
            **args_dict, "target_db": form.get("target_db"),
            "criteria": int(form.get("criteria", 500))}

    corr_results = pcorrelations(conn, args_dict)

    return render_template(
        "partial_correlations.html", **args_dict, target_dbs=target_dbs,
        corr_results=corr_results)
