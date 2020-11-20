"""Markdown routes

Render pages from github, or if they are unavailable, look for it else where
"""
import os
import requests
import mistune

from flask import Blueprint
from flask import render_template

glossary_blueprint = Blueprint('glossary_blueprint', __name__)


def render_markdown(file_name):
    """Try to fetch the file name from Github and if that fails, try to
look for it inside the file system

    """
    github_url = ("https://raw.githubusercontent.com/"
                  "genenetwork/gn-docs/master/")
    md_content = requests.get(f"{github_url}{file_name}")
    if md_content.status_code == 200:
        return mistune.html(md_content.content.decode("utf-8"))

    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           f"static/markdown/{file_name}")) as md_file:
        markdown = md_file.read()
        return mistune.html(markdown)


@glossary_blueprint.route('/')
def glossary():
    return render_template(
        "glossary.html",
        rendered_markdown=render_markdown("glossary.md")), 200
