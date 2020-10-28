import json

from flask import Flask, g
from base.data_set import create_dataset
from base.trait import create_trait
from db import webqtlDatabaseFunction

from base import webqtlConfig

from utility import hmac

from utility.type_checking import is_float, is_int, is_str, get_float, get_int, get_string
from utility.benchmark import Bench

from utility.logger import getLogger
logger = getLogger(__name__)

class GSearch(object):

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
                ProbeSetXRef.`additive` AS additive
                FROM Species, InbredSet, ProbeSetXRef, ProbeSet, ProbeFreeze, ProbeSetFreeze, Tissue
                WHERE InbredSet.`SpeciesId`=Species.`Id`
                AND ProbeFreeze.InbredSetId=InbredSet.`Id`
                AND ProbeFreeze.`TissueId`=Tissue.`Id`
                AND ProbeSetFreeze.ProbeFreezeId=ProbeFreeze.Id
                AND ( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,alias,GenbankId, UniGeneId, Probe_Target_Description) AGAINST ('%s' IN BOOLEAN MODE) )
                AND ProbeSet.Id = ProbeSetXRef.ProbeSetId
                AND ProbeSetXRef.ProbeSetFreezeId=ProbeSetFreeze.Id
                AND ProbeSetFreeze.confidentiality < 1
                AND ProbeSetFreeze.public > 0
                ORDER BY species_name, inbredset_name, tissue_name, probesetfreeze_name, probeset_name
                LIMIT 6000
                """ % (self.terms)
            with Bench("Running query"):
                logger.sql(sql)
                re = g.db.execute(sql).fetchall()

            trait_list = []
            with Bench("Creating trait objects"):
                for i, line in enumerate(re):
                    this_trait = {}
                    this_trait['index'] = i + 1
                    this_trait['name'] = line[5]
                    this_trait['dataset'] = line[3]
                    this_trait['dataset_fullname'] = line[4]
                    this_trait['hmac'] = hmac.data_hmac('{}:{}'.format(line[5], line[3]))
                    this_trait['species'] = line[0]
                    this_trait['group'] = line[1]
                    this_trait['tissue'] = line[2]
                    this_trait['symbol'] = line[6]
                    if line[7]:
                        this_trait['description'] = line[7].decode('utf-8', 'replace')
                    else:
                        this_trait['description'] = "N/A"
                    this_trait['location_repr'] = 'N/A'
                    if (line[8] != "NULL" and line[8] != "") and (line[9] != 0):
                        this_trait['location_repr'] = 'Chr%s: %.6f' % (line[8], float(line[9]))
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

                    #dataset = create_dataset(line[3], "ProbeSet", get_samplelist=False)
                    #trait_id = line[4]
                    #with Bench("Building trait object"):
                    trait_ob = create_trait(dataset_name=this_trait['dataset'], name=this_trait['name'], get_qtl_info=True, get_sample_info=False)
                    if not trait_ob:
                        continue
                    max_lrs_text = "N/A"
                    if trait_ob.locus_chr != "" and trait_ob.locus_mb != "":
                        max_lrs_text = "Chr" + str(trait_ob.locus_chr) + ": " + str(trait_ob.locus_mb)
                    this_trait['max_lrs_text'] = max_lrs_text

                    trait_list.append(this_trait)

            self.trait_count = len(trait_list)
            self.trait_list = json.dumps(trait_list)

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

        elif self.type == "phenotype":
            search_term = self.terms
            group_clause = ""
            if "_" in self.terms:
                if len(self.terms.split("_")[0]) == 3:
                    search_term = self.terms.split("_")[1]
                    group_clause = "AND InbredSet.`InbredSetCode` = '{}'".format(self.terms.split("_")[0])
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
                PublishXRef.`mean`
                FROM Species,InbredSet,PublishFreeze,PublishXRef,Phenotype,Publication
                WHERE PublishXRef.`InbredSetId`=InbredSet.`Id`
                AND PublishFreeze.`InbredSetId`=InbredSet.`Id`
                AND InbredSet.`SpeciesId`=Species.`Id`
                {0}
                AND PublishXRef.`PhenotypeId`=Phenotype.`Id`
                AND PublishXRef.`PublicationId`=Publication.`Id`
                AND	  (Phenotype.Post_publication_description REGEXP "[[:<:]]{1}[[:>:]]"
                    OR Phenotype.Pre_publication_description REGEXP "[[:<:]]{1}[[:>:]]"
                    OR Phenotype.Pre_publication_abbreviation REGEXP "[[:<:]]{1}[[:>:]]"
                    OR Phenotype.Post_publication_abbreviation REGEXP "[[:<:]]{1}[[:>:]]"
                    OR Phenotype.Lab_code REGEXP "[[:<:]]{1}[[:>:]]"
                    OR Publication.PubMed_ID REGEXP "[[:<:]]{1}[[:>:]]"
                    OR Publication.Abstract REGEXP "[[:<:]]{1}[[:>:]]"
                    OR Publication.Title REGEXP "[[:<:]]{1}[[:>:]]"
                    OR Publication.Authors REGEXP "[[:<:]]{1}[[:>:]]"
                    OR PublishXRef.Id REGEXP "[[:<:]]{1}[[:>:]]")
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
                        this_trait['display_name'] = str(line[12]) + "_" + this_trait['name']
                    else:
                        this_trait['display_name'] = this_trait['name']
                    this_trait['dataset'] = line[2]
                    this_trait['dataset_fullname'] = line[3]
                    this_trait['hmac'] = hmac.data_hmac('{}:{}'.format(line[4], line[2]))
                    this_trait['species'] = line[0]
                    this_trait['group'] = line[1]
                    if line[9] != None and line[6] != None:
                        this_trait['description'] = line[6].decode('utf-8', 'replace')
                    elif line[5] != None:
                        this_trait['description'] = line[5].decode('utf-8', 'replace')
                    else:
                        this_trait['description'] = "N/A"
                    if line[13] != None and line[13] != "":
                        this_trait['mean'] = line[13]
                    else:
                        this_trait['mean'] = "N/A"
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
                            this_trait['display_name'] = line[12] + "_" + str(this_trait['name'])
                    this_trait['LRS_score_repr'] = "N/A"
                    if line[10] != "" and line[10] != None:
                        this_trait['LRS_score_repr'] = '%3.1f' % line[10]
                    this_trait['additive'] = "N/A"
                    if line[11] != "" and line[11] != None:
                        this_trait['additive'] = '%.3f' % line[11]

                    this_trait['max_lrs_text'] = "N/A"
                    trait_ob = create_trait(dataset_name=this_trait['dataset'], name=this_trait['name'], get_qtl_info=True, get_sample_info=False)
                    if not trait_ob:
                        continue
                    if this_trait['dataset'] == this_trait['group'] + "Publish":
                      try:
                        if trait_ob.locus_chr != "" and trait_ob.locus_mb != "":
                            this_trait['max_lrs_text'] = "Chr" + str(trait_ob.locus_chr) + ": " + str(trait_ob.locus_mb)
                      except:
                          this_trait['max_lrs_text'] = "N/A"

                    trait_list.append(this_trait)

            self.trait_count = len(trait_list)
            self.trait_list = json.dumps(trait_list)

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
