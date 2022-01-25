from flask import Blueprint, render_template

jupyter_notebooks = Blueprint("jupyter_notebooks", __name__)


@jupyter_notebooks.route("/launcher", methods=("GET",))
def launcher():
    links = requests.get("http://notebook.genenetwork.org/api")
    return render_template("jupyter_notebooks.html", links=links.json())
