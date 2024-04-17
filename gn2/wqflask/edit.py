import uuid
import requests
import subprocess
import time

from urllib.parse import urljoin
from pathlib import Path

from gn2.wqflask.oauth2.client import oauth2_get
from gn2.wqflask.oauth2.session import session_info
from gn2.wqflask.oauth2.tokens import JWTToken

from pymonad.either import Either, Left, Right

from flask import (Blueprint,
                   flash,
                   redirect,
                   render_template,
                   request)

from gn2.wqflask.oauth2.checks import require_oauth2
from gn2.wqflask.oauth2.checks import require_oauth2_edit_resource_access


metadata = Blueprint("metadata", __name__)


@metadata.route("/edit")
@require_oauth2_edit_resource_access
@require_oauth2
def metadata_edit():
    """Endpoint that provides editing functionality for datasets."""
    from gn2.utility.tools import GN3_LOCAL_URL
    _name = request.args.get("name")
    match request.args.get("type"):
        case "dcat:Dataset":
            _metadata = requests.get(
                urljoin(
                    GN3_LOCAL_URL,
                    f"api/metadata/datasets/{ _name }"
                )
            ).json()
            _section = request.args.get("section")
            return render_template(
                "metadata/editor.html",
                name=_name,
                metadata=_metadata,
                section=_section,
                edit=_metadata.get(_section),
            )
        case _:
            return redirect(f"/datasets/{_name}")


@metadata.route("/save", methods=["POST"])
@require_oauth2_edit_resource_access
@require_oauth2
def save():
    """Save dataset edits in git."""
    from gn2.utility.tools import get_setting
    from gn2.utility.tools import GN3_LOCAL_URL
    # Call an endpoint to GN3 with special headers
    name = request.form.get('label')
    metadata = requests.get(
                urljoin(
                    GN3_LOCAL_URL,
                    f"api/metadata/datasets/{name}")).json()
    _session = session_info()["user"]
    outgoing_url = urljoin(
        GN3_LOCAL_URL,
        "api/metadata/datasets/edit")
    iat = int(time.time())
    exp = iat + 300  # Expire after 300 seconds
    token = JWTToken(
        key=get_setting("JWT_SECRET_KEY"),
        registered_claims={
            "iat": iat,
            "iss": request.url,
            "sub": request.form.get("label"),
            "aud": outgoing_url,
            "exp": exp,
            "jti": str(uuid.uuid4())},
        private_claims={
            "account-name": _session["name"],
            "email": _session['email'],
            "account-roles": oauth2_get(
                f"auth/resource/authorisation\
/{metadata.get('id', '').split('/')[-1]}"
            ).either(
                lambda err: {"roles": []},
                lambda val: val)})
    response = requests.post(
        outgoing_url,
        data=request.form,
        headers=token.bearer_token)
    if response.status_code == 201:
        flash("Unable to update data", "alert-danger")
    else:
        flash("Successfully updated data", "success")
    # Make a request to GN3 save endpoint
    return redirect(f"/datasets/{name}")
