# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import sys
print("sys.path is:", sys.path)

import csv
import xlsxwriter
import StringIO  # Todo: Use cStringIO?

import gc

import cPickle as pickle
import uuid

import simplejson as json
#import json
import yaml

#Switching from Redis to StrictRedis; might cause some issues
import redis
Redis = redis.StrictRedis()

import flask
import base64
import array
import sqlalchemy
#import config

from wqflask import app

from flask import (render_template, request, make_response, Response,
                   Flask, g, config, jsonify, redirect, url_for)

from wqflask import search_results
from wqflask import gsearch
from wqflask import docs
from wqflask import news
from base.data_set import DataSet    # Used by YAML in marker_regression
from base.data_set import create_datasets_list
from wqflask.show_trait import show_trait
from wqflask.show_trait import export_trait_data
from wqflask.heatmap import heatmap
from wqflask.marker_regression import marker_regression
from wqflask.marker_regression import marker_regression_gn1
from wqflask.interval_mapping import interval_mapping
from wqflask.correlation import show_corr_results
from wqflask.correlation_matrix import show_corr_matrix
from wqflask.correlation import corr_scatter_plot

from wqflask.wgcna import wgcna_analysis

from utility import temp_data

from base import webqtlFormData
from utility.benchmark import Bench

from pprint import pformat as pf

from wqflask import user_manager
from wqflask import collect

#import logging
#logging.basicConfig(filename="/tmp/gn_log", level=logging.INFO)
#_log = logging.getLogger("correlation")

@app.before_request
def connect_db():
    g.db = sqlalchemy.create_engine(app.config['DB_URI'])

#@app.before_request
#def trace_it():
#    from wqflask import tracer
#    tracer.turn_on()

@app.route("/")
def index_page():
    print("Sending index_page")
    #create_datasets_list()
    #key = "all_datasets"
    #result = Redis.get(key)
    #if result:
    #    print("Cache hit!!!")
    #    result = pickle.loads(result)
    #else:
    #    with Bench("Creating DataSets object"):
    #        ds = DataSets()
    #    Redis.set(key, pickle.dumps(result, pickle.HIGHEST_PROTOCOL))
    #    Redis.expire(key, 2*60)
    #print("[orange] ds:", ds.datasets)
    return render_template("index_page.html")


@app.route("/tmp/<img_path>")
def tmp_page(img_path):
    print("In tmp_page")
    print("img_path:", img_path)
    initial_start_vars = request.form
    print("initial_start_vars:", initial_start_vars)
    imgfile = open(webqtlConfig.TMPDIR + img_path, 'rb')
    imgdata = imgfile.read()
    imgB64 = imgdata.encode("base64")
    bytesarray = array.array('B', imgB64)
    return render_template("show_image.html",
                            img_base64 = bytesarray )


#@app.route("/data_sharing")
#def data_sharing_page():
#    print("In data_sharing")
#    fd = webqtlFormData.webqtlFormData(request.args)
#    print("1Have fd")
#    sharingInfoObject = SharingInfo.SharingInfo(request.args['GN_AccessionId'], None)
#    info, htmlfilelist = sharingInfoObject.getBody(infoupdate="")
#    print("type(htmlfilelist):", type(htmlfilelist))
#    htmlfilelist = htmlfilelist.encode("utf-8")
#    #template_vars = SharingInfo.SharingInfo(request.args['GN_AccessionId'], None)
#    print("1 Made it to rendering")
#    return render_template("data_sharing.html",
#                            info=info,
#                            htmlfilelist=htmlfilelist)


@app.route("/search", methods=('GET',))
def search_page():
    print("in search_page")
    if 'info_database' in request.args:
        print("Going to sharing_info_page")
        template_vars = sharing_info_page()
        if template_vars.redirect_url:
            print("Going to redirect")
            return flask.redirect(template_vars.redirect_url)
        else:
            return render_template("data_sharing.html", **template_vars.__dict__)
    else:
        key = "search_results:v3:" + json.dumps(request.args, sort_keys=True)
        print("key is:", pf(key))
        with Bench("Loading cache"):
            result = Redis.get(key)

        if result:
            print("Cache hit!!!")
            with Bench("Loading results"):
                result = pickle.loads(result)
        else:
            print("calling search_results.SearchResultPage")
            print("request.args is", request.args)
            the_search = search_results.SearchResultPage(request.args)
            result = the_search.__dict__

            print("result: ", pf(result))
            Redis.set(key, pickle.dumps(result, pickle.HIGHEST_PROTOCOL))
            Redis.expire(key, 60*60)

        if result['quick']:
            return render_template("quick_search.html", **result)
        elif result['search_term_exists']:
            return render_template("search_result_page.html", **result)
        else:
            return render_template("search_error.html")

