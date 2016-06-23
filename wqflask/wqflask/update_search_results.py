from __future__ import absolute_import, print_function, division

import json

from flask import Flask, g
from base.data_set import create_dataset
from base.trait import GeneralTrait
from db import webqtlDatabaseFunction

from utility.benchmark import Bench

from utility.logger import getLogger
logger = getLogger(__name__)

class GSearch(object):

    def __init__(self, kw):
        self.type = kw['type']
        self.terms = kw['terms']
        #self.row_range = kw['row_range']
        if self.type == "gene":
            sql = """
                SELECT
                Species.`Name` AS species_name,
                InbredSet.`Name` AS inbredset_name,
                Tissue.`Name` AS tissue_name,
                ProbeSetFreeze.Name AS probesetfreeze_name,
                ProbeSet.Name AS probeset_name,
                ProbeSet.Symbol AS probeset_symbol,
                ProbeSet.`description` AS probeset_description,
                ProbeSet.Chr AS chr,
                ProbeSet.Mb AS mb,
                ProbeSetXRef.Mean AS mean,
                ProbeSetXRef.LRS AS lrs,
                ProbeSetXRef.`Locus` AS locus,
                ProbeSetXRef.`pValue` AS pvalue,
                ProbeSetXRef.`additive` AS additive
                FROM Species, InbredSet, ProbeSetXRef, ProbeSet, ProbeFreeze, ProbeSetFreeze, Tissue
                WHERE InbredSet.`SpeciesId`=Species.`Id`
                AND ProbeFreeze.InbredSetId=InbredSet.`Id`
                AND ProbeFreeze.`TissueId`=Tissue.`Id`
                AND ProbeSetFreeze.ProbeFreezeId=ProbeFreeze.Id
                AND ( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,alias,GenbankId, UniGeneId, Probe_Target_Description) AGAINST ('%s' IN BOOLEAN MODE) )
                AND ProbeSet.Id = ProbeSetXRef.ProbeSetId
                AND ProbeSetXRef.ProbeSetFreezeId=ProbeSetFreeze.Id
                AND ProbeSetFreeze.public > 0
                ORDER BY species_name, inbredset_name, tissue_name, probesetfreeze_name, probeset_name
                LIMIT 6000
                """ % (self.terms)
            with Bench("Running query"):
                logger.sql(sql)
                re = g.db.execute(sql).fetchall()
            self.trait_list = []
            with Bench("Creating trait objects"):
                for line in re:
                    dataset = create_dataset(line[3], "ProbeSet", get_samplelist=False)
                    trait_id = line[4]
                    #with Bench("Building trait object"):
                    this_trait = GeneralTrait(dataset=dataset, name=trait_id, get_qtl_info=True, get_sample_info=False)
                    self.trait_list.append(this_trait)

        elif self.type == "phenotype":
            sql = """
                SELECT
                Species.`Name`,
                InbredSet.`Name`,
                PublishFreeze.`Name`,
                PublishXRef.`Id`,
                Phenotype.`Post_publication_description`,
                Publication.`Authors`,
                Publication.`Year`,
                PublishXRef.`LRS`,
                PublishXRef.`Locus`,
                PublishXRef.`additive`
                FROM Species,InbredSet,PublishFreeze,PublishXRef,Phenotype,Publication
                WHERE PublishXRef.`InbredSetId`=InbredSet.`Id`
                AND PublishFreeze.`InbredSetId`=InbredSet.`Id`
                AND InbredSet.`SpeciesId`=Species.`Id`
                AND PublishXRef.`PhenotypeId`=Phenotype.`Id`
                AND PublishXRef.`PublicationId`=Publication.`Id`
                AND	  (Phenotype.Post_publication_description REGEXP "[[:<:]]%s[[:>:]]"
                    OR Phenotype.Pre_publication_description REGEXP "[[:<:]]%s[[:>:]]"
                    OR Phenotype.Pre_publication_abbreviation REGEXP "[[:<:]]%s[[:>:]]"
                    OR Phenotype.Post_publication_abbreviation REGEXP "[[:<:]]%s[[:>:]]"
                    OR Phenotype.Lab_code REGEXP "[[:<:]]%s[[:>:]]"
                    OR Publication.PubMed_ID REGEXP "[[:<:]]%s[[:>:]]"
                    OR Publication.Abstract REGEXP "[[:<:]]%s[[:>:]]"
                    OR Publication.Title REGEXP "[[:<:]]%s[[:>:]]"
                    OR Publication.Authors REGEXP "[[:<:]]%s[[:>:]]"
                    OR PublishXRef.Id REGEXP "[[:<:]]%s[[:>:]]")
                ORDER BY Species.`Name`, InbredSet.`Name`, PublishXRef.`Id`
                LIMIT 6000
                """ % (self.terms, self.terms, self.terms, self.terms, self.terms, self.terms, self.terms, self.terms, self.terms, self.terms)
            logger.sql(sql)
            re = g.db.execute(sql).fetchall()
            self.trait_list = []
            with Bench("Creating trait objects"):
                for line in re:
                    dataset = create_dataset(line[2], "Publish")
                    trait_id = line[3]
                    this_trait = GeneralTrait(dataset=dataset, name=trait_id, get_qtl_info=True, get_sample_info=False)
                    self.trait_list.append(this_trait)

        self.results = self.convert_to_json()

    def convert_to_json(self):
        json_dict = {}
        #json_dict['draw'] = self.draw,
        json_dict['recordsTotal'] = len(self.trait_list),
        json_dict['data'] = []

        for i, trait in enumerate(self.trait_list):
            trait_row = { "checkbox": "<INPUT TYPE=\"checkbox\" NAME=\"searchResult\" class=\"checkbox trait_checkbox\" style=\"transform: scale(1.5);\" VALUE=\"{}:{}\">".format(trait.name, trait.dataset.name),
                         "index": i+1,
                         "species": trait.dataset.group.species,
                         "group": trait.dataset.group.name,
                         "tissue": trait.dataset.tissue,
                         "dataset": trait.dataset.fullname,
                         "record": "<a href=\"/show_trait?trait_id=" + trait.name + "&dataset=" + trait.dataset.name + "\" target=\"_blank\">" + trait.name + "</a>",
                         "symbol": trait.symbol,
                         "description": trait.description_display,
                         "location": trait.location_repr,
                         "mean": trait.mean,
                         "max_lrs": trait.LRS_score_repr,
                         "max_lrs_location": trait.LRS_location_repr,
                         "additive_effect": trait.additive}
            json_dict['data'].append(trait_row)

        json_results = json.dumps(json_dict)
        return json_results
