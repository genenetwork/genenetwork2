# GN2 API

from __future__ import absolute_import, division, print_function

import os, io, csv, json, datetime, requests
from zipfile import ZipFile

import StringIO

import flask
from flask import g, Response, request, make_response, render_template, send_from_directory, jsonify, redirect, send_file
import sqlalchemy
from wqflask import app

from wqflask.api import correlation, mapping, gen_menu

from utility.tools import flat_files

import utility.logger
logger = utility.logger.getLogger(__name__ )

version = "pre1"

@app.route("/api/v_{}/".format(version))
def hello_world():
    return flask.jsonify({"hello":"world"})

@app.route("/api/v_{}/species".format(version))
def get_species_list():
    results = g.db.execute("SELECT SpeciesId, Name, FullName, TaxonomyId FROM Species;")
    the_species = results.fetchall()
    species_list = []
    for species in the_species:
        species_dict = {
          "Id"         : species[0],
          "Name"       : species[1],
          "FullName"   : species[2],
          "TaxonomyId" : species[3]
        }
        species_list.append(species_dict)

    return flask.jsonify(species_list)

@app.route("/api/v_{}/species/<path:species_name>".format(version))
@app.route("/api/v_{}/species/<path:species_name>.<path:file_format>".format(version))
def get_species_info(species_name, file_format = "json"):
    results = g.db.execute("""SELECT SpeciesId, Name, FullName, TaxonomyId 
                              FROM Species 
                              WHERE (Name="{0}" OR FullName="{0}" OR SpeciesName="{0}");""".format(species_name))

    the_species = results.fetchone()
    species_dict = { 
      "Id"         : the_species[0],
      "Name"       : the_species[1],
      "FullName"   : the_species[2],
      "TaxonomyId" : the_species[3]
    }
    
    return flask.jsonify(species_dict)

@app.route("/api/v_{}/groups".format(version))
@app.route("/api/v_{}/groups/<path:species_name>".format(version))
def get_groups_list(species_name=None):
    if species_name:
        results = g.db.execute("""SELECT InbredSet.InbredSetId, InbredSet.SpeciesId, InbredSet.InbredSetName,
                                         InbredSet.Name, InbredSet.FullName, InbredSet.public,
                                         IFNULL(InbredSet.MappingMethodId, "None"), IFNULL(InbredSet.GeneticType, "None")
                                  FROM InbredSet, Species
                                  WHERE InbredSet.SpeciesId = Species.Id AND
                                        (Species.Name = "{0}" OR
                                         Species.FullName="{0}" OR
                                         Species.SpeciesName="{0}");""".format(species_name))
    else:
        results = g.db.execute("""SELECT InbredSet.InbredSetId, InbredSet.SpeciesId, InbredSet.InbredSetName, 
                                         InbredSet.Name, InbredSet.FullName, InbredSet.public, 
                                         IFNULL(InbredSet.MappingMethodId, "None"), IFNULL(InbredSet.GeneticType, "None")
                                  FROM InbredSet;""")

    the_groups = results.fetchall()
    if the_groups:
        groups_list = []
        for group in the_groups:
            group_dict = {
              "Id"              : group[0],
              "SpeciesId"       : group[1],
              "DisplayName"     : group[2],
              "Name"            : group[3],
              "FullName"        : group[4],
              "public"          : group[5],
              "MappingMethodId" : group[6],
              "GeneticType"     : group[7]
            }
            groups_list.append(group_dict)

        return flask.jsonify(groups_list)
    else:
        return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/group/<path:group_name>".format(version))
@app.route("/api/v_{}/group/<path:group_name>.<path:file_format>".format(version))
@app.route("/api/v_{}/group/<path:species_name>/<path:group_name>".format(version))
@app.route("/api/v_{}/group/<path:species_name>/<path:group_name>.<path:file_format>".format(version))
def get_group_info(group_name, species_name = None, file_format = "json"):
    if species_name:
        results = g.db.execute("""SELECT InbredSet.InbredSetId, InbredSet.SpeciesId, InbredSet.InbredSetName, 
                                         InbredSet.Name, InbredSet.FullName, InbredSet.public, 
                                         IFNULL(InbredSet.MappingMethodId, "None"), IFNULL(InbredSet.GeneticType, "None")
                                  FROM InbredSet, Species
                                  WHERE InbredSet.SpeciesId = Species.Id AND
                                        (InbredSet.InbredSetName = "{0}" OR
                                         InbredSet.Name = "{0}" OR
                                         InbredSet.FullName = "{0}") AND
                                        (Species.Name = "{1}" OR
                                         Species.FullName="{1}" OR
                                         Species.SpeciesName="{1}");""".format(group_name, species_name))
    else:
        results = g.db.execute("""SELECT InbredSet.InbredSetId, InbredSet.SpeciesId, InbredSet.InbredSetName, 
                                         InbredSet.Name, InbredSet.FullName, InbredSet.public, 
                                         IFNULL(InbredSet.MappingMethodId, "None"), IFNULL(InbredSet.GeneticType, "None")
                                  FROM InbredSet
                                  WHERE (InbredSet.InbredSetName = "{0}" OR
                                         InbredSet.Name = "{0}" OR
                                         InbredSet.FullName = "{0}");""".format(group_name))

    group = results.fetchone()
    if group:
        group_dict = {
          "Id"              : group[0],
          "SpeciesId"       : group[1],
          "DisplayName"     : group[2],
          "Name"            : group[3],
          "FullName"        : group[4],
          "public"          : group[5],
          "MappingMethodId" : group[6],
          "GeneticType"     : group[7]
        }

        return flask.jsonify(group_dict)
    else:
        return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/datasets/<path:group_name>".format(version))
