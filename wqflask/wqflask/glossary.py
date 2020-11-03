from flask import Blueprint
from flask import render_template

glossary_blueprint = Blueprint('glossary_blueprint', __name__)


@glossary_blueprint.route('/')
def glossary():
    return render_template("glossary.html"), 200
