from __future__ import absolute_import, division, print_function

import flask

from wqflask import app

from flask import render_template, request

from wqflask import search_results
from wqflask.show_trait import show_trait_page

from wqflask.dataSharing import SharingInfo, SharingInfoPage

from base import webqtlFormData

from pprint import pformat as pf

print("latest blue")

@app.route("/")
def index_page():
    return render_template("index_page.html")


@app.route("/data_sharing")
def data_sharing():
    print("In data_sharing")
    fd = webqtlFormData.webqtlFormData(request.args)
    print("1Have fd")
    sharingInfoObject = SharingInfo.SharingInfo(request.args['GN_AccessionId'], None)
    self.dict['body'] = sharingInfoObject.getBody(infoupdate="")
    template_vars = SharingInfo.SharingInfo(request.args['GN_AccessionId'], None)
    print("1 Made it to rendering")
    return template_vars

@app.route("/search")
def search():
    if 'info_database' in request.args:
        print("Going to sharing_info_page")
        template_vars = sharing_info_page()
        if template_vars.redirect_url:
            print("Going to redirect")
            return flask.redirect(template_vars.redirect_url)
        else:
            return render_template("data_sharing.html", **template_vars.__dict__)
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



# Todo: Can we simplify this? -Sam
def sharing_info_page():
    print("In sharing_info_page")
    fd = webqtlFormData.webqtlFormData(request.args)
    print("2Have fd")
    template_vars = SharingInfoPage.SharingInfoPage(fd)
    print("2 Made it to rendering")
    return template_vars
