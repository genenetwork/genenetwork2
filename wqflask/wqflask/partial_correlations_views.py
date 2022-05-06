import json
import math
import requests
from functools import reduce
from typing import Union, Tuple

from flask import (
    flash,
    request,
    url_for,
    redirect,
    current_app,
    render_template)

from wqflask import app
from utility.tools import GN_SERVER_URL
from wqflask.database import database_connection
from gn3.db.partial_correlations import traits_info

def publish_target_databases(conn, groups, threshold):
    query = (
        "SELECT PublishFreeze.FullName,PublishFreeze.Name "
        "FROM PublishFreeze, InbredSet "
        "WHERE PublishFreeze.InbredSetId = InbredSet.Id "
        f"AND InbredSet.Name IN ({', '.join(['%s'] * len(groups))}) "
        "AND PublishFreeze.public > %s")
    with conn.cursor() as cursor:
        cursor.execute(query, tuple(groups) + (threshold,))
        res = cursor.fetchall()
        if res:
            return tuple(
                dict(zip(("description", "value"), row)) for row in res)

    return tuple()

def geno_target_databases(conn, groups, threshold):
    query = (
        "SELECT GenoFreeze.FullName,GenoFreeze.Name "
        "FROM GenoFreeze, InbredSet "
        "WHERE GenoFreeze.InbredSetId = InbredSet.Id "
        f"AND InbredSet.Name IN ({', '.join(['%s'] * len(groups))}) "
        "AND GenoFreeze.public > %s")
    with conn.cursor() as cursor:
        cursor.execute(query, tuple(groups) + (threshold,))
        res = cursor.fetchall()
        if res:
            return tuple(
                dict(zip(("description", "value"), row)) for row in res)

    return tuple()

def probeset_target_databases(conn, groups, threshold):
    query1 = "SELECT Id, Name FROM Tissue order by Name"
    with conn.cursor() as cursor:
        cursor.execute(query1)
        tissue_res = cursor.fetchall()
        if tissue_res:
            tissue_ids = tuple(row[0] for row in tissue_res)
            groups_clauses = ["InbredSet.Name like %s"] * len(groups)
            query2 = (
                "SELECT ProbeFreeze.TissueId, ProbeSetFreeze.FullName, "
                "ProbeSetFreeze.Name "
                "FROM ProbeSetFreeze, ProbeFreeze, InbredSet "
                "WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                "AND ProbeFreeze.TissueId IN "
                f"({', '.join(['%s'] * len(tissue_ids))}) "
                "AND ProbeSetFreeze.public > %s "
                "AND ProbeFreeze.InbredSetId = InbredSet.Id "
                f"AND ({' OR '.join(groups_clauses)}) "
                "ORDER BY ProbeSetFreeze.CreateTime desc, ProbeSetFreeze.AvgId")
            cursor.execute(query2, tissue_ids + (threshold,) + tuple(groups))
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

def target_databases(conn, traits, threshold):
    """
    Retrieves the names of possible target databases from the database.
    """
    trait_info = traits_info(
        conn, threshold,
        tuple(f"{trait['dataset']}::{trait['trait_name']}" for trait in traits))
    groups = tuple(set(row["db"]["group"] for row in trait_info))
    return (
        publish_target_databases(conn, groups, threshold) +
        geno_target_databases(conn, groups, threshold) +
        probeset_target_databases(conn, groups, threshold))

def primary_error(args):
    if len(args["primary_trait"]) == 0 or len(args["primary_trait"]) > 1:
        return {
            **args,
            "errors": (args.get("errors", tuple()) +
                       ("You must provide one, and only one primary trait",))}
    return args

def controls_error(args):
    if len(args["control_traits"]) == 0 or len(args["control_traits"]) > 3:
        return {
            **args,
            "errors": (
                args.get("errors", tuple()) +
                (("You must provide at least one control trait, and a maximum "
                  "of three control traits"),))}
    return args

def target_traits_error(args, with_target_traits):
    target_traits_present = (
        (args.get("target_traits") is not None) and
        (len(args["target_traits"]) > 0))
    if with_target_traits and not target_traits_present:
        return {
            **args,
            "errors": (
                args.get("errors", tuple()) +
                (("You must provide at least one target trait"),))}
    return args

def target_db_error(args, with_target_db: bool):
    if with_target_db and not args["target_db"]:
        return {
            **args,
            "errors": (
                args.get("errors", tuple()) +
                ("The target database must be provided",))}
    return args

def method_error(args):
    methods = (
        "genetic correlation, pearson's r",
        "genetic correlation, spearman's rho",
        "sgo literature correlation",
        "tissue correlation, pearson's r",
        "tissue correlation, spearman's rho")
    if not args["method"] or args["method"].lower() not in methods:
        return {
            **args,
            "errors": (
                args.get("errors", tuple()) +
                ("Invalid correlation method provided",))}
    return args

def criteria_error(args):
    try:
        int(args.get("criteria", "invalid"))
        return args
    except ValueError:
        return {
            **args,
            "errors": (
                args.get("errors", tuple()) +
                ("Invalid return number provided",))}

def errors(args, with_target_db: bool):
    return criteria_error(
        method_error(
            target_traits_error(
                target_db_error(
                    controls_error(primary_error(args)),
                    with_target_db),
                not with_target_db)))

