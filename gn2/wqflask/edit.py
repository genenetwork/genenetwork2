import requests
import subprocess

from urllib.parse import urljoin
from pathlib import Path
from gn2.wqflask.oauth2.session import session_info

from pymonad.either import Either, Left, Right

from flask import (Blueprint,
                   flash,
                   redirect,
                   render_template,
                   request)

from gn2.wqflask.oauth2.checks import require_oauth2
from gn2.wqflask.oauth2.checks import require_oauth2_edit_resource_access


metadata = Blueprint("metadata", __name__)


def __run_cmd__(cmd) -> Either:
    """Run a given command and return it's results as an Either monad"""
    _result = ""
    try:
        _result = subprocess.run(
            cmd, capture_output=True
        )
    except Exception as e_:
        return Left({
            "command": cmd,
            "error": str(e_),
        })
    if _result.stderr:
        return Left({
            "command": cmd,
            "error": _result.stderr.decode()
        })
    return Right(_result.stdout)


def save_dataset_metadata(
        git_dir: str, output: str,
        author: str, content: str, msg: str
) -> Either:
    """Save dataset metadata to git"""
    def __write__():
        try:
            with Path(output).open(mode="w") as f_:
                f_.write(content)
                return Right(0)
        except Exception as e_:
            return Left({
                "command": "Writing to File",
                "error": str(e_)
            })

    return (
        __run_cmd__(f"git -C {git_dir} reset --hard origin".split(" "))
        .then(lambda _: __run_cmd__(f"git -C {git_dir} pull".split(" ")))
        .then(lambda _: __write__())
        .then(lambda _: __run_cmd__(f"git -C {git_dir} add .".split(" ")))
        .then(lambda _: __run_cmd__(
            f"git -C {git_dir} commit -m".split(" ") + [
                f'{msg}', f"--author='{author}'", "--no-gpg-sign"
            ]))
        .then(lambda _: __run_cmd__(f"git -C {git_dir} \
push origin master --dry-run".split(" ")))
    )


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
            return redirect(
                f"/datasets/{_name}"
            )


@metadata.route("/save", methods=["POST"])
@require_oauth2_edit_resource_access
@require_oauth2
def save():
    """Save dataset edits in git."""
    from gn2.utility.tools import get_setting
    _gn_docs = Path(
        get_setting("DATA_DIR"),
        "gn-docs"
    )
    # This maps the form elements to the actual path in the git
    # repository
    _map = {
        "description": "summary.rtf",
        "tissueInfo": "tissue.rtf",
        "specifics": "specifics.rtf",
        "caseInfo": "cases.rtf",
        "platformInfo": "platform.rtf",
        "processingInfo": "processing.rtf",
        "notes": "notes.rtf",
        "experimentDesignInfo": "experiment-design.rtf",
        "acknowledgement": "acknowledgement.rtf",
        "citation": "citation.rtf",
        "experimentType": "experiment-type.rtf",
        "contributors": "contributors.rtf"
    }
    _output = Path(
        _gn_docs,
        "general/datasets/",
        request.form.get("id").split("/")[-1],
        f"{_map.get(request.form.get('section'))}"
    )
    match request.form.get("type"):
        case "dcat:Dataset":
            _session = session_info()["user"]
            _author = f"{_session['name']} <{_session['email']}>"
            save_dataset_metadata(
                git_dir=_gn_docs,
                output=_output,
                author=_author,
                content=request.form.get("editor"),
                msg=request.form.get("edit-summary")
            ).either(
                lambda error: flash(
                    f"{error=}",
                    "error"
                ),
                lambda x: flash(
                    "Successfully updated data.",
                    "success"
                )
            )
    return redirect(
        f"/datasets/{request.form.get('label')}"
    )
