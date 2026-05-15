import re
import csv
import datetime
import math
import json
import io
import os
import logging
from pathlib import Path
from functools import reduce

from collections import namedtuple
from itertools import groupby
from typing import Dict, Optional

import difflib
import redis

from urllib.parse import urljoin
from pymonad.either import Left, Right

from flask import Blueprint
from flask import Response
from flask import current_app
from flask import flash
from flask import g
from flask import redirect
from flask import request
from flask import url_for
from gn_libs.mysqldb import database_connection
from gn_libs.privileges import resources
from gn_libs import monadic_requests as mrequests

from gn2.utility.json import CustomJSONEncoder

from gn2.wqflask.decorators import login_required
from gn2.wqflask.flask_extensions import render_template

from gn2.wqflask.oauth2 import client
from gn2.wqflask.oauth2 import session
from gn2.wqflask.oauth2.request_utils import flash_error, process_error

from gn3.csvcmp import create_dirs_if_not_exists
from gn3.csvcmp import csv_diff
from gn3.csvcmp import extract_invalid_csv_headers
from gn3.csvcmp import remove_insignificant_edits
from gn3.db import diff_from_dict
from gn3.db.datasets import (
    retrieve_sample_list,
    retrieve_mrna_group_name,
    retrieve_phenotype_group_name,
    retrieve_group_id)
from gn3.db.metadata_audit import (
    create_metadata_audit,
    fetch_probeset_metadata_audit_by_trait_name,
    fetch_phenotype_metadata_audit_by_dataset_id)
from gn3.db.probesets import (
    update_probeset as _update_probeset,
    fetch_probeset_metadata_by_name)
from gn3.db.phenotypes import (
    batch_update_descriptions,
    fetch_trait,
    fetch_metadata,
    update_publication,
    update_cross_reference,
    fetch_publication_by_id,
    fetch_publication_by_pubmed_id,
    update_phenotype as _update_phenotype)
from gn3.db.sample_data import (
    delete_sample_data,
    insert_sample_data,
    update_sample_data,
    batch_update_sample_data,
    get_pheno_sample_data,
    get_pheno_csv_sample_data,
    get_mrna_sample_data,
    get_mrna_csv_sample_data)

logger = logging.getLogger(__name__)

metadata_edit = Blueprint("metadata_edit", __name__)

def _get_user_name_by_id(user_id: str) -> str:
    """Fetch user full name from gn-auth API by user ID."""
    try:
        from gn2.wqflask.oauth2 import client
        response = client.get(f"auth/user/{user_id}")
        if response.is_right():
            user_data = response.value
            return user_data.get("name") or user_id
    except Exception:
        pass
    return user_id

