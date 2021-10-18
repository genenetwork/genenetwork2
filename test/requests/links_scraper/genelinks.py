import re
import requests
import urllib3
import os

from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
from urllib.parse import urljoin
from urllib.parse import urlparse


PORT = os.environ.get("PORT", "5004")
TEMPLATE_PATH = "../wqflask/wqflask/templates"

BROKEN_LINKS = set()


def search_templates():
    """searches for broken links in templates"""
    html_parsed_pages = []
    for subdir, dirs, files in os.walk(TEMPLATE_PATH):
        for file in files:
            file_path = os.path.join(subdir, file)
            if file_path.endswith(".html"):
                parsed_page = soup(
                    open(file_path, encoding="utf8"), "html.parser")
                html_parsed_pages.append(parsed_page)
    return html_parsed_pages


def is_valid_link(url_link):
    try:
        result = urlparse(url_link)
        return all([result.scheme, result.netloc, result.path])
    except Exception:
        return False


def test_link(link):
    print(f'Checking -->{link}')
    results = None
    try:
        results = requests.get(link, verify=False, timeout=10)
        status_code = results.status_code
    except Exception:
        status_code = 408
    return int(status_code) > 403


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
                raise SystemExit("Failed,the library should be "
                                 "packaged in guix. "
                                 "Please contact, "
                                 "http://genenetwork.org/ "
                                 "for more details")

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
    pages = [f"http://localhost:{PORT}/"]
    return pages


if __name__ == '__main__':
    for page in webpages_to_check():
        fetch_page_links(page)
        if len(BROKEN_LINKS) > 0:
            print("THE LINKS BELOW ARE BROKEN>>>>>>>>>>>>>")
            for link in BROKEN_LINKS:
                print(link)

    if len(BROKEN_LINKS) > 0:
        raise SystemExit(
            "The links Above are broken. "
            "Please contact genenetwork.org<<<<<<<<")
