import re
import requests
import urllib3
import os
import logging

from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
from urllib.parse import urljoin


PORT = os.environ.get("PORT", "5004")


def test_link(link, strict=True):
    print(f"link testing {link}")
    results = None
    try:

        results = requests.get(link, verify=False, timeout=10)

    except Exception as e:
        if strict:
            raise SystemExit(
                "The link does not exists or is wrongly formatted")
        else:
            logging.error(f"FAILED:{link} does not exists or is wrongly formatted")

    status_code = results.status_code if results is not None else "404"

    print(f'the link {link} ---> {status_code}')


def fetch_css_links(parsed_page):
    print("fetching css links")
    for link in parsed_page.findAll("link"):
        full_path = None

        link_url = link.attrs.get("href")
        if re.match(r"^http://", link_url):
            pass
            # not sure whether to raise an error here for external css links

        elif re.match(r"^/css", link_url) or re.match(r"^/js", link_url):
            full_path = urljoin('http://localhost:5004/', link_url)

        if full_path is not None:
            test_link(full_path)


def fetch_html_links(parsed_page):
    print("fetching a tags ")

    for link in parsed_page.findAll("a"):
        full_path = None
        link_url = link.attrs.get("href")
        if re.match(r"^/", link_url):
            full_path = urljoin('http://localhost:5004/', link_url)

        elif re.match(r'^http://', link_url):
            full_path = link_url

        if full_path is not None:
            test_link(full_path)


def fetch_script_tags(parsed_page):
    print("--->fetching js links")
    for link in parsed_page.findAll("script"):
        js_link = link.attrs.get("src")
        if js_link is not None:
            if re.match(r'^http://', js_link):
                raise SystemExit("Failed,the library should be packaged in guix.\
                                Please contact,http://genenetwork.org/ for more details")

            elif re.match(r"^/css", js_link) or re.match(r"^/js", js_link):
                full_path = urljoin('http://localhost:5004/', js_link)
                test_link(full_path)


def fetch_page_links(page_url):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    html_page = uReq(page_url)
    parsed_page = soup(html_page, "html.parser")

    fetch_script_tags(parsed_page=parsed_page)
    fetch_css_links(parsed_page=parsed_page)
    fetch_html_links(parsed_page=parsed_page)


fetch_page_links(f"http://localhost:{PORT}/")
