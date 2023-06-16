"""Top-Level routes."""
from flask import Blueprint

from .api import api_bp
# from .views import main_views
from base.trait import trait_bp
from .collect import collections_bp
from .partial_correlations_views import pcorrs_bp

# oauth2 = Blueprint("oauth2", __name__, template_folder="templates/oauth2")

toplevel = Blueprint("toplevel", __name__)

toplevel.register_blueprint(trait_bp)
toplevel.register_blueprint(pcorrs_bp)
# toplevel.register_blueprint(main_views)
toplevel.register_blueprint(collections_bp)

toplevel.register_blueprint(api_bp, url_prefix="/api")
