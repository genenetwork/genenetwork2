"""Main routing table for GN2"""
import array
import base64
import csv
import datetime
import flask
import hashlib
import io  # Todo: Use cStringIO?

import json
import numpy as np
import os
import pickle as pickle
import random
import requests
import sys
import traceback
import uuid
import xlsxwriter

from functools import reduce

from zipfile import ZipFile
from zipfile import ZIP_DEFLATED

from uuid import UUID

from urllib.parse import urljoin

from gn2.wqflask import app

from gn3.computations.gemma import generate_hash_of_string
from flask import current_app
from flask import g
from flask import Response
from flask import request
from flask import make_response
from flask import render_template
from flask import send_from_directory
from flask import redirect
from flask import send_file
from flask import url_for
from flask import flash

from gn2.wqflask import search_results
from gn2.wqflask import server_side
# Used by YAML in marker_regression
from gn2.base.data_set import create_dataset
from gn2.wqflask.show_trait import show_trait
from gn2.wqflask.show_trait import export_trait_data
from gn2.wqflask.show_trait.show_trait import get_diff_of_vals
from gn2.wqflask.heatmap import heatmap
from gn2.wqflask.external_tools import send_to_bnw
from gn2.wqflask.external_tools import send_to_webgestalt
from gn2.wqflask.external_tools import send_to_geneweaver
from gn2.wqflask.comparison_bar_chart import comparison_bar_chart
from gn2.wqflask.marker_regression import run_mapping
from gn2.wqflask.marker_regression.exceptions import NoMappingResultsError
from gn2.wqflask.marker_regression import display_mapping_results
from gn2.wqflask.network_graph import network_graph
from gn2.wqflask.correlation_matrix import show_corr_matrix
from gn2.wqflask.correlation import corr_scatter_plot
from gn2.wqflask.ctl.gn3_ctl_analysis import run_ctl

from gn2.wqflask.wgcna.gn3_wgcna import run_wgcna
from gn2.wqflask.snp_browser import snp_browser
from gn2.wqflask.search_results import SearchResultPage
from gn2.wqflask.export_traits import export_traits
from gn2.wqflask.gsearch import GSearch
from gn2.wqflask.update_search_results import GSearch as UpdateGSearch
from gn2.wqflask.docs import Docs, update_text

from gn2.wqflask.oauth2 import client
from gn2.wqflask.oauth2.client import no_token_get
from gn2.wqflask.oauth2.request_utils import with_flash_error

from gn2.utility import temp_data
from gn2.utility.tools import get_setting
from gn2.utility.tools import TEMPDIR
from gn2.utility.tools import USE_REDIS
from gn2.utility.tools import REDIS_URL
from gn2.utility.tools import GN_SERVER_URL
from gn2.utility.tools import GN3_LOCAL_URL
from gn2.utility.tools import JS_TWITTER_POST_FETCHER_PATH
from gn2.utility.tools import JS_GUIX_PATH
from gn2.utility.helper_functions import get_species_groups
from gn2.utility.redis_tools import get_redis_conn

import gn2.utility.hmac as hmac

from gn2.base.webqtlConfig import TMPDIR
from gn2.base.webqtlConfig import GENERATED_IMAGE_DIR

from gn2.wqflask.database import database_connection

import gn2.jobs.jobs as jobs

from gn2.wqflask.oauth2.session import session_info
from gn2.wqflask.oauth2.client import user_logged_in

from gn2.wqflask import requests as monad_requests

from gn2.wqflask.oauth2.checks import require_oauth2


Redis = get_redis_conn()


@app.errorhandler(Exception)
def handle_generic_exceptions(e):
    import werkzeug
    err_msg = str(e)
    now = datetime.datetime.utcnow()
    time_str = now.strftime('%l:%M%p UTC %b %d, %Y')
    # get the stack trace and send it to the logger
    exc_type, exc_value, exc_traceback = sys.exc_info()
    formatted_lines = (f"{request.url} ({time_str}) \n"
                       f"{traceback.format_exc()}")
    _message_templates = {
        werkzeug.exceptions.NotFound: ("404: Not Found: "
                                       f"{time_str}: {request.url}"),
        werkzeug.exceptions.BadRequest: ("400: Bad Request: "
                                         f"{time_str}: {request.url}"),
        werkzeug.exceptions.RequestTimeout: ("408: Request Timeout: "
                                             f"{time_str}: {request.url}")}
    # Default to the lengthy stack trace!
    app.logger.error(_message_templates.get(exc_type,
                                            formatted_lines))
    # Handle random animations
    # Use a cookie to have one animation on refresh
    animation = request.cookies.get(err_msg[:32])
    if not animation:
        animation = random.choice([fn for fn in os.listdir(
            "./gn2/wqflask/static/gif/error") if fn.endswith(".gif")])

    resp = make_response(render_template("error.html", message=err_msg,
                                         stack={formatted_lines},
                                         error_image=animation,
                                         version=current_app.config.get("GN_VERSION")))
    resp.set_cookie(err_msg[:32], animation)
    return resp


