"""Authentication endpoints."""
import uuid
import datetime
from urllib.parse import urljoin, urlparse, urlunparse

from authlib.jose import jwt, KeySet
from flask import (flash,
                   request,
                   url_for,
                   jsonify,
                   redirect,
                   Blueprint,
                   render_template,
                   current_app as app)

from . import session
from .checks import require_oauth2
from .request_utils import user_details, process_error
from .client import (
    SCOPE, no_token_post, user_logged_in, authserver_uri, oauth2_clientid)

toplevel = Blueprint("toplevel", __name__)

@toplevel.route("/register-client", methods=["GET", "POST"])
@require_oauth2
def register_client():
    """Register an OAuth2 client."""
    return "USER IS LOGGED IN AND SUCCESSFULLY ACCESSED THIS ENDPOINT!"


@toplevel.route("/code", methods=["GET"])
def authorisation_code():
    """Use authorisation code to get token."""
    code = request.args.get("code", "")
    if bool(code):
        base_url = urlparse(request.base_url, scheme=request.scheme)
        jwtkey = app.config["SSL_PRIVATE_KEY"]
        issued = datetime.datetime.now()
        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "code": code,
            "scope": SCOPE,
            "redirect_uri": urljoin(
                urlunparse(base_url),
                url_for("oauth2.toplevel.authorisation_code")),
            "assertion": jwt.encode(
                header={
                    "alg": "RS256",
                    "typ": "jwt",
                    "kid": jwtkey.as_dict()["kid"]},
                payload={
                    "iss": str(oauth2_clientid()),
                    "sub": request.args["user_id"],
                    "aud": urljoin(authserver_uri(), "auth/token"),
                    "exp": (issued + datetime.timedelta(minutes=5)).timestamp(),
                    "nbf": int(issued.timestamp()),
                    "iat": int(issued.timestamp()),
                    "jti": str(uuid.uuid4())},
                key=jwtkey).decode("utf8"),
            "client_id": app.config["OAUTH2_CLIENT_ID"]
        }

        def __error__(error):
            flash(f"{error['error']}: {error['error_description']}",
                  "alert-danger")
            app.logger.debug("Request error (%s) %s: %s",
                             error["status_code"], error["error_description"],
                             request_data)
            return redirect("/")

        def __success__(token):
            session.set_user_token(token)
            udets = user_details()
            session.set_user_details({
                "user_id": uuid.UUID(udets["user_id"]),
                "name": udets["name"],
                "email": udets["email"],
                "token": session.user_token(),
                "logged_in": True
            })
            return redirect("/")

        return no_token_post(
            "auth/token", json=request_data).either(
                lambda err: __error__(process_error(err)), __success__)
    flash("AuthorisationError: No code was provided.", "alert-danger")
    return redirect("/")


@toplevel.route("/public-jwks", methods=["GET"])
def public_jwks():
    """Provide endpoint that returns the public keys."""
    return jsonify({
        "documentation": "Returns a static key for the time being. This will change.",
        "jwks": KeySet([app.config["SSL_PRIVATE_KEY"]]).as_dict().get("keys")
    })
