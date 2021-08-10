"""Main routing table for GN2"""

import MySQLdb
import array
import base64
import csv
import difflib
import datetime
import flask
import io  # Todo: Use cStringIO?

import json
import numpy as np
import os
import pickle as pickle
import random
import sqlalchemy
import sys
import traceback
import uuid
import xlsxwriter

from itertools import groupby
from collections import namedtuple
from zipfile import ZipFile
from zipfile import ZIP_DEFLATED

from wqflask import app

from gn3.commands import run_cmd
from gn3.db import diff_from_dict
from gn3.db import fetchall
from gn3.db import fetchone
from gn3.db import insert
from gn3.db import update
from gn3.db.metadata_audit import MetadataAudit
from gn3.db.phenotypes import Phenotype
from gn3.db.phenotypes import Probeset
from gn3.db.phenotypes import Publication
from gn3.db.phenotypes import PublishXRef
from gn3.db.phenotypes import probeset_mapping
from gn3.db.traits import get_trait_csv_sample_data
from gn3.db.traits import update_sample_data


from flask import current_app
from flask import g
from flask import flash
from flask import Response
from flask import request
from flask import make_response
from flask import render_template
from flask import send_from_directory
from flask import redirect
from flask import url_for
from flask import send_file

# Some of these (like collect) might contain endpoints, so they're still used.
# Blueprints should probably be used instead.
from wqflask import collect
from wqflask import search_results
from wqflask import server_side
from base.data_set import create_dataset  # Used by YAML in marker_regression
from wqflask.show_trait import show_trait
from wqflask.show_trait import export_trait_data
from wqflask.heatmap import heatmap
from wqflask.external_tools import send_to_bnw
from wqflask.external_tools import send_to_webgestalt
from wqflask.external_tools import send_to_geneweaver
from wqflask.comparison_bar_chart import comparison_bar_chart
from wqflask.marker_regression import run_mapping
from wqflask.marker_regression import display_mapping_results
from wqflask.network_graph import network_graph
from wqflask.correlation.show_corr_results import set_template_vars
from wqflask.correlation.correlation_gn3_api import compute_correlation
from wqflask.correlation_matrix import show_corr_matrix
from wqflask.correlation import corr_scatter_plot
# from wqflask.wgcna import wgcna_analysis
# from wqflask.ctl import ctl_analysis
from wqflask.snp_browser import snp_browser
from wqflask.search_results import SearchResultPage
from wqflask.export_traits import export_search_results_csv
from wqflask.gsearch import GSearch
from wqflask.update_search_results import GSearch as UpdateGSearch
from wqflask.docs import Docs, update_text
from wqflask.decorators import admin_login_required
from wqflask.db_info import InfoPage

from utility import temp_data
from utility.tools import SQL_URI
from utility.tools import TEMPDIR
from utility.tools import USE_REDIS
from utility.tools import GN_SERVER_URL
from utility.tools import GN_VERSION
from utility.tools import JS_TWITTER_POST_FETCHER_PATH
from utility.tools import JS_GUIX_PATH
from utility.helper_functions import get_species_groups
from utility.authentication_tools import check_resource_availability
from utility.redis_tools import get_redis_conn


from base.webqtlConfig import GENERATED_IMAGE_DIR, DEFAULT_PRIVILEGES
from utility.benchmark import Bench

from pprint import pformat as pf

from wqflask.database import db_session


import utility.logger

Redis = get_redis_conn()

logger = utility.logger.getLogger(__name__)


@app.before_request
def connect_db():
    logger.info("@app.before_request connect_db")
    db = getattr(g, '_database', None)
    if db is None:
        g.db = g._database = sqlalchemy.create_engine(
            SQL_URI, encoding="latin1")
        logger.debug(g.db)


@app.before_request
def check_access_permissions():
    logger.debug("@app.before_request check_access_permissions")
    if 'dataset' in request.args:
        permissions = DEFAULT_PRIVILEGES
        if request.args['dataset'] != "Temp":
            dataset = create_dataset(request.args['dataset'])

            if dataset.type == "Temp":
                permissions = DEFAULT_PRIVILEGES
            elif 'trait_id' in request.args:
                permissions = check_resource_availability(
                    dataset, request.args['trait_id'])
            elif dataset.type != "Publish":
                permissions = check_resource_availability(dataset)

        if type(permissions['data']) is list:
            if 'view' not in permissions['data']:
                return redirect(url_for("no_access_page"))
        else:
            if permissions['data'] == 'no-access':
                return redirect(url_for("no_access_page"))