@app.route("/authentication_needed")
def no_access_page():
    return render_template("new_security/not_authenticated.html")


@app.route("/")
def index_page():
    anon_id = session_info()["anon_id"]

    def __render__(colls):
        return render_template("index_page.html", version=current_app.config.get("GN_VERSION"),
                               gn_server_url=GN_SERVER_URL,
                               anon_collections=(
                                   colls if user_logged_in() else []),
                               anon_id=anon_id)

    return no_token_get(
        f"auth/user/collections/{anon_id}/list").either(
            lambda err: __render__([]),
            __render__)


@app.route("/tmp/<img_path>")
def tmp_page(img_path):
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
    result = None
    if USE_REDIS:
        key = "search_results:v1:" + \
            json.dumps(request.args, sort_keys=True)
        result = Redis.get(key)
        if result:
            result = pickle.loads(result)
    result = SearchResultPage(request.args).__dict__
    valid_search = result['search_term_exists']
    if USE_REDIS and valid_search:
        # Redis.set(key, pickle.dumps(result, pickle.HIGHEST_PROTOCOL))
        Redis.expire(key, 60 * 60)

    if valid_search:
        return render_template("search_result_page.html", **result)
    else:
        return render_template("search_error.html")


@app.route("/search_table", methods=('GET',))
def search_page_table():
    the_search = search_results.SearchResultPage(request.args)
    current_page = server_side.ServerSideTable(
        len(the_search.trait_list),
        the_search.trait_list,
        the_search.header_data_names,
        request.args,
    ).get_page()

    return flask.jsonify(current_page)


@app.route("/gsearch", methods=('GET',))
def gsearchact():
    result = GSearch(request.args).__dict__
    type = request.args['type']
    if type == "gene":
        return render_template("gsearch_gene.html", **result)
    elif type == "phenotype":
        return render_template("gsearch_pheno.html", **result)


@app.route("/gsearch_table", methods=('GET',))
def gsearchtable():
    gsearch_table_data = GSearch(request.args)
    current_page = server_side.ServerSideTable(
        gsearch_table_data.trait_count,
        gsearch_table_data.trait_list,
        gsearch_table_data.header_data_names,
        request.args,
    ).get_page()

    return flask.jsonify(current_page)


@app.route("/gnqna", methods=["POST", "GET"])
@require_oauth2
def gnqna():

    if request.method == "POST":
        try:
            def __error__(resp):
                return resp.json()

            def error_page(error_msg):
                return render_template("gnqa_errors.html", error=error_msg)

            def __success__(resp):
                return render_template("gnqa_answer.html", **{"gn_server_url": GN3_LOCAL_URL, **(resp.json())})
            """
            disable gn-auth currently not stable
            if not user_logged_in():
                return error_page("Please Login/Register to  Genenetwork to access this Service")
            """
            token = session_info()["user"]["token"].either(
                lambda err: err, lambda tok: tok["access_token"])
            return monad_requests.post(
                urljoin(GN3_LOCAL_URL,
                        "/api/llm/gnqna"),
                json=dict(request.form),
                headers={
                    "Authorization": f"Bearer {token}"
                }
            ).then(
                lambda resp: resp
            ).either(
                __error__, __success__)
        except Exception as error:
            return flask.jsonify({"error": str(error)})
    prev_queries = (monad_requests.get(
        urljoin(GN3_LOCAL_URL,
                "/api/llm/get_hist_names")
    ).then(
        lambda resp: resp
    ).either(lambda x: [], lambda x: x.json()["prev_queries"]))

    return render_template("gnqa.html", prev_queries=prev_queries)


