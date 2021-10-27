import MySQLdb
import os
import json
import datetime
import difflib


from collections import namedtuple
from flask import (Blueprint, current_app, redirect,
                   flash, g, render_template, request)
from itertools import groupby

from wqflask.decorators import edit_access_required

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
from gn3.commands import run_cmd
from gn3.db.traits import get_trait_csv_sample_data
from gn3.db.traits import update_sample_data


metadata_edit = Blueprint('metadata_edit', __name__)


def edit_phenotype(conn, name, dataset_id):
    publish_xref = fetchone(
        conn=conn,
        table="PublishXRef",
        where=PublishXRef(id_=name,
                          inbred_set_id=dataset_id))
    phenotype_ = fetchone(
        conn=conn,
        table="Phenotype",
        where=Phenotype(id_=publish_xref.phenotype_id))
    publication_ = fetchone(
        conn=conn,
        table="Publication",
        where=Publication(id_=publish_xref.publication_id))
    json_data = fetchall(
        conn,
        "metadata_audit",
        where=MetadataAudit(dataset_id=publish_xref.id_))
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
                        Diff(author=author,
                             diff=Edit(field,
                                       data_.get("old"),
                                       data_.get("new"),
                                       "\n".join(difflib.ndiff(
                                           [data_.get("old")],
                                           [data_.get("new")]))),
                             timestamp=timestamp))
    diff_data_ = None
    if len(diff_data) > 0:
        diff_data_ = groupby(diff_data, lambda x: x.timestamp)
    return {
        "diff": diff_data_,
        "publish_xref": publish_xref,
        "phenotype": phenotype_,
        "publication": publication_,
    }


def edit_probeset(conn, name):
    probeset_ = fetchone(conn=conn,
                         table="ProbeSet",
                         columns=list(probeset_mapping.values()),
                         where=Probeset(name=name))
    json_data = fetchall(
        conn,
        "metadata_audit",
        where=MetadataAudit(dataset_id=probeset_.id_))
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
                        Diff(author=author,
                             diff=Edit(field,
                                       data_.get("old"),
                                       data_.get("new"),
                                       "\n".join(difflib.ndiff(
                                           [data_.get("old")],
                                           [data_.get("new")]))),
                             timestamp=timestamp))
    diff_data_ = None
    if len(diff_data) > 0:
        diff_data_ = groupby(diff_data, lambda x: x.timestamp)
    return {
        "diff": diff_data_,
        "probeset": probeset_,
    }


@metadata_edit.route("/<dataset_id>/traits/<name>")
@edit_access_required
def display_phenotype_metadata(dataset_id: str, name: str):
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    _d = edit_phenotype(conn=conn, name=name, dataset_id=dataset_id)
    return render_template(
        "edit_phenotype.html",
        diff=_d.get("diff"),
        publish_xref=_d.get("publish_xref"),
        phenotype=_d.get("phenotype"),
        publication=_d.get("publication"),
        dataset_id=dataset_id,
        resource_id=request.args.get("resource-id"),
        version=os.environ.get("GN_VERSION"),
    )


@metadata_edit.route("/traits/<name>")
@edit_access_required
def display_probeset_metadata(name: str):
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    _d = edit_probeset(conn=conn, name=name)
    return render_template(
        "edit_probeset.html",
        diff=_d.get("diff"),
        probeset=_d.get("probeset"),
        resource_id=request.args.get("resource-id"),
        version=os.environ.get("GN_VERSION"),
    )