def _get_diffs(diff_dir: str, redis_conn: redis.Redis, db_conn=None):
    """Get all the diff details."""
    def __get_file_metadata(file_name: str) -> Dict:
        author, resource_id, time_stamp, *_ = file_name.split(".")
        author = _get_user_name_by_id(author)
        # Parse timestamp and convert to human-readable format
        try:
            dt = datetime.datetime.fromisoformat(time_stamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            # Fallback to raw timestamp if parsing fails
            formatted_time = time_stamp
        return {
            "resource_id": resource_id,
            "file_name": file_name,
            "author": author,
            "time_stamp": formatted_time
        }

    def __get_diff__(diff_dir: str, diff_file_name: str) -> dict:
        """Get the contents of the diff at `filepath`."""
        with open(Path(diff_dir, diff_file_name), encoding="utf8") as dfile:
            return json.loads(dfile.read().strip())

    def __get_diff_summary__(diff_data: dict) -> Dict:
        """Create a summary of diff counts."""
        return {
            "additions": len(diff_data.get("Additions", {})),
            "modifications": len(diff_data.get("Modifications", {})),
            "deletions": len(diff_data.get("Deletions", {}))
        }

    return tuple({
        "filepath": Path(diff_dir, dname).absolute(),
        "meta": __get_file_metadata(file_name=dname),
        "diff": __get_diff__(diff_dir, dname),
        "summary": __get_diff_summary__(__get_diff__(diff_dir, dname))
    } for dname in os.listdir(diff_dir))

def edit_phenotype(conn, name, dataset_id):
    publish_xref = fetch_trait(conn, dataset_id=dataset_id, trait_name=name)
    return {
        "publish_xref": publish_xref,
        "phenotype": fetch_metadata(conn, publish_xref["phenotype_id"]),
        "publication": fetch_publication_by_id(conn, publish_xref["publication_id"])
    }

def _normalize_n_cases(value):
    """Treat N=0 as missing (equivalent to 'x'). Returns 'x' or str(value)."""
    return 'x' if value in (None, '0', 0) else str(value)

def get_sample_data_diff(dict1, dict2):
    """Get the diff between two sets of sample data"""

    # Samples with diffs, since we don't want to display them all
    diff_samples = {
        'Additions': [],
        'Modifications': [],
        'Deletions': []
    }

    diff = {
        "Additions": {},
        "Modifications": {},
        "Deletions": {}
    }

    all_keys = set(dict1.keys()) | set(dict2.keys())
    for key in all_keys:
        # Check presence in each dict
        in1 = key in dict1
        in2 = key in dict2

        if not in1:
            diff_samples['Additions'].append(key)
            diff["Additions"][key] = dict2[key]
            continue
        if not in2:
            diff_samples['Deletions'].append(key)
            diff["Deletions"][key] = dict1[key]
            continue

        sub1 = dict1[key].copy()
        sub2 = dict2[key].copy()

        if sub1 != sub2:
            sub_diff = {}
            for k in set(sub1.keys()) | set(sub2.keys()):
                v1_raw = sub1.get(k, None)
                v2_raw = sub2.get(k, None)

                # For n_cases (N field), treat 0 and 'x' as equivalent (both represent missing)
                if k == 'n_cases':
                    # Normalize 0 and None to 'x'
                    v1_norm = _normalize_n_cases(v1_raw)
                    v2_norm = _normalize_n_cases(v2_raw)
                    # Skip if both are missing
                    if v1_norm == 'x' and v2_norm == 'x':
                        continue
                    if v1_norm != v2_norm:
                        sub_diff[k] = {"Original": v1_norm, "Current": v2_norm}
                    continue
                
                try:
                    v1 = float(v1_raw)
                    v2 = float(v2_raw)
                    if not math.isclose(v1, v2, abs_tol=0.02):
                        sub_diff[k] = {"Original": v1, "Current": v2}
                except Exception:
                    # Fallback to string comparison if not numeric
                    # Normalize None to 'x' for missing values to avoid showing 'None' in templates
                    v1_disp = v1_raw if v1_raw is not None else 'x'
                    v2_disp = v2_raw if v2_raw is not None else 'x'
                    # Skip if both are 'x' (both represent missing/null values)
                    if v1_disp == 'x' and v2_disp == 'x':
                        continue
                    if v1_disp != v2_disp:
                        sub_diff[k] = {"Original": v1_disp, "Current": v2_disp}

            if sub_diff:
                diff_samples['Modifications'].append(key)
                diff["Modifications"][key] = sub_diff

    return diff, diff_samples

def get_dialect(file_text):
    """Determine the CSV dialect with improved tab detection"""
    sample = file_text[:2048]

    # First try tab detection
    if '\t' in sample:
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters='\t')
            if dialect.delimiter == '\t':
                return dialect
        except csv.Error:
            pass

    # Fall back to comma detection
    try:
        return csv.Sniffer().sniff(sample, delimiters=',')
    except csv.Error:
        # Default to tab if nothing else works
        return csv.excel_tab if '\t' in sample else csv.excel


