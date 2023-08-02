import re
import datetime
import json
import os

import logging
from pathlib import Path
from functools import reduce

from collections import namedtuple
from itertools import groupby
from typing import Dict

import difflib
import redis

from flask import Blueprint
from flask import Response
from flask import current_app
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from utility.json import CustomJSONEncoder

from wqflask.database import database_connection
from wqflask.decorators import login_required
from wqflask.decorators import required_access
from wqflask.decorators import edit_admins_access_required

from wqflask.oauth2 import client
from wqflask.oauth2 import session
from wqflask.oauth2.request_utils import flash_error, process_error

from gn3.authentication import AdminRole
from gn3.authentication import get_highest_user_access_role
from gn3.csvcmp import create_dirs_if_not_exists
from gn3.csvcmp import csv_diff
from gn3.csvcmp import extract_invalid_csv_headers
from gn3.csvcmp import remove_insignificant_edits
from gn3.db import diff_from_dict
from gn3.db import fetchall
from gn3.db import fetchone
from gn3.db import insert
from gn3.db import update
from gn3.db.datasets import retrieve_sample_list, retrieve_phenotype_group_name
from gn3.db.metadata_audit import (
    create_metadata_audit,
    fetch_probeset_metadata_audit_by_trait_name,
    fetch_phenotype_metadata_audit_by_dataset_id)
from gn3.db.phenotypes import Phenotype
from gn3.db.probesets import Probeset, probeset_mapping, fetch_probeset_metadata_by_name
from gn3.db.phenotypes import Publication
from gn3.db.phenotypes import PublishXRef
from gn3.db.phenotypes import (
    fetch_trait,
    fetch_metadata,
    update_publication,
    fetch_publication_by_id,
    fetch_publication_by_pubmed_id)
from gn3.db.sample_data import delete_sample_data
from gn3.db.sample_data import get_trait_sample_data, get_trait_csv_sample_data
from gn3.db.sample_data import insert_sample_data
from gn3.db.sample_data import update_sample_data


metadata_edit = Blueprint("metadata_edit", __name__)

def _get_diffs(diff_dir: str, redis_conn: redis.Redis):
    """Get all the diff details."""
    def __get_file_metadata(file_name: str) -> Dict:
        author, resource_id, time_stamp, *_ = file_name.split(".")
        try:
            author = json.loads(redis_conn.hget("users", author)).get(
               "full_name"
            )
        except (AttributeError, TypeError):
            author = author
        return {
            "resource_id": resource_id,
            "file_name": file_name,
            "author": author,
            "time_stamp": time_stamp
        }

    def __get_diff__(diff_dir: str, diff_file_name: str) -> dict:
        """Get the contents of the diff at `filepath`."""
        with open(Path(diff_dir, diff_file_name), encoding="utf8") as dfile:
            return json.loads(dfile.read().strip())

    return tuple({
        "filepath": Path(diff_dir, dname).absolute(),
        "meta": __get_file_metadata(file_name=dname),
        "diff": __get_diff__(diff_dir, dname)
    } for dname in os.listdir(diff_dir))


def edit_phenotype(conn, name, dataset_id):
    publish_xref = fetch_trait(conn, dataset_id=dataset_id, trait_name=name)
    return {
        "publish_xref": publish_xref,
        "phenotype": fetch_metadata(conn, publish_xref["phenotype_id"]),
        "publication": fetch_publication_by_id(conn, publish_xref["publication_id"])
    }


@metadata_edit.route("/<dataset_id>/traits/<name>")
@login_required(pagename="phenotype edit")
@required_access(
    ("group:resource:view-resource", "group:resource:edit-resource"))
