"""Main routing table for GN2"""
import time
import array
import base64
import csv
import logging
import datetime
import hashlib
import io  # Todo: Use cStringIO?

import json
import os
import pickle as pickle
import random
import sys
import tempfile
import traceback
import math
import uuid
import urllib.parse

from functools import reduce
from collections import defaultdict

from zipfile import ZipFile
from zipfile import ZIP_DEFLATED

from uuid import UUID

from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.parse import parse_qs
import xlsxwriter
import requests
import numpy as np
import flask
from typing import Optional
from gn_libs.privileges import resources
from gn_libs.mysqldb import database_connection
from gn3.computations.gemma import generate_hash_of_string
from flask import current_app
from flask import jsonify
from flask import g
from flask import Response
from flask import request
from flask import make_response
from flask import render_template
from flask import redirect
from flask import send_file
from flask import url_for
from flask import flash

from gn2.wqflask import app
from gn2.wqflask import search_results
from gn2.wqflask import server_side

# Used by YAML in marker_regression
from gn2.base.data_set import create_dataset
from gn2.base.trait import fetch_symbols
from gn2.wqflask.show_trait import show_trait
from gn2.wqflask.show_trait import export_trait_data
from gn2.wqflask.show_trait.show_trait import get_diff_of_vals
from gn2.wqflask.heatmap import heatmap
from gn2.wqflask.external_tools import send_to_bnw, send_to_webgestalt
from gn2.wqflask.external_tools import send_to_geneweaver
from gn2.wqflask.comparison_bar_chart import comparison_bar_chart
from gn2.wqflask.marker_regression import run_mapping
from gn2.wqflask.marker_regression.rqtl_mapping import RQTLError
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
from gn2.utility.tools import GN_GUILE_SERVER_URL
from gn2.utility.tools import GN_SERVER_URL
from gn2.utility.tools import GN3_LOCAL_URL
from gn2.utility.tools import JS_TWITTER_POST_FETCHER_PATH
from gn2.utility.tools import JS_GUIX_PATH
from gn2.utility.helper_functions import get_species_groups
from gn2.utility.helper_functions import clean_xapian_query
from gn2.utility.redis_tools import get_redis_conn
from gn2.utility.responses import send_from_directory

import gn2.utility.hmac as hmac
from gn2.base.webqtlConfig import TMPDIR, GENERATED_IMAGE_DIR
from gn2.base.webqtlConfig import GENE_CUP_URL

import gn2.jobs.jobs as jobs

from gn2.wqflask.decorators import login_required
from gn2.wqflask.oauth2.session import session_info
from gn2.wqflask.oauth2.client import user_logged_in

from gn2.wqflask import requests as monad_requests

from gn2.wqflask.oauth2.checks import require_oauth2
from gn2.wqflask.oauth2.checks import fetch_case_attribute_privs
from gn2.wqflask.oauth2.request_utils import system_privileges


logger = logging.getLogger(__name__)
Redis = get_redis_conn()


@app.errorhandler(Exception)
def handle_generic_exceptions(e):
    import werkzeug
    err_msg = str(e)
    # get the stack trace and send it to the logger
    exc_type, exc_value, exc_traceback = sys.exc_info()
    formatted_lines = (f"{request.url} \n"
                       f"{traceback.format_exc()}")
    _message_templates = {
        werkzeug.exceptions.NotFound: (f"404: Not Found: {request.url}"),
        werkzeug.exceptions.BadRequest: (f"400: Bad Request: {request.url}"),
        werkzeug.exceptions.RequestTimeout: (f"408: Request Timeout: {request.url}")}
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
    try:
        resp.status_code = exc_type.code
    except AttributeError:
        resp.status_code = 500
    resp.set_cookie(err_msg[:32], animation)
    return resp


@app.route("/authentication_needed")
def no_access_page():
    return render_template("new_security/not_authenticated.html")


@app.route("/test-network")
def test_network():
    start = time.time()
    http_url = urljoin(
            current_app.config["GN_SERVER_URL"],
            "version"
        )
    result =  requests.get(http_url)
    duration = time.time() - start
    app.logger.error(f"{http_url}: {duration:.4f}s")
    # Verify that we get the right thing.
    app.logger.error(f"result: {result.json()}")

    start = time.time()
    local_url = "http://localhost:9093/api/version"
    result =  requests.get(local_url)
    duration = time.time() - start
    app.logger.error(f"{local_url}: {duration:.4f}s")
    app.logger.error(f"result: {result.json()}")
    return result.json()


