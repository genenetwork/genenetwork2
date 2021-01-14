"""Main routing table for GN2"""

import traceback # for error page
import os        # for error gifs
import random    # for random error gif
import datetime  # for errors
import time      # for errors
import sys
import csv
import simplejson as json
import yaml
import xlsxwriter
import io  # Todo: Use cStringIO?

from zipfile import ZipFile, ZIP_DEFLATED

import gc
import numpy as np
import pickle as pickle
import uuid

import flask
import base64
import array
import sqlalchemy
from wqflask import app
from flask import g, Response, request, make_response, render_template, send_from_directory, jsonify, redirect, url_for, send_file

from wqflask import group_manager
from wqflask import resource_manager
from wqflask import search_results
from wqflask import export_traits
from wqflask import gsearch
from wqflask import update_search_results
from wqflask import docs
from wqflask import news
from wqflask import server_side
from wqflask.submit_bnw import get_bnw_input
from base.data_set import create_dataset, DataSet    # Used by YAML in marker_regression
from wqflask.show_trait import show_trait
from wqflask.show_trait import export_trait_data
from wqflask.heatmap import heatmap
from wqflask.external_tools import send_to_bnw, send_to_webgestalt, send_to_geneweaver
from wqflask.comparison_bar_chart import comparison_bar_chart
from wqflask.marker_regression import run_mapping
from wqflask.marker_regression import display_mapping_results
from wqflask.network_graph import network_graph
from wqflask.correlation import show_corr_results
from wqflask.correlation_matrix import show_corr_matrix
from wqflask.correlation import corr_scatter_plot
from wqflask.wgcna import wgcna_analysis
from wqflask.ctl import ctl_analysis
from wqflask.snp_browser import snp_browser
from wqflask.search_results import SearchResultPage
from wqflask.export_traits import export_search_results_csv
from wqflask.gsearch import GSearch
from wqflask.update_search_results import GSearch as UpdateGSearch
from wqflask.docs import Docs, update_text
from wqflask.db_info import InfoPage

from utility import temp_data
from utility.tools import SQL_URI, TEMPDIR, USE_REDIS, USE_GN_SERVER, GN_SERVER_URL, GN_VERSION, JS_TWITTER_POST_FETCHER_PATH, JS_GUIX_PATH, CSS_PATH
from utility.helper_functions import get_species_groups
from utility.authentication_tools import check_resource_availability
from utility.redis_tools import get_redis_conn
Redis = get_redis_conn()

from base.webqtlConfig import GENERATED_IMAGE_DIR, DEFAULT_PRIVILEGES
from utility.benchmark import Bench

from pprint import pformat as pf

from wqflask import collect
from wqflask.database import db_session

import werkzeug

import utility.logger
logger = utility.logger.getLogger(__name__ )


@app.before_request
def connect_db():
    logger.info("@app.before_request connect_db")
    db = getattr(g, '_database', None)
    if db is None:
        logger.debug("Get new database connector")
        g.db = g._database = sqlalchemy.create_engine(SQL_URI, encoding="latin1")
        logger.debug(g.db)

@app.before_request
def check_access_permissions():
    logger.debug("@app.before_request check_access_permissions")
    available = True
    if 'dataset' in request.args:
        permissions = DEFAULT_PRIVILEGES
        if request.args['dataset'] != "Temp":
            dataset = create_dataset(request.args['dataset'])

            if dataset.type == "Temp":
                permissions = DEFAULT_PRIVILEGES
            elif 'trait_id' in request.args:
                permissions = check_resource_availability(dataset, request.args['trait_id'])
            elif dataset.type != "Publish":
                permissions = check_resource_availability(dataset)

        if 'view' not in permissions['data']:
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
    formatted_lines = [request.url + " ("+time_str+")"]+traceback.format_exc().splitlines()

    # Handle random animations
    # Use a cookie to have one animation on refresh
    animation = request.cookies.get(err_msg[:32])
    if not animation:
        list = [fn for fn in os.listdir("./wqflask/static/gif/error") if fn.endswith(".gif") ]
        animation = random.choice(list)

    resp = make_response(render_template("error.html", message=err_msg, stack=formatted_lines, error_image=animation, version=GN_VERSION))

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
    #if USE_GN_SERVER:
    #    # The menu is generated using GN_SERVER
    #    return render_template("index_page.html", gn_server_url = GN_SERVER_URL, version=GN_VERSION)
    #else:

    # Old style static menu (OBSOLETE)
    return render_template("index_page_orig.html", version=GN_VERSION)


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
                            img_base64 = bytesarray )


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
            key = "search_results:v1:" + json.dumps(request.args, sort_keys=True)
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
        Redis.expire(key, 60*60)

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