@app.route("/gnqna/hist/", methods=["GET"])
@require_oauth2
def get_hist_titles():
    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    response = monad_requests.get(urljoin(GN3_LOCAL_URL,
                                          "/api/llm/hist/titles"),
                                  headers={
        "Authorization": f"Bearer {token}"
    }
    ).then(lambda resp: resp).either(
        lambda x:  x.json(), lambda x: x.json())
    return render_template("gnqa_search_history.html", **response)


@app.route("/gnqna/hist/search/<search_term>", methods=["GET"])
@require_oauth2
def fetch_hist_records(search_term):
    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    response = monad_requests.get(urljoin(GN3_LOCAL_URL,
                                          f"/api/llm/history/{search_term}"),
                                  headers={
        "Authorization": f"Bearer {token}"
    }
    ).then(lambda resp: resp).either(
        lambda x:  x.json(), lambda x: x.json())
    return render_template("gnqa_answer.html", **response)


@app.route("/gnqna/rating/<task_id>/<int(signed=True):weight>",
           methods=["POST"])
@require_oauth2
def gnqna_rating(task_id, weight):
    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    return monad_requests.post(
        urljoin(GN3_LOCAL_URL,
                f"/api/llm/rating/{task_id}"),
        json={**dict(request.form), "weight": weight},
        headers={
            "Authorization": f"Bearer {token}"
        }
    ).then(
        lambda resp: resp).either(lambda x: (x.json(), x.status_code),
                                  lambda x: (x.json(), x.status_code))


@app.route("/gsearch_updating", methods=('POST',))
def gsearch_updating():
    result = UpdateGSearch(request.args).__dict__
    return result['results']


@app.route("/docedit")
def docedit():
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
    return send_from_directory(GENERATED_IMAGE_DIR, filename)


@app.route("/help")
def help():
    doc = Docs("help", request.args)
    return render_template("docs.html", **doc.__dict__)


@app.route("/wgcna_setup", methods=('POST',))
def wcgna_setup():
    # We are going to get additional user input for the analysis
    # Display them using the template
    return render_template("wgcna_setup.html", **request.form)


@app.route("/wgcna_results", methods=('POST',))
def wcgna_results():
    """call the gn3 api to get wgcna response data"""
    results = run_wgcna(dict(request.form))
    return render_template("gn3_wgcna_results.html", **results)


@app.route("/ctl_setup", methods=('POST',))
def ctl_setup():
    # We are going to get additional user input for the analysis
    # Display them using the template
    return render_template("ctl_setup.html", **request.form)


@app.route("/ctl_results", methods=["POST"])
def ctl_results():
    ctl_results = run_ctl(request.form)
    return render_template("gn3_ctl_results.html", **ctl_results)


@app.route("/ctl_network_files/<file_name>/<file_type>")
def fetch_network_files(file_name, file_type):
    file_path = f"{file_name}.{file_type}"

    file_path = os.path.join("/tmp/", file_path)

    return send_file(file_path)


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
    species_and_groups = get_species_groups()
    return render_template(
        "submit_trait.html",
        species_and_groups=species_and_groups,
        gn_server_url=GN_SERVER_URL,
        version=current_app.config.get("GN_VERSION"))


@app.route("/create_temp_trait", methods=('POST',))
def create_temp_trait():
    doc = Docs("links")
    return render_template("links.html", **doc.__dict__)


@app.route('/export_trait_excel', methods=('POST',))
def export_trait_excel():
    """Excel file consisting of the sample data from the trait data and analysis page"""
    trait_name, sample_data = export_trait_data.export_sample_table(
        request.form)
    app.logger.info(request.url)
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
    trait_name, sample_data = export_trait_data.export_sample_table(
        request.form)

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
    file_list = export_traits(request.form, "metadata")

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


