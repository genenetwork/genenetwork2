"""Handle linking data to groups."""
import sys
import json
import uuid
from datetime import datetime
from urllib.parse import urljoin

from redis import Redis
from flask import (
    flash, request, jsonify, url_for, redirect, Response, Blueprint,
    current_app as app)

from jobs import jobs
from .ui import render_ui
from .request_utils import process_error
from .client import oauth2_get, oauth2_post

data = Blueprint("data", __name__)

def __search_mrna__(query, template, **kwargs):
    species_name = kwargs["species_name"]
    search_uri = urljoin(app.config["GN_SERVER_URL"], "oauth2/data/search")
    datasets = oauth2_get(
        "oauth2/data/search",
        json = {
            "query": query,
            "dataset_type": "mrna",
            "species_name": species_name,
            "selected": __selected_datasets__()
        }).either(
            lambda err: {"datasets_error": process_error(err)},
            lambda datasets: {"datasets": datasets})
    return render_ui(template, search_uri=search_uri, **datasets, **kwargs)

def __selected_datasets__():
    if bool(request.json):
        return request.json.get(
            "selected",
            request.args.get("selected",
                             request.form.get("selected", [])))
    return request.args.get("selected",
                            request.form.get("selected", []))

def __search_genotypes__(query, template, **kwargs):
    species_name = kwargs["species_name"]
    search_uri = urljoin(app.config["GN_SERVER_URL"], "oauth2/data/search")
    datasets = oauth2_get(
        "oauth2/data/search",
        json = {
            "query": query,
            "dataset_type": "genotype",
            "species_name": species_name,
            "selected": __selected_datasets__()
        }).either(
            lambda err: {"datasets_error": process_error(err)},
            lambda datasets: {"datasets": datasets})
    return render_ui(template, search_uri=search_uri, **datasets, **kwargs)

def __search_phenotypes__(query, template, **kwargs):
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    selected_traits = request.form.getlist("selected_traits")
    def __search_error__(error):
        raise Exception(error)
    def __search_success__(search_results):
        job_id = uuid.UUID(search_results["job_id"])
        return render_ui(
            template, traits=[], per_page=per_page, query=query,
            selected_traits=selected_traits, search_results=search_results,
            search_endpoint=urljoin(
                app.config["GN_SERVER_URL"], "oauth2/data/search"),
            gn_server_url = app.config["GN_SERVER_URL"],
            results_endpoint=urljoin(
                app.config["GN_SERVER_URL"],
                f"oauth2/data/search/phenotype/{job_id}"),
            **kwargs)
    return oauth2_get("oauth2/data/search", json={
        "dataset_type": "phenotype",
        "species_name": kwargs["species_name"],
        "per_page": per_page,
        "page": page,
        "gn3_server_uri": app.config["GN_SERVER_URL"]
    }).either(
        lambda err: __search_error__(process_error(err)),
        __search_success__)

@data.route("/genotype/search", methods=["POST"])
def json_search_genotypes() -> Response:
    def __handle_error__(err):
        error = process_error(err)
        return jsonify(error), error["status_code"]
    
    return oauth2_get(
        "oauth2/data/search",
        json = {
            "query": request.json["query"],
            "dataset_type": "genotype",
            "species_name": request.json["species_name"],
            "selected": __selected_datasets__()
        }).either(
            __handle_error__,
            lambda datasets: jsonify(datasets))

@data.route("/mrna/search", methods=["POST"])
def json_search_mrna() -> Response:
    def __handle_error__(err):
        error = process_error(err)
        return jsonify(error), error["status_code"]

    return oauth2_get(
        "oauth2/data/search",
        json = {
            "query": request.json["query"],
            "dataset_type": "mrna",
            "species_name": request.json["species_name"],
            "selected": __selected_datasets__()
        }).either(
            __handle_error__,
            lambda datasets: jsonify(datasets))

@data.route("/phenotype/search", methods=["POST"])
def json_search_phenotypes() -> Response:
    """Search for phenotypes."""
    form = request.json
    def __handle_error__(err):
        error = process_error(err)
        return jsonify(error), error["status_code"]

    return oauth2_get(
        "oauth2/data/search",
        json={
            "dataset_type": "phenotype",
            "species_name": form["species_name"],
            "query": form.get("query", ""),
            "per_page": int(form.get("per_page", 50)),
            "page": int(form.get("page", 1)),
            "gn3_server_uri": app.config["GN_SERVER_URL"],
            "selected_traits": form.get("selected_traits", [])
        }).either(__handle_error__, jsonify)

@data.route("/<string:species_name>/<string:dataset_type>/list",
            methods=["GET", "POST"])
def list_data_by_species_and_dataset(
        species_name: str, dataset_type: str) -> Response:
    templates = {
        "mrna": "oauth2/data-list-mrna.html",
        "genotype": "oauth2/data-list-genotype.html",
        "phenotype": "oauth2/data-list-phenotype.html"
    }
    search_fns = {
        "mrna": __search_mrna__,
        "genotype": __search_genotypes__,
        "phenotype": __search_phenotypes__
    }
    roles = oauth2_get("oauth2/user/roles").either(
        lambda err: {"roles_error": process_error(err)},
        lambda roles: {"roles": roles})
    groups = oauth2_get("oauth2/group/list").either(
        lambda err: {"groups_error": process_error(err)},
        lambda grps: {"groups": grps})
    query = request.args.get("query", "")
    return search_fns[dataset_type](
        query, templates[dataset_type], **roles, **groups,
        species_name=species_name, dataset_type=dataset_type)