@app.route("/api/v_{}/datasets/<path:species_name>/<path:group_name>".format(version))
def get_datasets_for_group(group_name, species_name=None):
    if species_name:
        results = g.db.execute("""
                                  SELECT ProbeSetFreeze.Id, ProbeSetFreeze.ProbeFreezeId, ProbeSetFreeze.AvgID,
                                         ProbeSetFreeze.Name, ProbeSetFreeze.Name2, ProbeSetFreeze.FullName,
                                         ProbeSetFreeze.ShortName, ProbeSetFreeze.CreateTime, ProbeSetFreeze.public,
                                         ProbeSetFreeze.confidentiality, ProbeSetFreeze.DataScale
                                  FROM ProbeSetFreeze, ProbeFreeze, InbredSet, Species
                                  WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id AND
                                        ProbeFreeze.InbredSetId = InbredSet.Id AND
                                        (InbredSet.Name = "{0}" OR InbredSet.InbredSetName = "{0}" OR InbredSet.FullName = "{0}") AND
                                        InbredSet.SpeciesId = Species.Id AND
                                        (Species.SpeciesName = "{1}" OR Species.MenuName = "{1}" OR Species.FullName = "{1}");
                               """.format(group_name, species_name))
    else:
        results = g.db.execute("""
                                  SELECT ProbeSetFreeze.Id, ProbeSetFreeze.ProbeFreezeId, ProbeSetFreeze.AvgID,
                                         ProbeSetFreeze.Name, ProbeSetFreeze.Name2, ProbeSetFreeze.FullName,
                                         ProbeSetFreeze.ShortName, ProbeSetFreeze.CreateTime, ProbeSetFreeze.public,
                                         ProbeSetFreeze.confidentiality, ProbeSetFreeze.DataScale
                                  FROM ProbeSetFreeze, ProbeFreeze, InbredSet
                                  WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id AND
                                        ProbeFreeze.InbredSetId = InbredSet.Id AND
                                        (InbredSet.Name = "{0}" OR InbredSet.InbredSetName = "{0}" OR InbredSet.FullName = "{0}");
                               """.format(group_name))

    the_datasets = results.fetchall()

    if the_datasets:
        datasets_list = []
        for dataset in the_datasets:
            dataset_dict = {
              "Id"                 : dataset[0],
              "ProbeFreezeId"      : dataset[1],
              "AvgID"              : dataset[2],
              "Short_Abbreviation" : dataset[3],
              "Long_Abbreviation"  : dataset[4],
              "FullName"           : dataset[5],
              "ShortName"          : dataset[6],
              "CreateTime"         : dataset[7],
              "public"             : dataset[8],
              "confidentiality"    : dataset[9],
              "DataScale"          : dataset[10]
            }
            datasets_list.append(dataset_dict)

        return flask.jsonify(datasets_list)
    else:
        return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/dataset/<path:dataset_name>".format(version))
