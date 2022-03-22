from flask import Blueprint, render_template

jupyter_notebooks = Blueprint("jupyter_notebooks", __name__)


@jupyter_notebooks.route("/launcher", methods=("GET",))
def launcher():
    links = (
        {
            "main_url": "http://notebook.genenetwork.org/58965/notebooks/2020-05-08/solberg-rat-analysis.ipynb",
            "notebook_name": "Quantitative Genetics Tools for Mapping Trait Variation to Mechanisms, Therapeutics, and Interventions - Webinar Series",
            "src_link_url": "https://github.com/senresearch/quant-genetics-webinars",
        },
        {
            "main_url": "http://notebook.genenetwork.org/58163/notebooks/BXD%20Analysis.ipynb",
            "notebook_name": "This shows how to model BXD mouse weight data using an AR(1) process.",
            "src_link_url": "https://github.com/BonfaceKilz/tsaf-analysis-of-bxd-mouse-colonies",
        },
        {
            "main_url": "http://notebook.genenetwork.org/46649/notebooks/genenetwork.ipynb",
            "notebook_name": "Querying the GeneNetwork API declaratively with python.",
            "src_link_url": "https://github.com/jgarte/genenetwork-jupyter-notebook-example",
        },
        {
            "main_url": "http://notebook.genenetwork.org/37279/notebooks/genenetwork-api-using-r.ipynb",
            "notebook_name": "R notebook showing how to query the GeneNetwork API.",
            "src_link_url": "https://github.com/jgarte/genenetwork-api-r-jupyter-notebook",
        },
    )

    return render_template("jupyter_notebooks.html", links=links)