@app.route('/export_collection', methods=('POST',))
def export_collection_csv():
    """CSV file consisting of trait list so collections can be exported/shared"""
    out_file = export_traits(request.form, "collection")
    return Response(out_file[1],
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=" + out_file[0] + ".csv"})


@app.route('/export_perm_data', methods=('POST',))
def export_perm_data():
    """CSV file consisting of the permutation data for the mapping results"""
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
    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
        user_id = ((g.user_session.record.get(b"user_id") or b"").decode("utf-8")
                   or g.user_session.record.get("user_id") or "")
        template_vars = show_trait.ShowTrait(cursor,
                                             user_id=user_id,
                                             kw=request.form)
        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")
        return redirect(url_for("show_trait_page", dataset=template_vars.dataset.name, trait_id=template_vars.trait_id))


@app.route("/show_trait")
def show_trait_page():
    def __show_trait__(privileges_data):
        assert len(privileges_data) == 1
        privileges_data = privileges_data[0]
        trait_privileges = tuple(
            item for item in privileges_data["privileges"])
        with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:

            user_id = ((g.user_session.record.get(b"user_id") or b"").decode("utf-8")
                       or g.user_session.record.get("user_id") or "")
            template_vars = show_trait.ShowTrait(cursor,
                                                 user_id=user_id,
                                                 kw=request.args)
            template_vars.js_data = json.dumps(template_vars.js_data,
                                               default=json_default_handler,
                                               indent="   ")
            return render_template(
                "show_trait.html",
                **{
                    **template_vars.__dict__,
                    "user": privileges_data["user"],
                    "trait_privileges": trait_privileges,
                    "resource_id": privileges_data["resource_id"]
                })
    dataset = request.args["dataset"]
    trait_id = request.args["trait_id"]

    return client.post(
        "auth/data/authorisation",
        json={
            "traits": [f"{dataset}::{trait_id}"]
        }).either(with_flash_error(render_template("show_trait_error.html")),
                  __show_trait__)


@app.route("/heatmap", methods=('POST',))
def heatmap_page():
    start_vars = request.form
    temp_uuid = uuid.uuid4()

    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
        if traits[0] != "":
            version = "v5"
            key = "heatmap:{}:".format(
                version) + json.dumps(start_vars, sort_keys=True)
            result = Redis.get(key)

            if result:
                result = pickle.loads(result)

            else:
                template_vars = heatmap.Heatmap(
                    cursor, request.form, temp_uuid)
                template_vars.js_data = json.dumps(template_vars.js_data,
                                                   default=json_default_handler,
                                                   indent="   ")

                result = template_vars.__dict__

                pickled_result = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
                Redis.set(key, pickled_result)
                Redis.expire(key, 60 * 60)
            rendered_template = render_template("heatmap.html", **result)

        else:
            rendered_template = render_template(
                "empty_collection.html", **{'tool': 'Heatmap'})

    return rendered_template


@app.route("/bnw_page", methods=('POST',))
def bnw_page():
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
    initial_start_vars = request.form
    start_vars_container = {}
    n_samples = 0  # ZS: So it can be displayed on loading page
    if 'wanted_inputs' in initial_start_vars:
        wanted = initial_start_vars['wanted_inputs'].split(",")
        start_vars = {}
        for key, value in list(initial_start_vars.items()):
            if key in wanted:
                start_vars[key] = value

        sample_vals_dict = json.loads(start_vars['sample_vals'])
        if 'n_samples' in start_vars:
            n_samples = int(start_vars['n_samples'])
        else:
            if 'group' in start_vars:
                dataset = create_dataset(
                    start_vars['dataset'], group_name=start_vars['group'])
            else:
                dataset = create_dataset(start_vars['dataset'])
            start_vars['trait_name'] = start_vars['trait_id']
            if dataset.type == "Publish":
                start_vars['trait_name'] = f"{dataset.group.code}_{start_vars['trait_name']}"
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
        start_vars['vals_hash'] = generate_hash_of_string(
            str(sample_vals_dict))
        if start_vars['dataset'] != "Temp":  # Currently can't get diff for temp traits
            start_vars['vals_diff'] = get_diff_of_vals(sample_vals_dict, str(
                start_vars['trait_id'] + ":" + str(start_vars['dataset'])))

        start_vars['wanted_inputs'] = initial_start_vars['wanted_inputs']

        start_vars_container['start_vars'] = start_vars
    else:
        start_vars_container['start_vars'] = initial_start_vars

    rendered_template = render_template("loading.html", **start_vars_container)

    return rendered_template


@app.route("/run_mapping", methods=('POST',))
@app.route("/run_mapping/<path:hash_of_inputs>")
def mapping_results_page(hash_of_inputs=None):
    if hash_of_inputs:
        initial_start_vars = json.loads(Redis.get(hash_of_inputs))
        initial_start_vars['hash_of_inputs'] = hash_of_inputs
    else:
        initial_start_vars = request.form

        # Get hash of inputs (as JSON) for sharing results
        inputs_json = json.dumps(initial_start_vars, sort_keys=True)
        dhash = hashlib.md5()
        dhash.update(inputs_json.encode())
        hash_of_inputs = dhash.hexdigest()

        # Just store for one hour on initial load; will be stored for longer if user clicks Share
        Redis.set(hash_of_inputs, inputs_json, ex=60*60*24*30)

    temp_uuid = initial_start_vars['temp_uuid']
    wanted = (
        'trait_id',
        'dataset',
        'group',
        'species',
        'samples',
        'vals',
        'sample_vals',
        'vals_hash',
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
        'showHomology',
        'showGenes',
        'viewLegend',
        'haplotypeAnalystCheck',
        'mapmethod_rqtl',
        'mapmodel_rqtl',
        'temp_trait',
        'n_samples',
        'transform',
        'hash_of_inputs',
        'dataid'
    )
    start_vars = {}
    for key, value in list(initial_start_vars.items()):
        if key in wanted:
            start_vars[key] = value

    start_vars['hash_of_inputs'] = hash_of_inputs

    # Store trait sample data in Redis, so additive effect scatterplots can include edited values
    dhash = hashlib.md5()
    dhash.update(start_vars['sample_vals'].encode())
    samples_hash = dhash.hexdigest()
    Redis.set(samples_hash, start_vars['sample_vals'], ex=7*24*60*60)
    start_vars['dataid'] = samples_hash

    version = "v3"
    key = "mapping_results:{}:".format(
        version) + json.dumps(start_vars, sort_keys=True)
    result = None  # Just for testing

    if result:
        result = pickle.loads(result)
    else:
        template_vars = run_mapping.RunMapping(start_vars, temp_uuid)
        if template_vars.no_results:
            raise NoMappingResultsError(
                start_vars["trait_id"], start_vars["dataset"], start_vars["method"])

        if not template_vars.pair_scan:
            template_vars.js_data = json.dumps(template_vars.js_data,
                                               default=json_default_handler,
                                               indent="   ")

        result = template_vars.__dict__

        if result['pair_scan']:
            rendered_template = render_template(
                "pair_scan_results.html", **result)
        else:
            gn1_template_vars = display_mapping_results.DisplayMappingResults(
                result).__dict__

            rendered_template = render_template(
                "mapping_results.html", **gn1_template_vars)

    return rendered_template


@app.route("/cache_mapping_inputs", methods=('POST',))
def cache_mapping_inputs():
    cache_id = request.form.get("inputs_hash")
    inputs_json = Redis.get(cache_id)
    Redis.set(cache_id, inputs_json)

    return "Success"


@app.route("/export_mapping_results", methods=('POST',))
def export_mapping_results():
    file_path = request.form.get("results_path")
    results_csv = open(file_path, "r").read()
    response = Response(results_csv,
                        mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=" + os.path.basename(file_path)})

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
    svg_xml = request.form.get("data", "Invalid data")
    filename = request.form.get("filename", "manhattan_plot_snp")
    response = Response(svg_xml, mimetype="image/svg+xml")
    response.headers["Content-Disposition"] = "attachment; filename=%s" % filename
    return response


@app.route("/export_pdf", methods=('POST',))
def export_pdf():
    import cairosvg
    svg_xml = request.form.get("data", "Invalid data")
    filename = request.form.get("filename", "interval_map_pdf")
    pdf_file = cairosvg.svg2pdf(bytestring=svg_xml)
    response = Response(pdf_file, mimetype="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=%s" % filename
    return response


@app.route("/network_graph", methods=('POST',))
def network_graph_page():
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


def __handle_correlation_error__(exc):
    return render_template(
        "correlation_error_page.html",
        error={
            "error-type": {
                "WrongCorrelationType": "Wrong Correlation Type"
            }[type(exc).__name__],
            "error-message": exc.args[0]
        })


@app.route("/corr_compute", methods=('POST', 'GET'))
def corr_compute_page():
    with Redis.from_url(REDIS_URL, decode_responses=True) as rconn:
        if request.method == "POST":
            request_received = datetime.datetime.utcnow()
            filename = hmac.hmac_creation(f"request_form_{request_received.isoformat()}")
            filepath = f"{TMPDIR}{filename}"
            with open(filepath, "wb") as pfile:
                pickle.dump(request.form, pfile,
                            protocol=pickle.HIGHEST_PROTOCOL)
                job_id = jobs.queue(
                    rconn, {
                        "command": [
                            sys.executable, "-m", "gn2.scripts.corr_compute", filepath,
                            g.user_session.user_id],
                        "request_received_time": request_received.isoformat(),
                        "status": "queued"
                    })
                jobs.run(job_id, REDIS_URL)

            return redirect(url_for("corr_compute_page", job_id=str(job_id)))

        job = jobs.job(
            rconn, UUID(request.args.get("job_id"))).maybe(
                {}, lambda the_job: the_job)

        if jobs.completed_successfully(job):
            output = json.loads(job.get("stdout", "{}"))
            return render_template("correlation_page.html", **output)

        if jobs.completed_erroneously(job):
            try:
                error_output = {
                    "error-type": "ComputeError",
                    "error-message": "There was an error computing the correlations",
                    **json.loads(job.get("stdout") or "{}"),
                    "stderr-output": job.get("stderr", "").split("\n")
                }
                return render_template(
                    "correlation_error_page.html", error=error_output)
            except json.decoder.JSONDecodeError as jde:
                raise Exception(f"STDOUT: {job.get('stdout')}") from jde

        return render_template("loading_corrs.html")


@app.route("/corr_matrix", methods=('POST',))
def corr_matrix_page():
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
    template_vars = corr_scatter_plot.CorrScatterPlot(request.args)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    return render_template("corr_scatterplot.html", **template_vars.__dict__)


@app.route("/snp_browser", methods=('GET',))
def snp_browser_page():
    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
        template_vars = snp_browser.SnpBrowser(cursor, request.args)
        return render_template("snp_browser.html", **template_vars.__dict__)


@app.route("/db_info", methods=('GET',))
def db_info_page():
    if request.args['accession_id'] != "None" and not any(x in request.args['dataset'] for x in ["Publish", "Geno"]):
        return redirect("https://info.genenetwork.org/infofile/source.php?GN_AccesionId=" + request.args['accession_id'])
    else:
        return redirect("https://info.genenetwork.org/species/source.php?SpeciesName=" + request.args['species'] + "&InbredSetName=" + request.args['group'])


@app.route("/snp_browser_table", methods=('GET',))
def snp_browser_table():
    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
        snp_table_data = snp_browser.SnpBrowser(cursor, request.args)
        current_page = server_side.ServerSideTable(
            snp_table_data.rows_count,
            snp_table_data.table_rows,
            snp_table_data.header_data_names,
            request.args,
        ).get_page()

        return flask.jsonify(current_page)


@app.route("/tutorial/WebQTLTour", methods=('GET',))
def tutorial_page():
    # Currently just links to GN1
    return redirect("http://gn1.genenetwork.org/tutorial/WebQTLTour/")


@app.route("/tutorial/security", methods=('GET',))
def security_tutorial_page():
    # ZS: Currently just links to GN1
    return render_template("admin/security_help.html")


@app.route("/submit_bnw", methods=('POST',))
def submit_bnw():
    return render_template("empty_collection.html", **{'tool': 'Correlation Matrix'})

# Take this out or secure it before putting into production


@app.route("/get_temp_data")
def get_temp_data():
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


@app.route("/user/data-sample/diffs/")
def display_diffs_users():
    TMPDIR = current_app.config.get("TMPDIR")
    DIFF_DIR = f"{TMPDIR}/sample-data/diffs"
    files = []
    author = g.user_session.record.get(b'user_name').decode("utf-8")
    if os.path.exists(DIFF_DIR):
        files = os.listdir(DIFF_DIR)
        files = filter(lambda x: not(x.endswith((".approved", ".rejected")))
                       and author in x,
                       files)
    return render_template("display_files_user.html",
                           files=files)


@app.route("/genewiki/<symbol>")
def display_generif_page(symbol):
    """Fetch GeneRIF metadata from GN3 and display it"""
    entries = requests.get(
        urljoin(
            GN3_LOCAL_URL,
            f"/api/metadata/genewiki/{symbol}"
        )
    ).json()
    return render_template(
        "generif.html",
        symbol=symbol,
        entries=entries
    )


@app.route("/datasets/<name>", methods=('GET',))
def get_dataset(name):
    from gn2.wqflask.oauth2.client import oauth2_get
    from gn2.wqflask.oauth2.client import user_logged_in
    from gn2.wqflask.oauth2.request_utils import user_details
    from gn2.wqflask.oauth2.request_utils import process_error

    result = oauth2_get(
        f"auth/resource/authorisation/{name}"
    ).either(
        lambda err: {"roles": []},
        lambda val: val
    )
    metadata = requests.get(
        urljoin(
            GN3_LOCAL_URL,
            f"/api/metadata/datasets/{name}")
    ).json()
    metadata["editable"] = "group:resource:edit-resource" in result["roles"]
    return render_template(
        "dataset.html",
        name=name,
        dataset=metadata
    )


@app.route("/publications/<name>", methods=('GET',))
def get_publication(name):
    metadata = requests.get(
        urljoin(
            GN3_LOCAL_URL,
            f"/api/metadata/publications/{name}")
    ).json()
    return render_template(
        "publication.html",
        metadata=metadata,
    )


@app.route("/phenotypes/<name>", methods=('GET',))
@app.route("/phenotypes/<group>/<name>", methods=('GET',))
def get_phenotype(name, group=None):
    if group:
        name = f"{group}_{name}"
    metadata = requests.get(
        urljoin(
            GN3_LOCAL_URL,
            f"/api/metadata/phenotypes/{name}")
    ).json()
    return render_template(
        "phenotype.html",
        metadata=metadata,
    )


@app.route("/probesets/<name>", methods=('GET',))
@app.route("/probesets/<dataset>/<name>", methods=["GET"])
def get_probeset(name, dataset=None):
    metadata = requests.get(
        urljoin(
            GN3_LOCAL_URL,
            f"/api/metadata/probesets/{name}")
    ).json()
    summary = None
    if gene_id := metadata.get("geneID"):
        gene_id = gene_id.get("id").split("=")[-1]
        result = json.loads(
            requests.get(
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id={gene_id}&retmode=json"
            ).content
        )['result']
        summary = result[gene_id]['summary']
    return render_template(
        "probeset.html",
        name=name,
        dataset=dataset,
        metadata=metadata,
        summary=summary,
    )


@app.route("/genotypes/<name>", methods=('GET',))
@app.route("/genotypes/<dataset>/<name>", methods=('GET',))
def get_genotype(name, dataset=None):
    if dataset:
        name = f"{dataset}/{name}"
    metadata = requests.get(
        urljoin(
            GN3_LOCAL_URL,
            f"/api/metadata/genotypes/{name}")
    ).json()
    return render_template(
        "genotype.html",
        name=name,
        metadata=metadata,
    )


@app.route("/case-attribute/<int:inbredset_id>/edit", methods=["GET", "POST"])
def edit_case_attributes(inbredset_id: int) -> Response:
    """
    Edit the case-attributes for InbredSet group identified by `inbredset_id`.
    """
    if request.method == "POST":
        form = request.form

        def __process_data__(acc, item):
            _new, strain, calabel = tuple(val.strip()
                                          for val in item[0].split(":"))
            old_row = acc.get(strain, {})
            return {
                **acc,
                strain: {
                    **old_row, "case-attributes": {
                        **old_row.get("case-attributes", {}),
                        calabel: item[1]
                    }
                }
            }

        edit_case_attributes_page = redirect(url_for(
            "edit_case_attributes", inbredset_id=inbredset_id))
        token = session_info()["user"]["token"].either(
            lambda err: err, lambda tok: tok["access_token"])

        def flash_success(resp):
            def __succ__(remote_resp):
                flash(f"Success: {remote_resp.json()['message']}", "alert-success")
                return resp
            return __succ__
        return monad_requests.post(
            urljoin(
                current_app.config["GN_SERVER_URL"],
                f"/api/case-attribute/{inbredset_id}/edit"),
            json={
                "edit-data": reduce(__process_data__, form.items(), {})
            },
            headers={
                "Authorization": f"Bearer {token}"}).either(
            with_flash_error(edit_case_attributes_page),
            flash_success(edit_case_attributes_page))

    def __fetch_strains__(inbredset_group):
        return monad_requests.get(urljoin(
            current_app.config["GN_SERVER_URL"],
            f"/api/case-attribute/{inbredset_id}/strains")).then(
                lambda resp: {**inbredset_group, "strains": resp.json()})

    def __fetch_names__(strains):
        return monad_requests.get(urljoin(
            current_app.config["GN_SERVER_URL"],
            f"/api/case-attribute/{inbredset_id}/names")).then(
                lambda resp: {**strains, "case_attribute_names": resp.json()})

    def __fetch_values__(canames):
        return monad_requests.get(urljoin(
            current_app.config["GN_SERVER_URL"],
            f"/api/case-attribute/{inbredset_id}/values")).then(
                lambda resp: {**canames, "case_attribute_values": {
                    value["StrainName"]: value for value in resp.json()}})

    return monad_requests.get(urljoin(
        current_app.config["GN_SERVER_URL"],
        f"/api/case-attribute/{inbredset_id}")).then(
            lambda resp: {"inbredset_group": resp.json()}).then(
                __fetch_strains__).then(__fetch_names__).then(
                    __fetch_values__).either(
                        lambda err: err,  # TODO: Handle error better
                        lambda values: render_template(
                            "edit_case_attributes.html", inbredset_id=inbredset_id, **values))


@app.route("/case-attribute/<int:inbredset_id>/list-diffs", methods=["GET"])
def list_case_attribute_diffs(inbredset_id: int) -> Response:
    """List any diffs awaiting review."""
    return monad_requests.get(urljoin(
        current_app.config["GN_SERVER_URL"],
        f"/api/case-attribute/{inbredset_id}/diff/list")).then(
            lambda resp: resp.json()).either(
                lambda err: render_template(
                    "list_case_attribute_diffs_error.html",
                    inbredset_id=inbredset_id,
                    error=err),
                lambda diffs: render_template(
                    "list_case_attribute_diffs.html",
                    inbredset_id=inbredset_id,
                    diffs=diffs))


@app.route("/case-attribute/<int:inbredset_id>/diff/<int:diff_id>/view", methods=["GET"])
def view_diff(inbredset_id: int, diff_id: int) -> Response:
    """View the pending diff."""
    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    return monad_requests.get(
        urljoin(current_app.config["GN_SERVER_URL"],
                f"/api/case-attribute/{inbredset_id}/diff/{diff_id}/view"),
        headers={"Authorization": f"Bearer {token}"}).then(
            lambda resp: resp.json()).either(
                lambda err: render_template(
                    "view_case_attribute_diff_error.html", error=err.json()),
                lambda diff: render_template(
                    "view_case_attribute_diff.html", diff=diff))


@app.route("/case-attribute/diff/approve-reject", methods=["POST"])
def approve_reject_diff() -> Response:
    """Approve/Reject the diff."""
    try:
        form = request.form
        action = form["action"]
        assert action in ("approve", "reject")
        diff_data = json.loads(form["diff_data"])
        diff_data = {
            **diff_data,
            "created": datetime.datetime.fromisoformat(diff_data["created"])}
        inbredset_id = diff_data["inbredset_id"]
        filename = (
            f"{inbredset_id}:::{diff_data['user_id']}:::"
            f"{diff_data['created'].isoformat()}.json")

        list_diffs_page = url_for("list_case_attribute_diffs",
                                  inbredset_id=inbredset_id)
        token = session_info()["user"]["token"].either(
            lambda err: err, lambda tok: tok["access_token"])

        def __error__(resp):
            error = resp.json()
            flash((f"{resp.status_code} {error['error']}: "
                   f"{error['error_description']}"),
                  "alert-danger")
            return redirect(list_diffs_page)

        def __success__(results):
            flash(results["message"], "alert-success")
            return redirect(list_diffs_page)
        return monad_requests.post(
            urljoin(current_app.config["GN_SERVER_URL"],
                    f"/api/case-attribute/{action}/{filename}"),
            headers={"Authorization": f"Bearer {token}"}).then(
                lambda resp: resp.json()
        ).either(
                __error__, __success__)
    except AssertionError as _ae:
        flash("Invalid action! Expected either 'approve' or 'reject'.",
              "alert-danger")
        return redirect(url_for("view_diff",
                                inbredset_id=inbredset_id,
                                diff_id=form["diff_id"]))
