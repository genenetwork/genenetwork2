from __future__ import print_function
import re
import requests
from lxml.html import parse
from requests.exceptions import ConnectionError

DO_FAIL=False  # fail on error

def is_root_link(link):
    pattern = re.compile("^/$")
    return pattern.match(link)

def is_mailto_link(link):
    pattern = re.compile("^mailto:.*")
    return pattern.match(link)

def is_internal_link(link):
    pattern = re.compile("^/.*")
    return pattern.match(link)

def is_in_page_link(link):
    pattern = re.compile("^#.*")
    return pattern.match(link)

def get_links(doc):
    return filter(
        lambda x: not (
            is_root_link(x)
            or is_mailto_link(x))
        , map(lambda y: y.get("href")
              , doc.cssselect("a")))

def verify_link(link):
    if link[0] == "#":
        # local link on page
        return
    print("verifying "+link)
    try:
        result = requests.get(link, timeout=20, verify=False)
        if result.status_code == 200:
            print(link+" ==> OK")
        elif result.status_code == 307:
            print(link+" ==> REDIRECT")
        else:
            print("ERROR: link `"+link+"` failed with status "
                  , result.status_code)

            if DO_FAIL:
                raise Exception("Failed verify")
    except ConnectionError as ex:
        print("ERROR: ", link, ex)
        if DO_FAIL:
            raise ex

def check_page(host, start_url):
    print("")
    print("Checking links host "+host+" in page `"+start_url+"`")
    doc = parse(start_url).getroot()
    links = get_links(doc)
    in_page_links = filter(is_in_page_link, links)
    internal_links = filter(is_internal_link, links)
    external_links = filter(lambda x: not (is_internal_link(x) or is_in_page_link(x)), links)

    for link in internal_links:
        verify_link(host+link)

    for link in external_links:
        verify_link(link)

def check_links(args_obj, parser):
    print("")
    print("Checking links")
    host = args_obj.host

    # Check the home page
    check_page(host, host)

    # Check traits page
    check_page(
        host,
        host+"/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P")


def check_packaged_js_files(args_obj, parser):
    host = args_obj.host
    js_files = [
        # Datatables Extensions:
        "/DataTablesExtensions/buttonsBootstrap/css/buttons.bootstrap.css",
        "/DataTablesExtensions/buttons/js/dataTables.buttons.min.js",
        "/DataTablesExtensions/buttonStyles/css/buttons.dataTables.min.css",
        "/DataTablesExtensions/buttons/js/dataTables.buttons.min.js",
        "/DataTablesExtensions/colResize/dataTables.colResize.js",
        "/DataTablesExtensions/colReorder/js/dataTables.colReorder.js",
        "/DataTablesExtensions/buttons/js/buttons.colVis.min.js",
        "/DataTables/js/jquery.dataTables.js",
        "/DataTablesExtensions/scroller/css/scroller.dataTables.min.css",
        # Datatables plugins:
        "/DataTablesExtensions/plugins/sorting/natural.js",
        "/DataTablesExtensions/plugins/sorting/scientific.js",
    ]

    print("Checking links")
    for link in js_files:
        verify_link(host+link)