@app.route("/api/v_{}/dataset/<path:dataset_name>.<path:file_format>".format(version))
@app.route("/api/v_{}/dataset/<path:group_name>/<path:dataset_name>".format(version))
@app.route("/api/v_{}/dataset/<path:group_name>/<path:dataset_name>.<path:file_format>".format(version))
def get_dataset_info(dataset_name, group_name = None, file_format="json"):
    #ZS: First get ProbeSet (mRNA expression) datasets and then get Phenotype datasets

    datasets_list = [] #ZS: I figure I might as well return a list if there are multiple matches, though I don"t know if this will actually happen in practice

    probeset_query = """
                SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.FullName,
                       ProbeSetFreeze.ShortName, ProbeSetFreeze.DataScale, ProbeFreeze.TissueId,
                       Tissue.Name, ProbeSetFreeze.public, ProbeSetFreeze.confidentiality
                FROM ProbeSetFreeze, ProbeFreeze, Tissue
            """

    where_statement = """
                         WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id AND
                               ProbeFreeze.TissueId = Tissue.Id AND
                               ProbeSetFreeze.public > 0 AND
                               ProbeSetFreeze.confidentiality < 1 AND
                      """
    if dataset_name.isdigit():
        where_statement += """
                              ProbeSetFreeze.Id = "{}"
                           """.format(dataset_name)
    else:
        where_statement += """
                              (ProbeSetFreeze.Name = "{0}" OR ProbeSetFreeze.Name2 = "{0}" OR
                              ProbeSetFreeze.FullName = "{0}" OR ProbeSetFreeze.ShortName = "{0}")
                           """.format(dataset_name)

    probeset_query += where_statement
    probeset_results = g.db.execute(probeset_query)
    dataset = probeset_results.fetchone()

    if dataset:
        dataset_dict = {
          "dataset_type" : "mRNA expression",
          "id"           : dataset[0],
          "name"         : dataset[1],
          "full_name"    : dataset[2],
          "short_name"   : dataset[3],
          "data_scale"   : dataset[4],
          "tissue_id"    : dataset[5],
          "tissue"       : dataset[6],
          "public"       : dataset[7],
          "confidential" : dataset[8]
        }

        datasets_list.append(dataset_dict)

    if group_name:
        pheno_query = """
                         SELECT PublishXRef.Id, Phenotype.Post_publication_abbreviation, Phenotype.Post_publication_description,
                                Phenotype.Pre_publication_abbreviation, Phenotype.Pre_publication_description,
                                Publication.PubMed_ID, Publication.Title, Publication.Year
                         FROM PublishXRef, Phenotype, Publication, InbredSet, PublishFreeze
                         WHERE PublishXRef.InbredSetId = InbredSet.Id AND
                               PublishXRef.PhenotypeId = Phenotype.Id AND
                               PublishXRef.PublicationId = Publication.Id AND
                               PublishFreeze.InbredSetId = InbredSet.Id AND
                               PublishFreeze.public > 0 AND
                               PublishFreeze.confidentiality < 1 AND
                               InbredSet.Name = "{0}" AND PublishXRef.Id = "{1}"
                      """.format(group_name, dataset_name)

        logger.debug("QUERY:", pheno_query)

        pheno_results = g.db.execute(pheno_query)
        dataset = pheno_results.fetchone()

        if dataset:
            if dataset[5]:
                dataset_dict = {
                  "dataset_type" : "phenotype",
                  "id"           : dataset[0],
                  "name"         : dataset[1],
                  "description"  : dataset[2],
                  "pubmed_id"    : dataset[5],
                  "title"        : dataset[6],
                  "year"         : dataset[7]
                }
            elif dataset[4]:
                dataset_dict = {
                  "dataset_type" : "phenotype",
                  "id"           : dataset[0],
                  "name"         : dataset[3],
                  "description"  : dataset[4]
                }
            else:
                dataset_dict = {
                  "dataset_type" : "phenotype",
                  "id"           : dataset[0]
                }

            datasets_list.append(dataset_dict)

    if len(datasets_list) > 1:
        return flask.jsonify(datasets_list)
    elif len(datasets_list) == 1:
        return flask.jsonify(dataset_dict)
    else:
        return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/traits/<path:dataset_name>".format(version), methods=("GET",))
