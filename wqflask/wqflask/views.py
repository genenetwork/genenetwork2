# -*- coding: utf-8 -*-
#
# Main routing table for GN2

from __future__ import absolute_import, division, print_function

import traceback # for error page
import os        # for error gifs
import random    # for random error gif
import datetime  # for errors
import time      # for errors
import sys
import csv
import xlsxwriter
import StringIO  # Todo: Use cStringIO?

import gc

import cPickle as pickle
import uuid

import simplejson as json
import yaml

#Switching from Redis to StrictRedis; might cause some issues
import redis
Redis = redis.StrictRedis()

import flask
import base64
import array
import sqlalchemy
from wqflask import app
from flask import g, Response, request, make_response, render_template, send_from_directory, jsonify, redirect
from wqflask import search_results
from wqflask import export_traits
from wqflask import gsearch
from wqflask import update_search_results
from wqflask import docs
from wqflask import news
from wqflask.submit_bnw import get_bnw_input
from base.data_set import DataSet    # Used by YAML in marker_regression
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
#from wqflask.trait_submission import submit_trait

from utility import temp_data
from utility.tools import SQL_URI,TEMPDIR,USE_REDIS,USE_GN_SERVER,GN_SERVER_URL,GN_VERSION,JS_TWITTER_POST_FETCHER_PATH,JS_GUIX_PATH, CSS_PATH
from utility.helper_functions import get_species_groups

from base.webqtlConfig import GENERATED_IMAGE_DIR
from utility.benchmark import Bench

from pprint import pformat as pf

from wqflask import user_manager
from wqflask import collect
from wqflask.database import db_session

import werkzeug

import utility.logger
logger = utility.logger.getLogger(__name__ )


@app.before_request
def connect_db():
    db = getattr(g, '_database', None)
    if db is None:
        logger.debug("Get new database connector")
        g.db = g._database = sqlalchemy.create_engine(SQL_URI, encoding="latin1")
        logger.debug(g.db)

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

    resp = make_response(render_template("error.html",message=err_msg,stack=formatted_lines,error_image=animation,version=GN_VERSION))

    # logger.error("Set cookie %s with %s" % (err_msg, animation))
    resp.set_cookie(err_msg[:32],animation)
    return resp

@app.route("/")
def index_page():
    logger.info("Sending index_page")
    logger.info(request.url)
    params = request.args
    if 'import_collections' in params:
        import_collections = params['import_collections']
        if import_collections == "true":
            g.cookie_session.import_traits_to_user()
    if USE_GN_SERVER:
        # The menu is generated using GN_SERVER
        return render_template("index_page.html", gn_server_url = GN_SERVER_URL, version=GN_VERSION)
    else:
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
    imgB64 = imgdata.encode("base64")
    bytesarray = array.array('B', imgB64)
    return render_template("show_image.html",
                            img_base64 = bytesarray )

@app.route("/js/<path:filename>")
def js(filename):
    return send_from_directory(JS_GUIX_PATH, filename)

@app.route("/css/<path:filename>")
def css(filename):
    return send_from_directory(CSS_PATH, filename)

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
    the_search = search_results.SearchResultPage(request.args)
    result = the_search.__dict__
    valid_search = result['search_term_exists']

    logger.debugf("result", result)

    if USE_REDIS and valid_search:
        Redis.set(key, pickle.dumps(result, pickle.HIGHEST_PROTOCOL))
        Redis.expire(key, 60*60)

    if valid_search:
        return render_template("search_result_page.html", **result)
    else:
        return render_template("search_error.html")

@app.route("/gsearch", methods=('GET',))
def gsearchact():
    logger.info(request.url)
    result = gsearch.GSearch(request.args).__dict__
    type = request.args['type']
    if type == "gene":
        return render_template("gsearch_gene.html", **result)
    elif type == "phenotype":
        return render_template("gsearch_pheno.html", **result)