@app.route("/gsearch_updating", methods=('POST',))
def gsearch_updating():
    logger.info("REQUEST ARGS:", request.values)
    logger.info(request.url)
    result = UpdateGSearch(request.args).__dict__
    return result['results']
    # type = request.args['type']
    # if type == "gene":
        # return render_template("gsearch_gene_updating.html", **result)
    # elif type == "phenotype":
        # return render_template("gsearch_pheno.html", **result)

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
    logger.info("In wgcna, request.form is:", request.form)             # We are going to get additional user input for the analysis
    logger.info(request.url)
    return render_template("wgcna_setup.html", **request.form)          # Display them using the template

@app.route("/wgcna_results", methods=('POST',))
def wcgna_results():
    logger.info("In wgcna, request.form is:", request.form)
    logger.info(request.url)
    wgcna = wgcna_analysis.WGCNA()                                # Start R, load the package and pointers and create the analysis
    wgcnaA = wgcna.run_analysis(request.form)                     # Start the analysis, a wgcnaA object should be a separate long running thread
    result = wgcna.process_results(wgcnaA)                        # After the analysis is finished store the result
    return render_template("wgcna_results.html", **result)        # Display them using the template

@app.route("/ctl_setup", methods=('POST',))
def ctl_setup():
    logger.info("In ctl, request.form is:", request.form)             # We are going to get additional user input for the analysis
    logger.info(request.url)
    return render_template("ctl_setup.html", **request.form)          # Display them using the template

@app.route("/ctl_results", methods=('POST',))
def ctl_results():
    logger.info("In ctl, request.form is:", request.form)
    logger.info(request.url)
    ctl = ctl_analysis.CTL()                                  # Start R, load the package and pointers and create the analysis
    ctlA = ctl.run_analysis(request.form)                     # Start the analysis, a ctlA object should be a separate long running thread
    result = ctl.process_results(ctlA)                        # After the analysis is finished store the result
    return render_template("ctl_results.html", **result)      # Display them using the template

@app.route("/news")
def news():
    doc = Docs("news", request.args)
    return render_template("docs.html", **doc.__dict__)


@app.route("/intro")
def intro():
    doc = Docs("intro", request.args)
    return render_template("docs.html", **doc.__dict__)



@app.route("/tutorials")
def tutorials():
    #doc = Docs("links", request.args)
    #return render_template("docs.html", **doc.__dict__)
    return render_template("tutorials.html")

@app.route("/credits")
def credits():
    #doc = Docs("links", request.args)
    #return render_template("docs.html", **doc.__dict__)
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
    return render_template("submit_trait.html", **{'species_and_groups' : species_and_groups, 'gn_server_url' : GN_SERVER_URL, 'version' : GN_VERSION})

@app.route("/create_temp_trait", methods=('POST',))
def create_temp_trait():
    logger.info(request.url)

    #template_vars = submit_trait.SubmitTrait(request.form)

    doc = Docs("links")
    return render_template("links.html", **doc.__dict__)
    #return render_template("show_trait.html", **template_vars.__dict__)

@app.route('/export_trait_excel', methods=('POST',))
def export_trait_excel():
    """Excel file consisting of the sample data from the trait data and analysis page"""
    logger.info("In export_trait_excel")
    logger.info("request.form:", request.form)
    logger.info(request.url)
    trait_name, sample_data = export_trait_data.export_sample_table(request.form)

    logger.info("sample_data - type: %s -- size: %s" % (type(sample_data), len(sample_data)))

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
                    headers={"Content-Disposition":"attachment;filename="+ trait_name + ".xlsx"})

