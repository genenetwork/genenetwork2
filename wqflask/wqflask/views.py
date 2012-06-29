from __future__ import absolute_import, division, print_function

from wqflask import app

from flask import render_template, request

from wqflask import search_results
from wqflask.show_trait import show_trait_page

from wqflask.dataSharing import SharingInfoPage

from base import webqtlFormData

from pprint import pformat as pf

@app.route("/")
def index_page():
    return render_template("index_page.html")


@app.route("/search")
def search():
    if 'info_database' in request.args:
        print("Going to data_sharing")
        data_sharing()
    else:
        the_search = search_results.SearchResultPage(request.args)
        return render_template("search_result_page.html", **the_search.__dict__)

@app.route("/showDatabaseBXD")
def showDatabaseBXD():
    # Here it's currently too complicated not to use an fd that is a webqtlFormData
    fd = webqtlFormData.webqtlFormData(request.args)
    template_vars = show_trait_page.ShowTraitPage(fd)
    print("showDatabaseBXD template_vars:", pf(template_vars.__dict__))
    return render_template("trait_data_and_analysis.html", **template_vars.__dict__)

#@app.route("/data_sharing")
def data_sharing():
    print("In data_sharing")
    fd = webqtlFormData.webqtlFormData(request.args)
    print("Have fd")
    template_vars = SharingInfoPage.SharingInfoPage(fd)
    print("Made it to rendering")
    return render_template("data_sharing.html", **template_vars.__dict__)
