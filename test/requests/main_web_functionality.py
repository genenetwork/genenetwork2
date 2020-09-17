import requests
from lxml.html import parse
from link_checker import check_page


def check_home(url):
    doc = parse(url).getroot()
    search_button = doc.cssselect("#btsearch")
    assert(search_button[0].value == "Search")
    print("OK")

def check_search_page(host):
    data = dict(
        species="mouse",
        group="BXD",
        type="Hippocampus mRNA",
        dataset="HC_M2_0606_P",
        search_terms_or="",
        search_terms_and="MEAN=(15 16) LRS=(23 46)")
    result = requests.get(host+"/search", params=data)
    found = result.text.find("records were found.")
    assert(found >= 0)
    assert(result.status_code == 200)
    print("OK")
    check_traits_page(host, ("/show_trait?trait_id=1435395_"
                             "s_at&dataset=HC_M2_0606_P"))


def check_traits_page(host, traits_url):
    doc = parse(host+traits_url).getroot()
    traits_form = doc.forms[1]
    assert(traits_form.fields["corr_dataset"] == "HC_M2_0606_P")
    print("OK")
    check_page(host, host+traits_url)


def check_main_web_functionality(args_obj, parser):
    print("")
    print("Checking main web functionality...")
    host = args_obj.host
    check_home(host)
    check_search_page(host)
