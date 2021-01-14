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
    return [x for x in [y.get("href") for y in doc.cssselect("a")] if not (
            is_root_link(x)
            or is_mailto_link(x))]

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


def verify_static_file(link):
    print("verifying "+link)
    try:
        result = requests.get(link, timeout=20, verify=False)
        if (result.status_code == 200 and
                result.content.find(bytes("Error: 404 Not Found", "utf-8")) <= 0):
            print(link+" ==> OK")
        else:
            print("ERROR: link {}".format(link))
            raise Exception("Failed verify")
    except ConnectionError as ex:
        print("ERROR: ", link, ex)


def check_page(host, start_url):
    print("")
    print("Checking links host "+host+" in page `"+start_url+"`")
    doc = parse(start_url).getroot()
    links = get_links(doc)
    in_page_links = list(filter(is_in_page_link, links))
    internal_links = list(filter(is_internal_link, links))
    external_links = [x for x in links if not (is_internal_link(x) or is_in_page_link(x))]

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
        "/css/DataTablesExtensions/buttonsBootstrap/css/buttons.bootstrap.css",
        "/js/DataTablesExtensions/buttons/js/dataTables.buttons.min.js",
        "/css/DataTablesExtensions/buttonStyles/css/buttons.dataTables.min.css",
        "/js/DataTablesExtensions/buttons/js/dataTables.buttons.min.js",
        "/js/DataTablesExtensions/colResize/dataTables.colResize.js",
        "/js/DataTablesExtensions/colReorder/js/dataTables.colReorder.js",
        "/js/DataTablesExtensions/buttons/js/buttons.colVis.min.js",
        "/js/DataTablesExtensions/scroller/js/dataTables.scroller.min.js",
        "/js/DataTables/js/jquery.dataTables.js",
        "/js/DataTablesExtensions/scrollerStyle/css/scroller.dataTables.min.css",
        # Datatables plugins:
        "/js/DataTablesExtensions/plugins/sorting/natural.js",
        "/js/DataTablesExtensions/plugins/sorting/scientific.js",
        # Other js libraries
        "/js/chroma/chroma.min.js",
        "/js/d3-tip/d3-tip.js",
        "/js/d3js/d3.min.js",
        "/js/js_alt/underscore.min.js",
        "/js/nvd3/nv.d3.min.css",
        "/js/qtip2/jquery.qtip.min.js",
        "/js/js_alt/md5.min.js",
        "/js/jquery-ui/jquery-ui.min.js",
        "/js/jquery-cookie/jquery.cookie.js",
        "/js/jquery/jquery.min.js",
        "/js/typeahead/typeahead.bundle.js",
        "/js/underscore-string/underscore.string.min.js",
        "/js/js_alt/jstat.min.js",
        "/js/js_alt/parsley.min.js",
        "/js/js_alt/timeago.min.js",
        "/js/plotly/plotly.min.js",
        "/js/ckeditor/ckeditor.js",
        "/js/jszip/jszip.min.js",
        "/js/jscolor/jscolor.js",
        "/js/DataTables/js/jquery.js",
        "/css/DataTables/css/jquery.dataTables.css",
        "/js/colorbox/jquery.colorbox-min.js",
        "/css/nouislider/nouislider.min.css",
        "/js/nouislider/nouislider.js",
        "/js/purescript-genome-browser/js/purescript-genetics-browser.js",
        "/js/purescript-genome-browser/css/purescript-genetics-browser.css",
        "/js/cytoscape/cytoscape.min.js",
        "/js/cytoscape-panzoom/cytoscape-panzoom.js",
        "/js/cytoscape-panzoom/cytoscape.js-panzoom.css",
        "/js/cytoscape-qtip/cytoscape-qtip.js",
        "/css/d3-tip/d3-tip.css",
        "/js/zxcvbn-async/zxcvbn-async.min.js",
        "/js/javascript-twitter-post-fetcher/js/twitterFetcher_min.js",
        "/js/DataTables/images/sort_asc_disabled.png",
        "/js/DataTables/images/sort_desc_disabled.png",
        "/js/shapiro-wilk/shapiro-wilk.js",
    ]

    print("Checking links")
    for link in js_files:
        verify_static_file(host+link)