def display_phenotype_metadata(dataset_id: str, name: str):
    from utility.tools import get_setting
    with database_connection(get_setting("SQL_URI")) as conn:
        _d = edit_phenotype(conn=conn, name=name, dataset_id=dataset_id)

        group_name = retrieve_phenotype_group_name(conn, dataset_id)
        sample_list = retrieve_sample_list(group_name)
        sample_data = get_trait_sample_data(conn, name, _d["publish_xref"]["phenotype_id"])

        return render_template(
            "edit_phenotype.html",
            sample_list = sample_list,
            sample_data = sample_data,
            publish_xref=_d.get("publish_xref"),
            phenotype=_d.get("phenotype"),
            publication=_d.get("publication"),
            dataset_id=dataset_id,
            name=name,
            resource_id=request.args.get("resource-id"),
            version=get_setting("GN_VERSION"),
            dataset_name=request.args["dataset_name"])


@metadata_edit.route("/traits/<name>")
@required_access(
    ("group:resource:view-resource", "group:resource:edit-resource"))
def display_probeset_metadata(name: str):
    from utility.tools import get_setting
    with database_connection(get_setting("SQL_URI")) as conn:
        _d = {"probeset": fetch_probeset_metadata_by_name(conn, name)}
        return render_template(
            "edit_probeset.html",
            diff=_d.get("diff"),
            probeset=_d.get("probeset"),
            name=name,
            resource_id=request.args.get("resource-id"),
            version=get_setting("GN_VERSION"),
            dataset_name=request.args["dataset_name"]
        )


@metadata_edit.route("/<dataset_id>/traits/<name>", methods=("POST",))
@login_required(pagename="phenotype update")
@required_access(
    ("group:resource:view-resource", "group:resource:edit-resource"))
