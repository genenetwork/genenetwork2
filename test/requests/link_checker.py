from __future__ import print_function
import re
import requests
from lxml import html
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

def check_css_js_tags(args_obj):
    """Check all script and css tags in a page"""

    def flatten_list(l):
        return [y for x in l for y in x]

    host = args_obj.host
    pages_arr = [
        host,
        host+"/help",
        host+"/intro",
        host+"/submit_trait",
        host+"/help",
        host+"/references",
        host+"/tutorials",
        host+"/policies",
        host+"/links",
        host+"/environments",
        host+"/news",
        host+"/snp_browser",
        host+"/collections/list",
        host+"/repositories",
        host+"/n/login",
        host+"/snp_browser?first_run=true&species=mouse&gene_name=Atp5j2&limit_strains=on",
        host+"/credits",
        host+"/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P"
    ]

    trees_arr = [html.fromstring(requests.get(page, timeout=20, verify=False).content)
                 for page in pages_arr]

    links_arr = flatten_list(
        [tree.xpath('//script[@type="text/javascript"]/@src|link[@type="text/css"]/@href')
         for tree in trees_arr]
    )
    links = list(set([host+l if l[0] == '/' and l[1] != '/' else l
                      for l in links_arr]))  # Make links unique
    for l in links:
        if l[0:2] == '//':
            l = l.replace("//", "http://")
        assert requests.get(l).status_code == 200, ("Failed for: " + l)
        print(l + " ==> OK")