@app.route("/gsearch", methods=('GET',))
def gsearchact():
    result = gsearch.GSearch(request.args).__dict__
    type = request.args['type']
    if type == "gene":
        return render_template("gsearch_gene.html", **result)
    elif type == "phenotype":
        return render_template("gsearch_pheno.html", **result)
	
@app.route("/docedit")
def docedit():
    doc = docs.Docs(request.args['entry'])
    return render_template("docedit.html", **doc.__dict__)

@app.route("/help")
def help():
    doc = docs.Docs("help")
    return render_template("docs.html", **doc.__dict__)

@app.route("/wgcna_setup", methods=('POST',))
def wcgna_setup():
    print("In wgcna, request.form is:", request.form)             # We are going to get additional user input for the analysis
    return render_template("wgcna_setup.html", **request.form)          # Display them using the template

@app.route("/wgcna_results", methods=('POST',))
def wcgna_results():
    print("In wgcna, request.form is:", request.form)
    wgcna = wgcna_analysis.WGCNA()                                # Start R, load the package and pointers and create the analysis
    wgcnaA = wgcna.run_analysis(request.form)                     # Start the analysis, a wgcnaA object should be a separate long running thread
    result = wgcna.process_results(wgcnaA)                        # After the analysis is finished store the result
    return render_template("wgcna_results.html", **result)        # Display them using the template


@app.route("/news")
def news_route():
    newsobject = news.News()
    return render_template("news.html", **newsobject.__dict__)

@app.route("/references")
def references():
    doc = docs.Docs("references")
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

