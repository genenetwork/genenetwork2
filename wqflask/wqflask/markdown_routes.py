"""Markdown routes

Render pages from github, or if they are unavailable, look for it else where
"""
import requests
import mistune

from flask import Blueprint
from flask import render_template

glossary_blueprint = Blueprint('glossary_blueprint', __name__)


@glossary_blueprint.route('/')
def glossary():
    markdown_url = ("https://raw.githubusercontent.com"
                    "/genenetwork/genenetwork2/"
                    "wqflask/wqflask/static"
                    "/glossary.md")
    md_content = requests.get(markdown_url)
    if md_content.status_code == 200:
        return render_template(
            "glossary_html",
            rendered_markdown=mistune.html(
                md_content.content.decode("utf-8"))), 200

    return render_template(
        "glossary.html",
        rendered_markdown=mistune.html("# Github Down!")), 200
