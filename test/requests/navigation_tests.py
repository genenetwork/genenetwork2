import re
import requests
from lxml.html import parse

def check_navigation(args_obj, parser):
    print("")
    print("Checking navigation.")

    host = args_obj.host
    url = host + "/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P"
    print("URL: ", url)
    page = requests.get(url)
    # Page is built by the javascript, hence using requests fails for this.
    # Investigate use of selenium maybe?