@app.route('/export_trait_excel', methods=('POST',))
def export_trait_excel():
    """Excel file consisting of the sample data from the trait data and analysis page"""
    print("In export_trait_excel")
    print("request.form:", request.form)
    sample_data = export_trait_data.export_sample_table(request.form)

    print("sample_data - type: %s -- size: %s" % (type(sample_data), len(sample_data)))

    buff = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(buff, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    for i, row in enumerate(sample_data):
        worksheet.write(i, 0, row[0])
        worksheet.write(i, 1, row[1])
    workbook.close()
    excel_data = buff.getvalue()
    buff.close()

    return Response(excel_data,
                    mimetype='application/vnd.ms-excel',
                    headers={"Content-Disposition":"attachment;filename=test.xlsx"})

@app.route('/export_trait_csv', methods=('POST',))
def export_trait_csv():
    """CSV file consisting of the sample data from the trait data and analysis page"""
    print("In export_trait_csv")
    print("request.form:", request.form)
    sample_data = export_trait_data.export_sample_table(request.form)

    print("sample_data - type: %s -- size: %s" % (type(sample_data), len(sample_data)))

    buff = StringIO.StringIO()
    writer = csv.writer(buff)
    for row in sample_data:
        writer.writerow(row)
    csv_data = buff.getvalue()
    buff.close()

    return Response(csv_data,
                    mimetype='text/csv',
                    headers={"Content-Disposition":"attachment;filename=test.csv"})

@app.route("/show_trait")
def show_trait_page():
    # Here it's currently too complicated not to use an fd that is a webqtlFormData
    #fd = webqtlFormData.webqtlFormData(request.args)
    #print("stp y1:", pf(vars(fd)))
    template_vars = show_trait.ShowTrait(request.args)
    #print("js_data before dump:", template_vars.js_data)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    # Sorting the keys messes up the ordered dictionary, so don't do that
                                       #sort_keys=True)

    #print("js_data after dump:", template_vars.js_data)
    #print("show_trait template_vars:", pf(template_vars.__dict__))
    return render_template("show_trait.html", **template_vars.__dict__)

@app.route("/heatmap", methods=('POST',))
def heatmap_page():
    print("In heatmap, request.form is:", pf(request.form))
    
    start_vars = request.form
    temp_uuid = uuid.uuid4()
    
    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if traits[0] != "":
        version = "v5"
        key = "heatmap:{}:".format(version) + json.dumps(start_vars, sort_keys=True)
        print("key is:", pf(key))
        with Bench("Loading cache"):
            result = Redis.get(key)
        
        if result:
            print("Cache hit!!!")
            with Bench("Loading results"):
                result = pickle.loads(result)
    
        else:
            print("Cache miss!!!")
    
            template_vars = heatmap.Heatmap(request.form, temp_uuid)
            template_vars.js_data = json.dumps(template_vars.js_data,
                                               default=json_default_handler,
                                               indent="   ")
        
            result = template_vars.__dict__

            for item in template_vars.__dict__.keys():
                print("  ---**--- {}: {}".format(type(template_vars.__dict__[item]), item))
    
            pickled_result = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
            print("pickled result length:", len(pickled_result))
            Redis.set(key, pickled_result)
            Redis.expire(key, 60*60)
    
        with Bench("Rendering template"):
            rendered_template = render_template("heatmap.html", **result)
     
    else:
        rendered_template = render_template("empty_collection.html", **{'tool':'Heatmap'})

    return rendered_template

@app.route("/mapping_results_container")
def mapping_results_container_page():
    return render_template("mapping_results_container.html")

@app.route("/marker_regression", methods=('POST',))
def marker_regression_page():
    initial_start_vars = request.form
    temp_uuid = initial_start_vars['temp_uuid']
    wanted = (
        'trait_id',
        'dataset',
        'method',
        'mapping_scale',
        'score_type',
        'suggestive',
        'num_perm',
        'maf',
        'manhattan_plot',
        'control_marker',
        'control_marker_db',
        'do_control',
        'pair_scan',
        'mapmethod_rqtl_geno',
        'mapmodel_rqtl_geno'
    )
    print("Marker regression called with initial_start_vars:", initial_start_vars)
    start_vars = {}
    for key, value in initial_start_vars.iteritems():
        if key in wanted or key.startswith(('value:')):
            start_vars[key] = value

    version = "v3"
    key = "marker_regression:{}:".format(version) + json.dumps(start_vars, sort_keys=True)
    print("key is:", pf(key))
    with Bench("Loading cache"):
        result = None # Just for testing
        #result = Redis.get(key)

    #print("************************ Starting result *****************")
    #print("result is [{}]: {}".format(type(result), result))
    #print("************************ Ending result ********************")

    if result:
        print("Cache hit!!!")
        with Bench("Loading results"):
            result = pickle.loads(result)
    else:
        print("Cache miss!!!")
        template_vars = marker_regression.MarkerRegression(start_vars, temp_uuid)

        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")

        result = template_vars.__dict__
        #print("initial result:", result['qtl_results'])

        #for item in template_vars.__dict__.keys():
        #    print("  ---**--- {}: {}".format(type(template_vars.__dict__[item]), item))

        #causeerror
        
        print("TESTING GN1!!!")
        gn1_template_vars = marker_regression_gn1.MarkerRegression(result).__dict__
        print("gn1_template_vars:", gn1_template_vars)
        causeerror


        #qtl_length = len(result['js_data']['qtl_results'])
        #print("qtl_length:", qtl_length)
        pickled_result = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
        print("pickled result length:", len(pickled_result))
        Redis.set(key, pickled_result)
        Redis.expire(key, 1*60)

    with Bench("Rendering template"):
        if result['pair_scan'] == True:
            img_path = result['pair_scan_filename']
            print("img_path:", img_path)
            initial_start_vars = request.form
            print("initial_start_vars:", initial_start_vars)
            imgfile = open('/home/zas1024/tmp/' + img_path, 'rb')
            imgdata = imgfile.read()
            imgB64 = imgdata.encode("base64")
            bytesarray = array.array('B', imgB64)
            result['pair_scan_array'] = bytesarray
            rendered_template = render_template("pair_scan_results.html", **result)
        else:
            rendered_template = render_template("marker_regression.html", **result)
            #rendered_template = render_template("marker_regression_gn1.html", **result)

    return rendered_template

@app.route("/export", methods = ('POST',))
def export():
    print("request.form:", request.form)
    svg_xml = request.form.get("data", "Invalid data")
    filename = request.form.get("filename", "manhattan_plot_snp")
    response = Response(svg_xml, mimetype="image/svg+xml")
    response.headers["Content-Disposition"] = "attachment; filename=%s"%filename
    return response

@app.route("/export_pdf", methods = ('POST',))
def export_pdf():
    import cairosvg
    print("request.form:", request.form)
    svg_xml = request.form.get("data", "Invalid data")
    print("svg_xml:", svg_xml)
    filename = request.form.get("filename", "interval_map_pdf")
    filepath = "/home/zas1024/gene/wqflask/output/"+filename
    pdf_file = cairosvg.svg2pdf(bytestring=svg_xml)
    response = Response(pdf_file, mimetype="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=%s"%filename
    return response

@app.route("/interval_mapping", methods=('POST',))
def interval_mapping_page():
    initial_start_vars = request.form
    temp_uuid = initial_start_vars['temp_uuid']
    wanted = (
        'trait_id',
        'dataset',
        'mapping_method',
        'chromosome',
        'num_perm',
        'manhattan_plot',
        'do_bootstraps',
        'display_additive',
        'default_control_locus',
        'control_locus'
    )

    start_vars = {}
    for key, value in initial_start_vars.iteritems():
        if key in wanted or key.startswith(('value:')):
            start_vars[key] = value

    version = "v1"
    key = "interval_mapping:{}:".format(version) + json.dumps(start_vars, sort_keys=True)
    print("key is:", pf(key))
    with Bench("Loading cache"):
        result = Redis.get(key)

    if result:
        print("Cache hit!!!")
        with Bench("Loading results"):
            result = pickle.loads(result)
    else:
        print("Cache miss!!!")
        template_vars = interval_mapping.IntervalMapping(start_vars, temp_uuid)

        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")

        result = template_vars.__dict__
        
        for item in template_vars.__dict__.keys():
            print("  ---**--- {}: {}".format(type(template_vars.__dict__[item]), item))
        
        #causeerror
        Redis.set(key, pickle.dumps(result, pickle.HIGHEST_PROTOCOL))
        Redis.expire(key, 60*60)

    with Bench("Rendering template"):
        rendered_template = render_template("marker_regression.html", **result)

    return rendered_template

@app.route("/corr_compute", methods=('POST',))
def corr_compute_page():
    print("In corr_compute, request.form is:", pf(request.form))
    #fd = webqtlFormData.webqtlFormData(request.form)
    template_vars = show_corr_results.CorrelationResults(request.form)
    return render_template("correlation_page.html", **template_vars.__dict__)

@app.route("/corr_matrix", methods=('POST',))
def corr_matrix_page():
    print("In corr_matrix, request.form is:", pf(request.form))

    start_vars = request.form
    traits = [trait.strip() for trait in start_vars['trait_list'].split(',')]
    if traits[0] != "":
        template_vars = show_corr_matrix.CorrelationMatrix(start_vars)
        template_vars.js_data = json.dumps(template_vars.js_data,
                                           default=json_default_handler,
                                           indent="   ")
    
        return render_template("correlation_matrix.html", **template_vars.__dict__)
    else:
        return render_template("empty_collection.html", **{'tool':'Correlation Matrix'})

@app.route("/corr_scatter_plot")
def corr_scatter_plot_page():
    template_vars = corr_scatter_plot.CorrScatterPlot(request.args)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    return render_template("corr_scatterplot.html", **template_vars.__dict__)

#@app.route("/int_mapping", methods=('POST',))
#def interval_mapping_page():
#    template_vars = interval_mapping.IntervalMapping(request.args)
#    return render_template("interval_mapping.html", **template_vars.__dict__)

# Todo: Can we simplify this? -Sam
def sharing_info_page():
    """Info page displayed when the user clicks the "Info" button next to the dataset selection"""
    print("In sharing_info_page")
    fd = webqtlFormData.webqtlFormData(request.args)
    template_vars = SharingInfoPage.SharingInfoPage(fd)
    return template_vars

# Take this out or secure it before putting into production
@app.route("/get_temp_data")
def get_temp_data():
    temp_uuid = request.args['key']
    return flask.jsonify(temp_data.TempData(temp_uuid).get_all())



###################################################################################################



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
    #     print("Not going to serialize Dataset")
    #    return None
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (
            type(obj), repr(obj))
