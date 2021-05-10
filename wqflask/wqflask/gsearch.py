import json
import datetime as dt
from types import SimpleNamespace

from flask import Flask, g
from base.data_set import create_dataset
from base.trait import create_trait
from db import webqtlDatabaseFunction

from base import webqtlConfig

from utility import hmac

from utility.benchmark import Bench
from utility.authentication_tools import check_resource_availability
from utility.type_checking import is_float, is_int, is_str, get_float, get_int, get_string

from utility.logger import getLogger
logger = getLogger(__name__)


class GSearch:

    def __init__(self, kw):
        assert('type' in kw)
        assert('terms' in kw)

        self.type = kw['type']
        self.terms = kw['terms']
        assert(is_str(self.type))

        if self.type == "gene":
            sql = """
                SELECT
                Species.`Name` AS species_name,
                InbredSet.`Name` AS inbredset_name,
                Tissue.`Name` AS tissue_name,
                ProbeSetFreeze.Name AS probesetfreeze_name,
                ProbeSetFreeze.FullName AS probesetfreeze_fullname,
                ProbeSet.Name AS probeset_name,
                ProbeSet.Symbol AS probeset_symbol,
                CAST(ProbeSet.`description` AS BINARY) AS probeset_description,
                ProbeSet.Chr AS chr,
                ProbeSet.Mb AS mb,
                ProbeSetXRef.Mean AS mean,
                ProbeSetXRef.LRS AS lrs,
                ProbeSetXRef.`Locus` AS locus,
                ProbeSetXRef.`pValue` AS pvalue,
                ProbeSetXRef.`additive` AS additive,
                ProbeSetFreeze.Id AS probesetfreeze_id,
                Geno.Chr as geno_chr,
                Geno.Mb as geno_mb
                FROM Species 
                INNER JOIN InbredSet ON InbredSet.`SpeciesId`=Species.`Id` 
                INNER JOIN ProbeFreeze ON ProbeFreeze.InbredSetId=InbredSet.`Id` 
                INNER JOIN Tissue ON ProbeFreeze.`TissueId`=Tissue.`Id` 
                INNER JOIN ProbeSetFreeze ON ProbeSetFreeze.ProbeFreezeId=ProbeFreeze.Id 
                INNER JOIN ProbeSetXRef ON ProbeSetXRef.ProbeSetFreezeId=ProbeSetFreeze.Id 
                INNER JOIN ProbeSet ON ProbeSet.Id = ProbeSetXRef.ProbeSetId 
                LEFT JOIN Geno ON ProbeSetXRef.Locus = Geno.Name AND Geno.SpeciesId = Species.Id
                WHERE ( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,ProbeSet.alias,ProbeSet.GenbankId, ProbeSet.UniGeneId, ProbeSet.Probe_Target_Description) AGAINST ('%s' IN BOOLEAN MODE) )
                AND ProbeSetFreeze.confidentiality < 1
                AND ProbeSetFreeze.public > 0
                ORDER BY species_name, inbredset_name, tissue_name, probesetfreeze_name, probeset_name
                LIMIT 6000
                """ % (self.terms)
            with Bench("Running query"):
                logger.sql(sql)
                re = g.db.execute(sql).fetchall()

            trait_list = []
            dataset_to_permissions = {}
            with Bench("Creating trait objects"):
                for i, line in enumerate(re):
                    this_trait = {}
                    this_trait['index'] = i + 1
                    this_trait['name'] = line[5]
                    this_trait['dataset'] = line[3]
                    this_trait['dataset_fullname'] = line[4]
                    this_trait['hmac'] = hmac.data_hmac(
                        '{}:{}'.format(line[5], line[3]))
                    this_trait['species'] = line[0]
                    this_trait['group'] = line[1]
                    this_trait['tissue'] = line[2]
                    this_trait['symbol'] = line[6]
                    if line[7]:
                        this_trait['description'] = line[7].decode(
                            'utf-8', 'replace')
                    else:
                        this_trait['description'] = "N/A"
                    this_trait['location_repr'] = 'N/A'
                    if (line[8] != "NULL" and line[8] != "") and (line[9] != 0):
                        this_trait['location_repr'] = 'Chr%s: %.6f' % (
                            line[8], float(line[9]))
                    try:
                        this_trait['mean'] = '%.3f' % line[10]
                    except:
                        this_trait['mean'] = "N/A"
                    this_trait['LRS_score_repr'] = "N/A"
                    if line[11] != "" and line[11] != None:
                        this_trait['LRS_score_repr'] = '%3.1f' % line[11]
                    this_trait['additive'] = "N/A"
                    if line[14] != "" and line[14] != None:
                        this_trait['additive'] = '%.3f' % line[14]
                    this_trait['dataset_id'] = line[15]
                    this_trait['locus_chr'] = line[16]
                    this_trait['locus_mb'] = line[17]

                    dataset_ob = SimpleNamespace(
                        id=this_trait["dataset_id"], type="ProbeSet", species=this_trait["species"])
                    if dataset_ob.id not in dataset_to_permissions:
                        permissions = check_resource_availability(dataset_ob)
                        dataset_to_permissions[dataset_ob.id] = permissions
                    else:
                        pemissions = dataset_to_permissions[dataset_ob.id]
                    if type(permissions['data']) is list:
                        if "view" not in permissions['data']:
                            continue
                    else:
                        if permissions['data'] == 'no-access':
                            continue

                    max_lrs_text = "N/A"
                    if this_trait['locus_chr'] and this_trait['locus_mb']:
                        max_lrs_text = f"Chr{str(this_trait['locus_chr'])}: {str(this_trait['locus_mb'])}"
                    this_trait['max_lrs_text'] = max_lrs_text

                    trait_list.append(this_trait)

            self.trait_count = len(trait_list)
            self.trait_list = trait_list

            self.header_fields = ['Index',
                                  'Record',
                                  'Species',
                                  'Group',
                                  'Tissue',
                                  'Dataset',
                                  'Symbol',
                                  'Description',
                                  'Location',
                                  'Mean',
                                  'Max LRS',
                                  'Max LRS Location',
                                  'Additive Effect']

            self.header_data_names = [
                'index',
                'name',
                'species',
                'group',
                'tissue',
                'dataset_fullname',
                'symbol',
                'description',
                'location_repr',
                'mean',
                'LRS_score_repr',
                'max_lrs_text',
                'additive',
            ]

        elif self.type == "phenotype":
            search_term = self.terms
            group_clause = ""
            if "_" in self.terms:
                if len(self.terms.split("_")[0]) == 3:
                    search_term = self.terms.split("_")[1]
                    group_clause = "AND InbredSet.`InbredSetCode` = '{}'".format(
                        self.terms.split("_")[0])
            sql = """
                SELECT
                Species.`Name`,
                InbredSet.`Name`,
                PublishFreeze.`Name`,
                PublishFreeze.`FullName`,
                PublishXRef.`Id`,
                CAST(Phenotype.`Pre_publication_description` AS BINARY),
                CAST(Phenotype.`Post_publication_description` AS BINARY),
                Publication.`Authors`,
                Publication.`Year`,
                Publication.`PubMed_ID`,
                PublishXRef.`LRS`,
                PublishXRef.`additive`,
                InbredSet.`InbredSetCode`,
                PublishXRef.`mean`,
                PublishFreeze.Id,
                Geno.Chr as geno_chr,
                Geno.Mb as geno_mb 
                FROM Species 
                INNER JOIN InbredSet ON InbredSet.`SpeciesId`=Species.`Id` 
                INNER JOIN PublishFreeze ON PublishFreeze.`InbredSetId`=InbredSet.`Id` 
                INNER JOIN PublishXRef ON PublishXRef.`InbredSetId`=InbredSet.`Id` 
                INNER JOIN Phenotype ON PublishXRef.`PhenotypeId`=Phenotype.`Id` 
                INNER JOIN Publication ON PublishXRef.`PublicationId`=Publication.`Id` 
                LEFT JOIN Geno ON PublishXRef.Locus = Geno.Name AND Geno.SpeciesId = Species.Id 
                WHERE 
                (
                    (MATCH (Phenotype.Post_publication_description, Phenotype.Pre_publication_description, Phenotype.Pre_publication_abbreviation, Phenotype.Post_publication_abbreviation, Phenotype.Lab_code) AGAINST ('{1}' IN BOOLEAN MODE) )
                    OR (MATCH (Publication.Abstract, Publication.Title, Publication.Authors) AGAINST ('{1}' IN BOOLEAN MODE) )
                )
                {0}
                ORDER BY Species.`Name`, InbredSet.`Name`, PublishXRef.`Id`
                LIMIT 6000
                """.format(group_clause, search_term)
            logger.sql(sql)
            re = g.db.execute(sql).fetchall()
            trait_list = []
            with Bench("Creating trait objects"):
                for i, line in enumerate(re):
                    this_trait = {}
                    this_trait['index'] = i + 1
                    this_trait['name'] = str(line[4])
                    if len(str(line[12])) == 3:
                        this_trait['display_name'] = str(
                            line[12]) + "_" + this_trait['name']
                    else:
                        this_trait['display_name'] = this_trait['name']
                    this_trait['dataset'] = line[2]
                    this_trait['dataset_fullname'] = line[3]
                    this_trait['hmac'] = hmac.data_hmac(
                        '{}:{}'.format(line[4], line[2]))
                    this_trait['species'] = line[0]
                    this_trait['group'] = line[1]
                    if line[9] != None and line[6] != None:
                        this_trait['description'] = line[6].decode(
                            'utf-8', 'replace')
                    elif line[5] != None:
                        this_trait['description'] = line[5].decode(
                            'utf-8', 'replace')
                    else:
                        this_trait['description'] = "N/A"
                    if line[13] != None and line[13] != "":
                        this_trait['mean'] = f"{line[13]:.3f}"
                    else:
                        this_trait['mean'] = "N/A"
                    this_trait['dataset_id'] = line[14]
                    this_trait['locus_chr'] = line[15]
                    this_trait['locus_mb'] = line[16]
                    this_trait['authors'] = line[7]
                    this_trait['year'] = line[8]
                    if this_trait['year'].isdigit():
                        this_trait['pubmed_text'] = this_trait['year']
                    else:
                        this_trait['pubmed_text'] = "N/A"
                    if line[9] != "" and line[9] != None:
                        this_trait['pubmed_link'] = webqtlConfig.PUBMEDLINK_URL % line[8]
                    else:
                        this_trait['pubmed_link'] = "N/A"
                        if line[12]:
                            this_trait['display_name'] = line[12] + \
                                "_" + str(this_trait['name'])
                    this_trait['LRS_score_repr'] = "N/A"
                    if line[10] != "" and line[10] != None:
                        this_trait['LRS_score_repr'] = '%3.1f' % line[10]
                    this_trait['additive'] = "N/A"
                    if line[11] != "" and line[11] != None:
                        this_trait['additive'] = '%.3f' % line[11]

                    dataset_ob = SimpleNamespace(id=this_trait["dataset_id"], type="Publish", species=this_trait["species"])
                    permissions = check_resource_availability(dataset_ob, this_trait['name'])
                    if type(permissions['data']) is list:
                        if "view" not in permissions['data']:
                            continue
                    else:
                        if permissions['data'] == 'no-access':
                            continue

                    this_trait['max_lrs_text'] = "N/A"
                    if this_trait['dataset'] == this_trait['group'] + "Publish":
                        try:
                            if this_trait['locus_chr'] and this_trait['locus_mb']:
                                this_trait['max_lrs_text'] = f"Chr{str(this_trait['locus_chr'])}: {str(this_trait['locus_mb'])}"
                        except:
                            this_trait['max_lrs_text'] = "N/A"

                    trait_list.append(this_trait)

            self.trait_count = len(trait_list)
            self.trait_list = trait_list

            self.header_fields = ['Index',
                                'Species',
                                'Group',
                                'Record',
                                'Description',
                                'Authors',
                                'Year',
                                'Max LRS',
                                'Max LRS Location',
                                'Additive Effect']

            self.header_data_names = [
                'index',
                'name',
                'species',
                'group',
                'tissue',
                'dataset_fullname',
                'symbol',
                'description',
                'location_repr',
                'mean',
                'LRS_score_repr',
                'max_lrs_text',
                'additive',
            ]
