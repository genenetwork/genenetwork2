"""Handle linking data to groups."""
import json
from urllib.parse import urljoin

from flask import (
    flash, request, url_for, redirect, Response, Blueprint, render_template,
    current_app as app)

from .request_utils import process_error
from .client import oauth2_get, oauth2_post

data = Blueprint("data", __name__)

def __render_template__(templatepath, **kwargs):
    roles = kwargs.get("roles", tuple())
    user_privileges = tuple(
        privilege["privilege_id"] for role in roles
        for privilege in role["privileges"])
    return render_template(
        templatepath, **kwargs, user_privileges=user_privileges)

def __search_mrna__(query, template, **kwargs):
    return __render_template__(template, **kwargs)

def __search_genotypes__(query, template, **kwargs):
    species_name = kwargs["species_name"]
    datasets = oauth2_get(
        "oauth2/data/search",
        data = {
            "query": query,
            "dataset_type": "genotype",
            "species_name": species_name
        }).either(
            lambda err: {"datasets_error": process_error(err)},
            lambda datasets: {"datasets": datasets})
    return __render_template__(template, **datasets, **kwargs)

def __search_phenotypes__(query, template, **kwargs):
    per_page = int(request.args.get("per_page", 500))
    species_name = kwargs["species_name"]
    search_uri = (f"search/?type=phenotype&per_page={per_page}&query="
                  f"species:{species_name}") + (
                      f" AND ({query})" if bool(query) else "")
    traits = oauth2_get(search_uri).either(
             lambda err: {"traits_error": process_error(err)},
             lambda trts: {"traits": tuple({
                 "index": idx, **trait
             } for idx, trait in enumerate(trts, start=1))})

    selected_traits = request.form.getlist("selected_traits")

    return __render_template__(
        template, **traits, per_page=per_page, query=query,
        selected_traits=selected_traits,
        search_endpoint=urljoin(app.config["GN_SERVER_URL"], "search/"),
        **kwargs)

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
        return render_template(
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
        "selected_datasets": tuple(json.loads(dataset) for dataset
                                   in form.getlist("selected_datasets"))
    }).either(lambda err: __link_error__(process_error(err)), __link_success__)