@app.route('/export_trait_csv', methods=('POST',))
def export_trait_csv():
    """CSV file consisting of the sample data from the trait data and analysis page"""
    logger.info("In export_trait_csv")
    logger.info("request.form:", request.form)
    logger.info(request.url)
    trait_name, sample_data = export_trait_data.export_sample_table(request.form)

    logger.info("sample_data - type: %s -- size: %s" % (type(sample_data), len(sample_data)))

    buff = io.StringIO()
    writer = csv.writer(buff)
    for row in sample_data:
        writer.writerow(row)
    csv_data = buff.getvalue()
    buff.close()

    return Response(csv_data,
                    mimetype='text/csv',
                    headers={"Content-Disposition":"attachment;filename="+ trait_name + ".csv"})

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
        memory_file = io.StringIO()
        with ZipFile(memory_file, mode='w', compression=ZIP_DEFLATED) as zf:
            for the_file in file_list:
                zf.writestr(the_file[0], the_file[1])

        memory_file.seek(0)

        return send_file(memory_file, attachment_filename=filename + ".zip", as_attachment=True)
    else:
        return Response(file_list[0][1],
                        mimetype='text/csv',
                        headers={"Content-Disposition":"attachment;filename=" + file_list[0][0]})

@app.route('/export_perm_data', methods=('POST',))
def export_perm_data():
    """CSV file consisting of the permutation data for the mapping results"""
    logger.info(request.url)
    perm_info = json.loads(request.form['perm_info'])

    now = datetime.datetime.now()
    time_str = now.strftime('%H:%M_%d%B%Y')

    file_name = "Permutation_" + perm_info['num_perm'] + "_" + perm_info['trait_name'] + "_" + time_str

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
        ["#Permutation_stratified_by: " + ", ".join([ str(cofactor) for cofactor in perm_info['strat_cofactors']])],
        ["#RESULTS_1: Suggestive LRS(p=0.63) = " + str(np.percentile(np.array(perm_info['perm_data']), 67))],
        ["#RESULTS_2: Significant LRS(p=0.05) = " + str(np.percentile(np.array(perm_info['perm_data']), 95))],
        ["#RESULTS_3: Highly Significant LRS(p=0.01) = " + str(np.percentile(np.array(perm_info['perm_data']), 99))],
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
                    headers={"Content-Disposition":"attachment;filename=" + file_name + ".csv"})

@app.route("/show_temp_trait", methods=('POST',))
def show_temp_trait_page():
    logger.info(request.url)
    template_vars = show_trait.ShowTrait(request.form)
    #logger.info("js_data before dump:", template_vars.js_data)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    # Sorting the keys messes up the ordered dictionary, so don't do that
                                       #sort_keys=True)

    #logger.info("js_data after dump:", template_vars.js_data)
    #logger.info("show_trait template_vars:", pf(template_vars.__dict__))
    return render_template("show_trait.html", **template_vars.__dict__)

@app.route("/show_trait")
def show_trait_page():
    logger.info(request.url)
    template_vars = show_trait.ShowTrait(request.args)
    #logger.info("js_data before dump:", template_vars.js_data)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    # Sorting the keys messes up the ordered dictionary, so don't do that
                                       #sort_keys=True)

    #logger.info("js_data after dump:", template_vars.js_data)
    #logger.info("show_trait template_vars:", pf(template_vars.__dict__))
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
        key = "heatmap:{}:".format(version) + json.dumps(start_vars, sort_keys=True)
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
                logger.info("  ---**--- {}: {}".format(type(template_vars.__dict__[item]), item))

            pickled_result = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
            logger.info("pickled result length:", len(pickled_result))
            Redis.set(key, pickled_result)
            Redis.expire(key, 60*60)

        with Bench("Rendering template"):
            rendered_template = render_template("heatmap.html", **result)

    else:
        rendered_template = render_template("empty_collection.html", **{'tool':'Heatmap'})

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
        rendered_template = render_template("empty_collection.html", **{'tool':'BNW'})

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
        rendered_template = render_template("empty_collection.html", **{'tool':'WebGestalt'})

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
        rendered_template = render_template("empty_collection.html", **{'tool':'GeneWeaver'})

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
        rendered_template = render_template("comparison_bar_chart.html", **result)
    else:
        rendered_template = render_template("empty_collection.html", **{'tool':'Comparison Bar Chart'})

    return rendered_template

@app.route("/mapping_results_container")
def mapping_results_container_page():
    return render_template("mapping_results_container.html")

