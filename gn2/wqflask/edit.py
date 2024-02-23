import requests
import subprocess

from pathlib import Path

from pymonad.either import Either, Left

from flask import (Blueprint,
                   flash,
                   redirect,
                   render_template,
                   request)

from gn2.wqflask.decorators import login_required


metadata = Blueprint("metadata", __name__)


def save_dataset_metadata(
        git_dir: str, output: str,
        content: str, msg: str
) -> Either:
    """Save dataset metadata to git"""
    def __run_cmd(cmd, status_code):
        __result = subprocess.run(
            cmd.split(" "), shell=True,
            capture_output=True
        )
        if __result.stderr or status_code != 0:
            return Left({
                "command": cmd,
                "error": __result.stderr.decode()
            })
        return 0

    with Path(output) as _f:
        _f.write(content)

    return (
        Either.insert(0)
        .then(__run_cmd(f"git -C {git_dir} pull"))
        .then(__run_cmd(f"git -C {git_dir} add ."))
        .then(__run_cmd(f"git -C {git_dir} commit --all --message {msg}"))
        .then(__run_cmd(f"git -C {git_dir} push origin master --dry-run"))
    )


@metadata.route("/edit")
@login_required(pagename="Dataset Metadata Editing")
def metadata_edit():
    from gn2.utility.tools import GN3_LOCAL_URL
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
    from gn2.utility.tools import get_setting
    __gn_docs = Path(
        get_setting("DATA_DIR"),
        "gn-docs"
    )
    __output = Path(
        __gn_docs,
        "general/datasets/",
        request.form.get("id").split("/")[-1]
    )
    match request.form.get("type"):
        case "dcat:Dataset":
            save_dataset_metadata(
                git_dir=__gn_docs,
                output=__output,
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
        Path("/datasets", request.form.get('label'))
    )
