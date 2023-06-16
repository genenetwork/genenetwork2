"""Main app creation module"""
import time

from flask import g, session, request

from wqflask import create_app
from wqflask.user_session import UserSession
from gn3.authentication import DataRole, AdminRole

app = create_app()

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

    token = session.get("oauth2_token", False)
    if token and not bool(session.get("user_details", False)):
        config = current_app.config
        client = OAuth2Session(
            config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
            token=token)
        resp = client.get(
            urljoin(config["GN_SERVER_URL"], "oauth2/user"))
        user_details = resp.json()
        session["user_details"] = user_details

        if user_details.get("error") == "invalid_token":
            flash(user_details["error_description"], "alert-danger")
            flash("You are now logged out.", "alert-info")
            session.pop("user_details", None)
            session.pop("oauth2_token", None)

@app.context_processor
def include_admin_role_class():
    return {'AdminRole': AdminRole}


@app.context_processor
def include_data_role_class():
    return {'DataRole': DataRole}

@app.before_request
def get_user_session():
    g.user_session = UserSession()
    # I think this should solve the issue of deleting the cookie and redirecting to the home page when a user's session has expired
    if not g.user_session:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('session_id_v2', '', expires=0)
        return response

@app.after_request
def set_user_session(response):
    if hasattr(g, 'user_session'):
        if not request.cookies.get(g.user_session.cookie_name):
            response.set_cookie(g.user_session.cookie_name,
                                g.user_session.cookie)
    else:
        response.set_cookie('session_id_v2', '', expires=0)
    return response
