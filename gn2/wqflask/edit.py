import requests

from pathlib import Path

from flask import (Blueprint,
                   redirect,
                   render_template,
                   request)

from gn2.wqflask.decorators import login_required
from gn2.utility.tools import GN3_LOCAL_URL


metadata = Blueprint("metadata", __name__)


@metadata.route("/edit")
@login_required(pagename="Dataset Metadata Editing")
def metadata_edit():
    match request.args.get("type"):
        case "dcat:Dataset":
            metadata = requests.get(
                Path(
                    GN3_LOCAL_URL,
                    "metadata/datasets/",
                    (_name := request.args.get("name"))
                ).as_posix()
            ).json()
            __section = request.args.get("section")
            return render_template(
                "metadata/editor.html",
                name=_name,
                metadata=metadata,
                section=__section,
                edit=metadata.get(__section),
            )


@metadata.route("/save", methods=["POST"])
@login_required(pagename="Dataset Metadata Editing")
def save():
    __content = request.form.get("editor")
    __summary = request.form.get("summary")
    __type = request.form.get("type")
    match __type:
        case "dcat:Dataset":
            # XXX: TODO: Method for saving data
            return redirect(f"/datasets/{request.form.get('label')}")
