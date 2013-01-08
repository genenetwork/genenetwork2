from __future__ import absolute_import, division, print_function

import csv
import StringIO  # Todo: Use cStringIO?

import simplejson as json
#import json
import yaml

import flask
import sqlalchemy
#import config

from wqflask import app

from flask import render_template, request, make_response, Response, Flask, g, config

from wqflask import search_results
from wqflask.show_trait import show_trait
from wqflask.show_trait import export_trait_data
from wqflask.marker_regression import marker_regression
from wqflask.correlation import CorrelationPage

from wqflask.dataSharing import SharingInfo, SharingInfoPage

from base import webqtlFormData

from pprint import pformat as pf

#import logging
#logging.basicConfig(filename="/tmp/gn_log", level=logging.INFO)
#_log = logging.getLogger("correlation")

@app.before_request
def connect_db():
    print("blue app.config:", app.config, pf(vars(app.config)))
    g.db = sqlalchemy.create_engine(app.config['DB_URI'])

@app.route("/")
def index_page():
    print("Sending index_page")
    return render_template("index_page.html")

@app.route("/data_sharing")
def data_sharing_page():
    print("In data_sharing")
    fd = webqtlFormData.webqtlFormData(request.args)
    print("1Have fd")
    sharingInfoObject = SharingInfo.SharingInfo(request.args['GN_AccessionId'], None)
    info, htmlfilelist = sharingInfoObject.getBody(infoupdate="")
    print("type(htmlfilelist):", type(htmlfilelist))
    htmlfilelist = htmlfilelist.encode("utf-8")
    #template_vars = SharingInfo.SharingInfo(request.args['GN_AccessionId'], None)
    print("1 Made it to rendering")
    return render_template("data_sharing.html",
                            info=info,
                            htmlfilelist=htmlfilelist)


@app.route("/search")
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
        print("calling search_results.SearchResultPage")
        the_search = search_results.SearchResultPage(request.args)
        print("template_vars is:", pf(the_search.__dict__))
        #print("trait_list is:", pf(the_search.__dict__['trait_list'][0].__dict__))
        #for trait in the_search.trait_list:
        #    print(" -", trait.description_display)

        return render_template("search_result_page.html", **the_search.__dict__)


@app.route("/whats_new")
def whats_new_page():
    #variables = whats_new.whats_new()
    with open("/home/sam/gene/wqflask/wqflask/yaml_data/whats_new.yaml") as fh:
        contents = fh.read()
        yamilized = yaml.safe_load(contents)
        news_items = yamilized['news']
    for news_item in news_items:
        print("\nnews_item is: %s\n" % (news_item))
    return render_template("whats_new.html", news_items=news_items)

@app.route('/export_trait_csv', methods=('POST',))
def export_trait_excel():
    """Excel file consisting of the sample data from the trait data and analysis page"""
    print("In export_trait_excel")
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
    print("js_data before dump:", template_vars.js_data)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    # Sorting the keys messes up the ordered dictionary, so don't do that
                                       #sort_keys=True)

    print("js_data after dump:", template_vars.js_data)
    print("show_trait template_vars:", pf(template_vars.__dict__))
    return render_template("show_trait.html", **template_vars.__dict__)

@app.route("/marker_regression", methods=('POST',))
def marker_regression_page():
    template_vars = marker_regression.MarkerRegression(request.form)
    #print("js_data before dump:", template_vars.js_data)
    template_vars.js_data = json.dumps(template_vars.js_data,
                                       default=json_default_handler,
                                       indent="   ")
    print("[dub] js_data after dump:", template_vars.js_data)
    print("marker_regression template_vars:", pf(template_vars.__dict__))
    return render_template("marker_regression.html", **template_vars.__dict__)

@app.route("/corr_compute", methods=('POST',))
def corr_compute_page():
    print("In corr_compute, request.args is:", pf(request.form))
    fd = webqtlFormData.webqtlFormData(request.form)
    template_vars = CorrelationPage.CorrelationPage(fd)
    return render_template("correlation_page.html", **template_vars.__dict__)

@app.route("/int_mapping", methods=('POST',))
def interval_mapping_page():
    template_vars = interval_mapping.IntervalMapping(request.args)
    return render_template("interval_mapping.html", **template_vars.__dict__)

# Todo: Can we simplify this? -Sam
def sharing_info_page():
    """Info page displayed when the user clicks the "Info" button next to the dataset selection"""
    print("In sharing_info_page")
    fd = webqtlFormData.webqtlFormData(request.args)
    template_vars = SharingInfoPage.SharingInfoPage(fd)
    return template_vars


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
