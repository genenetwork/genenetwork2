"""Application entry-point module"""

from wqflask import app

from base import trait
from wqflask import views
from wqflask import collect
from wqflask.api import router
from wqflask import user_login
from wqflask import user_session
from wqflask import partial_correlations_views