@app.route("/gsearch_updating", methods=('POST',))
def gsearch_updating():
    logger.info("REQUEST ARGS:", request.values)
    logger.info(request.url)
    result = update_search_results.GSearch(request.args).__dict__
    return result['results']
    # type = request.args['type']
    # if type == "gene":
        # return render_template("gsearch_gene_updating.html", **result)
    # elif type == "phenotype":
        # return render_template("gsearch_pheno.html", **result)

@app.route("/docedit")
def docedit():
    logger.info(request.url)
    doc = docs.Docs(request.args['entry'])
    return render_template("docedit.html", **doc.__dict__)

@app.route('/generated/<filename>')
def generated_file(filename):
    logger.info(request.url)
    return send_from_directory(GENERATED_IMAGE_DIR,filename)

@app.route("/help")
def help():
    logger.info(request.url)
    doc = docs.Docs("help")
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

#@app.route("/news")
#def news_route():
#    newsobject = news.News()
#    return render_template("news.html", **newsobject.__dict__)

@app.route("/news")
def news():
    doc = docs.Docs("news")
    return render_template("docs.html", **doc.__dict__)

@app.route("/references")
def references():
    # doc = docs.Docs("references")
    # return render_template("docs.html", **doc.__dict__)
    return render_template("reference.html")

@app.route("/intro")
def intro():
    doc = docs.Docs("intro")
    return render_template("docs.html", **doc.__dict__)

@app.route("/policies")
def policies():
    doc = docs.Docs("policies")
    return render_template("docs.html", **doc.__dict__)

@app.route("/links")
def links():
    doc = docs.Docs("links")
    return render_template("docs.html", **doc.__dict__)

@app.route("/environments")
def environments():
    doc = docs.Docs("environments")
    return render_template("docs.html", **doc.__dict__)

@app.route("/update_text", methods=('POST',))
def update_page():
    docs.update_text(request.form)
    doc = docs.Docs(request.form['entry_type'])
    return render_template("docs.html", **doc.__dict__)

@app.route("/submit_trait")
def submit_trait_form():
    logger.info(request.url)
    species_and_groups = get_species_groups()
    return render_template("submit_trait.html", **{'species_and_groups' : species_and_groups, 'gn_server_url' : GN_SERVER_URL, 'version' : GN_VERSION})

@app.route("/create_temp_trait", methods=('POST',))
def create_temp_trait():
    logger.info(request.url)
    print("REQUEST.FORM:", request.form)
    #template_vars = submit_trait.SubmitTrait(request.form)

    doc = docs.Docs("links")
    return render_template("links.html", **doc.__dict__)
    #return render_template("show_trait.html", **template_vars.__dict__)

@app.route('/export_trait_excel', methods=('POST',))
def export_trait_excel():
    """Excel file consisting of the sample data from the trait data and analysis page"""
    logger.info("In export_trait_excel")
    logger.info("request.form:", request.form)
    logger.info(request.url)
    sample_data = export_trait_data.export_sample_table(request.form)

    logger.info("sample_data - type: %s -- size: %s" % (type(sample_data), len(sample_data)))

    buff = StringIO.StringIO()
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
                    headers={"Content-Disposition":"attachment;filename=sample_data.xlsx"})

@app.route('/export_trait_csv', methods=('POST',))
def export_trait_csv():
    """CSV file consisting of the sample data from the trait data and analysis page"""
    logger.info("In export_trait_csv")
    logger.info("request.form:", request.form)
    logger.info(request.url)
    sample_data = export_trait_data.export_sample_table(request.form)

    logger.info("sample_data - type: %s -- size: %s" % (type(sample_data), len(sample_data)))

    buff = StringIO.StringIO()
    writer = csv.writer(buff)
    for row in sample_data:
        writer.writerow(row)
    csv_data = buff.getvalue()
    buff.close()

    return Response(csv_data,
                    mimetype='text/csv',
                    headers={"Content-Disposition":"attachment;filename=sample_data.csv"})

@app.route('/export_traits_csv', methods=('POST',))
def export_traits_csv():
    """CSV file consisting of the traits from the search result page"""
    logger.info("In export_traits_csv")
    logger.info("request.form:", request.form)
    logger.info(request.url)
    csv_data = export_traits.export_search_results_csv(request.form)

    return Response(csv_data,
                    mimetype='text/csv',
                    headers={"Content-Disposition":"attachment;filename=trait_list.csv"})