def calculate_sample_diffs(conn, upload_file, transposed, group_name):

    def is_number(value):
        try:
            float(value)
            return True
        except:
            return False

    sample_list = []

    all_diffs = {}

    # List of samples with diffs, since we only want to display those in review
    all_diff_samples = {
        'Additions': [],
        'Modifications': [],
        'Deletions': []
    }

    i = 0

    file_text = upload_file.read().decode('utf-8') if hasattr(upload_file, 'read') else upload_file
    dialect = get_dialect(file_text)
    upload_reader = csv.reader(io.StringIO(file_text), dialect=dialect)

    if transposed:
        upload_reader = list(zip(*list(upload_reader)))

    trait_name = "" # This gets set every 3 lines, since there are 3 lines per trait
    edited_sample_data = {} # Also set every 3 lines
    for line in upload_reader:
        if i == 0: # Header line
            sample_list = line[2:]

        if i >= 1:
            dataset_name = group_name + "Publish"
            if i % 3 == 1:
                trait_name = line[0]
            group_id = retrieve_group_id(conn, group_name)

            sample_data = line[2:]
            for j, sample in enumerate(sample_list):
                if sample not in edited_sample_data:
                    edited_sample_data[sample] = {}

                if i % 3 == 1:
                    if is_number(sample_data[j]):
                        edited_sample_data[sample]['value'] = f"{round(float(sample_data[j]), 2)}"
                    else:
                        edited_sample_data[sample]['value'] = 'x'
                if i % 3 == 2:
                    if is_number(sample_data[j]):
                        edited_sample_data[sample]['error'] = f"{round(float(sample_data[j]), 3)}"
                    else:
                        edited_sample_data[sample]['error'] = 'x'
                if i % 3 == 0:
                    if is_number(sample_data[j]):
                        edited_sample_data[sample]['n_cases'] = f"{int(sample_data[j])}"
                    else:
                        edited_sample_data[sample]['n_cases'] = 'x'

            if i % 3 == 0:
                orig_sample_data = get_pheno_sample_data(conn, trait_name, None, group_id=group_id)

                # Remove samples not in main samplelist
                extra_samples = list(set(orig_sample_data.keys()) - set(sample_list))
                for sample in extra_samples:
                    if sample in orig_sample_data:
                        del orig_sample_data[sample]

                diff, diff_samples = get_sample_data_diff(orig_sample_data, edited_sample_data)
                
                # Skip "additions" where all values are missing (represented as 'x' or N=0).
                # These are not real additions, just samples with no actual data.
                def has_real_data(sample_diff):
                    """Check if sample has any non-missing values."""
                    for k, v in sample_diff.items():
                        # For n_cases, treat 0 as missing; for other fields, 'x' is missing
                        if k == 'n_cases' and _normalize_n_cases(v) != 'x':
                            return True
                        if k != 'n_cases' and v != 'x':
                            return True
                    return False

                diff["Additions"] = {s: d for s, d in diff["Additions"].items() if has_real_data(d)}
                diff_samples['Additions'] = list(diff["Additions"].keys())
                
                for key in all_diff_samples:
                    all_diff_samples[key] = list(set(diff_samples[key]).union(set(all_diff_samples[key])))

                if (len(diff['Modifications']) > 0 or
                    len(diff['Additions']) > 0 or
                    len(diff['Deletions']) > 0):
                    all_diffs[dataset_name + ":" + trait_name] = diff

                edited_sample_data = {} # Reset every 3 lines
        i += 1

    return all_diffs, all_diff_samples

