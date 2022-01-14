from flask import Blueprint, render_template

jupyter_notebooks = Blueprint('jupyter_notebooks', __name__)

@jupyter_notebooks.route("/launcher", methods=("GET",))
def launcher():
    links = (
    {
        "main_url": "http://notebook.genenetwork.org/34301/notebooks/genenetwork-api-using-r.ipynb",
        "notebook_name": "R notebook showing how to query the GeneNetwork API.",
        "src_link_url": "https://github.com/jgarte/genenetwork-api-r-jupyter-notebook"},
    {
        "main_url": "http://notebook.genenetwork.org/57675/notebooks/genenetwork.ipynb",
        "notebook_name": "Querying the GeneNetwork API declaratively with python.",
        "src_link_url": "https://github.com/jgarte/genenetwork-jupyter-notebook-example"})

    return render_template("jupyter_notebooks.html", links=links)