@app.route("/")
def index_page():
    anon_id = session_info()["anon_id"]

    def __render__(colls):
        return render_template("index_page.html",
                               version=current_app.config.get("GN_VERSION"),
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
    return send_from_directory(js_path, name, mimetype="text/javascript")


@app.route("/css/<path:filename>")
def css(filename):
    js_path = JS_GUIX_PATH
    name = filename
    if 'js_alt/' in filename:
        js_path = js_path.replace('genenetwork2/javascript', 'javascript')
        name = name.replace('js_alt/', '')
    return send_from_directory(js_path, name, mimetype="text/css")


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


def is_valid_gnqna_user(session_info, request) -> bool:
    """
    Determine if the request is from a valid GNQNA user — either logged in or a safe anonymous visitor.
    Applies honeypot field logic, blocks headless bots, and validates referrer.
    """
    user_info = session_info.get("user", {})
    if user_info.get("logged_in", False):
        return True
    #  Honeypot trap
    honeypot = None
    if request.is_json:
        data = request.get_json(silent=True) or {}
        honeypot = data.get("gnqna_username", "").strip()
    elif request.form:
        honeypot = request.form.get("gnqna_username", "").strip()
    if not honeypot:
        honeypot = request.args.get("gnqna_username", "").strip()
    if honeypot:
        return False
    #  Reject known headless browser user agents
    user_agent = request.headers.get("User-Agent", "").lower()
    bot_indicators = ["headless", "selenium", "phantomjs"]
    if any(bot in user_agent for bot in bot_indicators):
        return False
    referrer = request.referrer
    if not referrer:
        return False
    parsed = urlparse(referrer)
    hostname = parsed.hostname or ""
    path = parsed.path
    valid_host = (
        (hostname.startswith("localhost") and current_app.config.get('TEST_FEATURE_SWITCH')) or
        hostname == "genenetwork.org" or
        hostname.endswith(".genenetwork.org")
    ) # ???cors origin  handles  this anyways
    query_params = parse_qs(parsed.query)
    if path == "/gnqna":
        has_query = "query" in query_params and any(query_params["query"]) # allow if referrer was gnqna had a  query
        return valid_host and has_query
    elif path == "/":
        return False
    return valid_host

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


@app.route("/gsearch", methods=("GET",))
def gsearchact():
    result = GSearch(request.args).__dict__
    search_type = request.args["type"]
    is_user_logged_in = session_info().get("user", {}).get("logged_in", False)

    ai_search_enabled = current_app.config.get("AI_SEARCH_ENABLED")
    search_count = result.get("trait_count", 0)
    is_valid_user = is_valid_gnqna_user(session_info(), request)
    do_ai_search = ai_search_enabled and is_valid_user and (search_count >= 30)

    if search_type == "gene":
        return render_template("gsearch_gene.html", **result,
                               ai_search_enabled=ai_search_enabled,
                               do_ai_search=do_ai_search,
                               llm_error_msg = ("Please login to View AI generated summary."
                                                    if not
                                                   is_valid_user else  ""),
                               result=result)
    elif search_type == "phenotype":
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
def gnqna():
    """Main endpoint to call gn3 gnqna Api endpoint"""
    def _error_(resp):
        return render_template(
            "gnqa_errors.html", **{"status_code": resp.status_code, **resp.json()}
        )

    def _success_(resp):
        return render_template("gnqa_answer.html", **resp.json())


    if request.method == "GET" and not request.args.get("query"):
        return render_template("gnqa.html")
    if  not is_valid_gnqna_user(session_info(), request):
        return render_template(
            "gnqa_errors.html",
            status_code=500,
            error="Login/Verification required to make this request",
            query= ""
        )
    content_type = request.headers.get("Content-Type")
    from pymonad.either import Left, Right
    token_monad = session_info()["user"]["token"]
    if token_monad.is_left():
         # example for this is : Left(INVALID-TOKEN)
        token = token_monad.value
        # add this extra metadata to allow verified anonymous  make request
        anonymous_headers = {
            "Anonymous-Id": str(uuid.uuid4()),
            "Anonymous-Status" : "verified",
            "Anony-Metadata" : json.dumps({"ip_address" : request.remote_addr})
        }
    else:
        token = token_monad.value["access_token"]
        anonymous_headers = {}
    headers = {"Authorization": f"Bearer {token}", **anonymous_headers}
    if request.method == "GET":
        query = request.args.get("query")
        query_type = request.args.get("type")
        if query_type == "xapian":
            query = clean_xapian_query(query)
            # todo; check if is empty
        safe_query = urllib.parse.urlencode({"query": query})

        search_result = requests.get(
            urljoin(GN3_LOCAL_URL, f"/api/llm/search?{safe_query}"),
            headers=headers,
        )
        search_result.raise_for_status()
        search_result = search_result.json()
        if content_type == "application/json":
            ai_result = {
                "search_term": query,
                "search_result": search_result["answer"],
                "search_url": f"/gnqna?{safe_query}",
            }
            return jsonify(ai_result)
        return render_template("gnqa.html", **search_result)

    if request.method == "POST":
        safe_query = urllib.parse.urlencode(
            {"query": request.form.get("querygnqa")})
        return monad_requests.get(
            urljoin(GN3_LOCAL_URL, f"/api/llm/search?{safe_query}"),
            headers=headers,
        ).either(_error_, _success_)


@app.route("/editor/edit", methods=["GET"])
@require_oauth2
def edit_gn_doc_file():
    """Edit the raw Markdown file."""
    def __back_to__(apath: str) -> Response:
        """Compute where to go back to."""
        match apath:
            case "general/glossary/glossary.md":
                _back = "glossary_blueprint.glossary"
            case "general/references/references.md":
                _back = "references_blueprint.references"
            case "general/environments/environments.md":
                _back = "environments_blueprint.environments"
            case "general/links/links.md":
                _back = "links_blueprint.links"
            case "general/policies/policies.md":
                _back = "policies_blueprint.policies"
            case "general/help/facilities.md":
                _back = "facilities_blueprint.facilities"
            case "general/news/news.md":
                _back = "news_blueprint.news"
            case "general/search/xapian_syntax.md":
                _back = "xapian_syntax_blueprint.xapian"
            case _:
                flash(("We couldn't figure out how to redirect you back to what "
                       "you were doing, so we brought you back to the home page."),
                      "alert alert-warning")
                return redirect("/")

        return redirect(url_for(_back))

    _path = request.args.get("file-path", "")
    if not "system:documentation:edit" in system_privileges():
        flash(
            "You lack the appropriate privileges to edit system documentation.",
            "alert alert-danger")
        return __back_to__(_path)

    file_path = urllib.parse.urlencode({"file_path": _path})
    response = requests.get(urljoin(GN_GUILE_SERVER_URL, f"/edit?{file_path}"))
    response.raise_for_status()
    return render_template("gn_editor.html", **response.json())


@app.route("/editor/settings", methods=["GET"])
@require_oauth2
def configure_gn_editor():
    return render_template("gn_editor_settings.html")


@app.route("/editor/commit", methods=["GET", "POST"])
@require_oauth2
def commit_gn_doc():
    # TODO add env variable for gn-guile web server
    if request.method == "GET":
        return render_template("gn_editor_commit.html")
    results = requests.post(urljoin(GN_GUILE_SERVER_URL, "commit"), json={
        "content":  request.form.get("content"),
        "filename": request.form.get("file_path"),
        "username": session_info()["user"]["name"],
        "email": session_info()["user"]["email"],
        "commit_message": request.form.get("msg"),
        "prev_commit": request.form.get("hash")})
    data = results.json()
    data["filename"] = request.form.get("file_path")
    return render_template("gn_editor_results_page.html", **data)


@app.route("/gnqna/records", methods=["GET"])
@require_oauth2
def get_gnqa_records():
    """Call the Api endpoint for fetching all gnqa records"""
    def _error_(resp):
        return render_template("gnqa_errors.html",
                               **{"status_code": resp.status_code,
                                  **resp.json()})

    def get_chunk(items, page, size):
        start_idx = ((page-1) * size)
        end_idx = (page*size)
        return iter(items[start_idx:end_idx])

    def _success_(resp):
        response = resp.json()
        page = int(request.args.get("page", 1))
        pagination_size = int(request.args.get("max_size", 10))
        prev_n_queries = get_chunk(response, page, pagination_size)
        return render_template("gnqa_search_history.html",
                               prev_queries=prev_n_queries,
                               num_pages=math.ceil(
                                   len(response)/pagination_size),
                               current=page)
    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    response_url = "/api/llm/search/records"
    return (monad_requests.get(urljoin(GN3_LOCAL_URL, response_url),
                               headers={
            "Authorization": f"Bearer {token}"
            }
    ).then(lambda resp: resp).either(
        _error_, _success_))


@app.route("/gnqna/record", methods=["GET"])
@require_oauth2
def get_gnqa_record_by_task_id():
    """Get specific record using task"""
    def _error_(resp):
        return render_template("gnqa_errors.html",
                               **{"status_code": resp.status_code,
                                  **resp.json()})

    def _success_(resp):
        response = resp.json()
        return render_template("gnqa_answer.html", **response)
    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    response_url = f"api/llm/search/record/{request.args.get('search_task_id')}"
    return (monad_requests.get(urljoin(GN3_LOCAL_URL, response_url),
                               headers={
            "Authorization": f"Bearer {token}"
            }).then(lambda resp: resp).either(
            _error_, _success_))


@app.route("/gnqna/records", methods=["DELETE"])
@require_oauth2
def delete_gnqa_records():
    """Call the Api endpoint for fetching all gnqa records"""
    def _error_(resp):
        return render_template("gnqa_errors.html",
                               **{"status_code": resp.status_code,
                                  **resp.json()})

    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    return (monad_requests.delete(urljoin(GN3_LOCAL_URL,
                                          "/api/llm/search/records"),
                                  json=dict(request.form),
                                  headers={
            "Authorization": f"Bearer {token}"})
            .then(lambda resp: resp).either(
                _error_, lambda x: x.json()))


@app.route("/gnqna/record", methods=["DELETE"])
@require_oauth2
def delete_gnqa_record_by_task_id():
    """Get specific record using task"""
    def _error_(resp):
        return render_template("gnqa_errors.html",
                               **{"status_code": resp.status_code,
                                  **resp.json()})

    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    response_url = f"api/llm/search/record/{request.args.get('search_task_id')}"
    return (monad_requests.get(urljoin(GN3_LOCAL_URL, response_url),
                               headers={
            "Authorization": f"Bearer {token}"}).then(lambda resp: resp)
            .either(
            _error_, lambda x: x.json()))


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
        if (g.user_session.record['user_email_address'] == "zachary.a.sloan@gmail.com"
                or g.user_session.record['user_email_address'] == "labwilliams@gmail.com"):
            doc = Docs(request.args['entry'], request.args)
            return render_template("docedit.html", **doc.__dict__)
        else:
            return "You shouldn't be here!"
    except Exception:
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
    if request.form.get("submitted_by") == "javascript":
        return render_template("ctl_setup.html", **request.form)
    return {
        "submit_url": url_for("ctl_setup"),
        "submit_method": "POST",
        "data": {
            "trait_list": request.form["trait_list"],
            "submitted_by": "javascript"
        }
    }


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

    # Use a temporary file for streaming with xlsxwriter's constant_memory mode
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_path = temp_file.name
    temp_file.close()

    try:
        # Write Excel file with constant_memory mode for better performance
        workbook = xlsxwriter.Workbook(temp_path, {'constant_memory': True})
        worksheet = workbook.add_worksheet()
        for i, row in enumerate(sample_data):
            for j, column in enumerate(row):
                worksheet.write(i, j, row[j])
        workbook.close()

        # Stream the file in chunks
        def generate():
            with open(temp_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk

        response = Response(generate(),
                          mimetype='application/vnd.ms-excel',
                          headers={"Content-Disposition": "attachment;filename=" + trait_name + ".xlsx"})

        # Clean up the temp file after response is sent
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(temp_path)
            except OSError:
                pass

        return response
    except Exception:
        # Clean up on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


@app.route('/export_trait_csv', methods=('POST',))
def export_trait_csv():
    """CSV file consisting of the sample data from the trait data and analysis page"""
    trait_name, sample_data = export_trait_data.export_sample_table(
        request.form)

    def generate():
        buff = io.StringIO()
        writer = csv.writer(buff)
        for row in sample_data:
            writer.writerow(row)
            buff.seek(0)
            data = buff.read()
            buff.seek(0)
            buff.truncate(0)
            if data:
                yield data

    return Response(generate(),
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=" + trait_name + ".csv"})


@app.route('/export_traits_csv', methods=('POST',))
def export_traits_csv():
    """CSV file consisting of the traits from the search result page"""
    file_list = export_traits(request.form, request.form['export_type'])

    if len(file_list) > 1:
        now = datetime.datetime.now()
        time_str = now.strftime('%H:%M_%d%B%Y')
        filename = "export_{}".format(time_str)

        def generate_zip():
            memory_file = io.BytesIO()
            with ZipFile(memory_file, mode='w', compression=ZIP_DEFLATED) as zf:
                for the_file in file_list:
                    zf.writestr(the_file[0], the_file[1])
            memory_file.seek(0)
            while True:
                chunk = memory_file.read(8192)
                if not chunk:
                    break
                yield chunk

        return Response(generate_zip(),
                        mimetype='application/zip',
                        headers={"Content-Disposition": f"attachment;filename={filename}.zip"})
    else:
        def generate_csv():
            data = file_list[0][1]
            chunk_size = 8192
            for i in range(0, len(data), chunk_size):
                yield data[i:i+chunk_size]

        return Response(generate_csv(),
                        mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=" + file_list[0][0]})


@app.route('/export_collection', methods=('POST',))
def export_collection_csv():
    """CSV file consisting of trait list so collections can be exported/shared"""
    out_file = export_traits(request.form, "collection")

    def generate():
        data = out_file[1]
        chunk_size = 8192
        for i in range(0, len(data), chunk_size):
            yield data[i:i+chunk_size]

    return Response(generate(),
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

    def generate():
        buff = io.StringIO()
        writer = csv.writer(buff)
        # Write header rows
        writer.writerows(the_rows)
        buff.seek(0)
        yield buff.read()
        buff.seek(0)
        buff.truncate(0)

        # Stream permutation data in chunks
        chunk_size = 1000
        for i in range(0, len(perm_info['perm_data']), chunk_size):
            chunk = perm_info['perm_data'][i:i+chunk_size]
            for item in chunk:
                writer.writerow([item])
            buff.seek(0)
            data = buff.read()
            buff.seek(0)
            buff.truncate(0)
            if data:
                yield data

    return Response(generate(),
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=" + file_name + ".csv"})


@app.route("/show_temp_trait", methods=('POST',))
def show_temp_trait_page():
    form_data = request.form.to_dict()

    # Handle file upload — takes priority over pasted values
    trait_file = request.files.get('trait_file')
    if trait_file and trait_file.filename:
        filename = trait_file.filename.lower()
        if filename.endswith('.xlsx'):
            file_bytes = trait_file.read()
            parsed = _parse_xlsx_file(file_bytes, form_data.get('group', ''))
        else:
            file_content = trait_file.read().decode('utf-8', errors='replace')
            parsed = _parse_trait_file(file_content, form_data.get('group', ''))
        form_data['trait_paste'] = parsed['trait_paste']
        if parsed.get('trait_se'):
            form_data['trait_se'] = parsed['trait_se']

    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
        user_id = ((g.user_session.record.get(b"user_id") or b"").decode("utf-8")
                   or g.user_session.record.get("user_id") or "")
        template_vars = show_trait.ShowTrait(cursor,
                                             user_id=user_id,
                                             kw=form_data)
        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")
        return redirect(url_for("show_trait_page", dataset=template_vars.dataset.name, trait_id=template_vars.trait_id))


def _parse_trait_file(file_content, group_name):
    """Parse an uploaded trait data file.

    Supports three formats:
      1. Values only — one value per line (or space/tab-separated on one line)
      2. Two columns — sample_name <delimiter> value
      3. Three columns — sample_name <delimiter> value <delimiter> SE

    When sample names are present, values are reordered to match the group's
    samplelist, with 'x' for any samples not in the file.
    """
    result = {'trait_paste': '', 'trait_se': '', 'has_sample_names': False}

    lines = [l.strip() for l in file_content.splitlines() if l.strip()]
    if not lines:
        return result

    # Detect delimiter: tab first, then comma, then whitespace
    first_line = lines[0]
    if '\t' in first_line:
        delimiter = '\t'
    elif ',' in first_line:
        delimiter = ','
    else:
        delimiter = None  # split() splits on any whitespace

    def split_line(line):
        if delimiter:
            return [f.strip() for f in line.split(delimiter)]
        return line.split()

    cols = split_line(lines[0])

    # Detect if there's a header row: second field (value column) is
    # not numeric and not 'x'
    has_header = False
    if len(cols) >= 2:
        first_val = cols[1]
        try:
            float(first_val)
        except ValueError:
            if first_val.lower() != 'x':
                has_header = True
    elif len(cols) == 1:
        try:
            float(cols[0])
        except ValueError:
            if cols[0].lower() != 'x':
                has_header = True

    data_lines = lines[1:] if has_header else lines
    if not data_lines:
        return result

    # Determine column count from the first data line
    first_data_cols = split_line(data_lines[0])
    num_cols = len(first_data_cols)

    # Check if this is a named-sample file (2+ columns where the first
    # column contains non-numeric sample/strain names)
    has_sample_names = False
    if num_cols >= 2:
        first_field = first_data_cols[0]
        try:
            float(first_field)
        except ValueError:
            if first_field.lower() != 'x':
                has_sample_names = True

    if has_sample_names:
        result['has_sample_names'] = True

        # Build a dict of sample_name -> (value, se)
        sample_data = {}
        for line in data_lines:
            parts = split_line(line)
            if len(parts) < 2:
                continue
            sample_name = parts[0]
            value = parts[1]
            se = parts[2] if len(parts) >= 3 else None
            sample_data[sample_name] = (value, se)

        # Reuse existing code: create a Temp dataset to get the full
        # sample ordering (parents + F1 + samplelist), which matches
        # how make_sample_lists builds primary_sample_names.
        try:
            dataset = create_dataset(
                "Temp", dataset_type="Temp", group_name=group_name)
            samplelist = dataset.group.all_samples_ordered()
        except Exception:
            samplelist = None

        if samplelist:
            values = []
            ses = []
            has_se = any(v[1] is not None for v in sample_data.values())
            for sample in samplelist:
                if sample in sample_data:
                    values.append(sample_data[sample][0])
                    if has_se:
                        ses.append(sample_data[sample][1] or 'x')
                else:
                    values.append('x')
                    if has_se:
                        ses.append('x')
            result['trait_paste'] = ' '.join(values)
            if has_se:
                result['trait_se'] = ' '.join(ses)
        else:
            # Fallback: no samplelist found, use values in file order
            values = [sample_data[s][0] for s in sample_data]
            result['trait_paste'] = ' '.join(values)
            has_se = any(v[1] is not None for v in sample_data.values())
            if has_se:
                ses = [sample_data[s][1] or 'x' for s in sample_data]
                result['trait_se'] = ' '.join(ses)
    else:
        # Values-only format — collect all values
        values = []
        for line in data_lines:
            parts = split_line(line)
            values.extend(parts)
        result['trait_paste'] = ' '.join(values)

    return result


def _parse_xlsx_file(file_bytes, group_name):
    """Parse an uploaded .xlsx file using pandas.

    Reads the first sheet, converts all cells to strings, and delegates
    to _parse_trait_file for the actual parsing logic.
    """
    import pandas as pd

    result = {'trait_paste': '', 'trait_se': '', 'has_sample_names': False}

    try:
        df = pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name=0,
            header=None,
            dtype=str,
            engine='openpyxl',
        )
    except Exception:
        return result

    if df.empty:
        return result

    # Convert the DataFrame to tab-delimited text that _parse_trait_file
    # understands, then delegate to it.
    df = df.fillna('')
    text_lines = []
    for _, row in df.iterrows():
        text_lines.append('\t'.join(str(v) for v in row))
    file_as_text = '\n'.join(text_lines)
    return _parse_trait_file(file_as_text, group_name)


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
            if template_vars.dataset.group.name == "DO":
                # this is for debugging purposes;
                # TODO Update the mapping methid in IbredSet Database
                template_vars.dataset.group.mapping_names.append("R/qtl")
            is_user_logged_in = session_info().get("user", {}).get("logged_in", False)
            return render_template(
                "show_trait.html",
                is_user_logged_in=is_user_logged_in,
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

@app.route("/save_trait", methods=('POST',))
def save_trait():
    Redis.set(request.form['trait_name'], request.form['trait_vals'], ex=60 * 60 * 24 * 365)
    return jsonify(request.form)

@app.route("/heatmap", methods=('POST','GET'))
def heatmap_page():
    if request.method == "POST":
        inputs_json = json.dumps(request.form, sort_keys=True)
        dhash = hashlib.md5()
        dhash.update(inputs_json.encode())
        hash_of_inputs = dhash.hexdigest()

        Redis.set(hash_of_inputs, inputs_json, ex=60*60)

        redirect_url = url_for('heatmap_page', hash_of_inputs=hash_of_inputs)
        return jsonify(redirect_url=redirect_url)
    else:
        start_vars = json.loads(Redis.get(request.args['hash_of_inputs']))
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
                        cursor, start_vars, temp_uuid)
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


@app.route("/genecup", methods=('POST',))
def genecup_page():
    start_vars = request.form

    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]

    if traits[0] != "":
        symbol_string = fetch_symbols(traits)
        return redirect(GENE_CUP_URL % symbol_string)
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
    run_id = request.args.get("id")  # get the id for this
    streaming_enabled = False
    if (run_id):
        streaming_enabled = True
    n_samples = 0  # ZS: So it can be displayed on loading page
    if 'wanted_inputs' in initial_start_vars:
        wanted = initial_start_vars['wanted_inputs'].split(",")
        start_vars = {}
        for key, value in list(initial_start_vars.items()):
            if key in wanted:
                start_vars[key] = value

        if 'group' in start_vars:
            dataset = create_dataset(
                start_vars['dataset'], group_name=start_vars['group'])
        else:
            dataset = create_dataset(start_vars['dataset'])
        start_vars['trait_name'] = start_vars['trait_id']
        samples = dataset.group.samplelist

        sample_vals_dict = json.loads(start_vars['sample_vals'])
        sample_vals_dict = {k: sample_vals_dict[k] for k in samples if k in sample_vals_dict}

        if 'n_samples' in start_vars:
            n_samples = int(start_vars['n_samples'])
        else:
            if dataset.type == "Publish":
                start_vars['trait_name'] = f"{dataset.group.code}_{start_vars['trait_name']}"
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
                start_vars['trait_id'] + ":" + str(start_vars['dataset'])), samples)

        start_vars['wanted_inputs'] = initial_start_vars['wanted_inputs']

        start_vars_container['start_vars'] = start_vars
    else:
        start_vars_container['start_vars'] = initial_start_vars
    start_vars_container["streaming_enabled"] = streaming_enabled
    start_vars_container["run_id"] = run_id
    rendered_template = render_template("loading.html", **start_vars_container)
    return rendered_template


@app.route("/run_mapping", methods=['POST'], endpoint='run_mapping_post')  # POST-only
@app.route("/run_mapping/<path:hash_of_inputs>", methods=['GET'], endpoint='run_mapping_get')
def mapping_results_page(hash_of_inputs=None):
    start_time = time.time()
    RUN_ID = request.args.get("id")  # require to stream output
    if not RUN_ID:
        RUN_ID = request.form.get("run_id")
    if hash_of_inputs:
        input_results  =  Redis.get(hash_of_inputs) # can be none
    else:
        input_results = None
    if input_results :
        initial_start_vars = json.loads(input_results)
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
    temp_uuid = initial_start_vars.get('temp_uuid')
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
        'dataid',
        'cross_type'
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
    Redis.set(samples_hash, start_vars['sample_vals'])
    start_vars['dataid'] = samples_hash

    version = "v3"
    key = "mapping_results:{}:".format(
        version) + str(hash_of_inputs)
    try:
        cached_mapping_results  = Redis.get(key)
        if cached_mapping_results:
            template_vars = pickle.loads(cached_mapping_results)
        else:
            template_vars = run_mapping.RunMapping(start_vars,
                                           temp_uuid, run_id=RUN_ID)
            Redis.set(key, pickle.dumps(template_vars), ex=7*24*60*60)
    except RQTLError as error:
        return render_template("rqtl_error.html",
                               error=error.message,
                               status_code=error.status_code,
                               log=error.log)
    if template_vars.no_results:
        raise NoMappingResultsError(
            start_vars["trait_id"], start_vars["dataset"], start_vars["method"])

    if not template_vars.pair_scan:
        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")

    result = template_vars.__dict__

    total_time = time.time() - start_time
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        redirect_url = url_for(
            'run_mapping_get',
            hash_of_inputs=hash_of_inputs,
            mapping_run_time=total_time
        )
        return jsonify(redirect_url=redirect_url)
    else:
        total_time +=float(request.args.get("mapping_run_time", 0.0))
        if result['pair_scan']:
            return render_template(
                "pair_scan_results.html",
                mapping_run_time=total_time,
                **result)
        else:
            gn1_template_vars = display_mapping_results.DisplayMappingResults(result).__dict__
            return render_template(
                "mapping_results.html",
                mapping_run_time=total_time,
                **gn1_template_vars)


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


@app.route("/network_graph", methods=('POST','GET'))
def network_graph_page():
    if request.method == "POST":
        inputs_json = json.dumps(request.form, sort_keys=True)
        dhash = hashlib.md5()
        dhash.update(inputs_json.encode())
        hash_of_inputs = dhash.hexdigest()

        Redis.set(hash_of_inputs, inputs_json, ex=60*60)

        redirect_url = url_for('network_graph_page', hash_of_inputs=hash_of_inputs)
        return jsonify(redirect_url=redirect_url)
    else:
        start_vars = json.loads(Redis.get(request.args['hash_of_inputs']))
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
            start_time = time.time()
            request_received = datetime.datetime.utcnow()
            filename = hmac.hmac_creation(
                f"request_form_{request_received.isoformat()}")
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
            Redis.set(f"{job_id}-running-time", "%.5f" % time.time())

            return {
                "status": "success",
                "message": "Successfully queued the job.",
                "job-id": str(job_id),
                "redirect_url": url_for("corr_compute_page", job_id=str(job_id))
            }

        job = jobs.job(
            rconn, UUID(request.args.get("job_id"))).maybe(
                {}, lambda the_job: the_job)

        if jobs.completed_successfully(job):
            total_time = None
            output = json.loads(job.get("stdout", "{}"))
            job_id = request.args.get("job_id")
            curr_time = Redis.get(f"{job_id}-running-time")
            if curr_time:
                total_time = "%.5fs" % (time.time() - float(curr_time.decode()))
                Redis.delete(f"{job_id}-running-time")
            return render_template(
                "correlation_page.html",
                correlation_run_time=total_time,
                **output
            )

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


@app.route("/corr_matrix", methods=('POST','GET'))
def corr_matrix_page():
    if request.method == "POST":
        inputs_json = json.dumps(request.form, sort_keys=True)
        dhash = hashlib.md5()
        dhash.update(inputs_json.encode())
        hash_of_inputs = dhash.hexdigest()

        Redis.set(hash_of_inputs, inputs_json, ex=60*60)

        redirect_url = url_for('corr_matrix_page', hash_of_inputs=hash_of_inputs)
        return jsonify(redirect_url=redirect_url)
    else:
        start_vars = json.loads(Redis.get(request.args['hash_of_inputs']))
        traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
        if len(traits) > 1:
            template_vars = show_corr_matrix.CorrelationMatrix(start_vars)
            template_vars.js_data = json.dumps(template_vars.js_data,
                                            default=json_default_handler,
                                            indent="   ")

            redirect_url = url_for('corr_matrix_page')
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

@app.route("/global_search_syntax")
def global_search_syntax():
    return render_template("global_search_syntax.html")

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


@app.route("/genewiki/<string:symbol>")
def display_genewiki_page(symbol: str):
    """Display RIF metadata from NCBI"""
    wiki, rif = [], []
    try:
        wiki = requests.get(
            urljoin(GN3_LOCAL_URL, f"/api/metadata/wiki/{symbol}"))
        if wiki.status_code != 404:
            wiki.raise_for_status()
        wiki = wiki.json()
    except requests.exceptions.HTTPError as excp:
        wiki = {}
    except requests.RequestException as excp:
        # Don't flash a warning message for an empty result
        if wiki.status_code not in (404,):
            flash(excp, "alert-warning")
    try:
        rif = requests.get(
            urljoin(GN3_LOCAL_URL, f"/api/metadata/rif/{symbol}"))
        rif.raise_for_status()
        rif = rif.json()
    except requests.RequestException as excp:
        # Don't flash a warning message for an empty result
        if rif.status_code not in (404,):
            flash(excp, "alert-warning")
    except requests.exceptions.HTTPError as excp:
        rif = {}
    sess_info = session_info()
    is_logged_in = sess_info.get("user", {}).get("logged_in", False)
    return render_template("wiki/genewiki.html",
                           symbol=symbol, wiki=wiki, rif=rif, is_logged_in=is_logged_in)


@app.route("/genewiki/<int:comment_id>/history")
def display_wiki_history(comment_id: str):
    entries = []
    try:
        entries = requests.get(
            urljoin(GN3_LOCAL_URL, f"/api/metadata/wiki/{comment_id}/history")
        )
        entries.raise_for_status()
        entries = entries.json()
    except requests.RequestException as excp:
        flash(excp, "alert-warning")
    return render_template("wiki/history.html", entries=entries)


@app.route("/datasets/<name>", methods=('GET',))
def get_dataset(name):
    from gn2.wqflask.oauth2.client import oauth2_get

    # We need to use the "id" as the identifier
    metadata = requests.get(
        urljoin(
            GN3_LOCAL_URL,
            f"/api/metadata/datasets/{name}")
    ).json()
    ## TODO: Fetch at least one trait belonging to this dataset, if the
    ## condition(s) below holds.
    result = oauth2_get(
        ## TODO: @bonz: I'm not sure what you were attempting here: we do not
        ## have an endpoint of the form
        ## `auth/resource/authorisation/<some-string>` which tells me that this
        ## code has not been run (at least with valid auth).
        ##
        ## Closest I can think of what you were attempting is:
        ## curl -H "Content-Type: application/json" \
        ##      -H "Authorization: Bearer <token>" \
        ##      -XPOST "http://localhost:8081/auth/data/authorisation" \
        ##      -d '{"traits": ["<dataset-name>::<a-trait>"]}'
        ##
        ## In that case, you need at least one trait from the dataset.
        ## Please verify that's what you wanted.
        f"auth/resource/authorisation/{metadata.get('label')}"
    ).then(
        lambda dataset_auths: {
            "dataset_privileges": dataset_auths[0]["privileges"]
        }
    ).then(
        ## If notes above hold, we also need to check for system-level
        ## privileges.
        lambda dset_privs: oauth2_get("auth/system/roles").then(
            lambda sys_roles: {
                **dset_privs,
                "system_privileges": tuple(
                    privilege["privilege_id"]
                    for role in sys_roles
                    for privilege in role["privileges"])
            })
    ).either(
        lambda err: {"privileges": []},
        lambda val: {
            # then we can combine all privileges
            **val,
            "privileges": val["dataset_privileges"] + val["system_privileges"]
        }
    )
    if metadata:
        metadata["editable"] = resources.can_edit(result["privileges"])
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
@login_required()
def edit_case_attributes(inbredset_id: int) -> Response:
    """
    Edit the case-attributes for InbredSet group identified by `inbredset_id`.
    """
    if request.method == "POST":
        user_name = session_info()["user"]["name"]
        payload = {
            "inbredset_id": inbredset_id,
            # KLUDGE: FIXME: It's unclear how to get this from gn3 for
            # now; or for the matter fetch this from here.
            "user": user_name,
        }
        form_filled = False

        original, current = defaultdict(dict), defaultdict(dict)
        for key, new_value in request.form.items():
            # KLUDGE: We use ASCII 30, Record Separator; \x1f since it's not
            # visible in normal text and is good for machine only
            # inter-change
            strain, case_attr, orig_value = key.split('\x1f')
            if orig_value != new_value:
                form_filled = True
                mods = payload.setdefault("Modifications", {})
                original = mods.setdefault("Original", {}).setdefault(strain, {})
                current = mods.setdefault("Current", {}).setdefault(strain, {})
                original[case_attr] = orig_value
                current[case_attr] = new_value
        edit_case_attributes_page = redirect(url_for(
            "edit_case_attributes", inbredset_id=inbredset_id))
        list_case_attributes_page = redirect(url_for(
            "list_case_attribute_diffs", inbredset_id=inbredset_id,
            change_type="review"))
        token = session_info()["user"]["token"].either(
            lambda err: err, lambda tok: tok["access_token"])

        if not form_filled:
            flash("Please make edits to the form before submitting.", "alert-warning")
            return edit_case_attributes_page

        def flash_success(resp):
            def __succ__(remote_resp):
                # KLUDGE: Consider emailing people who have edit
                # access, in addition to the user for a better UX.
                flash(
                    ("Your changes are submitted for review. "
                     f"Thank you, {user_name}! 📝"),
                    "alert-success")
                return redirect(url_for("list_case_attribute_diffs",
                                        inbredset_id=inbredset_id,
                                        change_type="review"))
            return __succ__
        return monad_requests.post(
            urljoin(
                current_app.config["GN_SERVER_URL"],
                f"case-attribute/{inbredset_id}/edit"),
            json={
                "edit-data": payload,
                "user-id": g.user_session.user_id,
            },
            headers={
                "Authorization": f"Bearer {token}"}).either(
            with_flash_error(edit_case_attributes_page),
            flash_success(list_case_attributes_page))

    def __remove_none_vals__(a_dict):
        return dict([(k,v) if v else (k,"") for k,v in a_dict.items()])

    def __fetch_strains__(inbredset_group):
        return monad_requests.get(urljoin(
            current_app.config["GN_SERVER_URL"],
            f"case-attribute/{inbredset_id}/strains")).then(
                lambda resp: {**inbredset_group, "strains": [__remove_none_vals__(d) for d in resp.json()]})

    def __fetch_names__(strains):
        return monad_requests.get(urljoin(
            current_app.config["GN_SERVER_URL"],
            f"case-attribute/{inbredset_id}/names")).then(
                lambda resp: {**strains, "case_attribute_names": resp.json()})

    def __fetch_values__(canames):
        return monad_requests.get(urljoin(
            current_app.config["GN_SERVER_URL"],
            f"case-attribute/{inbredset_id}/values")).then(
                lambda resp: {**canames, "case_attribute_values": {
                    value["StrainName"]: __remove_none_vals__(value) for value in resp.json()}})

    def __view_error__(err):
        current_app.logger.error("%s", err)
        return "We experienced an error"

    return monad_requests.get(urljoin(
        current_app.config["GN_SERVER_URL"],
        f"case-attribute/{inbredset_id}")).then(
            lambda resp: {"inbredset_group": resp.json()}).then(
                __fetch_strains__).then(__fetch_names__).then(
                    __fetch_values__).either(
                        __view_error__,
                        lambda values: render_template(
                            "edit_case_attributes.html", inbredset_id=inbredset_id, **values))


@app.route("/case-attribute/<int:inbredset_id>/diffs/<string:change_type>", methods=["GET"])
def list_case_attribute_diffs(inbredset_id: int, change_type: str) -> Response:
    """List any diffs awaiting review."""
    privs = fetch_case_attribute_privs(
        token=session_info()["user"]["token"].either(
            lambda err: err, lambda tok: tok["access_token"]),
        sql_uri=get_setting("SQL_URI"),
        inbredset_id=inbredset_id
    )
    return monad_requests.get(urljoin(
        current_app.config["GN_SERVER_URL"],
        f"case-attribute/{inbredset_id}/diffs/{change_type}/list")).then(
            lambda resp: resp.json()).either(
                lambda err: render_template(
                    "list_case_attribute_diffs_error.html",
                    inbredset_id=inbredset_id,
                    error=err),
                lambda diffs: render_template(
                    "list_case_attribute_diffs.html",
                    inbredset_id=inbredset_id,
                    change_type=change_type,
                    privs=privs,
                    count=diffs.get("count", {}),
                    diffs=diffs.get("data", {})))


@app.route("/case-attribute/diff/approve-reject", methods=["POST"])
def approve_reject_diff() -> Response:
    """Approve/Reject the diff."""
    form = request.form
    action = form.get("action")
    inbredset_id = form.get("inbredset_id")
    _id = form.get("diff_id")
    list_case_attributes_page = url_for(
        "list_case_attribute_diffs", inbredset_id=inbredset_id,
        change_type="review")
    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"])
    username = session_info()["user"]["name"]
    def __error__(resp):
        error = resp.json()
        # KLUDGE: Consider emailing people who have edit
        # access, in addition to the user for a better UX.
        flash(f"Hey {username}, something went wrong.",
              "alert-danger")
        return redirect(list_case_attributes_page)

    def __success__(results):
        return redirect(list_case_attributes_page)

    return monad_requests.post(
                urljoin(current_app.config["GN_SERVER_URL"],
                        f"case-attribute/{inbredset_id}/{action}/{_id}"),
                headers={"Authorization": f"Bearer {token}"}).then(
                    lambda resp: resp.json()
                ).either(
                    __error__, __success__)


@app.route("/genewiki/edit", methods=["GET", "POST"], defaults={'comment_id': None})
@app.route("/genewiki/<int:comment_id>/edit", methods=["GET", "POST"])
def edit_wiki(comment_id: Optional[int]):
    """fetch generif metadata from gn3 and display it"""
    if request.method == "GET":
        last_wiki_content = {}
        if comment_id:
            last_wiki_resp = requests.get(
                urljoin(GN3_LOCAL_URL, f"/api/metadata/wiki/{comment_id}")
            )
            last_wiki_resp.raise_for_status()
            last_wiki_content = last_wiki_resp.json()
        else:
            last_wiki_content["symbol"] = request.args.get("symbol")

        species_dict_resp = requests.get(
            urljoin(GN3_LOCAL_URL, "/api/metadata/wiki/species")
        )
        species_dict_resp.raise_for_status()
        species_dict = species_dict_resp.json()
        species_dict["no specific species"] = "no specific species"

        session_email = session_info()["user"]["email"]
        return render_template(
            "wiki/edit_wiki.html",
            content=last_wiki_content,
            species_dict=species_dict,
            session_email=session_email,
        )
    if request.method == "POST":
        post_data = request.form
        web_url = post_data["web_url"]
        if web_url == "http://":  # default prefilled value in form
            web_url = ""
        payload = {
            "symbol": post_data["symbol"],
            "pubmed_ids": [x.strip() for x in post_data["pubmed_ids"].split()],
            "species": post_data["species"],
            "comment": post_data["comment"],
            "email": post_data["email"],
            "web_url": web_url,
            "initial": post_data["initial"],
            "categories": post_data.getlist("genecategory"),
            "reason": post_data.get("reason", ""),
        }
        edit_wiki_url = "/api/metadata/wiki/edit"
        if comment_id:
            edit_wiki_url = f"/api/metadata/wiki/{comment_id}/edit"

        post_response = requests.post(
            urljoin(GN3_LOCAL_URL, edit_wiki_url),
            json=payload,
        )
        post_response.raise_for_status()

        flash(f"Wiki entry successfully {'updated' if comment_id else 'created'}",
              "alert-success")
        return redirect(url_for("display_genewiki_page", symbol=post_data["symbol"]))


@app.route("/genewiki", methods=["POST", "GET"])
def search_wiki():
    """Search genewiki for a given symbol"""
    if request.method == "GET":
        return render_template(
            "wiki/search.html",
        )
    return redirect(url_for(
        "display_genewiki_page",
        symbol=request.form.get("search")))


@app.route("/genewiki/<int:comment_id>/delete", methods=["GET", "POST"])
@require_oauth2
def delete_wiki(comment_id: int):
    token = session_info()["user"]["token"].either(
        lambda err: err, lambda tok: tok["access_token"]
    )
    post_response = requests.post(
        urljoin(GN3_LOCAL_URL, f"/api/metadata/wiki/{comment_id}/delete"),
        headers={"Authorization": f"Bearer {token}"},
    )
    post_response.raise_for_status()

    flash(f"Wiki entry successfully deleted", "alert-success")
    return redirect(request.referrer)


@app.route("/streaming/", methods=["POST", "GET"])
def streaming():
    """Search genewiki for a given symbol"""
    if request.method == "GET":
        return render_template(
            "streaming.html",
        )
    run_id = request.json.get("run_id", "output")
    results = requests.get(urljoin(GN3_LOCAL_URL,
                                   f"/api/stream/{run_id}?peak={request.args.get('peak')}"))
    return results.json()
