import requests
from lxml.html import parse
from link_checker import check_page

def do_request(host, data):
    return request.get(
        f"{host}/corr_compute",
        params={
            **data,
            "corr_dataset": "HC_M2_0606_P",
            "corr_return_results": "100",
            "corr_samples_group": "samples_primary",})

def check_sample_correlations(baseurl):
    data = {
        "corr_type": "sample",
        "corr_sample_method": "pearson",
        "location_type": "gene"
    }
    result = do_request(host, data)
    assert result.status == 200
    assert (result.text.find("Values of record 1435464_at") >= 0), ""

def check_tissue_correlations(baseurl):
    data = {
        "corr_type": "tissue"
    }
    result = do_request(host, data)
    assert False, "Not implemented yet."

def check_lit_correlations(baseurl):
    data = {
        "corr_type": "lit"
    }
    result = do_request(host, data)
    assert False, "Not implemented yet."

def check_correlations(args_obj, parser):
    print("")
    print("Checking the correlations...")
    host = args_obj.host
    check_sample_correlations(host)
    check_tissue_correlations(host)
    check_lit_correlations(host)
