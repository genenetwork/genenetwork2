import datetime
import json
import os

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

from wqflask.database import database_connection
from wqflask.decorators import edit_access_required
from wqflask.decorators import edit_admins_access_required
from wqflask.decorators import login_required

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
from gn3.db.metadata_audit import MetadataAudit
from gn3.db.phenotypes import Phenotype
from gn3.db.phenotypes import Probeset
from gn3.db.phenotypes import Publication
from gn3.db.phenotypes import PublishXRef
from gn3.db.phenotypes import probeset_mapping
from gn3.db.sample_data import delete_sample_data
from gn3.db.sample_data import get_trait_csv_sample_data
from gn3.db.sample_data import insert_sample_data
from gn3.db.sample_data import update_sample_data
from gn3.db.sample_data import get_case_attributes


metadata_edit = Blueprint("metadata_edit", __name__)


def _get_diffs(
    diff_dir: str, user_id: str, redis_conn: redis.Redis, gn_proxy_url: str
):
    def __get_file_metadata(file_name: str) -> Dict:
        author, resource_id, time_stamp, *_ = file_name.split(".")

        return {
            "resource_id": resource_id,
            "file_name": file_name,
            "author": json.loads(redis_conn.hget("users", author)).get(
                "full_name"
            ),
            "time_stamp": time_stamp,
            "roles": get_highest_user_access_role(
                resource_id=resource_id,
                user_id=user_id,
                gn_proxy_url=gn_proxy_url,
            ),
        }

    approved, rejected, waiting = [], [], []
    if os.path.exists(diff_dir):
        for name in os.listdir(diff_dir):
            file_metadata = __get_file_metadata(file_name=name)
            admin_status = file_metadata["roles"].get("admin")
            append_p = user_id in name or admin_status > AdminRole.EDIT_ACCESS
            if name.endswith(".rejected") and append_p:
                rejected.append(__get_file_metadata(file_name=name))
            elif name.endswith(".approved") and append_p:
                approved.append(__get_file_metadata(file_name=name))
            elif append_p:  # Normal file
                waiting.append(__get_file_metadata(file_name=name))
    return {
        "approved": approved,
        "rejected": rejected,
        "waiting": waiting,
    }


def edit_phenotype(conn, name, dataset_id):
    publish_xref = fetchone(
        conn=conn,
        table="PublishXRef",
        where=PublishXRef(id_=name, inbred_set_id=dataset_id),
    )
    return {
        "publish_xref": publish_xref,
        "phenotype": fetchone(
            conn=conn,
            table="Phenotype",
            where=Phenotype(id_=publish_xref.phenotype_id),
        ),
        "publication": fetchone(
            conn=conn,
            table="Publication",
            where=Publication(id_=publish_xref.publication_id),
        ),
    }


def edit_probeset(conn, name):
    probeset_ = fetchone(
        conn=conn,
        table="ProbeSet",
        columns=list(probeset_mapping.values()),
        where=Probeset(name=name),
    )
    json_data = fetchall(
        conn, "metadata_audit", where=MetadataAudit(dataset_id=probeset_.id_)
    )
    Edit = namedtuple("Edit", ["field", "old", "new", "diff"])
    Diff = namedtuple("Diff", ["author", "diff", "timestamp"])
    diff_data = []
    for data in json_data:
        json_ = json.loads(data.json_data)
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
                                data_.get("old"),
                                data_.get("new"),
                                "\n".join(
                                    difflib.ndiff(
                                        [data_.get("old")], [data_.get("new")]
                                    )
                                ),
                            ),
                            timestamp=timestamp,
                        )
                    )
    diff_data_ = None
    if len(diff_data) > 0:
        diff_data_ = groupby(diff_data, lambda x: x.timestamp)
    return {
        "diff": diff_data_,
        "probeset": probeset_,
    }


@metadata_edit.route("/<dataset_id>/traits/<name>")
@edit_access_required
@login_required
def display_phenotype_metadata(dataset_id: str, name: str):
    with database_connection() as conn:
        _d = edit_phenotype(conn=conn, name=name, dataset_id=dataset_id)
        return render_template(
            "edit_phenotype.html",
            publish_xref=_d.get("publish_xref"),
            phenotype=_d.get("phenotype"),
            publication=_d.get("publication"),
            dataset_id=dataset_id,
            name=name,
            resource_id=request.args.get("resource-id"),
            headers=get_case_attributes(conn),
            version=os.environ.get("GN_VERSION"),
        )


@metadata_edit.route("/traits/<name>")
@edit_access_required
@login_required
def display_probeset_metadata(name: str):
    with database_connection() as conn:
        _d = edit_probeset(conn=conn, name=name)
        return render_template(
            "edit_probeset.html",
            diff=_d.get("diff"),
            probeset=_d.get("probeset"),
            name=name,
            resource_id=request.args.get("resource-id"),
            version=os.environ.get("GN_VERSION"),
        )