def calculate_desc_diffs(conn, upload_file, group_name):
    all_diffs = {}

    file_text = upload_file.read().decode('utf-8') if hasattr(upload_file, 'read') else upload_file
    dialect = get_dialect(file_text)
    upload_reader = csv.reader(io.StringIO(file_text), dialect=dialect)

    group_id = retrieve_group_id(conn, group_name)

    # Choose Post_publication_description when a PubMed ID exists for the
    # cross-referenced publication, otherwise fall back to
    # Pre_publication_description.
    desc_query = """
            SELECT
                CASE
                    WHEN pub.PubMed_ID IS NOT NULL AND pub.PubMed_ID <> ''
                        THEN p.Post_publication_description
                    ELSE p.Pre_publication_description
                END AS chosen_description,
                p.*, pub.PubMed_ID
            FROM PublishXRef px
            JOIN Phenotype p ON px.PhenotypeId = p.Id
            LEFT JOIN Publication pub ON px.PublicationId = pub.Id
            WHERE px.InbredSetId = %(dataset_id)s
                AND px.Id = %(trait_id)s
    """

    for line in upload_reader:
        # Skip header if it exists (Record IDs will always either be integers or have underscores)
        if "_" not in line[0] and not line[0].isdigit():
            continue

        trait_id, new_desc = line[0], line[1]
        with conn.cursor() as cursor:
            cursor.execute(desc_query, {"dataset_id": group_id, "trait_id": trait_id})
            result = cursor.fetchone()
            if result:
                current_desc = result[0]
                if current_desc != new_desc:
                    all_diffs[group_name + ":" + trait_id] = {
                        "Original": current_desc,
                        "Current": new_desc
                    }

    return all_diffs


def __edit_with_authorisation__(thunk, dataset_name, trait_name, *auth_checkers):
    """Run `thunk` with authorisation enforced by `auth_checkers`."""
    assert(trait_name), "Invalid `trait_name` provided."
    assert(dataset_name), "Invalid `dataset_name` provided."
    authserver_url = current_app.config["AUTH_SERVER_URL"]
    def __headers__(token):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    def __handle_error__(error):
        flash(error, "alert alert-danger")
        return redirect(url_for(
            "show_trait_page", trait_id=trait_name, dataset=dataset_name))

    return session.user_token().then(
        lambda wrapper: wrapper["access_token"]
    ).then(# Fetch system roles
        lambda token: mrequests.get(
            urljoin(authserver_url, "auth/system/roles"),
            headers=__headers__(token)
        ).then(
            lambda system_roles: {
                "token": token,
                "system_privileges": tuple(privilege["privilege_id"]
                                           for role in system_roles
                                           for privilege in role["privileges"])
            }
        )
    ).then(# Fetch resource privileges
        lambda _bag_: mrequests.post(
            urljoin(authserver_url, "auth/data/authorisation"),
            headers=__headers__(_bag_["token"]),
            json={
                "traits": [f"{dataset_name}::{trait_name}"]
            }
        ).then(
            lambda resource_details: {
                **_bag_,
                "resource_privileges": tuple(resource_details[0]["privileges"])
            }
        )
    ).then(
        lambda _bag_: (
            Right(_bag_)
            if all(checker(_bag_["resource_privileges"],
                           _bag_["system_privileges"])
                   for checker in auth_checkers)
            else Left("You do not have sufficient privileges to edit this "
                      "trait's metadata."))
    ).either(
        __handle_error__,
        lambda _bag_: thunk(**_bag_))