@app.route("/api/v_{}/traits/<path:dataset_name>.<path:file_format>".format(version), methods=("GET",))
def fetch_traits(dataset_name, file_format = "json"):
    trait_ids, trait_names, data_type, dataset_id = get_dataset_trait_ids(dataset_name, request.args)
    if ("ids_only" in request.args) and (len(trait_ids) > 0):
        if file_format == "json":
            filename = dataset_name + "_trait_ids.json"
            return flask.jsonify(trait_ids)
        else:
            filename = dataset_name + "_trait_ids.csv"

            si = StringIO.StringIO()
            csv_writer = csv.writer(si)
            csv_writer.writerows([[trait_id] for trait_id in trait_ids])
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=" + filename
            output.headers["Content-type"] = "text/csv"
            return output
    elif ("names_only" in request.args) and (len(trait_ids) > 0):
        if file_format == "json":
            filename = dataset_name + "_trait_names.json"
            return flask.jsonify(trait_names)
        else:
            filename = dataset_name + "_trait_names.csv"

            si = StringIO.StringIO()
            csv_writer = csv.writer(si)
            csv_writer.writerows([[trait_name] for trait_name in trait_names])
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=" + filename
            output.headers["Content-type"] = "text/csv"
            return output
    else:
        if len(trait_ids) > 0:
            if data_type == "ProbeSet":
                query = """
                            SELECT
                                ProbeSet.Id, ProbeSet.Name, ProbeSet.Symbol, ProbeSet.description, ProbeSet.Chr, ProbeSet.Mb, ProbeSet.alias,
                                ProbeSetXRef.mean, ProbeSetXRef.se, ProbeSetXRef.Locus, ProbeSetXRef.LRS, ProbeSetXRef.pValue, ProbeSetXRef.additive, ProbeSetXRef.h2
                            FROM
                                ProbeSet, ProbeSetXRef, ProbeSetFreeze
                            WHERE
                                ProbeSetXRef.ProbeSetFreezeId = "{0}" AND
                                ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                                ProbeSetFreeze.public > 0 AND
                                ProbeSetFreeze.confidentiality < 1
                            ORDER BY
                                ProbeSet.Id
                        """

                field_list = ["Id", "Name", "Symbol", "Description", "Chr", "Mb", "Aliases", "Mean", "SE", "Locus", "LRS", "P-Value", "Additive", "h2"]
            elif data_type == "Geno":
                query = """
                            SELECT
                                Geno.Id, Geno.Name, Geno.Marker_Name, Geno.Chr, Geno.Mb, Geno.Sequence, Geno.Source
                            FROM
                                Geno, GenoXRef, GenoFreeze
                            WHERE
                                GenoXRef.GenoFreezeId = "{0}" AND
                                GenoXRef.GenoId = Geno.Id AND
                                GenoXRef.GenoFreezeId = GenoFreeze.Id AND
                                GenoFreeze.public > 0 AND
                                GenoFreeze.confidentiality < 1
                            ORDER BY
                                Geno.Id
                        """

                field_list = ["Id", "Name", "Marker_Name", "Chr", "Mb", "Sequence", "Source"]
            else:
                query = """
                            SELECT
                                PublishXRef.Id, PublishXRef.PhenotypeId, PublishXRef.PublicationId, PublishXRef.Locus, PublishXRef.LRS, PublishXRef.additive, PublishXRef.Sequence
                            FROM
                                PublishXRef, PublishFreeze
                            WHERE
                                PublishXRef.InbredSetId = {0} AND
                                PublishFreeze.InbredSetId = PublishXRef.InbredSetId AND
                                PublishFreeze.public > 0 AND
                                PublishFreeze.confidentiality < 1
                            ORDER BY
                                PublishXRef.Id
                        """

                field_list = ["Id", "PhenotypeId", "PublicationId", "Locus", "LRS", "Additive", "Sequence"]

            if 'limit_to' in request.args:
                limit_number = request.args['limit_to']
                query += "LIMIT " + str(limit_number)

            if file_format == "json":
                filename = dataset_name + "_traits.json"

                final_query = query.format(dataset_id)

                result_list = []
                for result in g.db.execute(final_query).fetchall():
                    trait_dict = {}
                    for i, field in enumerate(field_list):
                        if result[i]:
                            trait_dict[field] = result[i]
                    result_list.append(trait_dict)

                return flask.jsonify(result_list)
            elif file_format == "csv":
                filename = dataset_name + "_traits.csv"

                results_list = []
                header_list = []
                header_list += field_list
                results_list.append(header_list)

                final_query = query.format(dataset_id)
                for result in g.db.execute(final_query).fetchall():
                    results_list.append(result)

                si = StringIO.StringIO()
                csv_writer = csv.writer(si)
                csv_writer.writerows(results_list)
                output = make_response(si.getvalue())
                output.headers["Content-Disposition"] = "attachment; filename=" + filename
                output.headers["Content-type"] = "text/csv"
                return output
            else:
                return return_error(code=400, source=request.url_rule.rule, title="Invalid Output Format", details="Current formats available are JSON and CSV, with CSV as default")
        else:
            return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/sample_data/<path:dataset_name>".format(version))
