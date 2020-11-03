from flask import Blueprint


glossary_blueprint = Blueprint('glossary_blueprint', __name__)


@glossary_blueprint.route('/')
def glossary():
    return "This is a test", 200