@metadata_edit.route("/<dataset_id>/traits/<name>", methods=("POST",))
@edit_access_required
@login_required
def update_phenotype(dataset_id: str, name: str):
    data_ = request.form.to_dict()
    TMPDIR = current_app.config.get("TMPDIR")
    author = (
        (g.user_session.record.get(b"user_id") or b"").decode("utf-8")
        or g.user_session.record.get("user_id")
        or ""
    )
    phenotype_id = str(data_.get("phenotype-id"))
    if not (file_ := request.files.get("file")):
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
        with database_connection() as conn:
            headers = ["Strain Name", "Value", "SE", "Count"] \
                      + list(get_case_attributes(conn).keys())
            diff_data = remove_insignificant_edits(
                diff_data=csv_diff(
                    base_csv=(
                        base_csv := get_trait_csv_sample_data(
                            conn=conn,
                            trait_name=str(name),
                            phenotype_id=str(phenotype_id),
                        )
                    ),
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
                )
        # Edge case where the csv file has not been edited!
        if not any(diff_data.values()):
            flash(
                "You have not modified the csv file you downloaded!", "warning"
            )
            return redirect(
                f"/datasets/{dataset_id}/traits/{name}"
                f"?resource-id={request.args.get('resource-id')}"
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
                    "dataset_id": name,
                    "resource_id": request.args.get("resource-id"),
                    "author": author,
                    "timestamp": (
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ),
                }
            )
            f.write(json.dumps(diff_data))
        flash("Sample-data has been successfully uploaded", "success")
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
    with database_connection() as conn:
        updated_phenotypes = update(
            conn,
            "Phenotype",
            data=Phenotype(**phenotype_),
            where=Phenotype(id_=data_.get("phenotype-id")),
        )
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
        "pubmed_id": data_.get("pubmed-id"),
        "abstract": data_.get("abstract"),
        "authors": data_.get("authors"),
        "title": data_.get("title"),
        "journal": data_.get("journal"),
        "volume": data_.get("volume"),
        "pages": data_.get("pages"),
        "month": data_.get("month"),
        "year": data_.get("year"),
    }
    updated_publications = ""
    with database_connection() as conn:
        updated_publications = update(
            conn,
            "Publication",
            data=Publication(**publication_),
            where=Publication(
                id_=data_.get("old_id_")
            ),
        )
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
                "dataset_id": name,
                "resource_id": request.args.get("resource-id"),
                "author": author,
                "timestamp": (
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            }
        )
        with database_connection() as conn:
            insert(
                conn,
                table="metadata_audit",
                data=MetadataAudit(
                    dataset_id=name,
                    editor=author,
                    json_data=json.dumps(diff_data),
                ),
            )
        flash(f"Diff-data: \n{diff_data}\nhas been uploaded", "success")
    return redirect(
        f"/datasets/{dataset_id}/traits/{name}"
        f"?resource-id={request.args.get('resource-id')}"
    )


@metadata_edit.route("/traits/<name>", methods=("POST",))
@edit_access_required
@login_required
def update_probeset(name: str):
    with database_connection() as conn:
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
            insert(
                conn,
                table="metadata_audit",
                data=MetadataAudit(
                    dataset_id=data_.get("id"),
                    editor=author,
                    json_data=json.dumps(diff_data),
                ),
            )
        return redirect(
            f"/datasets/traits/{name}"
            f"?resource-id={request.args.get('resource-id')}"
        )


@metadata_edit.route("/<dataset_id>/traits/<phenotype_id>/csv")
@login_required
def get_sample_data_as_csv(dataset_id: str, phenotype_id: int):
    with database_connection() as conn:
        return Response(
            get_trait_csv_sample_data(
                conn=conn,
                trait_name=str(dataset_id),
                phenotype_id=str(phenotype_id),
            ),
            mimetype="text/csv",
            headers={
                "Content-disposition": f"attachment; filename=sample-data-{dataset_id}.csv"
            },
        )


@metadata_edit.route("/diffs")
@login_required
def list_diffs():
    files = _get_diffs(
        diff_dir=f"{current_app.config.get('TMPDIR')}/sample-data/diffs",
        user_id=(
            (g.user_session.record.get(b"user_id") or b"").decode("utf-8")
            or g.user_session.record.get("user_id")
            or ""
        ),
        redis_conn=redis.from_url(
            current_app.config["REDIS_URL"], decode_responses=True
        ),
        gn_proxy_url=current_app.config.get("GN2_PROXY"),
    )
    return render_template(
        "display_files.html",
        approved=sorted(
            files.get("approved"),
            reverse=True,
            key=lambda d: d.get("time_stamp"),
        ),
        rejected=sorted(
            files.get("rejected"),
            reverse=True,
            key=lambda d: d.get("time_stamp"),
        ),
        waiting=sorted(
            files.get("waiting"),
            reverse=True,
            key=lambda d: d.get("time_stamp"),
        ),
    )