@app.route("/api/v_{}/sample_data/<path:dataset_name>.<path:file_format>".format(version))
def all_sample_data(dataset_name, file_format = "csv"):
    trait_ids, trait_names, data_type, dataset_id = get_dataset_trait_ids(dataset_name, request.args)

    if len(trait_ids) > 0:
        sample_list = get_samplelist(dataset_name)

        if data_type == "ProbeSet":
            query = """
                        SELECT
                            Strain.Name, Strain.Name2, ProbeSetData.value, ProbeSetData.Id, ProbeSetSE.error
                        FROM
                            (ProbeSetData, Strain, ProbeSetXRef, ProbeSetFreeze)
                        LEFT JOIN ProbeSetSE ON
                            (ProbeSetSE.DataId = ProbeSetData.Id AND ProbeSetSE.StrainId = ProbeSetData.StrainId)
                        WHERE
                            ProbeSetXRef.ProbeSetFreezeId = "{0}" AND
                            ProbeSetXRef.ProbeSetId = "{1}" AND
                            ProbeSetXRef.DataId = ProbeSetData.Id AND
                            ProbeSetData.StrainId = Strain.Id AND
                            ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                            ProbeSetFreeze.public > 0 AND
                            ProbeSetFreeze.confidentiality < 1
                        ORDER BY
                            Strain.Name
                    """
        elif data_type == "Geno":
            query = """
                        SELECT
                            Strain.Name, Strain.Name2, GenoData.value, GenoData.Id, GenoSE.error
                        FROM
                            (GenoData, Strain, GenoXRef, GenoFreeze)
                        LEFT JOIN GenoSE ON
                            (GenoSE.DataId = GenoData.Id AND GenoSE.StrainId = GenoData.StrainId)
                        WHERE
                            GenoXRef.GenoFreezeId = "{0}" AND
                            GenoXRef.GenoId = "{1}" AND
                            GenoXRef.DataId = GenoData.Id AND
                            GenoData.StrainId = Strain.Id AND
                            GenoXRef.GenoFreezeId = GenoFreeze.Id AND
                            GenoFreeze.public > 0 AND
                            GenoFreeze.confidentiality < 1
                        ORDER BY
                            Strain.Name
                    """
        else:
            query = """
                        SELECT
                            Strain.Name, Strain.Name2, PublishData.value, PublishData.Id, PublishSE.error, NStrain.count
                        FROM
                            (PublishData, Strain, PublishXRef, PublishFreeze)
                        LEFT JOIN PublishSE ON
                            (PublishSE.DataId = PublishData.Id AND PublishSE.StrainId = PublishData.StrainId)
                        LEFT JOIN NStrain ON
                            (NStrain.DataId = PublishData.Id AND
                            NStrain.StrainId = PublishData.StrainId)
                        WHERE
                            PublishXRef.InbredSetId = "{0}" AND
                            PublishXRef.PhenotypeId = "{1}" AND
                            PublishData.Id = PublishXRef.DataId AND
                            PublishData.StrainId = Strain.Id AND
                            PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                            PublishFreeze.public > 0 AND
                            PublishFreeze.confidentiality < 1
                        ORDER BY
                            Strain.Name
                    """

        if file_format == "csv":
            filename = dataset_name + "_sample_data.csv"

            results_list = []
            header_list = []
            header_list.append("id")
            header_list += sample_list
            results_list.append(header_list)
            for i, trait_id in enumerate(trait_ids):
                line_list = []
                line_list.append(str(trait_names[i]))
                final_query = query.format(dataset_id, trait_id)
                results = g.db.execute(final_query).fetchall()
                results_dict = {}
                for item in results:
                    results_dict[item[0]] = item[2]
                for sample in sample_list:
                    if sample in results_dict:
                        line_list.append(results_dict[sample])
                    else:
                        line_list.append("x")
                results_list.append(line_list)

            si = StringIO.StringIO()
            csv_writer = csv.writer(si)
            csv_writer.writerows(results_list)
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=" + filename
            output.headers["Content-type"] = "text/csv"
            return output
        else:
            return return_error(code=415, source=request.url_rule.rule, title="Unsupported file format", details="")
    else:
        return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/sample_data/<path:dataset_name>/<path:trait_name>".format(version))