@metadata_edit.route("/batch_edit", methods=["GET", "POST"])
def batch_edit_page() -> Response:
    if request.method == "POST":
        from gn2.utility.tools import get_setting
        with database_connection(get_setting("SQL_URI")) as conn:
            if 'traits_file' in request.files: # Review page
                data_type = request.form['data_type']
                upload_file = request.files['traits_file'].read().decode('utf-8')
                if data_type == 'samples':
                    transposed = True if 'transpose_file' in request.form else False
                    all_diffs, sample_list = calculate_sample_diffs(conn, upload_file, transposed, group_name=request.form['group'])
                    return render_template("batch_edit_samples_review.html", diffs = all_diffs, diffs_str = json.dumps(all_diffs), sample_list = sample_list)
                elif data_type == 'descriptions': # Description updates
                    all_diffs = calculate_desc_diffs(conn, upload_file, group_name=request.form['group'])
                    return render_template("batch_edit_desc_review.html", diffs=all_diffs, diffs_str=json.dumps(all_diffs))
            elif 'diffs' in request.form: # Actual DB update
                data_type = request.form['data_type']
                if data_type == 'samples':
                    diff_data = batch_update_sample_data(conn, json.loads(request.form['diffs']))
                elif data_type == 'descriptions':
                    diff_data = batch_update_descriptions(conn, json.loads(request.form['diffs']))
                return render_template("batch_edit_complete.html", diffs=diff_data, data_type=data_type)
    else:
        return client.get(
            "auth/system/roles"
        ).then(
            lambda sysroles: tuple(
                priv["privilege_id"] for role in sysroles
                for priv in role["privileges"])
        ).then(
            lambda sysprivileges: {
                "can_batch_edit": resources.can_batch_edit(sysprivileges)
            }
        ).either(
            lambda err: render_template(
                "batch_edit_submit.html",
                gn_server_url=current_app.config["GN_SERVER_URL"],
                **process_error(err)),
            lambda databag: render_template(
                "batch_edit_submit.html",
                gn_server_url=current_app.config["GN_SERVER_URL"],
                **databag))


@metadata_edit.route("/<dataset_id>/traits/<name>")
@login_required(pagename="phenotype edit")
def display_phenotype_metadata(dataset_id: str, name: str):
    def __do_display__(*args, **kwargs):
        from gn2.utility.tools import get_setting
        with database_connection(get_setting("SQL_URI")) as conn:
            _d = edit_phenotype(conn=conn, name=name, dataset_id=dataset_id)

            group_name = retrieve_phenotype_group_name(conn, dataset_id)
            sample_list = retrieve_sample_list(group_name)
            sample_data = {}
            if len(sample_list) < 5000:
                pheno_data = get_pheno_sample_data(conn, name, _d["publish_xref"]["phenotype_id"])
                # Ensure sample_data is a dict (some datasets may return a list or None)
                sample_data = pheno_data if isinstance(pheno_data, dict) else {}

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
                version=current_app.config.get("GN_VERSION"),
                dataset_name=request.args["dataset_name"])

    return __edit_with_authorisation__(__do_display__,
                                       request.args.get("dataset_name", ""),
                                       name,
                                       resources.can_view,
                                       resources.can_edit)


@metadata_edit.route("/traits/<name>")
def display_probeset_metadata(name: str):
    def __do_display__(*args, **kwargs):
        from gn2.utility.tools import get_setting
        with database_connection(get_setting("SQL_URI")) as conn:
            dataset_name=request.args["dataset_name"]
            _d = {"probeset": fetch_probeset_metadata_by_name(conn, name, dataset_name)}

            group_name = retrieve_mrna_group_name(conn, _d["probeset"]["id_"], dataset_name)
            sample_list = retrieve_sample_list(group_name)
            sample_data = get_mrna_sample_data(conn, _d["probeset"]["id_"], dataset_name)

            return render_template(
                "edit_probeset.html",
                diff=_d.get("diff"),
                probeset=_d.get("probeset"),
                probeset_id=_d["probeset"]["id_"],
                name=name,
                resource_id=request.args.get("resource-id"),
                version=current_app.config.get("GN_VERSION"),
                dataset_name=request.args["dataset_name"],
                sample_list=sample_list,
                sample_data=sample_data
            )

    return __edit_with_authorisation__(__do_display__,
                                       request.args.get("dataset_name", ""),
                                       name,
                                       resources.can_view,
                                       resources.can_edit)


