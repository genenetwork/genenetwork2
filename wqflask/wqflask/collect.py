import hashlib
import datetime
import simplejson as json

from flask import g
from flask import render_template
from flask import url_for
from flask import request
from flask import redirect
from flask import flash

from wqflask import app
from utility import hmac
from utility.formatting import numify
from utility.redis_tools import get_redis_conn

from base.trait import create_trait
from base.trait import retrieve_trait_info
from base.trait import jsonable
from base.data_set import create_dataset

from utility.logger import getLogger

logger = getLogger(__name__)
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

    return traits


def report_change(len_before, len_now):
    new_length = len_now - len_before
    if new_length:
        flash("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))
    else:
        logger.debug("No new traits were added.")


@app.route("/collections/store_trait_list", methods=('POST',))
def store_traits_list():
   params = request.form

   traits = params['traits']
   hash = params['hash']

   Redis.set(hash, traits)

   return hash


@app.route("/collections/add")
def collections_add():

    collections = g.user_session.user_collections
    if len(collections) < 1:
        collection_name = "Your Default Collection"
        uc_id = g.user_session.add_collection(collection_name, set())
        collections = g.user_session.user_collections

    # ZS: One of these might be unnecessary
    if 'traits' in request.args:
        traits = request.args['traits']
        return render_template("collections/add.html",
                                traits=traits,
                                collections=collections,
                              )
    else:
        hash = request.args['hash']
        return render_template("collections/add.html",
                                hash=hash,
                                collections=collections,
                              )


@app.route("/collections/new")
def collections_new():
    params = request.args

    if "sign_in" in params:
        return redirect(url_for('login'))
    if "create_new" in params:
        collection_name = params['new_collection']
        if collection_name.strip() == "":
            collection_name = datetime.datetime.utcnow().strftime('Collection_%b_%d_%H:%M')
        return create_new(collection_name)
    elif "add_to_existing" in params:
        if 'existing_collection' not in params:
            collections = g.user_session.user_collections
            for collection in collections:
                if collection["name"] == "Your Default Collection":
                    collection_id = collection["id"]
                    collection_name = collection["name"]
                    default_collection_exists = True
            if not default_collection_exists:
                return create_new("Your Default Collection")
        else:
            collection_id = params['existing_collection'].split(":")[0]
            collection_name = params['existing_collection'].split(":")[1]

        if "hash" in params:
            unprocessed_traits = Redis.get(params['hash'])
        else:
            unprocessed_traits = params['traits']
        traits = list(process_traits(unprocessed_traits))
        g.user_session.add_traits_to_collection(collection_id, traits)
        return redirect(url_for('view_collection', uc_id=collection_id))
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

    user_collections = list(g.user_session.user_collections)
    return render_template("collections/list.html",
                            params=params,
                            collections=user_collections,
                            )


@app.route("/collections/remove", methods=('POST',))
def remove_traits():
    params = request.form

    uc_id = params['uc_id']
    traits_to_remove = params['trait_list']
    traits_to_remove = process_traits(traits_to_remove)

    members_now = g.user_session.remove_traits_from_collection(uc_id, traits_to_remove)

    return redirect(url_for("view_collection", uc_id=uc_id))


@app.route("/collections/delete", methods=('POST',))
def delete_collection():
    params = request.form
    uc_id = ""

    uc_id = params['uc_id']
    if len(uc_id.split(":")) > 1:
        for this_uc_id in uc_id.split(":"):
            collection_name = g.user_session.delete_collection(this_uc_id)
    else:
        collection_name = g.user_session.delete_collection(uc_id)

    if uc_id != "":
        if len(uc_id.split(":")) > 1:
            flash("We've deleted the selected collections.", "alert-info")
        else:
            flash("We've deleted the selected collection.", "alert-info")
    else:
        flash("We've deleted the collection: {}.".format(collection_name), "alert-info")

    return redirect(url_for('list_collections'))


@app.route("/collections/view")
def view_collection():
    params = request.args

    uc_id = params['uc_id']
    uc = next((collection for collection in g.user_session.user_collections if collection["id"] == uc_id))
    traits = uc["members"]

    trait_obs = []
    json_version = []

    for atrait in traits:
        if ':' not in atrait:
            continue
        name, dataset_name = atrait.split(':')
        if dataset_name == "Temp":
            group = name.split("_")[2]
            dataset = create_dataset(dataset_name, dataset_type="Temp", group_name=group)
            trait_ob = create_trait(name=name, dataset=dataset)
        else:
            dataset = create_dataset(dataset_name)
            trait_ob = create_trait(name=name, dataset=dataset)
            trait_ob = retrieve_trait_info(trait_ob, dataset, get_qtl_info=True)
        trait_obs.append(trait_ob)

        json_version.append(jsonable(trait_ob))

    collection_info = dict(trait_obs=trait_obs,
                           uc=uc)

    if "json" in params:
        return json.dumps(json_version)
    else:
        return render_template("collections/view.html",
                           **collection_info
                           )


@app.route("/collections/change_name", methods=('POST',))
def change_collection_name():
    params = request.form

    collection_id = params['collection_id']
    new_name = params['new_name']

    g.user_session.change_collection_name(collection_id, new_name)

    return new_name