@metadata_edit.route("/<dataset_id>/traits/<name>", methods=("POST",))
@edit_access_required
def update_phenotype(dataset_id: str, name: str):
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
    data_ = request.form.to_dict()
    TMPDIR = current_app.config.get("TMPDIR")
    author = ((g.user_session.record.get(b"user_id") or b"").decode("utf-8")
               or g.user_session.record.get("user_id") or "")
    phenotype_id = str(data_.get('phenotype-id'))
    if 'file' not in request.files:
        flash("No sample-data has been uploaded", "warning")
    else:
        file_ = request.files['file']
        SAMPLE_DATADIR = os.path.join(TMPDIR, "sample-data")
        if not os.path.exists(SAMPLE_DATADIR):
            os.makedirs(SAMPLE_DATADIR)
        if not os.path.exists(os.path.join(SAMPLE_DATADIR,
                                           "diffs")):
            os.makedirs(os.path.join(SAMPLE_DATADIR,
                                     "diffs"))
        if not os.path.exists(os.path.join(SAMPLE_DATADIR,
                                           "updated")):
            os.makedirs(os.path.join(SAMPLE_DATADIR,
                                     "updated"))
        current_time = str(datetime.datetime.now().isoformat())
        new_file_name = (os.path.join(TMPDIR,
                                      "sample-data/updated/",
                                      (f"{author}."
                                       f"{name}.{phenotype_id}."
                                       f"{current_time}.csv")))
        uploaded_file_name = (os.path.join(
            TMPDIR,
            "sample-data/updated/",
            (f"updated.{author}."
             f"{request.args.get('resource-id')}."
             f"{current_time}.csv")))
        file_.save(new_file_name)
        publishdata_id = ""
        lines = []
        with open(new_file_name, "r") as f:
            lines = f.read()
            first_line = lines.split('\n', 1)[0]
            publishdata_id = first_line.split("Id:")[-1].strip()
        with open(new_file_name, "w") as f:
            f.write(lines.split("\n\n")[-1])
        csv_ = get_trait_csv_sample_data(conn=conn,
                                         trait_name=str(name),
                                         phenotype_id=str(phenotype_id))
        with open(uploaded_file_name, "w") as f_:
            f_.write(csv_.split("\n\n")[-1])
        r = run_cmd(cmd=("csvdiff "
                         f"'{uploaded_file_name}' '{new_file_name}' "
                         "--format json"))
        diff_output = (f"{TMPDIR}/sample-data/diffs/"
                       f"{author}.{request.args.get('resource-id')}."
                       f"{current_time}.json")
        with open(diff_output, "w") as f:
            dict_ = json.loads(r.get("output"))
            dict_.update({
                "author": author,
                "publishdata_id": publishdata_id,
                "dataset_id": data_.get("dataset-name"),
                "timestamp": datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S")
            })
            f.write(json.dumps(dict_))
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
    updated_phenotypes = update(
        conn, "Phenotype",
        data=Phenotype(**phenotype_),
        where=Phenotype(id_=data_.get("phenotype-id")))
    diff_data = {}
    if updated_phenotypes:
        diff_data.update({"Phenotype": diff_from_dict(old={
            k: data_.get(f"old_{k}") for k, v in phenotype_.items()
            if v is not None}, new=phenotype_)})
    publication_ = {
        "abstract": data_.get("abstract"),
        "authors": data_.get("authors"),
        "title": data_.get("title"),
        "journal": data_.get("journal"),
        "volume": data_.get("volume"),
        "pages": data_.get("pages"),
        "month": data_.get("month"),
        "year": data_.get("year")
    }
    updated_publications = update(
        conn, "Publication",
        data=Publication(**publication_),
        where=Publication(id_=data_.get("pubmed-id",
                                        data_.get("old_id_"))))
    if updated_publications:
        diff_data.update({"Publication": diff_from_dict(old={
            k: data_.get(f"old_{k}") for k, v in publication_.items()
            if v is not None}, new=publication_)})
    if diff_data:
        diff_data.update({"dataset_id": name})
        diff_data.update({"resource_id": request.args.get('resource-id')})
        diff_data.update({"author": author})
        diff_data.update({"timestamp": datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")})
        insert(conn,
               table="metadata_audit",
               data=MetadataAudit(dataset_id=name,
                                  editor=author,
                                  json_data=json.dumps(diff_data)))
        flash(f"Diff-data: \n{diff_data}\nhas been uploaded", "success")
    return redirect(f"/datasets/{dataset_id}/traits/{name}"
                    f"?resource-id={request.args.get('resource-id')}")


@metadata_edit.route("/traits/<name>", methods=["POST"])
@edit_access_required
def update_probeset(name: str):
    conn = MySQLdb.Connect(db=current_app.config.get("DB_NAME"),
                           user=current_app.config.get("DB_USER"),
                           passwd=current_app.config.get("DB_PASS"),
                           host=current_app.config.get("DB_HOST"))
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
        "flag": data_.get("flag")
    }
    diff_data = {}
    author = ((g.user_session.record.get(b"user_id") or b"").decode("utf-8")
               or g.user_session.record.get("user_id") or "")
    if (updated_probeset := update(
            conn, "ProbeSet",
            data=Probeset(**probeset_),
            where=Probeset(id_=data_.get("id")))):
        diff_data.update({"Probeset": diff_from_dict(old={
            k: data_.get(f"old_{k}") for k, v in probeset_.items()
            if v is not None}, new=probeset_)})
    if diff_data:
        diff_data.update({"probeset_name": data_.get("probeset_name")})
        diff_data.update({"author": author})
        diff_data.update({"resource_id": request.args.get('resource-id')})
        diff_data.update({"timestamp": datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")})
        insert(conn,
               table="metadata_audit",
               data=MetadataAudit(dataset_id=data_.get("id"),
                                  editor=author.decode("utf-8"),
                                  json_data=json.dumps(diff_data)))
    return redirect(f"/datasets/traits/{name}"
                    f"?resource-id={request.args.get('resource-id')}")

