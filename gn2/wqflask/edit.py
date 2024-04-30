import uuid
import requests
import time

from urllib.parse import urljoin

from gn2.wqflask.oauth2.client import oauth2_get
from gn2.wqflask.oauth2.session import session_info
from gn2.wqflask.oauth2.tokens import JWTToken

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
    from gn2.utility.tools import GN3_LOCAL_URL
    # Call an endpoint to GN3 with special headers
    name = request.form.get('label')
    metadata = requests.get(
                urljoin(
                    GN3_LOCAL_URL,
                    f"api/metadata/datasets/{name}")).json()
    headers = oauth2_get(
        f"auth/resource/authorisation/{metadata.get('label')}",
        jsonify_p=True
    ).either(
        lambda err: {},
        lambda val: {"Authorization": val.headers.get("Authorization", "")}
    )
    response = requests.post(
        urljoin(GN3_LOCAL_URL, "api/metadata/datasets/edit"),
        data=request.form,
        headers=headers)
    if response.status_code == 201:
        flash("Unable to update data", "alert-danger")
    else:
        flash("Successfully updated data", "success")
    # Make a request to GN3 save endpoint
    return redirect(f"/datasets/{name}")
