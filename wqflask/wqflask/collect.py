import os
import uuid
import hashlib
import datetime
import simplejson as json
from urllib.parse import urljoin

from flask import g
from flask import render_template
from flask import url_for
from flask import request
from flask import redirect
from flask import flash
from flask import current_app

from wqflask import app
from utility import hmac
from utility.formatting import numify
from utility.tools import get_setting
from utility.redis_tools import get_redis_conn

from base.trait import create_trait
from base.trait import retrieve_trait_info
from base.trait import jsonable
from base.data_set import create_dataset

from wqflask.oauth2 import client
from wqflask.oauth2 import session
from wqflask.oauth2.session import session_info
from wqflask.oauth2.checks import user_logged_in
from wqflask.oauth2.request_utils import (
    process_error, with_flash_error, with_flash_success)
from wqflask.oauth2.client import (
    oauth2_get, oauth2_post, no_token_get, no_token_post)


Redis = get_redis_conn()


def process_traits(unprocessed_traits):
    if isinstance(unprocessed_traits, bytes):
        unprocessed_traits = unprocessed_traits.decode('utf-8').split(",")
    else:  # It's a string
        unprocessed_traits = unprocessed_traits.split(",")
    traits = set()
    for trait in unprocessed_traits:
        data, _separator, the_hmac = trait.rpartition(':')
        data = data.strip()
        if g.user_session.logged_in:
            assert the_hmac == hmac.hmac_creation(data), "Data tampering?"
        traits.add(str(data))

    return tuple(traits)