def update_phenotype(dataset_id: str, name: str):
    from utility.tools import get_setting
    data_ = request.form.to_dict()
    TMPDIR = current_app.config.get("TMPDIR")
    author = session.session_info()["user"]["user_id"]
    phenotype_id = str(data_.get("phenotype-id"))
    if not (file_ := request.files.get("file")) and data_.get('edited') == "false":
        flash("No sample-data has been uploaded", "warning")
    else:
        create_dirs_if_not_exists(
            [
                SAMPLE_DATADIR := os.path.join(TMPDIR, "sample-data"),
                DIFF_DATADIR := os.path.join(SAMPLE_DATADIR, "diffs"),
                UPLOAD_DATADIR := os.path.join(SAMPLE_DATADIR, "updated"),
            ]
        )

        current_time = str(datetime.datetime.now().isoformat())
        _file_name = (
            f"{author}.{request.args.get('resource-id')}." f"{current_time}"
        )
        diff_data = {}
        with database_connection(get_setting("SQL_URI")) as conn:
            group_name = retrieve_phenotype_group_name(conn, dataset_id)
            sample_list = retrieve_sample_list(group_name)
            headers = ["Strain Name", "Value", "SE", "Count"]
            base_csv = get_trait_csv_sample_data(
                    conn=conn,
                    trait_name=str(name),
                    phenotype_id=str(phenotype_id),
                    sample_list=sample_list,
            )
            if not (file_) and data_.get('edited') == "true":
                delta_csv = create_delta_csv(base_csv, data_, sample_list)
                diff_data = remove_insignificant_edits(
                    diff_data=csv_diff(
                        base_csv=base_csv,
                        delta_csv=delta_csv,
                        tmp_dir=TMPDIR,
                    ),
                    epsilon=0.001,
                )
            else:
                diff_data = remove_insignificant_edits(
                    diff_data=csv_diff(
                        base_csv=base_csv,
                        delta_csv=(delta_csv := file_.read().decode()),
                        tmp_dir=TMPDIR,
                    ),
                    epsilon=0.001,
                )

            invalid_headers = extract_invalid_csv_headers(
                allowed_headers=headers, csv_text=delta_csv
            )
            if invalid_headers:
                flash(
                    "You have invalid headers: "
                    f"""{', '.join(invalid_headers)}.  Valid headers """
                    f"""are: {', '.join(headers)}""",
                    "warning",
                )
                return redirect(
                    f"/datasets/{dataset_id}/traits/{name}"
                    f"?resource-id={request.args.get('resource-id')}"
                    f"&dataset_name={request.args['dataset_name']}"
                )
        # Edge case where the csv file has not been edited!
        if not any(diff_data.values()):
            flash(
                "You have not modified the csv file you downloaded!", "warning"
            )
            return redirect(
                f"/datasets/{dataset_id}/traits/{name}"
                f"?resource-id={request.args.get('resource-id')}"
                f"&dataset_name={request.args['dataset_name']}"
            )

        with open(
            os.path.join(UPLOAD_DATADIR, f"{_file_name}.csv"), "w"
        ) as f_:
            f_.write(base_csv)
        with open(
            os.path.join(UPLOAD_DATADIR, f"{_file_name}.delta.csv"), "w"
        ) as f_:
            f_.write(delta_csv)

        with open(os.path.join(DIFF_DATADIR, f"{_file_name}.json"), "w") as f:
            diff_data.update(
                {
                    "trait_name": str(name),
                    "phenotype_id": str(phenotype_id),
                    "dataset_id": dataset_id,
                    "dataset_name": request.args["dataset_name"],
                    "resource_id": request.args.get("resource-id"),
                    "author": author,
                    "timestamp": (
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ),
                }
            )
            f.write(json.dumps(diff_data, cls=CustomJSONEncoder))
        url = url_for("metadata_edit.list_diffs")
        flash(f"Sample-data has been successfully uploaded.  \
View the diffs <a href='{url}' target='_blank'>here</a>", "success")
    # Run updates:
    phenotype_ = {
        "pre_pub_description": data_.get("pre-pub-desc"),
        "post_pub_description": data_.get("post-pub-desc"),
        "original_description": data_.get("orig-desc"),
        "units": data_.get("units"),
        "pre_pub_abbreviation": data_.get("pre-pub-abbrev"),
        "post_pub_abbreviation": data_.get("post-pub-abbrev"),
        "lab_code": data_.get("labcode"),
        "submitter": data_.get("submitter"),
        "owner": data_.get("owner"),
        "authorized_users": data_.get("authorized-users"),
    }
    updated_phenotypes = ""
    with database_connection(get_setting("SQL_URI")) as conn:
        updated_phenotypes = update(
            conn,
            "Phenotype",
            data=Phenotype(**phenotype_),
            where=Phenotype(id_=data_.get("phenotype-id")),
        )
        conn.commit()
    diff_data = {}
    if updated_phenotypes:
        diff_data.update(
            {
                "Phenotype": diff_from_dict(
                    old={
                        k: data_.get(f"old_{k}")
                        for k, v in phenotype_.items()
                        if v is not None
                    },
                    new=phenotype_,
                )
            }
        )
        publication_ = {
            key: val for key, val in {
                "pubmed_id": data_.get("pubmed-id"),
                "abstract": data_.get("abstract"),
                "authors": data_.get("authors"),
                "title": data_.get("title"),
                "journal": data_.get("journal"),
                "volume": data_.get("volume"),
                "pages": data_.get("pages"),
                "month": data_.get("month"),
                "year": data_.get("year"),
            }.items() if val is not None
        }
    updated_publications = ""
    with database_connection(get_setting("SQL_URI")) as conn:
        existing_publication = (# fetch publication
            data_.get("pubmed-id") and # only if `pubmed-id` exists
            fetch_publication_by_pubmed_id(conn, data_["pubmed-id"]))

        if existing_publication:
            update(
                conn,
                "PublishXRef",
                data=PublishXRef(publication_id=existing_publication.id_),
                where=PublishXRef(id_=name, inbred_set_id=dataset_id)
            )
        else:
            updated_publications = update_publication(
                conn, {"id_": data_["old_id_"], **publication_})
        conn.commit()

    if updated_publications:
        diff_data.update(
            {
                "Publication": diff_from_dict(
                    old={
                        k: data_.get(f"old_{k}")
                        for k, v in publication_.items()
                        if v is not None
                    },
                    new=publication_,
                )
            }
        )
    if diff_data:
        diff_data.update(
            {
                "phenotype_id": str(phenotype_id),
                "dataset_id": dataset_id,
                "trait_name": name,
                "resource_id": request.args.get("resource-id"),
                "author": author,
                "timestamp": (
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            }
        )
        with database_connection(get_setting("SQL_URI")) as conn:
            create_metadata_audit(conn, {
                "dataset_id": dataset_id,
                "editor": author,
                "json_data": json.dumps(diff_data, cls=CustomJSONEncoder)})
        flash(f"Diff-data: \n{diff_data}\nhas been uploaded", "success")
    return redirect(
        f"/datasets/{dataset_id}/traits/{name}"
        f"?resource-id={request.args.get('resource-id')}"
        f"&dataset_name={request.args['dataset_name']}"
    )


@metadata_edit.route("/traits/<name>", methods=("POST",))
@required_access(
    ("group:resource:view-resource", "group:resource:edit-resource"),
    dataset_key="dataset_id", trait_key="name")
def update_probeset(name: str):
    from utility.tools import get_setting
    with database_connection(get_setting("SQL_URI")) as conn:
        data_ = request.form.to_dict()
        probeset_ = {
            "id_": data_.get("id"),
            "symbol": data_.get("symbol"),
            "description": data_.get("description"),
            "probe_target_description": data_.get("probe_target_description"),
            "chr_": data_.get("chr"),
            "mb": data_.get("mb"),
            "alias": data_.get("alias"),
            "geneid": data_.get("geneid"),
            "homologeneid": data_.get("homologeneid"),
            "unigeneid": data_.get("unigeneid"),
            "omim": data_.get("OMIM"),
            "refseq_transcriptid": data_.get("refseq_transcriptid"),
            "blatseq": data_.get("blatseq"),
            "targetseq": data_.get("targetseq"),
            "strand_probe": data_.get("Strand_Probe"),
            "probe_set_target_region": data_.get("probe_set_target_region"),
            "probe_set_specificity": data_.get("probe_set_specificity"),
            "probe_set_blat_score": data_.get("probe_set_blat_score"),
            "probe_set_blat_mb_start": data_.get("probe_set_blat_mb_start"),
            "probe_set_blat_mb_end": data_.get("probe_set_blat_mb_end"),
            "probe_set_strand": data_.get("probe_set_strand"),
            "probe_set_note_by_rw": data_.get("probe_set_note_by_rw"),
            "flag": data_.get("flag"),
        }
        diff_data = {}
        author = (
            (g.user_session.record.get(b"user_id") or b"").decode("utf-8")
            or g.user_session.record.get("user_id")
            or ""
        )
        if update(
            conn,
            "ProbeSet",
            data=Probeset(**probeset_),
            where=Probeset(id_=data_.get("id")),
        ):
            diff_data.update(
                {
                    "Probeset": diff_from_dict(
                        old={
                            k: data_.get(f"old_{k}")
                            for k, v in probeset_.items()
                            if v is not None
                        },
                        new=probeset_,
                    )
                }
            )
        if diff_data:
            diff_data.update({"probeset_name": data_.get("probeset_name")})
            diff_data.update({"author": author})
            diff_data.update({"resource_id": request.args.get("resource-id")})
            diff_data.update(
                {
                    "timestamp": datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }
            )
            create_metadata_audit(conn, {
                "dataset_id": data_["id"],
                "editor": author,
                "json_data": json.dumps(diff_data, cls=CustomJSONEncoder)})
            edited_values = {k: v for (k, v) in diff_data['Probeset'].items()
                             if k not in {"id_", "timestamp", "author"}}
            changes = []
            for k in edited_values.keys():
                changes.append(f"<b><span data-message-id='{k}'></span></b>")
            message = f"You successfully updated the following entries \
            at {diff_data['timestamp']}: {', '.join(changes)}"
            flash(f"You successfully edited: {message}", "success")
        else:
            flash("No edits were made!", "warning")
        return redirect(
            f"/datasets/traits/{name}"
            f"?resource-id={request.args.get('resource-id')}"
            f"&dataset_name={request.args['dataset_id']}"
        )


@metadata_edit.route("/<dataset_id>/traits/<phenotype_id>/csv")
@login_required()
def get_sample_data_as_csv(dataset_id: str, phenotype_id: int):
    from utility.tools import get_setting
    with database_connection(get_setting("SQL_URI")) as conn:
        return Response(
            get_trait_csv_sample_data(
                conn=conn,
                trait_name=str(dataset_id),
                phenotype_id=str(phenotype_id),
                sample_list=retrieve_sample_list(
                    retrieve_phenotype_group_name(conn, dataset_id))
            ),
            mimetype="text/csv",
            headers={
                "Content-disposition": f"attachment; \
filename=sample-data-{dataset_id}.csv"
            },
        )


@metadata_edit.route("/diffs")
@login_required(pagename="Sample Data Diffs")
def list_diffs():
    files = _get_diffs(
        diff_dir=f"{current_app.config.get('TMPDIR')}/sample-data/diffs",
        redis_conn=redis.from_url(current_app.config["REDIS_URL"],
                                  decode_responses=True))

    def __filter_authorised__(diffs, auth_details):
        """Retain only those diffs that the current user has edit access to."""
        return list({
            diff["filepath"]: diff for diff in diffs
            for auth in auth_details
            if (diff["diff"]["dataset_name"] == auth["dataset_name"]
                 and
                 diff["diff"]["trait_name"] == auth["trait_name"]) }.values())

    def __organise_diffs__(acc, item):
        if item["filepath"].name.endswith(".rejected"):
            return {**acc, "rejected": acc["rejected"]  + [item]}
        if item["filepath"].name.endswith(".approved"):
            return {**acc, "approved": acc["approved"]  + [item]}
        return {**acc, "waiting": acc["waiting"] + [item]}

    accessible_diffs = client.post(
        "oauth2/data/authorisation",
        json={
            "traits": [
                f"{meta['diff']['dataset_name']}::{meta['diff']['trait_name']}"
                for meta in files
            ]
        }
    ).map(
        lambda lst: [
            auth_item for auth_item in lst
            if (("group:resource:edit-resource" in auth_item["privileges"])
                or
                ("system:resources:edit-all" in auth_item["privileges"]))]
    ).map(
        lambda alst: __filter_authorised__(files, alst)
    ).map(lambda diffs: reduce(__organise_diffs__,
                               diffs,
                               {"approved": [], "rejected": [], "waiting": []}))

    def __handle_error__(error):
        flash_error(process_error(error))
        return render_template(
            "display_files.html", approved=[], rejected=[], waiting=[])

    def __success__(org_diffs):
        return render_template(
            "display_files.html",
            approved=sorted(
                org_diffs["approved"],
                reverse=True,
                key=lambda d: d["meta"]["time_stamp"]),
            rejected=sorted(
                org_diffs["rejected"],
                reverse=True,
                key=lambda d: d["meta"]["time_stamp"]),
            waiting=sorted(
                org_diffs["waiting"],
                reverse=True,
                key=lambda d: d["meta"]["time_stamp"]))

    return accessible_diffs.either(__handle_error__, __success__)


@metadata_edit.route("/diffs/<name>")
@login_required(pagename="diff display")
def show_diff(name):
    TMPDIR = current_app.config.get("TMPDIR")
    with open(
        os.path.join(f"{TMPDIR}/sample-data/diffs", name), "r"
    ) as myfile:
        content = myfile.read()
    content = json.loads(content)
    for data in content.get("Modifications"):
        data["Diff"] = "\n".join(
            difflib.ndiff([data.get("Original")], [data.get("Current")])
        )
    return render_template("display_diffs.html", diff=content)

@metadata_edit.route("/<dataset_id>/traits/<name>/history")
@metadata_edit.route("/probeset/<name>")
def show_history(dataset_id: str = "", name: str = ""):
    from utility.tools import get_setting
    diff_data_ = None
    with database_connection(get_setting("SQL_URI")) as conn:
        json_data = None
        if dataset_id:  # This is a published phenotype
            json_data = fetch_phenotype_metadata_audit_by_dataset_id(
                conn, dataset_id)
        else:  # This is a probeset
            json_data = fetch_probeset_metadata_audit_by_trait_name(
                conn, name)
        Edit = namedtuple("Edit", ["field", "old", "new", "diff"])
        Diff = namedtuple("Diff", ["author", "diff", "timestamp"])
        diff_data = []
        for data in json_data:
            json_ = data["json_data"]
            timestamp = json_.get("timestamp")
            author = json_.get("author")
            for key, value in json_.items():
                if isinstance(value, dict):
                    for field, data_ in value.items():
                        diff_data.append(
                            Diff(
                                author=author,
                                diff=Edit(
                                    field,
                                    data_.get("old") or "",
                                    data_.get("new") or "",
                                    "\n".join(difflib.ndiff(
                                        [str(data_.get("old")) or ""],
                                        [str(data_.get("new")) or ""],
                                    ))),
                                timestamp=timestamp))

    if len(diff_data) > 0:
        diff_data_ = groupby(
            (diff for diff in diff_data if (
                diff.diff.diff.startswith("-") or
                diff.diff.diff.startswith("+"))),
            lambda x: x.timestamp)
    return render_template(
        "edit_history.html",
        diff=diff_data_,
        version=get_setting("GN_VERSION"),
    )

def __authorised_p__(dataset_name, trait_name):
    """Check whether the user is authorised to edit the trait."""
    def __error__(error):
        flash_error(process_error(error))
        return False

    def __success__(auth_details):
        key = f"{dataset_name}::{trait_name}"
        dets = auth_details.get(key)
        if not bool(dets):
            return False
        return (("group:resource:edit-resource" in dets["privileges"])
                or
                ("system:resources:edit-all" in dets["privileges"]))

    return client.post(
        "oauth2/data/authorisation",
        json={"traits": [f"{dataset_name}::{trait_name}"]}
    ).map(
        lambda adets: {
            f"{dets['dataset_name']}::{dets['trait_name']}": dets
            for dets in adets
        }
    ).either(__error__, __success__)

@metadata_edit.route("<resource_id>/diffs/<file_name>/reject")
@login_required(pagename="sample data rejection")
@required_access(
    ("group:resource:view-resource", "group:resource:edit-resource"),
    trait_key="trait_name")
def reject_data(resource_id: str, file_name: str):
    diffs_page = redirect(url_for("metadata_edit.list_diffs"))
    TMPDIR = current_app.config.get("TMPDIR")
    sampledir = Path(TMPDIR, "sample-data/diffs")
    samplefile = Path(sampledir, file_name)

    if not samplefile.exists():
        flash("No such diffs file!", "alert-danger")
        return diffs_page

    with open(samplefile, "r") as sfile:
        sample_data = json.loads(sfile.read())
        if not __authorised_p__(sample_data["dataset_name"],
                                sample_data["trait_name"]):
            flash("You are not authorised to edit that trait."
                  "alert-danger")
            return diffs_page

    samplefile.rename(Path(sampledir, f"{file_name}.rejected"))
    flash(f"{file_name} has been rejected!", "alert-success")
    return diffs_page

@metadata_edit.route("<resource_id>/diffs/<file_name>/approve")
@login_required(pagename="Sample Data Approval")
@required_access(
    ("group:resource:view-resource", "group:resource:edit-resource"),
    trait_key="trait_name")
def approve_data(resource_id: str, file_name: str):
    from utility.tools import get_setting
    sample_data = {file_name: str}
    TMPDIR = current_app.config.get("TMPDIR")
    diffpath = Path(TMPDIR, "sample-data/diffs", file_name)
    if not diffpath.exists():
        flash(f"Could not find diff with the name '{diffpath.name}'",
              "alert-danger")
        return redirect(url_for("metadata_edit.list_diffs"))

    n_deletions = 0
    n_insertions = 0
    with (open(diffpath, "r") as myfile,
          database_connection(get_setting("SQL_URI")) as conn):
        sample_data = json.load(myfile)

        if not __authorised_p__(sample_data["dataset_name"],
                                sample_data["trait_name"]):
            flash("You are not authorised to edit that trait.", "alert-danger")
            return redirect(url_for("metadata_edit.list_diffs"))

        for modification in (
                modifications := [d for d in sample_data.get("Modifications")]):
            if modification.get("Current"):
                update_sample_data(
                    conn=conn,
                    trait_name=sample_data.get("trait_name"),
                    original_data=modification.get("Original"),
                    updated_data=modification.get("Current"),
                    csv_header=sample_data.get(
                        "Columns", "Strain Name,Value,SE,Count"
                    ),
                    phenotype_id=int(sample_data.get("phenotype_id")),
                )

        # Deletions
        for data in [d for d in sample_data.get("Deletions")]:
            __deletions = delete_sample_data(
                conn=conn,
                trait_name=sample_data.get("trait_name"),
                data=data,
                csv_header=sample_data.get(
                    "Columns", "Strain Name,Value,SE,Count"
                ),
                phenotype_id=int(sample_data.get("phenotype_id")),
            )
            if __deletions:
                n_deletions += 1
            # Remove any data that already exists from sample_data deletes
            else:
                sample_data.get("Deletions").remove(data)

        ## Insertions
        for data in [d for d in sample_data.get("Additions")]:
            if insert_sample_data(
                conn=conn,
                trait_name=sample_data.get("trait_name"),
                data=data,
                csv_header=sample_data.get(
                    "Columns", "Strain Name,Value,SE,Count"
                ),
                phenotype_id=int(sample_data.get("phenotype_id")),
            ):
                n_insertions += 1
    if any(
        [
            sample_data.get("Additions"),
            sample_data.get("Modifications"),
            sample_data.get("Deletions"),
        ]
    ):
        with database_connection(get_setting("SQL_URI")) as conn:
            create_metadata_audit(conn, {
                "dataset_id": sample_data.get("dataset_id"),
                "editor": sample_data.get("author"),
                "json_data": json.dumps(sample_data, cls=CustomJSONEncoder)
            })
        # Once data is approved, rename it!
        os.rename(
            os.path.join(f"{TMPDIR}/sample-data/diffs", file_name),
            os.path.join(
                f"{TMPDIR}/sample-data/diffs", f"{file_name}.approved"
            ),
        )
        if n_deletions:
            flash(f"# Deletions: {n_deletions}", "success")
        if n_insertions:
            flash(f"# Additions: {len(modifications)}", "success")
        if len(modifications):
            flash(f"# Modifications: {len(modifications)}", "success")
    else:  # Edge case where you need to automatically reject the file
        os.rename(
            os.path.join(f"{TMPDIR}/sample-data/diffs", file_name),
            os.path.join(
                f"{TMPDIR}/sample-data/diffs", f"{file_name}.rejected"
            ),
        )
        flash(
            (
                "Automatically rejecting this file since no "
                "changes could be applied."
            ),
            "warning",
        )
    return redirect(url_for("metadata_edit.list_diffs"))

def is_a_number(value: str):
    """Check whether the string is a number"""
    return bool(re.search(r"^[0-9]+\.*[0-9]*$", value))

def create_delta_csv(base_csv, form_data, sample_list):
    base_csv_lines = base_csv.split("\n")
    delta_csv_lines = [base_csv_lines[0]]

    for line in base_csv_lines[1:]:
        sample = {}
        sample['name'], sample['value'], sample['error'], sample['n_cases'] = line.split(",")
        for key in form_data:
            if sample['name'] in key:
                new_line_items = [sample['name']]
                for field in ["value", "error", "n_cases"]:
                    the_value = form_data.get(f"{field}:{sample['name']}")
                    if the_value:
                        if is_a_number(the_value) or the_value.lower() == "x":
                            new_line_items.append(the_value)
                            continue
                    new_line_items.append(sample[field])
                delta_csv_lines.append(",".join(new_line_items))
                break
        else:
            delta_csv_lines.append(line)

    return "\n".join(delta_csv_lines)
