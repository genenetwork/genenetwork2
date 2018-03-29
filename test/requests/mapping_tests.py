from __future__ import print_function
import re
import json
import requests
from lxml.html import fromstring

def get_data(list_item):
    try:
        value = list_item[1]
    except:
        value = None
    #print("list_item:", list_item, "==>", value)
    return value

def load_data_from_file():
    filename = "../test/data/input/mapping/1435395_s_at_HC_M2_0606_P.json"
    file_handle = open(filename, "r")
    file_data = json.loads(file_handle.read().encode("utf-8"))
    return file_data

def check_pylmm_tool_selection(host, data):
    data["method"] = "pylmm"
    page = requests.post(host+"/marker_regression", data=data)
    doc = fromstring(page.text)
    form = doc.forms[1]
    assert form.fields["dataset"] == "HC_M2_0606_P"
    assert form.fields["value:BXD1"] == "15.034" # Check value in the file

def check_R_qtl_tool_selection(host, data):
    pass

def check_CIM_tool_selection(host, data):
    pass

def check_mapping(args_obj, parser):
    print("")
    print("Checking mapping")

    host = args_obj.host
    data = load_data_from_file()
    check_pylmm_tool_selection(host, data)
    check_R_qtl_tool_selection(host, data)
    check_CIM_tool_selection(host, data)
