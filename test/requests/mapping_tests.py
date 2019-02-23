from __future__ import print_function
import re
import copy
import json
import requests
from lxml.html import fromstring

def load_data_from_file():
    filename = "../test/data/input/mapping/1435395_s_at_HC_M2_0606_P.json"
    file_handle = open(filename, "r")
    file_data = json.loads(file_handle.read().encode("utf-8"))
    return file_data

def check_R_qtl_tool_selection(host, data):
    print("")
    print("R/qtl mapping tool selection")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    page = requests.post(host+"/marker_regression", data=data, headers=headers)
    doc = fromstring(page.text)
    form = doc.forms[1]
    assert form.fields["dataset"] == "HC_M2_0606_P"
    assert form.fields["value:BXD1"] == "15.034"

def check_CIM_tool_selection(host, data):
    print("")
    print("CIM mapping tool selection (using reaper)")
    data["method"] = "reaper"
    page = requests.post(host+"/marker_regression", data=data)
    doc = fromstring(page.text)
    form = doc.forms[1]
    assert form.fields["dataset"] == "HC_M2_0606_P"
    assert form.fields["value:BXD1"] == "15.034"

def check_mapping(args_obj, parser):
    print("")
    print("Checking mapping")

    host = args_obj.host
    data = load_data_from_file()
    check_pylmm_tool_selection(host, copy.deepcopy(data))
    check_R_qtl_tool_selection(host, copy.deepcopy(data)) ## Why does this fail?
    check_CIM_tool_selection(host, copy.deepcopy(data))