@app.route("/api/v_{}/sample_data/<path:dataset_name>/<path:trait_name>.<path:file_format>".format(version))
def trait_sample_data(dataset_name, trait_name, file_format = "json"):
    probeset_query = """
                        SELECT
                            Strain.Name, Strain.Name2, ProbeSetData.value, ProbeSetData.Id, ProbeSetSE.error
                        FROM
                            (ProbeSetData, ProbeSetFreeze, Strain, ProbeSet, ProbeSetXRef)
                        LEFT JOIN ProbeSetSE ON
                            (ProbeSetSE.DataId = ProbeSetData.Id AND ProbeSetSE.StrainId = ProbeSetData.StrainId)
                        WHERE
                            ProbeSet.Name = "{0}" AND ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                            ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                            ProbeSetFreeze.Name = "{1}" AND
                            ProbeSetXRef.DataId = ProbeSetData.Id AND
                            ProbeSetData.StrainId = Strain.Id
                        ORDER BY
                            Strain.Name
                     """.format(trait_name, dataset_name)

    probeset_results = g.db.execute(probeset_query)

    sample_data = probeset_results.fetchall()
    if len(sample_data) > 0:
        sample_list = []
        for sample in sample_data:
            sample_dict = {
              "sample_name"   : sample[0],
              "sample_name_2" : sample[1],
              "value"         : sample[2],
              "data_id"       : sample[3],
            }
            if sample[4]:
                sample_dict["se"] = sample[4]
            sample_list.append(sample_dict)

        return flask.jsonify(sample_list)
    else:
        if not dataset_name.isdigit():
            group_id = get_group_id(dataset_name)
            if group_id:
                dataset_or_group = group_id
            else:
                dataset_or_group = dataset_name
        else:
            dataset_or_group = dataset_name

        pheno_query = """
                         SELECT DISTINCT
                             Strain.Name, Strain.Name2, PublishData.value, PublishData.Id, PublishSE.error, NStrain.count
                         FROM
                             (PublishData, Strain, PublishXRef, PublishFreeze)
                         LEFT JOIN PublishSE ON
                             (PublishSE.DataId = PublishData.Id AND PublishSE.StrainId = PublishData.StrainId)
                         LEFT JOIN NStrain ON
                             (NStrain.DataId = PublishData.Id AND
                             NStrain.StrainId = PublishData.StrainId)
                         WHERE
                             PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                             PublishData.Id = PublishXRef.DataId AND PublishXRef.Id = "{1}" AND
                             (PublishFreeze.Id = "{0}" OR PublishFreeze.Name = "{0}" OR
                              PublishFreeze.ShortName = "{0}" OR PublishXRef.InbredSetId = "{0}") AND
                             PublishData.StrainId = Strain.Id
                         ORDER BY
                             Strain.Name
                      """.format(dataset_or_group, trait_name)

        pheno_results = g.db.execute(pheno_query)

        sample_data = pheno_results.fetchall()
        if len(sample_data) > 0:
            sample_list = []
            for sample in sample_data:
                sample_dict = {
                  "sample_name"   : sample[0],
                  "sample_name_2" : sample[1],
                  "value"         : sample[2],
                  "data_id"       : sample[3]
                }
                if sample[4]:
                    sample_dict["se"] = sample[4]
                if sample[5]:
                    sample_dict["n_cases"] = sample[5]
                sample_list.append(sample_dict)

            return flask.jsonify(sample_list)
        else:
            return return_error(code=204, source=request.url_rule.rule, title="No Results", details="") 

@app.route("/api/v_{}/trait/<path:dataset_name>/<path:trait_name>".format(version))
@app.route("/api/v_{}/trait/<path:dataset_name>/<path:trait_name>.<path:file_format>".format(version))
@app.route("/api/v_{}/trait_info/<path:dataset_name>/<path:trait_name>".format(version))
@app.route("/api/v_{}/trait_info/<path:dataset_name>/<path:trait_name>.<path:file_format>".format(version))
def get_trait_info(dataset_name, trait_name, file_format = "json"):
    probeset_query = """
                        SELECT
                            ProbeSet.Id, ProbeSet.Name, ProbeSet.Symbol, ProbeSet.description, ProbeSet.Chr, ProbeSet.Mb, ProbeSet.alias,
                            ProbeSetXRef.mean, ProbeSetXRef.se, ProbeSetXRef.Locus, ProbeSetXRef.LRS, ProbeSetXRef.pValue, ProbeSetXRef.additive
                        FROM
                            ProbeSet, ProbeSetXRef, ProbeSetFreeze
                        WHERE
                            ProbeSet.Name = "{0}" AND
                            ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                            ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                            ProbeSetFreeze.Name = "{1}"
                     """.format(trait_name, dataset_name)

    probeset_results = g.db.execute(probeset_query)

    trait_info = probeset_results.fetchone()
    if trait_info:
        trait_dict = {
            "id"          : trait_info[0],
            "name"        : trait_info[1],
            "symbol"      : trait_info[2],
            "description" : trait_info[3],
            "chr"         : trait_info[4],
            "mb"          : trait_info[5],
            "alias"       :trait_info[6],
            "mean"        : trait_info[7],
            "se"          : trait_info[8],
            "locus"       : trait_info[9],
            "lrs"         : trait_info[10],
            "p_value"     : trait_info[11],
            "additive"    : trait_info[12]
        }

        return flask.jsonify(trait_dict)
    else:
        if "Publish" in dataset_name: #ZS: Check if the user input the dataset_name as BXDPublish, etc (which is always going to be the group name + "Publish"
            dataset_name = dataset_name.replace("Publish", "")
        
        group_id = get_group_id(dataset_name)
        pheno_query = """
                         SELECT
                             PublishXRef.PhenotypeId, PublishXRef.Locus, PublishXRef.LRS, PublishXRef.additive
                         FROM
                             PublishXRef
                         WHERE
                             PublishXRef.Id = "{0}" AND
                             PublishXRef.InbredSetId = "{1}"
                      """.format(trait_name, group_id)

        pheno_results = g.db.execute(pheno_query)

        trait_info = pheno_results.fetchone()
        if trait_info:
            trait_dict = {
                "id"       : trait_info[0],
                "locus"    : trait_info[1],
                "lrs"      : trait_info[2],
                "additive" : trait_info[3]
            }

            return flask.jsonify(trait_dict)
        else:
            return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/correlation".format(version), methods=("GET",))