@data.route("/list", methods=["GET", "POST"])
def list_data():
    """List ungrouped data."""
    def __render__(**kwargs):
        roles = kwargs.get("roles", [])
        user_privileges = tuple(
                privilege["privilege_id"] for role in roles
                for privilege in role["privileges"])
        return render_ui(
            "oauth2/data-list.html",
            groups=kwargs.get("groups", []),
            data_items=kwargs.get("data_items", []),
            user_privileges=user_privileges,
            **{key:val for key,val in kwargs.items()
               if key not in ("groups", "data_items", "user_privileges")})

    groups = oauth2_get("oauth2/group/list").either(
        lambda err: {"groups_error": process_error(err)},
        lambda grp: {"groups": grp})
    roles = oauth2_get("oauth2/user/roles").either(
        lambda err: {"roles_error": process_error(err)},
        lambda roles: {"roles": roles})
    species = oauth2_get("oauth2/data/species").either(
        lambda err: {"species_error": process_error(err)},
        lambda species: {"species": species})

    if request.method == "GET":
        return __render__(**{**groups, **roles, **species})

    species_name = request.form["species_name"]
    dataset_type = request.form["dataset_type"]
    if dataset_type not in ("mrna", "genotype", "phenotype"):
        flash("InvalidDatasetType: An invalid dataset type was provided",
              "alert-danger")
        return __render__(**{**groups, **roles, **species})

    return redirect(url_for(
        "oauth2.data.list_data_by_species_and_dataset",
        species_name=species_name, dataset_type=dataset_type))

@data.route("/link", methods=["POST"])
def link_data():
    """Link the selected data to a specific group."""
    def __error__(err, form_data):
        error = process_error(err)
        flash(f"{error['error']}: {error['error_description']}", "alert-danger")
        return redirect(url_for("oauth2.data.list_data", **form_data), code=307)
    def __success__(success, form_data):
        flash("Data successfully linked!", "alert-success")
        return redirect(url_for("oauth2.data.list_data", **form_data), code=307)

    form = request.form
    try:
        keys = ("dataset_type", "group_id")
        assert all(item in form for item in keys)
        assert all(bool(form[item]) for item in keys)
        state_data = {
            "dataset_type": form["dataset_type"],
            "offset": form.get("offset", 0)}
        dataset_ids = form.getlist("dataset_ids")
        if len(dataset_ids) == 0:
            flash("You must select at least one item to link", "alert-danger")
            return redirect(url_for(
                "oauth2.data.list_data", **state_data))
        return oauth2_post(
            "oauth2/group/data/link",
            data={
                "dataset_type": form["dataset_type"],
                "dataset_ids": dataset_ids,
                "group_id": form["group_id"]
            }).either(lambda err: __error__(err, state_data),
                      lambda success: __success__(success, state_data))
    except AssertionError as aserr:
        flash("You must provide all the expected data.", "alert-danger")
        return redirect(url_for("oauth2.data.list_data"))

@data.route("/link/genotype", methods=["POST"])
def link_genotype_data():
    """Link genotype data to a group."""
    form = request.form
    link_source_url = redirect(url_for("oauth2.data.list_data"))
    if bool(form.get("species_name")):
        link_source_url = redirect(url_for(
            "oauth2.data.list_data_by_species_and_dataset",
            species_name=form["species_name"], dataset_type="genotype"))

    def __link_error__(err):
        flash(f"{err['error']}: {err['error_description']}", "alert-danger")
        return link_source_url

    def __link_success__(success):
        flash(success["description"], "alert-success")
        return link_source_url

    return oauth2_post("oauth2/data/link/genotype", json={
        "species_name": form.get("species_name"),
        "group_id": form.get("group_id"),
        "selected": tuple(json.loads(dataset) for dataset
                                   in form.getlist("selected"))
    }).either(lambda err: __link_error__(process_error(err)), __link_success__)


@data.route("/link/mrna", methods=["POST"])
def link_mrna_data():
    """Link mrna data to a group."""
    form = request.form
    link_source_url = redirect(url_for("oauth2.data.list_data"))
    if bool(form.get("species_name")):
        link_source_url = redirect(url_for(
            "oauth2.data.list_data_by_species_and_dataset",
            species_name=form["species_name"], dataset_type="mrna"))

    def __link_error__(err):
        error = process_error(err)
        flash(f"{err['error']}: {err['error_description']}", "alert-danger")
        return link_source_url

    def __link_success__(success):
        flash(success["description"], "alert-success")
        return link_source_url

    return oauth2_post("oauth2/data/link/mrna", json={
        "species_name": form.get("species_name"),
        "group_id": form.get("group_id"),
        "selected": tuple(json.loads(dataset) for dataset
                                   in form.getlist("selected"))
    }).either(lambda err: __link_error__(process_error(err)), __link_success__)

@data.route("/link/phenotype", methods=["POST"])
def link_phenotype_data():
    """Link phenotype data to a group."""
    form = request.form
    link_source_url = redirect(url_for("oauth2.data.list_data"))
    if bool(form.get("species_name")):
        link_source_url = redirect(url_for(
            "oauth2.data.list_data_by_species_and_dataset",
            species_name=form["species_name"], dataset_type="phenotype"))

    def __link_error__(err):
        error = process_error(err)
        flash(f"{error['error']}: {error['error_description']}", "alert-danger")
        return link_source_url

    def __link_success__(success):
        flash(success["description"], "alert-success")
        return link_source_url

    return oauth2_post("oauth2/data/link/phenotype", json={
        "species_name": form.get("species_name"),
        "group_id": form.get("group_id"),
        "selected": tuple(
            json.loads(trait) for trait in form.getlist("selected"))}).either(
                __link_error__, __link_success__)
