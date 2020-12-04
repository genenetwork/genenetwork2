"""Markdown routes

Render pages from github, or if they are unavailable, look for it else where
"""
import requests
import markdown

from flask import Blueprint
from flask import render_template

glossary_blueprint = Blueprint('glossary_blueprint', __name__)
references_blueprint = Blueprint("references_blueprint", __name__)
environments_blueprint = Blueprint("environments_blueprint", __name__)
links_blueprint = Blueprint("links_blueprint", __name__)
policies_blueprint = Blueprint("policies_blueprint", __name__)
facilities_blueprint = Blueprint("facilities_blueprint", __name__)


def render_markdown(file_name):
    """Try to fetch the file name from Github and if that fails, try to
look for it inside the file system """
    github_url = ("https://raw.githubusercontent.com/"
                  "genenetwork/gn-docs/master/")

    md_content = requests.get(f"{github_url}{file_name}")
    if md_content.status_code == 200:

        return markdown.markdown(md_content.content.decode("utf-8"), extensions=['tables'])
    # TODO: Add fallback on our git server by checking the mirror.
    # Content not available
    return (f"\nContent for {file_name} not available. "
            "Please check "
            "(here to see where content exists)"
            "[https://github.com/genenetwork/gn-docs]. "
            "Please reach out to the gn2 team to have a look at this")


@glossary_blueprint.route('/')
def glossary():
    return render_template(
        "glossary.html",
        rendered_markdown=render_markdown("general/glossary/glossary.md")), 200


@references_blueprint.route('/')
def references():
    return render_template(
        "references.html",
        rendered_markdown=render_markdown("general/references/references.md")), 200


@environments_blueprint.route("/")
def environments():
    return render_template("environment.html", rendered_markdown=render_markdown("general/environments/environments.md")), 200


@links_blueprint.route("/")
def links():
    return render_template(
        "links.html",
        rendered_markdown=render_markdown("general/links/links.md")), 200


@policies_blueprint.route("/")
def policies():
    return render_template(
        "policies.html",
        rendered_markdown=render_markdown("general/policies/policies.md")), 200


@facilities_blueprint.route("/")
def facilities():
    return render_template("facilities.html", rendered_markdown=render_markdown("general/help/facilities.md")), 200