def get_corr_results():
    results = correlation.do_correlation(request.args)

    if len(results) > 0:
        return flask.jsonify(results) #ZS: I think flask.jsonify expects a dict/list instead of JSON
    else:
        return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/mapping".format(version), methods=("GET",))
def get_mapping_results():
    results, format = mapping.do_mapping_for_api(request.args)

    if len(results) > 0:
        if format == "csv":
            filename = "mapping_" + datetime.datetime.utcnow().strftime("%b_%d_%Y_%I:%M%p") + ".csv"

            si = StringIO.StringIO()
            csv_writer = csv.writer(si)
            csv_writer.writerows(results)
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=" + filename
            output.headers["Content-type"] = "text/csv"

            return output
        elif format == "json":
            return flask.jsonify(results)
        else:
            return return_error(code=415, source=request.url_rule.rule, title="Unsupported Format", details="")
    else:
        return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

@app.route("/api/v_{}/genotypes/<path:group_name>.<path:file_format>".format(version))
@app.route("/api/v_{}/genotypes/<path:file_format>/<path:group_name>".format(version))
@app.route("/api/v_{}/genotypes/<path:group_name>.<path:file_format>".format(version))
def get_genotypes(group_name, file_format="csv"):
    limit_num = None
    if 'limit_to' in request.args:
        if request.args['limit_to'].isdigit():
            limit_num = int(request.args['limit_to'])

    si = StringIO.StringIO()
    if file_format == "csv" or file_format == "geno":
        filename = group_name + ".geno"

        if os.path.isfile("{0}/{1}.geno".format(flat_files("genotype"), group_name)):
            output_lines = []
            with open("{0}/{1}.geno".format(flat_files("genotype"), group_name)) as genofile:
                i = 0
                for line in genofile:
                    if line[0] == "#" or line[0] == "@":
                        output_lines.append([line.strip()])
                    else:
                        if limit_num and i >= limit_num:
                            break
                        output_lines.append(line.split())
                        i += 1

            csv_writer = csv.writer(si, delimiter = "\t", escapechar = "\\", quoting = csv.QUOTE_NONE)
        else:
            return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")
    elif file_format == "rqtl2":
        memory_file = io.BytesIO()
        filename = group_name + "_rqtl.zip"

        if os.path.isfile("{0}/{1}_geno.csv".format(flat_files("genotype/rqtl2"), group_name)):
            config_file = open("{0}/{1}.yaml".format(flat_files("genotype/rqtl2"), group_name))
            geno_file = open("{0}/{1}_geno.csv".format(flat_files("genotype/rqtl2"), group_name))
            gmap_file = open("{0}/{1}_gmap.csv".format(flat_files("genotype/rqtl2"), group_name))
            phenotypes = requests.get("http://gn2.genenetwork.org/api/v_pre1/sample_data/" + group_name + "Publish")

            with ZipFile(memory_file, 'w') as zf:
                for this_file in [config_file, geno_file, gmap_file]:
                    zf.writestr(this_file.name.split("/")[-1], this_file.read())
                zf.writestr("{0}_pheno.csv".format(group_name), phenotypes.content)

            memory_file.seek(0)

            return send_file(memory_file, attachment_filename=filename, as_attachment=True)
        else:
            return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")
    else:
        filename = group_name + ".bimbam"

        if os.path.isfile("{0}/{1}.geno".format(flat_files("genotype"), group_name)):
            output_lines = []
            with open("{0}/{1}_geno.txt".format(flat_files("genotype/bimbam"), group_name)) as genofile:
                i = 0
                for line in genofile:
                    if limit_num and i >= limit_num:
                        break
                    output_lines.append([line.strip() for line in line.split(",")])
                    i += 1

            csv_writer = csv.writer(si, delimiter = ",")
        else:
            return return_error(code=204, source=request.url_rule.rule, title="No Results", details="")

    csv_writer.writerows(output_lines)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=" + filename
    output.headers["Content-type"] = "text/csv"

    return output

