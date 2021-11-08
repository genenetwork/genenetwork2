from Flask import BluePrint, render_template

jupyter_notebooks = Blueprint('jupyter_notebooks', __name__)

@jupyter_notebooks.route("/jupyter-notebooks-launcher", methods=("GET",))
def jupyter_notebooks_launcher():
    links = (
    {
        "main_url": "http://notebook.genenetwork.org/51091/tree?",
        "notebook_name": "COVID-19 in mybinder.org federation",
        "src_link_url": "https://github.com/jgarte/covid19_in_binder"},
    {
        "main_url": "http://notebook.genenetwork.org/35639/tree?",
        "notebook_name": "Simple requirements.txt based example",
        "src_link_url": "https://github.com/jgarte/requirements"},
    {
        "main_url": "http://notebook.genenetwork.org/40733/tree?",
        "notebook_name": "Guile Jupyter Notebook Querying GeneNetwork API",
        "src_link_url": "https://github.com/jgarte/guile-notebook-genenetwork-api"})

    return render_template("jupyter_notebooks.html", links=links)
