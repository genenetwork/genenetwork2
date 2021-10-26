import MySQLdb
import os
import json
import difflib


from collections import namedtuple
from flask import Blueprint, current_app, render_template, request
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


@metadata_edit.route("/<dataset_id>/traits/<name>/edit")
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
        resource_id=request.args.get("resource-id"),
        version=os.environ.get("GN_VERSION"),
    )


@metadata_edit.route("/traits/<name>/edit")
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