@app.teardown_appcontext
def shutdown_session(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        logger.debug("remove db_session")
        db_session.remove()
        g.db = None


@app.errorhandler(Exception)
def handle_bad_request(e):
    err_msg = str(e)
    logger.error(err_msg)
    logger.error(request.url)
    # get the stack trace and send it to the logger
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error(traceback.format_exc())
    now = datetime.datetime.utcnow()
    time_str = now.strftime('%l:%M%p UTC %b %d, %Y')
    formatted_lines = [request.url
                       + " (" + time_str + ")"] + traceback.format_exc().splitlines()

    # Handle random animations
    # Use a cookie to have one animation on refresh
    animation = request.cookies.get(err_msg[:32])
    if not animation:
        list = [fn for fn in os.listdir(
            "./wqflask/static/gif/error") if fn.endswith(".gif")]
        animation = random.choice(list)

    resp = make_response(render_template("error.html", message=err_msg,
                                         stack=formatted_lines, error_image=animation, version=GN_VERSION))

    # logger.error("Set cookie %s with %s" % (err_msg, animation))
    resp.set_cookie(err_msg[:32], animation)
    return resp


@app.route("/authentication_needed")
def no_access_page():
    return render_template("new_security/not_authenticated.html")


@app.route("/")
def index_page():
    logger.info("Sending index_page")
    logger.info(request.url)
    params = request.args
    if 'import_collections' in params:
        import_collections = params['import_collections']
        if import_collections == "true":
            g.user_session.import_traits_to_user(params['anon_id'])
    return render_template("index_page.html", version=GN_VERSION)


@app.route("/tmp/<img_path>")
def tmp_page(img_path):
    logger.info("In tmp_page")
    logger.info("img_path:", img_path)
    logger.info(request.url)
    initial_start_vars = request.form
    logger.info("initial_start_vars:", initial_start_vars)
    imgfile = open(GENERATED_IMAGE_DIR + img_path, 'rb')
    imgdata = imgfile.read()
    imgB64 = base64.b64encode(imgdata)
    bytesarray = array.array('B', imgB64)
    return render_template("show_image.html",
                           img_base64=bytesarray)


@app.route("/js/<path:filename>")
def js(filename):
    js_path = JS_GUIX_PATH
    name = filename
    if 'js_alt/' in filename:
        js_path = js_path.replace('genenetwork2/javascript', 'javascript')
        name = name.replace('js_alt/', '')
    return send_from_directory(js_path, name)


@app.route("/css/<path:filename>")
def css(filename):
    js_path = JS_GUIX_PATH
    name = filename
    if 'js_alt/' in filename:
        js_path = js_path.replace('genenetwork2/javascript', 'javascript')
        name = name.replace('js_alt/', '')
    return send_from_directory(js_path, name)


@app.route("/twitter/<path:filename>")
def twitter(filename):
    return send_from_directory(JS_TWITTER_POST_FETCHER_PATH, filename)


@app.route("/search", methods=('GET',))
def search_page():
    logger.info("in search_page")
    logger.info(request.url)
    result = None
    if USE_REDIS:
        with Bench("Trying Redis cache"):
            key = "search_results:v1:" + \
                json.dumps(request.args, sort_keys=True)
            logger.debug("key is:", pf(key))
            result = Redis.get(key)
            if result:
                logger.info("Redis cache hit on search results!")
                result = pickle.loads(result)
    else:
        logger.info("Skipping Redis cache (USE_REDIS=False)")

    logger.info("request.args is", request.args)
    the_search = SearchResultPage(request.args)
    result = the_search.__dict__
    valid_search = result['search_term_exists']

    if USE_REDIS and valid_search:
        Redis.set(key, pickle.dumps(result, pickle.HIGHEST_PROTOCOL))
        Redis.expire(key, 60 * 60)

    if valid_search:
        return render_template("search_result_page.html", **result)
    else:
        return render_template("search_error.html")


@app.route("/search_table", methods=('GET',))
def search_page_table():
    logger.info("in search_page table")
    logger.info(request.url)

    logger.info("request.args is", request.args)
    the_search = search_results.SearchResultPage(request.args)

    logger.info(type(the_search.trait_list))
    logger.info(the_search.trait_list)

    current_page = server_side.ServerSideTable(
        len(the_search.trait_list),
        the_search.trait_list,
        the_search.header_data_names,
        request.args,
    ).get_page()

    return flask.jsonify(current_page)


@app.route("/gsearch", methods=('GET',))
def gsearchact():
    logger.info(request.url)
    result = GSearch(request.args).__dict__
    type = request.args['type']
    if type == "gene":
        return render_template("gsearch_gene.html", **result)
    elif type == "phenotype":
        return render_template("gsearch_pheno.html", **result)


@app.route("/gsearch_table", methods=('GET',))
def gsearchtable():
    logger.info(request.url)

    gsearch_table_data = GSearch(request.args)
    current_page = server_side.ServerSideTable(
        gsearch_table_data.trait_count,
        gsearch_table_data.trait_list,
        gsearch_table_data.header_data_names,
        request.args,
    ).get_page()

    return flask.jsonify(current_page)


@app.route("/gsearch_updating", methods=('POST',))
def gsearch_updating():
    logger.info("REQUEST ARGS:", request.values)
    logger.info(request.url)
    result = UpdateGSearch(request.args).__dict__
    return result['results']


@app.route("/docedit")
def docedit():
    logger.info(request.url)
    try:
        if g.user_session.record['user_email_address'] == "zachary.a.sloan@gmail.com" or g.user_session.record['user_email_address'] == "labwilliams@gmail.com":
            doc = Docs(request.args['entry'], request.args)
            return render_template("docedit.html", **doc.__dict__)
        else:
            return "You shouldn't be here!"
    except:
        return "You shouldn't be here!"


@app.route('/generated/<filename>')
def generated_file(filename):
    logger.info(request.url)
    return send_from_directory(GENERATED_IMAGE_DIR, filename)


@app.route("/help")
def help():
    logger.info(request.url)
    doc = Docs("help", request.args)
    return render_template("docs.html", **doc.__dict__)


@app.route("/wgcna_setup", methods=('POST',))
def wcgna_setup():
    # We are going to get additional user input for the analysis
    logger.info("In wgcna, request.form is:", request.form)
    logger.info(request.url)
    # Display them using the template
    return render_template("wgcna_setup.html", **request.form)


# @app.route("/wgcna_results", methods=('POST',))
# def wcgna_results():
#     logger.info("In wgcna, request.form is:", request.form)
#     logger.info(request.url)
#     # Start R, load the package and pointers and create the analysis
#     wgcna = wgcna_analysis.WGCNA()
#     # Start the analysis, a wgcnaA object should be a separate long running thread
#     wgcnaA = wgcna.run_analysis(request.form)
#     # After the analysis is finished store the result
#     result = wgcna.process_results(wgcnaA)
#     # Display them using the template
#     return render_template("wgcna_results.html", **result)


@app.route("/ctl_setup", methods=('POST',))
def ctl_setup():
    # We are going to get additional user input for the analysis
    logger.info("In ctl, request.form is:", request.form)
    logger.info(request.url)
    # Display them using the template
    return render_template("ctl_setup.html", **request.form)


# @app.route("/ctl_results", methods=('POST',))
# def ctl_results():
#     logger.info("In ctl, request.form is:", request.form)
#     logger.info(request.url)
#     # Start R, load the package and pointers and create the analysis
#     ctl = ctl_analysis.CTL()
#     # Start the analysis, a ctlA object should be a separate long running thread
#     ctlA = ctl.run_analysis(request.form)
#     # After the analysis is finished store the result
#     result = ctl.process_results(ctlA)
#     # Display them using the template
#     return render_template("ctl_results.html", **result)


@app.route("/intro")
def intro():
    doc = Docs("intro", request.args)
    return render_template("docs.html", **doc.__dict__)


@app.route("/tutorials")
def tutorials():
    return render_template("tutorials.html")


@app.route("/credits")
def credits():
    return render_template("credits.html")


@app.route("/update_text", methods=('POST',))
def update_page():
    update_text(request.form)
    doc = Docs(request.form['entry_type'], request.form)
    return render_template("docs.html", **doc.__dict__)


@app.route("/submit_trait")
def submit_trait_form():
    logger.info(request.url)
    species_and_groups = get_species_groups()
    return render_template(
        "submit_trait.html",
        species_and_groups=species_and_groups,
        gn_server_url=GN_SERVER_URL,
        version=GN_VERSION)


@app.route("/trait/<name>/edit/phenotype-id/<phenotype_id>")
@admin_login_required
def edit_phenotype(name, phenotype_id):
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    publish_xref = fetchone(
        conn=conn,
        table="PublishXRef",
        where=PublishXRef(id_=name,
                          phenotype_id=phenotype_id))
    phenotype_ = fetchone(
        conn=conn,
        table="Phenotype",
        where=Phenotype(id_=publish_xref.phenotype_id))
    publication_ = fetchone(
        conn=conn,
        table="Publication",
        where=Publication(id_=publish_xref.publication_id))
    json_data = fetchall(
        conn,
        "metadata_audit",
        where=MetadataAudit(dataset_id=publish_xref.id_))

    Edit = namedtuple("Edit", ["field", "old", "new", "diff"])
    Diff = namedtuple("Diff", ["author", "diff", "timestamp"])
    diff_data = []
    for data in json_data:
        json_ = json.loads(data.json_data)
        timestamp = json_.get("timestamp")
        author = json_.get("author")
        for key, value in json_.items():
            if isinstance(value, dict):
                for field, data_ in value.items():
                    diff_data.append(
                        Diff(author=author,
                             diff=Edit(field,
                                       data_.get("old"),
                                       data_.get("new"),
                                       "\n".join(difflib.ndiff(
                                           [data_.get("old")],
                                           [data_.get("new")]))),
                             timestamp=timestamp))
    diff_data_ = None
    if len(diff_data) > 0:
        diff_data_ = groupby(diff_data, lambda x: x.timestamp)
    return render_template(
        "edit_phenotype.html",
        diff=diff_data_,
        publish_xref=publish_xref,
        phenotype=phenotype_,
        publication=publication_,
        version=GN_VERSION,
    )


@app.route("/trait/edit/probeset-name/<dataset_name>")
# @admin_login_required
def edit_probeset(dataset_name):
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    probeset_ = fetchone(conn=conn,
                         table="ProbeSet",
                         columns=list(probeset_mapping.values()),
                         where=Probeset(name=dataset_name))
    json_data = fetchall(
        conn,
        "metadata_audit",
        where=MetadataAudit(dataset_id=probeset_.id_))
    Edit = namedtuple("Edit", ["field", "old", "new", "diff"])
    Diff = namedtuple("Diff", ["author", "diff", "timestamp"])
    diff_data = []
    for data in json_data:
        json_ = json.loads(data.json_data)
        timestamp = json_.get("timestamp")
        author = json_.get("author")
        for key, value in json_.items():
            if isinstance(value, dict):
                for field, data_ in value.items():
                    diff_data.append(
                        Diff(author=author,
                             diff=Edit(field,
                                       data_.get("old"),
                                       data_.get("new"),
                                       "\n".join(difflib.ndiff(
                                           [data_.get("old")],
                                           [data_.get("new")]))),
                             timestamp=timestamp))
    diff_data_ = None
    if len(diff_data) > 0:
        diff_data_ = groupby(diff_data, lambda x: x.timestamp)
    return render_template(
        "edit_probeset.html",
        diff=diff_data_,
        probeset=probeset_)


@app.route("/trait/update", methods=["POST"])
@admin_login_required
def update_phenotype():
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    data_ = request.form.to_dict()
    TMPDIR = current_app.config.get("TMPDIR")
    author = g.user_session.record.get(b'user_name')
    if 'file' not in request.files:
        flash("No sample-data has been uploaded", "warning")
    else:
        file_ = request.files['file']
        trait_name = str(data_.get('dataset-name'))
        phenotype_id = str(data_.get('phenotype-id', 35))
        SAMPLE_DATADIR = os.path.join(TMPDIR, "sample-data")
        if not os.path.exists(SAMPLE_DATADIR):
            os.makedirs(SAMPLE_DATADIR)
        if not os.path.exists(os.path.join(SAMPLE_DATADIR,
                                           "diffs")):
            os.makedirs(os.path.join(SAMPLE_DATADIR,
                                     "diffs"))
        if not os.path.exists(os.path.join(SAMPLE_DATADIR,
                                           "updated")):
            os.makedirs(os.path.join(SAMPLE_DATADIR,
                                     "updated"))
        current_time = str(datetime.datetime.now().isoformat())
        new_file_name = (os.path.join(TMPDIR,
                                      "sample-data/updated/",
                                      (f"{author.decode('utf-8')}."
                                       f"{trait_name}.{phenotype_id}."
                                       f"{current_time}.csv")))
        uploaded_file_name = (os.path.join(
            TMPDIR,
            "sample-data/updated/",
            (f"updated.{author.decode('utf-8')}."
             f"{trait_name}.{phenotype_id}."
             f"{current_time}.csv")))
        file_.save(new_file_name)
        publishdata_id = ""
        lines = []
        with open(new_file_name, "r") as f:
            lines = f.read()
            first_line = lines.split('\n', 1)[0]
            publishdata_id = first_line.split("Id:")[-1].strip()
        with open(new_file_name, "w") as f:
            f.write(lines.split("\n\n")[-1])
        csv_ = get_trait_csv_sample_data(conn=conn,
                                         trait_name=str(trait_name),
                                         phenotype_id=str(phenotype_id))
        with open(uploaded_file_name, "w") as f_:
            f_.write(csv_.split("\n\n")[-1])
        r = run_cmd(cmd=("csvdiff "
                         f"'{uploaded_file_name}' '{new_file_name}' "
                         "--format json"))
        diff_output = (f"{TMPDIR}/sample-data/diffs/"
                       f"{trait_name}.{author.decode('utf-8')}."
                       f"{phenotype_id}.{current_time}.json")
        with open(diff_output, "w") as f:
            dict_ = json.loads(r.get("output"))
            dict_.update({
                "author": author.decode('utf-8'),
                "publishdata_id": publishdata_id,
                "dataset_id": data_.get("dataset-name"),
                "timestamp": datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S")
            })
            f.write(json.dumps(dict_))
        flash("Sample-data has been successfully uploaded", "success")
    # Run updates:
    phenotype_ = {
        "pre_pub_description": data_.get("pre-pub-desc"),
        "post_pub_description": data_.get("post-pub-desc"),
        "original_description": data_.get("orig-desc"),
        "units": data_.get("units"),
        "pre_pub_abbreviation": data_.get("pre-pub-abbrev"),
        "post_pub_abbreviation": data_.get("post-pub-abbrev"),
        "lab_code": data_.get("labcode"),
        "submitter": data_.get("submitter"),
        "owner": data_.get("owner"),
        "authorized_users": data_.get("authorized-users"),
    }
    updated_phenotypes = update(
        conn, "Phenotype",
        data=Phenotype(**phenotype_),
        where=Phenotype(id_=data_.get("phenotype-id")))
    diff_data = {}
    if updated_phenotypes:
        diff_data.update({"Phenotype": diff_from_dict(old={
            k: data_.get(f"old_{k}") for k, v in phenotype_.items()
            if v is not None}, new=phenotype_)})
    publication_ = {
        "abstract": data_.get("abstract"),
        "authors": data_.get("authors"),
        "title": data_.get("title"),
        "journal": data_.get("journal"),
        "volume": data_.get("volume"),
        "pages": data_.get("pages"),
        "month": data_.get("month"),
        "year": data_.get("year")
    }
    updated_publications = update(
        conn, "Publication",
        data=Publication(**publication_),
        where=Publication(id_=data_.get("pubmed-id",
                                        data_.get("old_id_"))))
    if updated_publications:
        diff_data.update({"Publication": diff_from_dict(old={
            k: data_.get(f"old_{k}") for k, v in publication_.items()
            if v is not None}, new=publication_)})
    if diff_data:
        diff_data.update({"dataset_id": data_.get("dataset-name")})
        diff_data.update({"author": author.decode('utf-8')})
        diff_data.update({"timestamp": datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")})
        insert(conn,
               table="metadata_audit",
               data=MetadataAudit(dataset_id=data_.get("dataset-name"),
                                  editor=author.decode("utf-8"),
                                  json_data=json.dumps(diff_data)))
        flash(f"Diff-data: \n{diff_data}\nhas been uploaded", "success")
    return redirect(f"/trait/{data_.get('dataset-name')}"
                    f"/edit/phenotype-id/{data_.get('phenotype-id')}")


@app.route("/probeset/update", methods=["POST"])
@admin_login_required
def update_probeset():
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    data_ = request.form.to_dict()
    probeset_ = {
        "id_": data_.get("id"),
        "symbol": data_.get("symbol"),
        "description": data_.get("description"),
        "probe_target_description": data_.get("probe_target_description"),
        "chr_": data_.get("chr"),
        "mb": data_.get("mb"),
        "alias": data_.get("alias"),
        "geneid": data_.get("geneid"),
        "homologeneid": data_.get("homologeneid"),
        "unigeneid": data_.get("unigeneid"),
        "omim": data_.get("OMIM"),
        "refseq_transcriptid": data_.get("refseq_transcriptid"),
        "blatseq": data_.get("blatseq"),
        "targetseq": data_.get("targetseq"),
        "strand_probe": data_.get("Strand_Probe"),
        "probe_set_target_region": data_.get("probe_set_target_region"),
        "probe_set_specificity": data_.get("probe_set_specificity"),
        "probe_set_blat_score": data_.get("probe_set_blat_score"),
        "probe_set_blat_mb_start": data_.get("probe_set_blat_mb_start"),
        "probe_set_blat_mb_end": data_.get("probe_set_blat_mb_end"),
        "probe_set_strand": data_.get("probe_set_strand"),
        "probe_set_note_by_rw": data_.get("probe_set_note_by_rw"),
        "flag": data_.get("flag")
    }
    updated_probeset = update(
        conn, "ProbeSet",
        data=Probeset(**probeset_),
        where=Probeset(id_=data_.get("id")))

    diff_data = {}
    author = g.user_session.record.get(b'user_name')
    if updated_probeset:
        diff_data.update({"Probeset": diff_from_dict(old={
            k: data_.get(f"old_{k}") for k, v in probeset_.items()
            if v is not None}, new=probeset_)})
    if diff_data:
        diff_data.update({"probeset_name": data_.get("probeset_name")})
        diff_data.update({"author": author.decode('utf-8')})
        diff_data.update({"timestamp": datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")})
        insert(conn,
               table="metadata_audit",
               data=MetadataAudit(dataset_id=data_.get("id"),
                                  editor=author.decode("utf-8"),
                                  json_data=json.dumps(diff_data)))
    return redirect(f"/trait/edit/probeset-name/{data_.get('probeset_name')}")


@app.route("/create_temp_trait", methods=('POST',))
def create_temp_trait():
    logger.info(request.url)
    doc = Docs("links")
    return render_template("links.html", **doc.__dict__)


@app.route('/export_trait_excel', methods=('POST',))
def export_trait_excel():
    """Excel file consisting of the sample data from the trait data and analysis page"""
    logger.info("In export_trait_excel")
    logger.info("request.form:", request.form)
    logger.info(request.url)
    trait_name, sample_data = export_trait_data.export_sample_table(
        request.form)

    logger.info("sample_data - type: %s -- size: %s" %
                (type(sample_data), len(sample_data)))

    buff = io.BytesIO()
    workbook = xlsxwriter.Workbook(buff, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    for i, row in enumerate(sample_data):
        for j, column in enumerate(row):
            worksheet.write(i, j, row[j])
    workbook.close()
    excel_data = buff.getvalue()
    buff.close()

    return Response(excel_data,
                    mimetype='application/vnd.ms-excel',
                    headers={"Content-Disposition": "attachment;filename=" + trait_name + ".xlsx"})


@app.route('/export_trait_csv', methods=('POST',))
def export_trait_csv():
    """CSV file consisting of the sample data from the trait data and analysis page"""
    logger.info("In export_trait_csv")
    logger.info("request.form:", request.form)
    logger.info(request.url)
    trait_name, sample_data = export_trait_data.export_sample_table(
        request.form)

    logger.info("sample_data - type: %s -- size: %s" %
                (type(sample_data), len(sample_data)))

    buff = io.StringIO()
    writer = csv.writer(buff)
    for row in sample_data:
        writer.writerow(row)
    csv_data = buff.getvalue()
    buff.close()

    return Response(csv_data,
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=" + trait_name + ".csv"})


@app.route('/export_traits_csv', methods=('POST',))
def export_traits_csv():
    """CSV file consisting of the traits from the search result page"""
    logger.info("In export_traits_csv")
    logger.info("request.form:", request.form)
    logger.info(request.url)
    file_list = export_search_results_csv(request.form)

    if len(file_list) > 1:
        now = datetime.datetime.now()
        time_str = now.strftime('%H:%M_%d%B%Y')
        filename = "export_{}".format(time_str)
        memory_file = io.BytesIO()
        with ZipFile(memory_file, mode='w', compression=ZIP_DEFLATED) as zf:
            for the_file in file_list:
                zf.writestr(the_file[0], the_file[1])

        memory_file.seek(0)

        return send_file(memory_file, attachment_filename=filename + ".zip", as_attachment=True)
    else:
        return Response(file_list[0][1],
                        mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=" + file_list[0][0]})


@app.route('/export_perm_data', methods=('POST',))
def export_perm_data():
    """CSV file consisting of the permutation data for the mapping results"""
    logger.info(request.url)
    perm_info = json.loads(request.form['perm_info'])

    now = datetime.datetime.now()
    time_str = now.strftime('%H:%M_%d%B%Y')

    file_name = "Permutation_" + \
        perm_info['num_perm'] + "_" + perm_info['trait_name'] + "_" + time_str

    the_rows = [
        ["#Permutation Test"],
        ["#File_name: " + file_name],
        ["#Metadata: From GeneNetwork.org"],
        ["#Trait_ID: " + perm_info['trait_name']],
        ["#Trait_description: " + perm_info['trait_description']],
        ["#N_permutations: " + str(perm_info['num_perm'])],
        ["#Cofactors: " + perm_info['cofactors']],
        ["#N_cases: " + str(perm_info['n_samples'])],
        ["#N_genotypes: " + str(perm_info['n_genotypes'])],
        ["#Genotype_file: " + perm_info['genofile']],
        ["#Units_linkage: " + perm_info['units_linkage']],
        ["#Permutation_stratified_by: "
            + ", ".join([str(cofactor) for cofactor in perm_info['strat_cofactors']])],
        ["#RESULTS_1: Suggestive LRS(p=0.63) = "
         + str(np.percentile(np.array(perm_info['perm_data']), 67))],
        ["#RESULTS_2: Significant LRS(p=0.05) = " + str(
            np.percentile(np.array(perm_info['perm_data']), 95))],
        ["#RESULTS_3: Highly Significant LRS(p=0.01) = " + str(
            np.percentile(np.array(perm_info['perm_data']), 99))],
        ["#Comment: Results sorted from low to high peak linkage"]
    ]

    buff = io.StringIO()
    writer = csv.writer(buff)
    writer.writerows(the_rows)
    for item in perm_info['perm_data']:
        writer.writerow([item])
    csv_data = buff.getvalue()
    buff.close()

    return Response(csv_data,
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=" + file_name + ".csv"})


@app.route("/show_temp_trait", methods=('POST',))
def show_temp_trait_page():
    logger.info(request.url)
    template_vars = show_trait.ShowTrait(request.form)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    return render_template("show_trait.html", **template_vars.__dict__)


@app.route("/show_trait")
def show_trait_page():
    logger.info(request.url)
    template_vars = show_trait.ShowTrait(request.args)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    return render_template("show_trait.html", **template_vars.__dict__)


@app.route("/heatmap", methods=('POST',))
def heatmap_page():
    logger.info("In heatmap, request.form is:", pf(request.form))
    logger.info(request.url)

    start_vars = request.form
    temp_uuid = uuid.uuid4()

    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if traits[0] != "":
        version = "v5"
        key = "heatmap:{}:".format(
            version) + json.dumps(start_vars, sort_keys=True)
        logger.info("key is:", pf(key))
        with Bench("Loading cache"):
            result = Redis.get(key)

        if result:
            logger.info("Cache hit!!!")
            with Bench("Loading results"):
                result = pickle.loads(result)

        else:
            logger.info("Cache miss!!!")

            template_vars = heatmap.Heatmap(request.form, temp_uuid)
            template_vars.js_data = json.dumps(template_vars.js_data,
                                               default=json_default_handler,
                                               indent="   ")

            result = template_vars.__dict__

            for item in list(template_vars.__dict__.keys()):
                logger.info(
                    "  ---**--- {}: {}".format(type(template_vars.__dict__[item]), item))

            pickled_result = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
            logger.info("pickled result length:", len(pickled_result))
            Redis.set(key, pickled_result)
            Redis.expire(key, 60 * 60)

        with Bench("Rendering template"):
            rendered_template = render_template("heatmap.html", **result)

    else:
        rendered_template = render_template(
            "empty_collection.html", **{'tool': 'Heatmap'})

    return rendered_template


@app.route("/bnw_page", methods=('POST',))
def bnw_page():
    logger.info("In run BNW, request.form is:", pf(request.form))
    logger.info(request.url)

    start_vars = request.form

    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if traits[0] != "":
        template_vars = send_to_bnw.SendToBNW(request.form)

        result = template_vars.__dict__
        rendered_template = render_template("bnw_page.html", **result)
    else:
        rendered_template = render_template(
            "empty_collection.html", **{'tool': 'BNW'})

    return rendered_template


@app.route("/webgestalt_page", methods=('POST',))
def webgestalt_page():
    logger.info("In run WebGestalt, request.form is:", pf(request.form))
    logger.info(request.url)

    start_vars = request.form

    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if traits[0] != "":
        template_vars = send_to_webgestalt.SendToWebGestalt(request.form)

        result = template_vars.__dict__
        rendered_template = render_template("webgestalt_page.html", **result)
    else:
        rendered_template = render_template(
            "empty_collection.html", **{'tool': 'WebGestalt'})

    return rendered_template


@app.route("/geneweaver_page", methods=('POST',))
def geneweaver_page():
    logger.info("In run WebGestalt, request.form is:", pf(request.form))
    logger.info(request.url)

    start_vars = request.form

    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if traits[0] != "":
        template_vars = send_to_geneweaver.SendToGeneWeaver(request.form)

        result = template_vars.__dict__
        rendered_template = render_template("geneweaver_page.html", **result)
    else:
        rendered_template = render_template(
            "empty_collection.html", **{'tool': 'GeneWeaver'})

    return rendered_template


@app.route("/comparison_bar_chart", methods=('POST',))
def comp_bar_chart_page():
    logger.info("In comp bar chart, request.form is:", pf(request.form))
    logger.info(request.url)

    start_vars = request.form

    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if traits[0] != "":
        template_vars = comparison_bar_chart.ComparisonBarChart(request.form)
        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")

        result = template_vars.__dict__
        rendered_template = render_template(
            "comparison_bar_chart.html", **result)
    else:
        rendered_template = render_template(
            "empty_collection.html", **{'tool': 'Comparison Bar Chart'})

    return rendered_template


@app.route("/mapping_results_container")
def mapping_results_container_page():
    return render_template("mapping_results_container.html")


@app.route("/loading", methods=('POST',))
def loading_page():
    # logger.info(request.url)
    initial_start_vars = request.form
    start_vars_container = {}
    n_samples = 0  # ZS: So it can be displayed on loading page
    if 'wanted_inputs' in initial_start_vars:
        wanted = initial_start_vars['wanted_inputs'].split(",")
        start_vars = {}
        for key, value in list(initial_start_vars.items()):
            if key in wanted:
                start_vars[key] = value

        if 'n_samples' in start_vars:
            n_samples = int(start_vars['n_samples'])
        else:
            sample_vals_dict = json.loads(start_vars['sample_vals'])
            if 'group' in start_vars:
                dataset = create_dataset(
                    start_vars['dataset'], group_name=start_vars['group'])
            else:
                dataset = create_dataset(start_vars['dataset'])
            samples = dataset.group.samplelist
            if 'genofile' in start_vars:
                if start_vars['genofile'] != "":
                    genofile_string = start_vars['genofile']
                    dataset.group.genofile = genofile_string.split(":")[0]
                    genofile_samples = run_mapping.get_genofile_samplelist(
                        dataset)
                    if len(genofile_samples) > 1:
                        samples = genofile_samples

            for sample in samples:
                if sample in sample_vals_dict:
                    if sample_vals_dict[sample] != "x":
                        n_samples += 1

        start_vars['n_samples'] = n_samples
        start_vars['wanted_inputs'] = initial_start_vars['wanted_inputs']

        start_vars_container['start_vars'] = start_vars
    else:
        start_vars_container['start_vars'] = initial_start_vars

    rendered_template = render_template("loading.html", **start_vars_container)

    return rendered_template


@app.route("/run_mapping", methods=('POST',))
def mapping_results_page():
    initial_start_vars = request.form
    logger.info(request.url)
    temp_uuid = initial_start_vars['temp_uuid']
    wanted = (
        'trait_id',
        'dataset',
        'group',
        'species',
        'samples',
        'vals',
        'sample_vals',
        'first_run',
        'output_files',
        'geno_db_exists',
        'method',
        'mapping_results_path',
        'trimmed_markers',
        'selected_chr',
        'chromosomes',
        'mapping_scale',
        'plotScale',
        'score_type',
        'suggestive',
        'significant',
        'num_perm',
        'permCheck',
        'perm_strata',
        'strat_var',
        'categorical_vars',
        'perm_output',
        'num_bootstrap',
        'bootCheck',
        'bootstrap_results',
        'LRSCheck',
        'covariates',
        'maf',
        'use_loco',
        'manhattan_plot',
        'color_scheme',
        'manhattan_single_color',
        'control_marker',
        'do_control',
        'genofile',
        'genofile_string',
        'pair_scan',
        'startMb',
        'endMb',
        'graphWidth',
        'lrsMax',
        'additiveCheck',
        'showSNP',
        'showGenes',
        'viewLegend',
        'haplotypeAnalystCheck',
        'mapmethod_rqtl_geno',
        'mapmodel_rqtl_geno',
        'temp_trait',
        'reaper_version',
        'n_samples',
        'transform'
    )
    start_vars = {}
    for key, value in list(initial_start_vars.items()):
        if key in wanted:
            start_vars[key] = value

    version = "v3"
    key = "mapping_results:{}:".format(
        version) + json.dumps(start_vars, sort_keys=True)
    with Bench("Loading cache"):
        result = None  # Just for testing
        #result = Redis.get(key)

    #logger.info("************************ Starting result *****************")
    #logger.info("result is [{}]: {}".format(type(result), result))
    #logger.info("************************ Ending result ********************")

    if result:
        logger.info("Cache hit!!!")
        with Bench("Loading results"):
            result = pickle.loads(result)
    else:
        logger.info("Cache miss!!!")
        with Bench("Total time in RunMapping"):
            try:
                template_vars = run_mapping.RunMapping(start_vars, temp_uuid)
                if template_vars.no_results:
                    rendered_template = render_template("mapping_error.html")
                    return rendered_template
            except:
                rendered_template = render_template("mapping_error.html")
                return rendered_template

            template_vars.js_data = json.dumps(template_vars.js_data,
                                               default=json_default_handler,
                                               indent="   ")

            result = template_vars.__dict__

            if result['pair_scan']:
                with Bench("Rendering template"):
                    img_path = result['pair_scan_filename']
                    logger.info("img_path:", img_path)
                    initial_start_vars = request.form
                    logger.info("initial_start_vars:", initial_start_vars)
                    imgfile = open(TEMPDIR + img_path, 'rb')
                    imgdata = imgfile.read()
                    imgB64 = base64.b64encode(imgdata)
                    bytesarray = array.array('B', imgB64)
                    result['pair_scan_array'] = bytesarray
                    rendered_template = render_template(
                        "pair_scan_results.html", **result)
            else:
                gn1_template_vars = display_mapping_results.DisplayMappingResults(
                    result).__dict__

                rendered_template = render_template(
                    "mapping_results.html", **gn1_template_vars)

    return rendered_template


@app.route("/export_mapping_results", methods=('POST',))
def export_mapping_results():
    logger.info("request.form:", request.form)
    logger.info(request.url)
    file_path = request.form.get("results_path")
    results_csv = open(file_path, "r").read()
    response = Response(results_csv,
                        mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=mapping_results.csv"})

    return response


@app.route("/export_corr_matrix", methods=('POST',))
def export_corr_matrix():
    file_path = request.form.get("export_filepath")
    file_name = request.form.get("export_filename")
    results_csv = open(file_path, "r").read()
    response = Response(results_csv,
                        mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=" + file_name + ".csv"})

    return response


@app.route("/export", methods=('POST',))
def export():
    logger.info("request.form:", request.form)
    logger.info(request.url)
    svg_xml = request.form.get("data", "Invalid data")
    filename = request.form.get("filename", "manhattan_plot_snp")
    response = Response(svg_xml, mimetype="image/svg+xml")
    response.headers["Content-Disposition"] = "attachment; filename=%s" % filename
    return response


@app.route("/export_pdf", methods=('POST',))
def export_pdf():
    import cairosvg
    logger.info("request.form:", request.form)
    logger.info(request.url)
    svg_xml = request.form.get("data", "Invalid data")
    logger.info("svg_xml:", svg_xml)
    filename = request.form.get("filename", "interval_map_pdf")
    pdf_file = cairosvg.svg2pdf(bytestring=svg_xml)
    response = Response(pdf_file, mimetype="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=%s" % filename
    return response


@app.route("/network_graph", methods=('POST',))
def network_graph_page():
    logger.info("In network_graph, request.form is:", pf(request.form))
    logger.info(request.url)
    start_vars = request.form
    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if traits[0] != "":
        template_vars = network_graph.NetworkGraph(start_vars)
        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")

        return render_template("network_graph.html", **template_vars.__dict__)
    else:
        return render_template("empty_collection.html", **{'tool': 'Network Graph'})


@app.route("/corr_compute", methods=('POST',))
def corr_compute_page():
    correlation_results = compute_correlation(request.form, compute_all=True)
    correlation_results = set_template_vars(request.form, correlation_results)
    return render_template("correlation_page.html", **correlation_results)


@app.route("/test_corr_compute", methods=["POST"])
def test_corr_compute_page():
    correlation_data = compute_correlation(request.form, compute_all=True)
    return render_template("test_correlation_page.html", **correlation_data)


@app.route("/corr_matrix", methods=('POST',))
def corr_matrix_page():
    logger.info("In corr_matrix, request.form is:", pf(request.form))
    logger.info(request.url)

    start_vars = request.form
    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if len(traits) > 1:
        template_vars = show_corr_matrix.CorrelationMatrix(start_vars)
        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")

        return render_template("correlation_matrix.html", **template_vars.__dict__)
    else:
        return render_template("empty_collection.html", **{'tool': 'Correlation Matrix'})


@app.route("/corr_scatter_plot")
def corr_scatter_plot_page():
    logger.info(request.url)
    template_vars = corr_scatter_plot.CorrScatterPlot(request.args)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    return render_template("corr_scatterplot.html", **template_vars.__dict__)


@app.route("/snp_browser", methods=('GET',))
def snp_browser_page():
    logger.info(request.url)
    template_vars = snp_browser.SnpBrowser(request.args)

    return render_template("snp_browser.html", **template_vars.__dict__)


@app.route("/db_info", methods=('GET',))
def db_info_page():
    template_vars = InfoPage(request.args)

    return render_template("info_page.html", **template_vars.__dict__)


@app.route("/snp_browser_table", methods=('GET',))
def snp_browser_table():
    logger.info(request.url)
    snp_table_data = snp_browser.SnpBrowser(request.args)
    current_page = server_side.ServerSideTable(
        snp_table_data.rows_count,
        snp_table_data.table_rows,
        snp_table_data.header_data_names,
        request.args,
    ).get_page()

    return flask.jsonify(current_page)


@app.route("/tutorial/WebQTLTour", methods=('GET',))
def tutorial_page():
    # ZS: Currently just links to GN1
    logger.info(request.url)
    return redirect("http://gn1.genenetwork.org/tutorial/WebQTLTour/")


@app.route("/tutorial/security", methods=('GET',))
def security_tutorial_page():
    # ZS: Currently just links to GN1
    logger.info(request.url)
    return render_template("admin/security_help.html")


@app.route("/submit_bnw", methods=('POST',))
def submit_bnw():
    logger.info(request.url)
    return render_template("empty_collection.html", **{'tool': 'Correlation Matrix'})

# Take this out or secure it before putting into production


@app.route("/get_temp_data")
def get_temp_data():
    logger.info(request.url)
    temp_uuid = request.args['key']
    return flask.jsonify(temp_data.TempData(temp_uuid).get_all())


@app.route("/browser_input", methods=('GET',))
def browser_inputs():
    """  Returns JSON from tmp directory for the purescript genome browser"""

    filename = request.args['filename']

    with open("{}/gn2/".format(TEMPDIR) + filename + ".json", "r") as the_file:
        file_contents = json.load(the_file)

    return flask.jsonify(file_contents)


def json_default_handler(obj):
    """Based on http://stackoverflow.com/a/2680060/1175849"""
    # Handle datestamps
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    # Handle integer keys for dictionaries
    elif isinstance(obj, int) or isinstance(obj, uuid.UUID):
        return str(obj)
    # Handle custom objects
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        raise TypeError('Object of type %s with value of %s is not JSON serializable' % (
            type(obj), repr(obj)))


@app.route("/trait/<trait_name>/sampledata/<phenotype_id>")
def get_sample_data_as_csv(trait_name: int, phenotype_id: int):
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    csv_ = get_trait_csv_sample_data(conn, str(trait_name),
                                     str(phenotype_id))
    return Response(
        csv_,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=myplot.csv"}
    )


@app.route("/admin/data-sample/diffs/")
@admin_login_required
def display_diffs_admin():
    TMPDIR = current_app.config.get("TMPDIR")
    DIFF_DIR = f"{TMPDIR}/sample-data/diffs"
    files = []
    if os.path.exists(DIFF_DIR):
        files = os.listdir(DIFF_DIR)
        files = filter(lambda x: not(x.endswith((".approved", ".rejected"))),
                       files)
    return render_template("display_files_admin.html",
                           files=files)


@app.route("/user/data-sample/diffs/")
def display_diffs_users():
    TMPDIR = current_app.config.get("TMPDIR")
    DIFF_DIR = f"{TMPDIR}/sample-data/diffs"
    files = []
    author = g.user_session.record.get(b'user_name').decode("utf-8")
    if os.path.exists(DIFF_DIR):
        files = os.listdir(DIFF_DIR)
        files = filter(lambda x: not(x.endswith((".approved", ".rejected"))) \
                       and author in x,
                       files)
    return render_template("display_files_user.html",
                           files=files)


@app.route("/data-samples/approve/<name>")
def approve_data(name):
    sample_data = {}
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    TMPDIR = current_app.config.get("TMPDIR")
    with open(os.path.join(f"{TMPDIR}/sample-data/diffs",
                           name), 'r') as myfile:
        sample_data = json.load(myfile)
    PUBLISH_ID = sample_data.get("publishdata_id")
    modifications = [d for d in sample_data.get("Modifications")]
    row_counts = len(modifications)
    for modification in modifications:
        if modification.get("Current"):
            (strain_id,
             strain_name,
             value, se, count) = modification.get("Current").split(",")
            update_sample_data(
                conn=conn,
                strain_name=strain_name,
                strain_id=int(strain_id),
                publish_data_id=int(PUBLISH_ID),
                value=value,
                error=se,
                count=count
            )
            insert(conn,
                   table="metadata_audit",
                   data=MetadataAudit(
                       dataset_id=name.split(".")[0],  # use the dataset name
                       editor=sample_data.get("author"),
                       json_data=json.dumps(sample_data)))
    if modifications:
        # Once data is approved, rename it!
        os.rename(os.path.join(f"{TMPDIR}/sample-data/diffs", name),
                  os.path.join(f"{TMPDIR}/sample-data/diffs",
                               f"{name}.approved"))
        flash((f"Just updated data from: {name}; {row_counts} "
               "row(s) modified!"),
              "success")
    return redirect("/admin/data-sample/diffs/")


@app.route("/data-samples/reject/<name>")
def reject_data(name):
    TMPDIR = current_app.config.get("TMPDIR")
    os.rename(os.path.join(f"{TMPDIR}/sample-data/diffs", name),
              os.path.join(f"{TMPDIR}/sample-data/diffs",
                           f"{name}.rejected"))
    flash(f"{name} has been rejected!", "success")
    return redirect("/admin/data-sample/diffs/")


@app.route("/display-file/<name>")
def display_file(name):
    TMPDIR = current_app.config.get("TMPDIR")
    with open(os.path.join(f"{TMPDIR}/sample-data/diffs",
                           name), 'r') as myfile:
        content = myfile.read()
    return Response(content, mimetype='text/json')
