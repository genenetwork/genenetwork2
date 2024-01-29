import requests
from lxml.html import document_fromstring
from link_checker import check_page


def check_home(url):
    results = requests.get(url)
    doc = document_fromstring(results.text)
    search_button = doc.cssselect("#btsearch")
    assert("Search" in ''.join(search_button[0].text_content()))
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
    found = result.text.find("records found")
    assert(found >= 0)
    assert(result.status_code == 200)
    print("OK")
    check_traits_page(host, ("/show_trait?trait_id=1435395_"
                             "s_at&dataset=HC_M2_0606_P"))


def check_traits_page(host, traits_url):
    results = requests.get(host+traits_url)
    doc = document_fromstring(results.text)
    traits_forms = doc.xpath('//form[@id="trait_data_form"]')

    assert len(traits_forms) > 0, "Traits' form not found!"
    assert len(traits_forms) == 1, "More than one form with the same ID"
    traits_form2 = traits_forms[0]

    assert(traits_form2.fields["corr_dataset"] == "HC_M2_0606_P")
    print("OK")
    check_page(host, host+traits_url)


def check_main_web_functionality(args_obj, parser):
    print("")
    print("Checking main web functionality...")
    host = args_obj.host
    check_home(host)
    check_search_page(host)
