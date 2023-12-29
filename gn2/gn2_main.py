"""Main application entry point."""

from gn2.wqflask import app


from gn2.wqflask import docs
from gn2.wqflask import gsearch
from gn2.wqflask import db_info
from gn2.wqflask import user_login
from gn2.wqflask.api import router
from gn2.wqflask import user_session
from gn2.wqflask import group_manager
from gn2.wqflask import export_traits
from gn2.wqflask import search_results
from gn2.wqflask import resource_manager
from gn2.wqflask import update_search_results

import gn2.wqflask.views
import gn2.wqflask.partial_correlations_views
