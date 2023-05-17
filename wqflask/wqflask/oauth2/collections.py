"""Functions for collections."""
from .session import session_info
from .checks import user_logged_in
from .client import oauth2_get, no_token_get

def num_collections() -> int:
    """Compute the number of collections available for tte current sussion."""
    anon_id = session_info()["anon_id"]
    all_collections = no_token_get(
        f"oauth2/user/collections/{anon_id}/list").either(
            lambda _err: [], lambda colls: colls)
    if user_logged_in():
        all_collections = all_collections + oauth2_get(
            "oauth2/user/collections/list").either(
                lambda _err: [], lambda colls: colls)
    return len(all_collections)