@app.route("/api/v_{}/gen_dropdown".format(version), methods=("GET",))
def gen_dropdown_menu():
    results = gen_menu.gen_dropdown_json()

    if len(results) > 0:
        return flask.jsonify(results)
    else:
        return return_error(code=500, source=request.url_rule.rule, title="Some error occurred", details="")

def return_error(code, source, title, details):
    json_ob = {"errors": [
        {
            "status": code,
            "source": { "pointer": source },
            "title" : title,
            "detail": details
        }
    ]}

    return flask.jsonify(json_ob)

def get_dataset_trait_ids(dataset_name, start_vars):

    if 'limit_to' in start_vars:
        limit_string = "LIMIT " + str(start_vars['limit_to'])
    else:
        limit_string = ""

    if "Geno" in dataset_name:
        data_type = "Geno" #ZS: Need to pass back the dataset type
        query =    """
                            SELECT
                                GenoXRef.GenoId, Geno.Name, GenoXRef.GenoFreezeId
                            FROM
                                Geno, GenoXRef, GenoFreeze
                            WHERE
                                Geno.Id = GenoXRef.GenoId AND
                                GenoXRef.GenoFreezeId = GenoFreeze.Id AND
                                GenoFreeze.Name = "{0}"
                            {1}
                        """.format(dataset_name, limit_string)

        results = g.db.execute(query).fetchall()

        trait_ids = [result[0] for result in results]
        trait_names = [result[1] for result in results]
        dataset_id = results[0][2]
        return trait_ids, trait_names, data_type, dataset_id

    elif "Publish" in dataset_name or get_group_id(dataset_name):
        data_type = "Publish"
        dataset_name = dataset_name.replace("Publish", "")
        dataset_id = get_group_id(dataset_name)
        
        query = """
                         SELECT
                             PublishXRef.PhenotypeId
                         FROM
                             PublishXRef
                         WHERE
                             PublishXRef.InbredSetId = "{0}"
                         {1}
                      """.format(dataset_id, limit_string)

        results = g.db.execute(query).fetchall()

        trait_ids = [result[0] for result in results]
        trait_names = trait_ids
        return trait_ids, trait_names, data_type, dataset_id

    else:
        data_type = "ProbeSet"
        query = """
                        SELECT
                            ProbeSetXRef.ProbeSetId, ProbeSet.Name, ProbeSetXRef.ProbeSetFreezeId
                        FROM
                            ProbeSet, ProbeSetXRef, ProbeSetFreeze
                        WHERE
                            ProbeSet.Id = ProbeSetXRef.ProbeSetId AND
                            ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                            ProbeSetFreeze.Name = "{0}"
                        {1}
                     """.format(dataset_name, limit_string)

        results = g.db.execute(query).fetchall()

        trait_ids = [result[0] for result in results]
        trait_names = [result[1] for result in results]
        dataset_id = results[0][2]
        return trait_ids, trait_names, data_type, dataset_id

def get_samplelist(dataset_name):
    group_id = get_group_id_from_dataset(dataset_name)

    query = """
               SELECT Strain.Name
               FROM Strain, StrainXRef
               WHERE StrainXRef.StrainId = Strain.Id AND
                     StrainXRef.InbredSetId = {}
            """.format(group_id)
    
    results = g.db.execute(query).fetchall()
    
    samplelist = [result[0] for result in results]

    return samplelist

def get_group_id_from_dataset(dataset_name):
    if "Publish" in dataset_name:
        query = """
                    SELECT
                            InbredSet.Id
                    FROM
                            InbredSet, PublishFreeze
                    WHERE
                            PublishFreeze.InbredSetId = InbredSet.Id AND
                            PublishFreeze.Name = "{}"
                """.format(dataset_name)
    elif "Geno" in dataset_name:
        query = """
                    SELECT
                            InbredSet.Id
                    FROM
                            InbredSet, GenoFreeze
                    WHERE
                            GenoFreeze.InbredSetId = InbredSet.Id AND
                            GenoFreeze.Name = "{}"
                """.format(dataset_name)
    else:
        query = """
                    SELECT
                            InbredSet.Id
                    FROM
                            InbredSet, ProbeSetFreeze, ProbeFreeze
                    WHERE
                            ProbeFreeze.InbredSetId = InbredSet.Id AND
                            ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId AND
                            ProbeSetFreeze.Name = "{}"
                """.format(dataset_name)

    result = g.db.execute(query).fetchone()

    if len(result) > 0:
        return result[0]
    else:
        return None

def get_group_id(group_name):
    query = """
               SELECT InbredSet.Id
               FROM InbredSet
               WHERE InbredSet.Name = "{}"
            """.format(group_name)

    group_id = g.db.execute(query).fetchone()
    if group_id:
        return group_id[0]
    else:
        return None