def report_change(len_before, len_now):
    new_length = len_now - len_before
    if new_length:
        flash("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))


@app.route("/collections/store_trait_list", methods=('POST',))
def store_traits_list():
    params = request.form

    traits = params['traits']
    hash = params['hash']

    Redis.set(hash, traits)

    return hash


@app.route("/collections/add", methods=["POST"])
def collections_add():
    anon_id = session_info()["anon_id"]
    traits = request.args.get("traits", request.form.get("traits"))
    the_hash = request.args.get("hash", request.form.get("hash"))
    collections = g.user_session.user_collections
    collections = oauth2_get("oauth2/user/collections/list").either(
        lambda _err: tuple(), lambda colls: tuple(colls)) + no_token_get(
            f"oauth2/user/collections/{anon_id}/list").either(
                lambda _err: tuple(), lambda colls: tuple(colls))

    def __create_new_coll_error__(error):
        err = process_error(error)
        flash(f"{err['error']}:{err['error_description']}", "alert-danger")
        return redirect("/")

    if len(collections) < 1:
        new_coll = client.post(
            "oauth2/user/collections/new",
            json={
                "anon_id": str(anon_id),
                "name": "Your Default Collection",
                "traits": []
            }).either(__create_new_coll_error__, lambda coll: coll)
        collections = (new_coll,)

    if bool(traits):
        return render_template("collections/add.html",
                               traits=traits,
                               collections=collections)
    else:
        return render_template("collections/add.html",
                               hash=the_hash,
                               collections=collections)

def __compute_traits__(params):
    if "hash" in params:
        unprocessed_traits = Redis.get(params['hash']) or ""
        Redis.delete(params['hash'])
    else:
        unprocessed_traits = params['traits']
    return process_traits(unprocessed_traits)

@app.route("/collections/new")
def collections_new():
    params = request.args
    anon_id = session_info()["anon_id"]

    if "sign_in" in params:
        return redirect(url_for('login'))
    if "create_new" in params:
        collection_name = (
            params.get("new_collection", "").strip() or
            datetime.datetime.utcnow().strftime('Collection_%b_%d_%H:%M'))
        request_data = {
            "uri_path": "oauth2/user/collections/new",
            "json": {
                "name": collection_name,
                "anon_id": str(anon_id),
                "traits": __compute_traits__(params),
                "hash": params.get("hash", False)
            }}
        if user_logged_in():
            resp = oauth2_post(**request_data)
        else:
            resp = no_token_post(**request_data)
        #return create_new(collection_name)
        def __error__(err):
            error = process_error(err)
            flash(f"{error['error']}: {error['error_description']}",
                  "alert-danger")
            return redirect("/")
        def __view_collection__(collection):
            return redirect(url_for("view_collection", uc_id=collection["id"]))
        return resp.either(__error__, __view_collection__)
    elif "add_to_existing" in params:
        traits = process_traits(params["traits"])
        coll_id, *_coll_name = tuple(
            part.strip() for part in params["existing_collection"].split(":"))
        collection_id = uuid.UUID(coll_id)
        resp = redirect(url_for('view_collection', uc_id=collection_id))
        return client.post(
            f"oauth2/user/collections/{collection_id}/traits/add",
            json={
                "anon_id": str(anon_id),
                "traits": traits
            }).either(
                with_flash_error(resp), with_flash_success(resp))
    else:
        # CauseAnError
        pass


def create_new(collection_name):
    params = request.args
    if "hash" in params:
        unprocessed_traits = Redis.get(params['hash'])
        Redis.delete(params['hash'])
    else:
        unprocessed_traits = params['traits']

    traits = process_traits(unprocessed_traits)

    uc_id = g.user_session.add_collection(collection_name, traits)

    return redirect(url_for('view_collection', uc_id=uc_id))


@app.route("/collections/list")
def list_collections():
    params = request.args
    anon_id = session.session_info()["anon_id"]
    anon_collections = no_token_get(
        f"oauth2/user/collections/{anon_id}/list").either(
            lambda err: {"anon_collections_error": process_error(err)},
            lambda colls: {"anon_collections": colls})

    user_collections = {"collections": []}
    if user_logged_in():
        user_collections = oauth2_get("oauth2/user/collections/list").either(
            lambda err: {"user_collections_error": process_error(err)},
            lambda colls: {"collections": colls})

    return render_template("collections/list.html",
                           params=params,
                           **user_collections,
                           **anon_collections)

@app.route("/collections/handle_anonymous", methods=["POST"])
def handle_anonymous_collections():
    """Handle any anonymous collection on logging in."""
    choice = request.form.get("anon_choice")
    if choice not in ("import", "delete"):
        flash("Invalid choice!", "alert-danger")
        return redirect("/")
    def __impdel_error__(err):
        error = process_error(err)
        flash(f"{error['error']}: {error['error_description']}",
              "alert-danger")
        return redirect("/")
    def __impdel_success__(msg):
        flash(f"Success: {msg['message']}", "alert-success")
        return redirect("/")
    return oauth2_post(
        f"oauth2/user/collections/anonymous/{choice}",
        json={
            "anon_id": str(session_info()["anon_id"])
        }).either(__impdel_error__, __impdel_success__)

@app.route("/collections/remove", methods=('POST',))
def remove_traits():
    params = request.form
    uc_id = params['uc_id']
    traits_to_remove = process_traits(params['trait_list'])
    resp = redirect(url_for("view_collection", uc_id=uc_id))
    return client.post(
        f"oauth2/user/collections/{uc_id}/traits/remove",
        json = {
            "anon_id": str(session_info()["anon_id"]),
            "traits": traits_to_remove
        }).either(with_flash_error(resp), with_flash_success(resp))


@app.route("/collections/delete", methods=('POST',))
def delete_collection():
    def __error__(err):
        error = process_error(err)
        flash(f"{error['error']}: {error['error_description']}",
              "alert-danger")
        return redirect(url_for('list_collections'))

    def __success__(msg):
        flash(msg["message"], "alert-success")
        return redirect(url_for('list_collections'))

    uc_ids = [item for item in request.form.get("uc_id", "").split(":")
              if bool(item)]
    if len(uc_ids) > 0:
        return (oauth2_post if user_logged_in() else no_token_post)(
            "oauth2/user/collections/delete",
            json = {
                "anon_id": str(session_info()["anon_id"]),
                "collection_ids": uc_ids
            }).either(
                __error__, __success__)

    flash("Nothing to delete.", "alert-info")
    return redirect(url_for('list_collections'))


def trait_info_str(trait):
    """Provide a string representation for given trait"""
    def __trait_desc(trt):
        if trait.dataset.type == "Geno":
            return f"Marker: {trt.name}"
        return trt.description_display or "N/A"

    def __symbol(trt):
        return (trt.symbol or trt.abbreviation or "N/A")[:20]

    def __lrs(trt):
        if trait.dataset.type == "Geno":
            return 0
        else:
            if trait.LRS_score_repr != "N/A":
                return (
                    f"{float(trait.LRS_score_repr):0.3f}" if float(trait.LRS_score_repr) > 0
                    else f"{trait.LRS_score_repr}")
            else:
                return "N/A"

    def __lrs_location(trt):
        if hasattr(trt, "LRS_location_repr"):
            return trt.LRS_location_repr
        else:
            return "N/A"

    def __location(trt):
        if hasattr(trt, "location_repr"):
            return trt.location_repr
        return None

    def __mean(trt):
        if trait.mean:
            return trt.mean
        else:
            return 0

    return "{}|||{}|||{}|||{}|||{}|||{:0.3f}|||{}|||{}".format(
        trait.name, trait.dataset.name, __trait_desc(trait), __symbol(trait),
        __location(trait), __mean(trait), __lrs(trait), __lrs_location(trait))

@app.route("/collections/import", methods=('POST',))
def import_collection():
    import_file = request.files['import_file']
    if import_file.filename != '':
        file_path = os.path.join(get_setting(app, "TEMPDIR"), import_file.filename)
        import_file.save(file_path)
        collection_csv = open(file_path, "r")
        traits = [row.strip() for row in collection_csv if row[0] != "#"]
        os.remove(file_path)

        return json.dumps(traits)
    else:
        return render_template(
            "collections/list.html")

@app.route("/collections/view")
def view_collection():
    params = request.args

    uc_id = params['uc_id']
    request_data = {
        "uri_path": f"oauth2/user/collections/{uc_id}/view",
        "json": {"anon_id": str(session_info()["anon_id"])}
    }
    if user_logged_in():
        coll = oauth2_post(**request_data)
    else:
        coll = no_token_post(**request_data)

    def __view__(uc):
        traits = uc["members"]

        trait_obs = []
        json_version = []

        for atrait in traits:
            if ':' not in atrait:
                continue
            name, dataset_name = atrait.split(':')
            if dataset_name == "Temp":
                group = name.split("_")[2]
                dataset = create_dataset(
                    dataset_name, dataset_type="Temp", group_name=group)
                trait_ob = create_trait(name=name, dataset=dataset)
            else:
                dataset = create_dataset(dataset_name)
                trait_ob = create_trait(name=name, dataset=dataset)
                trait_ob = retrieve_trait_info(
                    trait_ob, dataset, get_qtl_info=True)
            trait_obs.append(trait_ob)

            trait_json = jsonable(trait_ob)
            trait_json['trait_info_str'] = trait_info_str(trait_ob)

            json_version.append(trait_json)

        collection_info = dict(
            trait_obs=trait_obs,
            uc=uc,
            heatmap_data_url=urljoin(get_setting(app, "GN_SERVER_URL"), "heatmaps/clustered"))

        if "json" in params:
            return json.dumps(json_version)
        else:
            return render_template(
                "collections/view.html",
                traits_json=json_version,
                trait_info_str=trait_info_str,
                **collection_info)

    def __error__(err):
        error = process_error(err)
        flash(f"{error['error']}: {error['error_description']}", "alert-danger")
        return redirect(url_for("list_collections"))

    return coll.either(__error__, __view__)

@app.route("/collections/change_name", methods=('POST',))
def change_collection_name():
    collection_id = request.form['collection_id']
    resp = redirect(url_for("view_collection", uc_id=collection_id))
    return client.post(
        f"oauth2/user/collections/{collection_id}/rename",
        json={
            "anon_id": str(session_info()["anon_id"]),
            "new_name": request.form["new_collection_name"]
        }).either(with_flash_error(resp), with_flash_success(resp))