def __classify_args(acc, item):
    if item[1].startswith("primary_"):
        return {
            **acc,
            "primary_trait": (acc.get("primary_trait", tuple()) + (item,))}
    if item[1].startswith("controls_"):
        return {**acc, "control_traits": (acc.get("control_traits", tuple()) + (item,))}
    if item[1].startswith("targets_"):
        return {**acc, "target_traits": (acc.get("target_traits", tuple()) + (item,))}
    if item[0] == "target_db":
        return {**acc, "target_db": item[1]}
    if item[0] == "method":
        return {**acc, "method": item[1]}
    if item[0] == "criteria":
        return {**acc, "criteria": item[1]}
    return acc

def __build_args(raw_form, traits):
    args = reduce(__classify_args, raw_form.items(), {})
    return {
        **args,
        "primary_trait": [
            item for item in traits if item["trait_name"] in
            (name[1][8:] for name in args["primary_trait"])],
        "control_traits": [
            item for item in traits if item["trait_name"] in
            (name[1][9:] for name in args["control_traits"])],
        "target_traits": [
            item for item in traits if item["trait_name"] in
            (name[1][8:] for name in args["target_traits"])]
    }

def parse_trait(trait_str):
    return dict(zip(
        ("trait_name", "dataset", "description", "symbol", "location", "mean",
         "lrs", "lrs_location"),
        trait_str.strip().split("|||")))

def response_error_message(response):
    error_messages = {
        404: ("We could not connect to the API server at this time. "
              "Try again later."),
        500: ("The API server experienced a problem. We will be working on a "
              "fix. Please try again later.")
    }
    return error_messages.get(
        response.status_code,
        "General API server error!!")

def render_error(error_message):
    return render_template(
        "partial_correlations/pcorrs_error.html",
        message = error_message)

def __format_number(num):
    if num is None or math.isnan(num):
        return ""
    if abs(num) <= 1.04E-4:
        return f"{num:.2e}"
    return f"{num:.5f}"

def handle_200_response(response):
    if response["status"] == "queued":
        return redirect(
            url_for(
                "poll_partial_correlation_results",
                command_id=response["results"]),
            code=303)
    if response["status"] == "success":
        return render_template(
            "partial_correlations/pcorrs_results_with_target_traits.html",
            primary = response["results"]["results"]["primary_trait"],
            controls = response["results"]["results"]["control_traits"],
            pcorrs = sorted(
                response["results"]["results"]["correlations"],
                key = lambda item: item["partial_corr_p_value"]),
            method = response["results"]["results"]["method"],
            enumerate = enumerate,
            format_number = __format_number)
    return render_error(response["results"])

def handle_response(response):
    if response.status_code != 200:
        return render_template(
            "partial_correlations/pcorrs_error.html",
            message = response_error_message(response))
    return handle_200_response(response.json())

@app.route("/partial_correlations", methods=["POST"])
def partial_correlations():
    form = request.form
    traits = tuple(
        parse_trait(trait) for trait in
        form.get("trait_list").split(";;;"))

    submit = form.get("submit")

    if submit in ("with_target_pearsons", "with_target_spearmans"):
        method = "pearsons" if "pearsons" in submit else "spearmans"
        args = {
            **errors(__build_args(form, traits), with_target_db=False),
            "method": method
        }
        if len(args.get("errors", [])) == 0:
            post_data = {
                **args,
                "primary_trait": args["primary_trait"][0],
                "with_target_db": False
            }
            return handle_response(requests.post(
                url=f"{GN_SERVER_URL}api/correlation/partial",
                json=post_data))

        for error in args["errors"]:
            flash(error, "alert-danger")

    if submit == "Run Partial Correlations":
        args = errors(__build_args(form, traits), with_target_db=True)
        if len(args.get("errors", [])) == 0:
            post_data = {
                **args,
                "primary_trait": args["primary_trait"][0],
                "with_target_db": False
            }
            return handle_response(requests.post(
                url=f"{GN_SERVER_URL}api/correlation/partial",
                json=post_data))

        for error in args["errors"]:
            flash(error, "alert-danger")

    with database_connection() as conn:
        target_dbs = target_databases(conn, traits, threshold=0)
        return render_template(
            "partial_correlations/pcorrs_select_operations.html",
            trait_list_str=form.get("trait_list"),
            traits=traits,
            target_dbs=target_dbs)

def process_pcorrs_command_output(result):
    if result["status"] == "success":

        return render_template(
            "partial_correlations/pcorrs_results_presentation.html",
            primary=result["results"]["primary_trait"],
            controls=result["results"]["control_traits"],
            correlations=result["results"]["correlations"],
            dataset_type=result["results"]["dataset_type"],
            method=result["results"]["method"],
            format_number=__format_number)
    if result["status"] == "error":
        return render_error(
            "The partial correlations computation failed with an error")

@app.route("/partial_correlations/<command_id>", methods=["GET"])
def poll_partial_correlation_results(command_id):
    response = requests.get(
        url=f"{GN_SERVER_URL}api/async_commands/state/{command_id}")
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "error":
            return render_error(response["result"])
        if data["status"] == "success":
            return process_pcorrs_command_output(json.loads(data["result"]))
        return render_template(
            "partial_correlations/pcorrs_poll_results.html",
            command_id = command_id)
