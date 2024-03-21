import requests
import subprocess

from urllib.parse import urljoin
from pathlib import Path
from gn2.wqflask.oauth2.session import session_info

from pymonad.tools import curry
from pymonad.either import Either, Left

from flask import (Blueprint,
                   flash,
                   redirect,
                   render_template,
                   request)

from gn2.wqflask.oauth2.checks import require_oauth2


metadata = Blueprint("metadata", __name__)


def save_dataset_metadata(
        git_dir: str, output: str,
        author: str, content: str, msg: str
) -> Either:
    """Save dataset metadata to git"""
    @curry(2)
    def __run_cmd(cmd, status_code):
        __result = subprocess.run(
            cmd, capture_output=True
        )
        if __result.stderr or status_code != 0:
            return Left({
                "command": cmd,
                "error": __result.stderr.decode()
            })
        return 0

    (Either.insert(0)
        .then(__run_cmd(f"git -C {git_dir} reset --hard origin".split(" ")))
        .then(__run_cmd(f"git -C {git_dir} pull".split(" "))))

    with Path(output).open(mode="w") as _f:
        _f.write(content)
    return (
        Either.insert(0)
        .then(__run_cmd(f"git -C {git_dir} add .".split(" ")))
        .then(__run_cmd(f"git -C {git_dir} commit -m".split(" ") + [
            f'{msg}', f"--author='{author}'", "--no-gpg-sign"
        ]))
        .then(__run_cmd(f"git -C {git_dir} \
push origin master --dry-run".split(" ")))
    )


@metadata.route("/edit")
@require_oauth2
def metadata_edit():
    from gn2.utility.tools import GN3_LOCAL_URL
    __name = request.args.get("name")
    match request.args.get("type"):
        case "dcat:Dataset":
            __metadata = requests.get(
                urljoin(
                    GN3_LOCAL_URL,
                    f"api/metadata/datasets/{ __name }"
                )
            ).json()
            __section = request.args.get("section")
            return render_template(
                "metadata/editor.html",
                name=__name,
                metadata=__metadata,
                section=__section,
                edit=__metadata.get(__section),
            )


@metadata.route("/save", methods=["POST"])
@require_oauth2
def save():
    from gn2.utility.tools import get_setting
    __gn_docs = Path(
        get_setting("DATA_DIR"),
        "gn-docs"
    )
    __map = {
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
    __output = Path(
        __gn_docs,
        "general/datasets/",
        request.form.get("id").split("/")[-1],
        f"{__map.get(request.form.get('section'))}"
    )
    match request.form.get("type"):
        case "dcat:Dataset":
            __session = session_info()["user"]
            __author = f"{__session['name']} <{__session['email']}>"
            save_dataset_metadata(
                git_dir=__gn_docs,
                output=__output,
                author=__author,
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
