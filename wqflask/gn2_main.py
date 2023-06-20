"""Main application entry point."""

from wqflask import app


from wqflask import docs
from wqflask import gsearch
from wqflask import db_info
from wqflask import user_login
from wqflask.api import router
from wqflask import user_session
from wqflask import group_manager
from wqflask import export_traits
from wqflask import search_results
from wqflask import resource_manager
from wqflask import update_search_results

import wqflask.views
import wqflask.partial_correlations_views
