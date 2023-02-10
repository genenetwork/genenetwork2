"""Routes for the OAuth2 auth system in GN3"""
from flask import Blueprint

from .data import data
from .users import users
from .roles import roles
from .groups import groups
from .toplevel import toplevel
from .resources import resources

oauth2 = Blueprint("oauth2", __name__, template_folder="templates/oauth2")

oauth2.register_blueprint(toplevel, url_prefix="/")
oauth2.register_blueprint(data, url_prefix="/data")
oauth2.register_blueprint(users, url_prefix="/user")
oauth2.register_blueprint(roles, url_prefix="/role")
oauth2.register_blueprint(groups, url_prefix="/group")
oauth2.register_blueprint(resources, url_prefix="/resource")
