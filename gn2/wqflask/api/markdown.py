"""Markdown routes

Render pages from github, or if they are unavailable, look for it else where
"""

import requests
import markdown
import os
import sys
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup  # type: ignore

from flask import send_from_directory
from flask import Blueprint
from flask import render_template

from typing import Dict
from typing import List

glossary_blueprint = Blueprint('glossary_blueprint', __name__)
references_blueprint = Blueprint("references_blueprint", __name__)
environments_blueprint = Blueprint("environments_blueprint", __name__)
links_blueprint = Blueprint("links_blueprint", __name__)
policies_blueprint = Blueprint("policies_blueprint", __name__)
facilities_blueprint = Blueprint("facilities_blueprint", __name__)
news_blueprint = Blueprint("news_blueprint", __name__)
xapian_syntax_blueprint = Blueprint("xapian_syntax_blueprint", __name__)

blogs_blueprint = Blueprint("blogs_blueprint", __name__)
gn_docs_blueprint = Blueprint("gn_docs_blueprint", __name__)


def fetch_raw_markdown(file_path):
    """
    This method fetches files from genenetwork:gn docs repo
    """
    # todo remove hardcoded file path
    safe_query = urllib.parse.urlencode({"file_path": file_path})
    response = requests.get(
        f"http://localhost:8091/edit?{safe_query}")
    response.raise_for_status()
    return response.json()


def render_markdown_as_html(content):
    """This method converts markdown to html for render"""
    return markdown.markdown(content, extensions=["tables"])


def render_markdown(file_name, is_remote_file=True):
    """Try to fetch the file name from Github and if that fails, try to
look for it inside the file system """
    github_url = ("https://raw.githubusercontent.com/"
                  "genenetwork/gn-docs/master/")

    if not is_remote_file:
        text = ""
        with open(file_name, "r", encoding="utf-8") as input_file:
            text = input_file.read()
        return markdown.markdown(text,
                                 extensions=['tables'])

    md_content = requests.get(f"{github_url}{file_name}")

    if md_content.status_code == 200:
        return markdown.markdown(md_content.content.decode("utf-8"),
                                 extensions=['tables'])

    return (f"\nContent for {file_name} not available. "
            "Please check "
            "(here to see where content exists)"
            "[https://github.com/genenetwork/gn-docs]. "
            "Please reach out to the gn2 team to have a look at this")


def get_file_from_python_search_path(pathname_suffix):
    cands = [os.path.join(d, pathname_suffix) for d in sys.path]
    try:
        return list(filter(os.path.exists, cands))[0]
    except IndexError:
        return None


def get_blogs(user: str = "genenetwork",
              repo_name: str = "gn-docs") -> dict:

    blogs: Dict[int, List] = {}
    github_url = f"https://api.github.com/repos/{user}/{repo_name}/git/trees/master?recursive=1"

    repo_tree = requests.get(github_url).json()["tree"]

    for data in repo_tree:
        path_name = data["path"]
        if path_name.startswith("blog") and path_name.endswith(".md"):
            split_path = path_name.split("/")[1:]
            try:
                year, title, file_name = split_path
            except Exception as e:
                year, file_name = split_path
                title = ""

            subtitle = os.path.splitext(file_name)[0]

            blog = {
                "title": title,
                "subtitle": subtitle,
                "full_path": path_name
            }

            if year in blogs:
                blogs[int(year)].append(blog)
            else:
                blogs[int(year)] = [blog]

    return dict(sorted(blogs.items(), key=lambda x: x[0], reverse=True))


@glossary_blueprint.route('/')
def glossary():
    file_data = fetch_raw_markdown(file_path="general/glossary/glossary.md")
    return render_template(
        "generic_gn_docs.html",
        rendered_markdown=render_markdown_as_html(file_data["content"]),
        file_path=file_data["file_path"],
        file_title=Path(file_data["file_path"]).stem
    )


@references_blueprint.route('/')
def references():

    file_data = fetch_raw_markdown(
        file_path="general/references/references.md")
    return render_template(
        "generic_gn_docs.html",
        rendered_markdown=render_markdown_as_html(file_data["content"]),
        file_path=file_data["file_path"],
        file_title=Path(file_data["file_path"]).stem
    )


@news_blueprint.route('/')
def news():
    file_data = fetch_raw_markdown(file_path="general/news/news.md")
    return render_template(
        "generic_gn_docs.html",
        render_markdown=render_markdown_as_html(file_data["content"]),
        file_path=file_data["file_path"],
        file_title=Path(file_data["file_path"]).stem
    )


@xapian_syntax_blueprint.route('/')
def xapian():
    file_data = fetch_raw_markdown(file_path="general/search/xapian_syntax.md")
    return render_template(
        "generic_gn_docs.html",
        rendered_markdown=render_markdown_as_html(file_data["content"]),
        file_path=file_data["file_path"],
        file_title=Path(file_data["file_path"]).stem
    )


@environments_blueprint.route("/")
def environments():

    md_file = get_file_from_python_search_path("wqflask/DEPENDENCIES.md")
    svg_file = get_file_from_python_search_path(
        "wqflask/dependency-graph.html")
    svg_data = None
    if svg_file:
        with open(svg_file, 'r') as f:
            svg_data = "".join(
                BeautifulSoup(f.read(),
                              'lxml').body.script.contents)

    if md_file is not None:
        return (
            render_template("environment.html",
                            svg_data=svg_data,
                            rendered_markdown=render_markdown(
                                md_file,
                                is_remote_file=False)),
            200
        )
    # Fallback: Fetch file from server
    file_data = fetch_raw_markdown(
        file_path="general/environments/environments.md")
    return (render_template(
        "environment.html",
        svg_data=None,
        rendered_markdown=render_markdown_as_html(file_data["content"])))


@environments_blueprint.route('/svg-dependency-graph')
def svg_graph():
    directory, file_name, _ = get_file_from_python_search_path(
        "wqflask/dependency-graph.svg").partition("dependency-graph.svg")
    return send_from_directory(directory, file_name)


@links_blueprint.route("/")
def links():
    file_data = fetch_raw_markdown(file_path="general/links/links.md")
    return render_template(
        "generic_gn_docs.html",
        rendered_markdown=render_markdown_as_html(file_data["content"]),
        file_path=file_data["file_path"],
        file_title=Path(file_data["file_path"]).stem
    )


@policies_blueprint.route("/")
def policies():
    file_data = fetch_raw_markdown(file_path="general/policies/policies.md")
    return render_template(
        "generic_gn_docs.html",
        rendered_markdown=render_markdown_as_html(file_data["content"]),
        file_path=file_data["file_path"],
        file_title=Path(file_data["file_path"]).stem
    )


@facilities_blueprint.route("/")
def facilities():
    file_data = fetch_raw_markdown(file_path="general/help/facilities.md")
    return render_template("generic_gn_docs.html",
                           rendered_markdown=render_markdown_as_html(
                               file_data["content"]),
                           file_path=file_data["file_path"],
                           file_title=Path(file_data["file_path"]).stem
                           )


@blogs_blueprint.route("/<path:blog_path>")
def display_blog(blog_path):
    return render_template("blogs.html", rendered_markdown=render_markdown(blog_path))


@blogs_blueprint.route("/")
def blogs_list():
    blogs = get_blogs()

    return render_template("blogs_list.html", blogs=blogs)


@gn_docs_blueprint.errorhandler(requests.exceptions.HTTPError)
def page_not_found(error):
    """ Return error 404 """
    return {"Reason": error.response.reason,
            "error_status_code": error.response.status_code,
            "error_msg": error.response.text
            }
