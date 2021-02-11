import re
import requests
import urllib3
import os
import logging

from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
from urllib.parse import urljoin
from urllib.parse import urlparse


PORT = os.environ.get("PORT", "5004")

BROKEN_LINKS = set()


def is_valid_link(url_link):
    try:
        result = urlparse(url_link)
        return all([result.scheme, result.netloc, result.path])
    except Exception as e:
        return False


def test_link(link):
    print(f'Checking -->{link}')
    results = None
    try:

        results = requests.get(link, verify=False, timeout=10)
        status_code = results.status_code

    except Exception as e:
        status_code = 408

    if int(status_code) > 403:
        return True

    return False


def fetch_css_links(parsed_page):
    print("fetching css links")
    for link in parsed_page.findAll("link"):
        full_path = None

        link_url = link.attrs.get("href")
        if is_valid_link(link_url):
            full_path = link_url

        elif re.match(r"^/css", link_url) or re.match(r"^/js", link_url):
            full_path = urljoin('http://localhost:5004/', link_url)

        if full_path is not None:
            if test_link(full_path):
                BROKEN_LINKS.add(full_path)


def fetch_html_links(parsed_page):
    print("fetching a tags ")

    for link in parsed_page.findAll("a"):
        full_path = None
        link_url = link.attrs.get("href")
        if re.match(r"^/", link_url):
            full_path = urljoin('http://localhost:5004/', link_url)

        elif is_valid_link(link_url):
            full_path = link_url

        if full_path is not None:
            if test_link(full_path):
                BROKEN_LINKS.add(full_path)


def fetch_script_tags(parsed_page):
    print("--->fetching js links")
    for link in parsed_page.findAll("script"):
        js_link = link.attrs.get("src")
        if js_link is not None:
            if is_valid_link(js_link):
                raise SystemExit("Failed,the library should be packaged in guix.\
                                Please contact,http://genenetwork.org/ for more details")

            elif re.match(r"^/css", js_link) or re.match(r"^/js", js_link):
                full_path = urljoin('http://localhost:5004/', js_link)
                if test_link(full_path):
                    BROKEN_LINKS.add(full_path)


def fetch_page_links(page_url):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    html_page = uReq(page_url)
    parsed_page = soup(html_page, "html.parser")

    fetch_script_tags(parsed_page=parsed_page)
    fetch_css_links(parsed_page=parsed_page)
    fetch_html_links(parsed_page=parsed_page)


def webpages_to_check():
    pages = [

        "http://localhost:/5004",






    ]

    return pages


if __name__ == '__main__':
    for page in webpages_to_check():
        fetch_page_links(f"http://localhost:{PORT}/")
        if BROKEN_LINKS is not None:
            print("THE LINKS BELOW ARE BROKEN>>>>>>>>>>>>>")
            for link in BROKEN_LINKS:
                print(link)

            raise SystemExit(
                "The links Above are broken.Please contact genenetwork.org<<<<<<<<")
