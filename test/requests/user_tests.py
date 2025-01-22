"""Check for regressions in user-related features"""
import sys
import logging
from typing import Union

import requests
from lxml import etree
from lxml.etree import _Element as Element

def parse_form_from_html(html_text: str) -> Union[bool, Element]:
    """Return the user registration form, if it exists."""
    doc  = etree.HTML(html_text)
    form = doc.xpath("//form[@id='oauth2-register-user-form']")
    return len(form) == 1 and form[0]

def has_input_element(form: Element, xpath: str) -> bool:
    element = form.xpath(xpath)
    return len(element) == 1

def check_user_registration(host):
    _uri = f"{host}/oauth2/user/register"
    print(f"Checking user registration page: ({_uri}): ", end="\t")
    try:
        response = requests.get(_uri)
        form = parse_form_from_html(response.text)
        if (form != False) and  all([
                has_input_element(form, "//input[@id='user_name']"),
                has_input_element(form, "//input[@id='email_address']"),
                has_input_element(form, "//input[@id='password']"),
                has_input_element(form, "//input[@id='confirm_password']"),
                has_input_element(form, "//input[@id='submit']"),
        ]):
            print("Success.")
            return True
    except Exception as _exc:
        logging.error(f"An exception was raised while attempting to '{_uri}'.",
                      exc_info=True)

    print("Fail!")
    return False

def check_user_features(args, parser):
    """Check that user-related features are all working"""
    print("")
    print("Checking user features…")
    if not all([check_user_registration(args.host),]):
        sys.exit(1)
