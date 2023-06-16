"""
Set up the package's top-level objects.
"""
from flask import Blueprint

from . import router as router

api_bp = Blueprint("api", __name__)
api_bp.register_blueprint(router.pre1_router)