@metadata_edit.route("/<dataset_id>/traits/<name>", methods=("POST",))
@login_required(pagename="phenotype update")
def update_phenotype(dataset_id: str, name: str):
    def __do_update__(*args, **kwargs):
        from gn2.utility.tools import get_setting
        data_ = request.form.to_dict()
        TMPDIR = current_app.config.get("TMPDIR")
        author = session.session_info()["user"]["user_id"]
        phenotype_id = str(data_.get("phenotype-id"))
        file_ = request.files.get("file")
        if not file_ and data_.get('edited') == "false":
            pass
        else:
            SAMPLE_DATADIR = os.path.join(TMPDIR, "sample-data")
            DIFF_DATADIR = os.path.join(SAMPLE_DATADIR, "diffs")
            UPLOAD_DATADIR = os.path.join(SAMPLE_DATADIR, "updated")
            create_dirs_if_not_exists([SAMPLE_DATADIR, DIFF_DATADIR, UPLOAD_DATADIR])

            current_time = str(datetime.datetime.now().isoformat())
            _file_name = (
                f"{author}.{request.args.get('resource-id')}." f"{current_time}"
            )
            diff_data = {}
            with database_connection(get_setting("SQL_URI")) as conn:
                group_name = retrieve_phenotype_group_name(conn, dataset_id)
                sample_list = retrieve_sample_list(group_name)
                headers = ["Strain Name", "Value", "SE", "Count"]
                base_csv = get_pheno_csv_sample_data(
                        conn=conn,
                        trait_name=name,
                        group_id=dataset_id,
                        sample_list=sample_list,
                )
                if not file_ and data_.get('edited') == "true":
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
                    delta_csv = file_.read().decode()
                    diff_data = remove_insignificant_edits(
                        diff_data=csv_diff(
                            base_csv=base_csv,
                            delta_csv=delta_csv,
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
            updated_phenotypes = _update_phenotype(
                conn, {"id_": data_["phenotype-id"], **{
                    key: value for key,value in phenotype_.items()
                    if value is not None}})
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
        def __parse_int__(val) -> Optional[int]:
            """Safe parser for integers"""
            try:
                return int(val, base=10)
            except ValueError as _verr:
                return None
            except TypeError as _terr:
                # trying to convert None
                return None
        publication_ = {
            key: val for key, val in {
                "pubmed_id": __parse_int__(data_.get("pubmed-id")),
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
                update_cross_reference(conn,
                                       dataset_id,
                                       name,
                                       {"publication_id": existing_publication['id_']})
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

    return __edit_with_authorisation__(__do_update__,
                                       request.args.get("dataset_name", ""),
                                       name,
                                       resources.can_view,
                                       resources.can_edit)


@metadata_edit.route("/traits/<name>", methods=("POST",))
def update_probeset(name: str):
    def __do_update__(*args, **kwargs):
        from gn2.utility.tools import get_setting
        data_ = request.form.to_dict()
        TMPDIR = current_app.config.get("TMPDIR")
        author = session.session_info()["user"]["user_id"]
        probeset_id=str(data_.get("id"))
        trait_name = str(data_.get("probeset_name"))
        dataset_name = str(data_.get("dataset_name"))

        file_ = request.files.get("file")
        if not file_ and data_.get('edited') == "false":
            pass
        else:
            SAMPLE_DATADIR = os.path.join(TMPDIR, "sample-data")
            DIFF_DATADIR = os.path.join(SAMPLE_DATADIR, "diffs")
            UPLOAD_DATADIR = os.path.join(SAMPLE_DATADIR, "updated")
            create_dirs_if_not_exists([SAMPLE_DATADIR, DIFF_DATADIR, UPLOAD_DATADIR])

            current_time = str(datetime.datetime.now().isoformat())
            _file_name = (
                f"{author}.{request.args.get('resource-id')}." f"{current_time}"
            )
            diff_data = {}
            with database_connection(get_setting("SQL_URI")) as conn:
                group_name = retrieve_mrna_group_name(conn, probeset_id, dataset_name)
                sample_list = retrieve_sample_list(group_name)
                headers = ["Strain Name", "Value", "SE", "Count"]

                base_csv = get_mrna_csv_sample_data(
                    conn=conn,
                    probeset_id=probeset_id,
                    dataset_name=dataset_name,
                    sample_list=retrieve_sample_list(group_name)
                )
                if not file_ and data_.get('edited') == "true":
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
                    delta_csv = file_.read().decode()
                    diff_data = remove_insignificant_edits(
                        diff_data=csv_diff(
                            base_csv=base_csv,
                            delta_csv=delta_csv,
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
                        f"/datasets/{dataset_name}/traits/{name}"
                        f"?resource-id={request.args.get('resource-id')}"
                        f"&dataset_name={request.args['dataset_name']}"
                    )
            # Edge case where the csv file has not been edited!
            if not any(diff_data.values()):
                flash(
                    "You have not modified the csv file you downloaded!", "warning"
                )
                return redirect(
                    f"/datasets/{dataset_name}/traits/{name}"
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
                        "trait_name": str(trait_name),
                        "probeset_id": str(probeset_id),
                        "dataset_name": dataset_name,
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

            updated_probesets = ""
            updated_probesets = _update_probeset(
                conn, probeset_id, {"id_": data_["id"], **{
                    key: value for key,value in probeset_.items()
                    if value is not None}})

            if updated_probesets:
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

    return __edit_with_authorisation__(__do_update__,
                                       request.args.get("dataset_id", ""),
                                       name,
                                       resources.can_view,
                                       resources.can_edit)


@metadata_edit.route("/pheno/<name>/group/<group_id>/csv")
@login_required()
def get_pheno_sample_data_as_csv(name: int, group_id: int):
    from gn2.utility.tools import get_setting
    with database_connection(get_setting("SQL_URI")) as conn:
        group_name = retrieve_phenotype_group_name(conn, group_id)
        return Response(
            get_pheno_csv_sample_data(
                conn=conn,
                trait_name=name,
                group_id=group_id,
                sample_list=retrieve_sample_list(group_name)
            ),
            mimetype="text/csv",
            headers={
                "Content-disposition": f"attachment; \
filename=sample-data-{group_name}-{name}.csv"
            },
        )

@metadata_edit.route("/mrna/<probeset_id>/dataset/<dataset_name>/csv")
@login_required()
def get_mrna_sample_data_as_csv(probeset_id: int, dataset_name: str):
    from gn2.utility.tools import get_setting

    with database_connection(get_setting("SQL_URI")) as conn:
        csv_data = get_mrna_csv_sample_data(
                conn=conn,
                probeset_id=str(probeset_id),
                dataset_name=str(dataset_name),
                sample_list=retrieve_sample_list(
                    retrieve_mrna_group_name(conn, probeset_id, dataset_name))
            )
        return Response(
            get_mrna_csv_sample_data(
                conn=conn,
                probeset_id=str(probeset_id),
                dataset_name=str(dataset_name),
                sample_list=retrieve_sample_list(
                    retrieve_mrna_group_name(conn, probeset_id, dataset_name))
            ),
            mimetype="text/csv",
            headers={
                "Content-disposition": f"attachment; \
filename=sample-data-{probeset_id}.csv"
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
        "auth/data/authorisation",
        json={
            "traits": [
                f"{meta['diff']['dataset_name']}::{meta['diff']['trait_name']}"
                for meta in files
            ]
        }
    ).map(
        lambda lst: [auth_item for auth_item in lst
                     if resources.can_edit(auth_item["privileges"])]
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
    from gn2.utility.tools import get_setting
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
        diff={key: set(val) for key,val in diff_data_},
        version=current_app.config.get("GN_VERSION"),
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
        return resources.can_edit(dets["privileges"])

    return client.post(
        "auth/data/authorisation",
        json={"traits": [f"{dataset_name}::{trait_name}"]}
    ).map(
        lambda adets: {
            f"{dets['dataset_name']}::{dets['trait_name']}": dets
            for dets in adets
        }
    ).either(__error__, __success__)

@metadata_edit.route("<resource_id>/diffs/<file_name>/reject")
@login_required(pagename="sample data rejection")
def reject_data(resource_id: str, file_name: str):
    def __do_reject__(*args, **kwargs):
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

    return __edit_with_authorisation__(__do_reject__,
                                       request.args.get("dataset_name", ""),
                                       request.args.get("trait_name", ""),
                                       resources.can_view,
                                       resources.can_edit)

@metadata_edit.route("<resource_id>/diffs/<file_name>/approve")
@login_required(pagename="Sample Data Approval")
def approve_data(resource_id: str, file_name: str):
    def __do_approve__(*args, **kwargs):
        from gn2.utility.tools import get_setting
        sample_data = {file_name: str}
        TMPDIR = current_app.config.get("TMPDIR")
        diffpath = Path(TMPDIR, "sample-data/diffs", file_name)
        if not diffpath.exists():
            flash(f"Could not find diff with the name '{diffpath.name}'",
                  "alert-danger")
            return redirect(url_for("metadata_edit.list_diffs"))

        n_deletions = 0
        n_insertions = 0
        with open(diffpath, "r") as myfile:
            sample_data = json.load(myfile)

        if not __authorised_p__(sample_data["dataset_name"],
                                sample_data["trait_name"]):
            flash("You are not authorised to edit that trait.", "alert-danger")
            return redirect(url_for("metadata_edit.list_diffs"))

        # Define the trait_info that is passed into the update functions, by data type
        if sample_data.get("probeset_id"):  # if trait is ProbeSet
            trait_info = {
                'probeset_id': int(sample_data.get("probeset_id")),
                'dataset_name': sample_data.get("dataset_name")
            }
        else:  # if trait is Publish
            trait_info = {
                'trait_name': sample_data.get("trait_name"),
                'phenotype_id': int(sample_data.get("phenotype_id"))
            }

        with database_connection(get_setting("SQL_URI")) as conn:
            modifications = [d for d in sample_data.get("Modifications")]
            for modification in modifications:
                if modification.get("Current"):
                    update_sample_data(
                        conn=conn,
                        original_data=modification.get("Original"),
                        updated_data=modification.get("Current"),
                        csv_header=sample_data.get(
                            "Columns", "Strain Name,Value,SE,Count"
                        ),
                        trait_info=trait_info,
                    )

            # Deletions
            for data in [d for d in sample_data.get("Deletions")]:
                __deletions = delete_sample_data(
                    conn=conn,
                    data=data,
                    csv_header=sample_data.get(
                        "Columns", "Strain Name,Value,SE,Count"
                    ),
                    trait_info=trait_info
                )
                if __deletions:
                    n_deletions += 1
                # Remove any data that already exists from sample_data deletes
                else:
                    sample_data.get("Deletions").remove(data)

            ## Insertions
            for data in [d for d in sample_data.get("Additions")]:

                __insertions = insert_sample_data(
                    conn=conn,
                    data=data,
                    csv_header=sample_data.get(
                        "Columns", "Strain Name,Value,SE,Count"
                    ),
                    trait_info=trait_info
                )
                if __insertions:
                    n_insertions += 1
                else:
                    sample_data.get("Additions").remove(data)
        if any(
            [
                sample_data.get("Additions"),
                sample_data.get("Modifications"),
                sample_data.get("Deletions"),
            ]
        ):
            with database_connection(get_setting("SQL_URI")) as conn:
                if sample_data.get("dataset_id"): # if phenotype
                    create_metadata_audit(conn, {
                        "dataset_id": sample_data.get("dataset_id"),
                        "editor": sample_data.get("author"),
                        "json_data": json.dumps(sample_data, cls=CustomJSONEncoder)
                    })
                else:
                    create_metadata_audit(conn, {
                        "dataset_id": sample_data.get("probeset_id"),
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
                flash(f"# Additions: {len(n_insertions)}", "success")
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

    return __edit_with_authorisation__(__do_approve__,
                                       request.args.get("dataset_name", ""),
                                       request.args.get("trait_name", ""),
                                       resources.can_view,
                                       resources.can_edit)


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