@app.route('/export_perm_data', methods=('POST',))
def export_perm_data():
    """CSV file consisting of the permutation data for the mapping results"""
    logger.info(request.url)
    num_perm = float(request.form['num_perm'])
    perm_data = json.loads(request.form['perm_results'])

    buff = StringIO.StringIO()
    writer = csv.writer(buff)
    writer.writerow(["Suggestive LRS (p=0.63) = " + str(perm_data[int(num_perm*0.37-1)])])
    writer.writerow(["Significant LRS (p=0.05) = " + str(perm_data[int(num_perm*0.95-1)])])
    writer.writerow(["Highly Significant LRS (p=0.01) = " + str(perm_data[int(num_perm*0.99-1)])])
    writer.writerow("")
    writer.writerow([str(num_perm) + " Permutations"])
    writer.writerow("")
    for item in perm_data:
        writer.writerow([item])
    csv_data = buff.getvalue()
    buff.close()

    return Response(csv_data,
                    mimetype='text/csv',
                    headers={"Content-Disposition":"attachment;filename=perm_data.csv"})

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

            for item in template_vars.__dict__.keys():
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
    num_vals = 0 #ZS: So it can be displayed on loading page
    if 'wanted_inputs' in initial_start_vars:
        wanted = initial_start_vars['wanted_inputs'].split(",")
        start_vars = {}
        for key, value in initial_start_vars.iteritems():
            if key in wanted or key.startswith(('value:')):
                start_vars[key] = value

        if 'primary_samples' in start_vars:
            samples = start_vars['primary_samples'].split(",")
            for sample in samples:
                value = start_vars.get('value:' + sample)
                if value != "x":
                    num_vals += 1

        start_vars['num_vals'] = num_vals

        start_vars_container['start_vars'] = start_vars
    else:
        start_vars_container['start_vars'] = initial_start_vars
    rendered_template = render_template("loading.html", **start_vars_container)

    return rendered_template

@app.route("/run_mapping", methods=('POST',))
def mapping_results_page():
    initial_start_vars = request.form
    logger.debug("Mapping called with initial_start_vars:", initial_start_vars.items())
    logger.info(request.url)
    temp_uuid = initial_start_vars['temp_uuid']
    wanted = (
        'trait_id',
        'dataset',
        'group',
        'species',
        'samples',
        'vals',
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
        'perm_output',
        'num_bootstrap',
        'bootCheck',
        'bootstrap_results',
        'LRSCheck',
        'covariates',
        'maf',
        'use_loco',
        'manhattan_plot',
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
        'num_vals'
    )
    start_vars = {}
    for key, value in initial_start_vars.iteritems():
        if key in wanted or key.startswith(('value:')):
            start_vars[key] = value
    logger.debug("Mapping called with start_vars:", start_vars)

    version = "v3"
    key = "mapping_results:{}:".format(version) + json.dumps(start_vars, sort_keys=True)
    logger.info("key is:", pf(key))
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
            template_vars = run_mapping.RunMapping(start_vars, temp_uuid)

        if template_vars.no_results:
            rendered_template = render_template("mapping_error.html")
        else:
            #if template_vars.mapping_method != "gemma" and template_vars.mapping_method != "plink":
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
                    imgB64 = imgdata.encode("base64")
                    bytesarray = array.array('B', imgB64)
                    result['pair_scan_array'] = bytesarray
                    rendered_template = render_template("pair_scan_results.html", **result)
            else:
                gn1_template_vars = display_mapping_results.DisplayMappingResults(result).__dict__
                #pickled_result = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
                #logger.info("pickled result length:", len(pickled_result))
                #Redis.set(key, pickled_result)
                #Redis.expire(key, 1*60)

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
    elif isinstance(obj, int):
        return str(int)
    # Handle custom objects
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    #elif type(obj) == "Dataset":
    #     logger.info("Not going to serialize Dataset")
    #    return None
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (
            type(obj), repr(obj))