@app.route("/loading", methods=('POST',))
def loading_page():
    logger.info(request.url)
    initial_start_vars = request.form
    start_vars_container = {}
    n_samples = 0 #ZS: So it can be displayed on loading page
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
                dataset = create_dataset(start_vars['dataset'], group_name = start_vars['group'])
            else:
                dataset = create_dataset(start_vars['dataset'])
            genofile_samplelist = []
            samples = start_vars['primary_samples'].split(",")
            if 'genofile' in start_vars:
                if start_vars['genofile'] != "":
                    genofile_string = start_vars['genofile']
                    dataset.group.genofile = genofile_string.split(":")[0]
                    genofile_samples = run_mapping.get_genofile_samplelist(dataset)
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
        'control_marker_db',
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
    key = "mapping_results:{}:".format(version) + json.dumps(start_vars, sort_keys=True)
    with Bench("Loading cache"):
        result = None # Just for testing
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
                    rendered_template = render_template("pair_scan_results.html", **result)
            else:
                gn1_template_vars = display_mapping_results.DisplayMappingResults(result).__dict__

                with Bench("Rendering template"):
                    #if (gn1_template_vars['mapping_method'] == "gemma") or (gn1_template_vars['mapping_method'] == "plink"):
                    #gn1_template_vars.pop('qtlresults', None)
                    rendered_template = render_template("mapping_results.html", **gn1_template_vars)

    return rendered_template

@app.route("/export_mapping_results", methods = ('POST',))
def export_mapping_results():
    logger.info("request.form:", request.form)
    logger.info(request.url)
    file_path = request.form.get("results_path")
    results_csv = open(file_path, "r").read()
    response = Response(results_csv,
                        mimetype='text/csv',
                        headers={"Content-Disposition":"attachment;filename=mapping_results.csv"})

    return response

@app.route("/export_corr_matrix", methods = ('POST',))
def export_corr_matrix():
    file_path = request.form.get("export_filepath")
    file_name = request.form.get("export_filename")
    results_csv = open(file_path, "r").read()
    response = Response(results_csv,
                        mimetype='text/csv',
                        headers={"Content-Disposition":"attachment;filename=" + file_name + ".csv"})

    return response

@app.route("/export", methods = ('POST',))
def export():
    logger.info("request.form:", request.form)
    logger.info(request.url)
    svg_xml = request.form.get("data", "Invalid data")
    filename = request.form.get("filename", "manhattan_plot_snp")
    response = Response(svg_xml, mimetype="image/svg+xml")
    response.headers["Content-Disposition"] = "attachment; filename=%s"%filename
    return response

@app.route("/export_pdf", methods = ('POST',))
def export_pdf():
    import cairosvg
    logger.info("request.form:", request.form)
    logger.info(request.url)
    svg_xml = request.form.get("data", "Invalid data")
    logger.info("svg_xml:", svg_xml)
    filename = request.form.get("filename", "interval_map_pdf")
    filepath = GENERATED_IMAGE_DIR+filename
    pdf_file = cairosvg.svg2pdf(bytestring=svg_xml)
    response = Response(pdf_file, mimetype="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=%s"%filename
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
        return render_template("empty_collection.html", **{'tool':'Network Graph'})

@app.route("/corr_compute", methods=('POST',))
def corr_compute_page():
    logger.info("In corr_compute, request.form is:", pf(request.form))
    logger.info(request.url)
    template_vars = show_corr_results.CorrelationResults(request.form)
    return render_template("correlation_page.html", **template_vars.__dict__)

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
        return render_template("empty_collection.html", **{'tool':'Correlation Matrix'})

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
    #ZS: Currently just links to GN1
    logger.info(request.url)
    return redirect("http://gn1.genenetwork.org/tutorial/WebQTLTour/")

@app.route("/tutorial/security", methods=('GET',))
def security_tutorial_page():
    #ZS: Currently just links to GN1
    logger.info(request.url)
    return render_template("admin/security_help.html")

@app.route("/submit_bnw", methods=('POST',))
def submit_bnw():
    logger.info(request.url)
    template_vars = get_bnw_input(request.form)
    return render_template("empty_collection.html", **{'tool':'Correlation Matrix'})

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

##########################################################################

def json_default_handler(obj):
    '''Based on http://stackoverflow.com/a/2680060/1175849'''
    # Handle datestamps
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    # Handle integer keys for dictionaries
    elif isinstance(obj, int) or isinstance(obj, uuid.UUID):
        return str(obj)
    # Handle custom objects
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    #elif type(obj) == "Dataset":
    #     logger.info("Not going to serialize Dataset")
    #    return None
    else:
        raise TypeError('Object of type %s with value of %s is not JSON serializable' % (
            type(obj), repr(obj)))