@metadata_edit.route("/diffs/<name>")
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
def show_history(dataset_id: str, name: str):
    diff_data_ = None
    with database_connection() as conn:
        publish_xref = fetchone(
            conn=conn,
            table="PublishXRef",
            where=PublishXRef(id_=name, inbred_set_id=dataset_id))

        json_data = fetchall(
            conn,
            "metadata_audit",
            where=MetadataAudit(dataset_id=publish_xref.id_),
        )

        Edit = namedtuple("Edit", ["field", "old", "new", "diff"])
        Diff = namedtuple("Diff", ["author", "diff", "timestamp"])
        diff_data = []
        for data in json_data:
            json_ = json.loads(data.json_data)
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
                                    data_.get("old"),
                                    data_.get("new"),
                                    "\n".join(
                                        difflib.ndiff(
                                            [data_.get("old") or ""],
                                            [data_.get("new")]
                                        )
                                    ),
                                ),
                                timestamp=timestamp,
                            )
                        )
        if len(diff_data) > 0:
            diff_data_ = groupby(diff_data, lambda x: x.timestamp)
    return render_template(
        "edit_history.html",
        diff=diff_data_,
        version=os.environ.get("GN_VERSION"))


@metadata_edit.route("<resource_id>/diffs/<file_name>/reject")
@edit_admins_access_required
@login_required
def reject_data(resource_id: str, file_name: str):
    TMPDIR = current_app.config.get("TMPDIR")
    os.rename(
        os.path.join(f"{TMPDIR}/sample-data/diffs", file_name),
        os.path.join(f"{TMPDIR}/sample-data/diffs", f"{file_name}.rejected"),
    )
    flash(f"{file_name} has been rejected!", "success")
    return redirect(url_for("metadata_edit.list_diffs"))


@metadata_edit.route("<resource_id>/diffs/<file_name>/approve")
@edit_admins_access_required
@login_required
def approve_data(resource_id: str, file_name: str):
    sample_data = {file_name: str}
    TMPDIR = current_app.config.get("TMPDIR")
    with open(
        os.path.join(f"{TMPDIR}/sample-data/diffs", file_name), "r"
    ) as myfile:
        sample_data = json.load(myfile)
    with database_connection() as conn:
        for modification in (
            modifications := [d for d in sample_data.get("Modifications")]
        ):
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

    n_deletions = 0
    with database_connection() as conn:
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

    n_insertions = 0
    with database_connection() as conn:
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
        with database_connection() as conn:
            insert(
                conn,
                table="metadata_audit",
                data=MetadataAudit(
                    dataset_id=sample_data.get("trait_name"),
                    editor=sample_data.get("author"),
                    json_data=json.dumps(sample_data),
                ),
            )
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


@metadata_edit.route("/case-attributes")
def show_case_attribute_columns():
    diff_data = None
    with database_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT editor, json_diff_data FROM "
                "caseattributes_audit WHERE status = 'review'")
            diff_data = cursor.fetchall()
    modifications, deletions, inserts = [], [], []
    if diff_data:
        for author, diff in diff_data:
            diff = json.loads(diff)
            diff["author"] = author
            if (m_ := diff.get("Modification")):
                if m_.get("description"):
                    m_["description"]["Diff"] = "\n".join(
                        difflib.ndiff(
                            [m_.get("description")["Original"]],
                            [m_.get("description")["Current"]]
                        ))
                if m_.get("name"):
                    m_["name"]["Diff"] = "\n".join(
                        difflib.ndiff(
                            [m_.get("name")["Original"]],
                            [m_.get("name")["Current"]]
                        ))
                    modifications.append(m_)
            if (d_ := diff.get("Deletion")):
                deletions.append(d_)
            if (i_ := diff.get("Insert")):
                inserts.append(i_)
    # import pudb; pu.db

    with database_connection() as cursor:
        return render_template(
            "case_attributes.html",
            case_attributes=get_case_attributes(cursor),
            modifications=modifications,
            deletions=deletions,
            inserts=inserts
        )


@metadata_edit.route("/case-attributes", methods=("POST",))
@edit_admins_access_required
@login_required
def update_case_attributes():
    data_ = request.form.to_dict().get("data")
    if data_:
        author = (
            (g.user_session.record.get(b"user_id") or b"").decode("utf-8")
            or g.user_session.record.get("user_id")
            or ""
        )
        with database_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO caseattributes_audit "
                        "(status, editor, json_diff_data) "
                        "VALUES (%s, %s, %s)",
                        ('review', author, data_),
                    )
            except Exception as _e:
                import MySQLdb
                conn.rollback()
                raise MySQLdb.Error(_e) from _e
            conn.commit()

    return redirect(url_for("metadata_edit.show_case_attribute_columns"))
