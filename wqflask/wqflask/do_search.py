from __future__ import print_function, division

import string
import requests
import json

from flask import Flask, g

from MySQLdb import escape_string as escape
from pprint import pformat as pf

import sys
# sys.path.append("..") Never in a running webserver

from db import webqtlDatabaseFunction

import logging
from utility.logger import getLogger
logger = getLogger(__name__)

class DoSearch(object):
    """Parent class containing parameters/functions used for all searches"""

    # Used to translate search phrases into classes
    search_types = dict()

    def __init__(self, search_term, search_operator=None, dataset=None, search_type=None):
        self.search_term = search_term
        # Make sure search_operator is something we expect
        assert search_operator in (None, "=", "<", ">", "<=", ">="), "Bad search operator"
        self.search_operator = search_operator
        self.dataset = dataset
        self.search_type = search_type

        if self.dataset:
            logger.debug("self.dataset is boo: ", type(self.dataset), pf(self.dataset))
            logger.debug("self.dataset.group is: ", pf(self.dataset.group))
            #Get group information for dataset and the species id
            self.species_id = webqtlDatabaseFunction.retrieve_species_id(self.dataset.group.name)

    def execute(self, query):
        """Executes query and returns results"""
        query = self.normalize_spaces(query)
        logger.sql(query)
        results = g.db.execute(query, no_parameters=True).fetchall()
        return results

    def handle_wildcard(self, str):
        keyword = str.strip()
        keyword.replace("*",".*")
        keyword.replace("?",".")

        return keyword

    #def escape(self, stringy):
    #    """Shorter name than self.db_conn.escape_string"""
    #    return escape(str(stringy))

    def mescape(self, *items):
        """Multiple escape"""
        escaped = [escape(str(item)) for item in items]
        logger.debug("escaped is:", escaped)
        return tuple(escaped)

    def normalize_spaces(self, stringy):
        """Strips out newlines/extra spaces and replaces them with just spaces"""
        step_one = " ".join(stringy.split())
        return step_one

    @classmethod
    def get_search(cls, search_type):
        logger.debug("search_types are:", pf(cls.search_types))

        search_type_string = search_type['dataset_type']
        if 'key' in search_type and search_type['key'] != None:
            search_type_string += '_' + search_type['key']

        logger.debug("search_type_string is:", search_type_string)

        if search_type_string in cls.search_types:
            return cls.search_types[search_type_string]
        else:
            return None

class MrnaAssaySearch(DoSearch):
    """A search within an expression dataset, including mRNA, protein, SNP, but not phenotype or metabolites"""

    DoSearch.search_types['ProbeSet'] = "MrnaAssaySearch"

    base_query = """SELECT distinct ProbeSet.Name as TNAME,
                0 as thistable,
                ProbeSetXRef.Mean as TMEAN,
                ProbeSetXRef.LRS as TLRS,
                ProbeSetXRef.PVALUE as TPVALUE,
                ProbeSet.Chr_num as TCHR_NUM,
                ProbeSet.Mb as TMB,
                ProbeSet.Symbol as TSYMBOL,
                ProbeSet.name_num as TNAME_NUM
                FROM ProbeSetXRef, ProbeSet """

    header_fields = ['Index',
                     'Record',
                     'Symbol',
                     'Description',
                     'Location',
                     'Mean',
                     'Max LRS',
                     'Max LRS Location',
                     'Additive Effect']

    def get_alias_where_clause(self):
        search_string = escape(self.search_term[0])

        if self.search_term[0] != "*":
            match_clause = """((MATCH (ProbeSet.symbol) AGAINST ('%s' IN BOOLEAN MODE))) and """ % (search_string)
        else:
            match_clause = ""

        where_clause = (match_clause +
            """ProbeSet.Id = ProbeSetXRef.ProbeSetId
               and ProbeSetXRef.ProbeSetFreezeId = %s
                        """ % (escape(str(self.dataset.id))))

        return where_clause

    def get_where_clause(self):
        search_string = escape(self.search_term[0])

        if self.search_term[0] != "*":
            match_clause = """((MATCH (ProbeSet.Name,
                        ProbeSet.description,
                        ProbeSet.symbol,
                        alias,
                        GenbankId,
                        UniGeneId,
                        Probe_Target_Description)
                        AGAINST ('%s' IN BOOLEAN MODE))) AND
                                """ % (search_string)
        else:
            match_clause = ""

        where_clause = (match_clause +
            """ProbeSet.Id = ProbeSetXRef.ProbeSetId
               and ProbeSetXRef.ProbeSetFreezeId = %s
                        """ % (escape(str(self.dataset.id))))

        return where_clause

    def compile_final_query(self, from_clause = '', where_clause = ''):
        """Generates the final query string"""

        from_clause = self.normalize_spaces(from_clause)

        query = (self.base_query +
            """%s
                WHERE %s
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    and ProbeSetXRef.ProbeSetFreezeId = %s
                ORDER BY ProbeSet.symbol ASC
                            """ % (escape(from_clause),
                                    where_clause,
                                    escape(str(self.dataset.id))))
        return query

    def run_combined(self, from_clause = '', where_clause = ''):
        """Generates and runs a combined search of an mRNA expression dataset"""

        logger.debug("Running ProbeSetSearch")
        #query = self.base_query + from_clause + " WHERE " + where_clause

        from_clause = self.normalize_spaces(from_clause)

        query = (self.base_query +
            """%s
                WHERE %s
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    and ProbeSetXRef.ProbeSetFreezeId = %s
                ORDER BY ProbeSet.symbol ASC
                            """ % (escape(from_clause),
                                    where_clause,
                                    escape(str(self.dataset.id))))

        return self.execute(query)

    def run(self):
        """Generates and runs a simple search of an mRNA expression dataset"""

        logger.debug("Running ProbeSetSearch")
        where_clause = self.get_where_clause()
        query = self.base_query + "WHERE " + where_clause + "ORDER BY ProbeSet.symbol ASC"

        return self.execute(query)


class PhenotypeSearch(DoSearch):
    """A search within a phenotype dataset"""

    DoSearch.search_types['Publish'] = "PhenotypeSearch"

    base_query = """SELECT PublishXRef.Id,
                PublishFreeze.createtime as thistable,
                Publication.PubMed_ID as Publication_PubMed_ID,
                Phenotype.Post_publication_description as Phenotype_Name
                FROM Phenotype, PublishFreeze, Publication, PublishXRef """

    search_fields = ('Phenotype.Post_publication_description',
                    'Phenotype.Pre_publication_description',
                    'Phenotype.Pre_publication_abbreviation',
                    'Phenotype.Post_publication_abbreviation',
                    'Phenotype.Lab_code',
                    'Publication.PubMed_ID',
                    'Publication.Abstract',
                    'Publication.Title',
                    'Publication.Authors',
                    'PublishXRef.Id')

    header_fields = ['Index',
                     'Record',
                     'Description',
                     'Authors',
                     'Year',
                     'Max LRS',
                     'Max LRS Location',
                     'Additive Effect']

    def get_where_clause(self):
        """Generate clause for WHERE portion of query"""

        #Todo: Zach will figure out exactly what both these lines mean
        #and comment here
        if "'" not in self.search_term[0]:
            search_term = "[[:<:]]" + self.handle_wildcard(self.search_term[0]) + "[[:>:]]"

        # This adds a clause to the query that matches the search term
        # against each field in the search_fields tuple
        where_clause_list = []
        for field in self.search_fields:
            where_clause_list.append('''%s REGEXP "%s"''' % (field, search_term))
        where_clause = "(%s) " % ' OR '.join(where_clause_list)

        return where_clause

    def compile_final_query(self, from_clause = '', where_clause = ''):
        """Generates the final query string"""

        from_clause = self.normalize_spaces(from_clause)

        if self.search_term[0] == "*":
            query = (self.base_query +
                    """%s
                        WHERE PublishXRef.InbredSetId = %s
                        and PublishXRef.PhenotypeId = Phenotype.Id
                        and PublishXRef.PublicationId = Publication.Id
                        and PublishFreeze.Id = %s
                        ORDER BY PublishXRef.Id""" % (
                            from_clause,
                            escape(str(self.dataset.group.id)),
                            escape(str(self.dataset.id))))
        else:
            query = (self.base_query +
                    """%s
                        WHERE %s
                        and PublishXRef.InbredSetId = %s
                        and PublishXRef.PhenotypeId = Phenotype.Id
                        and PublishXRef.PublicationId = Publication.Id
                        and PublishFreeze.Id = %s
                        ORDER BY PublishXRef.Id""" % (
                            from_clause,
                            where_clause,
                            escape(str(self.dataset.group.id)),
                            escape(str(self.dataset.id))))

        return query

    def run_combined(self, from_clause, where_clause):
        """Generates and runs a combined search of an phenotype dataset"""

        logger.debug("Running PhenotypeSearch")

        from_clause = self.normalize_spaces(from_clause)

        query = (self.base_query +
                """%s
                    WHERE %s
                    PublishXRef.InbredSetId = %s and
                    PublishXRef.PhenotypeId = Phenotype.Id and
                    PublishXRef.PublicationId = Publication.Id and
                    PublishFreeze.Id = %s""" % (
                        from_clause,
                        where_clause,
                        escape(str(self.dataset.group.id)),
                        escape(str(self.dataset.id))))

        return self.execute(query)

    def run(self):
        """Generates and runs a simple search of a phenotype dataset"""

        query = self.compile_final_query(where_clause = self.get_where_clause())

        return self.execute(query)

class GenotypeSearch(DoSearch):
    """A search within a genotype dataset"""

    DoSearch.search_types['Geno'] = "GenotypeSearch"

    base_query = """SELECT Geno.Name,
                GenoFreeze.createtime as thistable,
                Geno.Name as Geno_Name,
                Geno.Source2 as Geno_Source2,
                Geno.chr_num as Geno_chr_num,
                Geno.Mb as Geno_Mb
                FROM GenoXRef, GenoFreeze, Geno """

    search_fields = ('Name', 'Chr')

    header_fields = ['Index',
                     'Record',
                     'Location']

    def get_where_clause(self):
        """Generate clause for part of the WHERE portion of query"""

        # This adds a clause to the query that matches the search term
        # against each field in search_fields (above)
        where_clause = []

        if "'" not in self.search_term[0]:
            self.search_term = "[[:<:]]" + self.search_term[0] + "[[:>:]]"

        for field in self.search_fields:
            where_clause.append('''%s REGEXP "%s"''' % ("%s.%s" % self.mescape(self.dataset.type,
                                                                               field),
                                                                               self.search_term))
        logger.debug("hello ;where_clause is:", pf(where_clause))
        where_clause = "(%s) " % ' OR '.join(where_clause)

        return where_clause

    def compile_final_query(self, from_clause = '', where_clause = ''):
        """Generates the final query string"""

        from_clause = self.normalize_spaces(from_clause)


        if self.search_term[0] == "*":
            query = (self.base_query +
                    """WHERE Geno.Id = GenoXRef.GenoId
                        and GenoXRef.GenoFreezeId = GenoFreeze.Id
                        and GenoFreeze.Id = %s"""% (escape(str(self.dataset.id))))
        else:
            query = (self.base_query +
                    """WHERE %s
                        and Geno.Id = GenoXRef.GenoId
                        and GenoXRef.GenoFreezeId = GenoFreeze.Id
                        and GenoFreeze.Id = %s"""% (where_clause,
                                                escape(str(self.dataset.id))))

        return query

    def run(self):
        """Generates and runs a simple search of a genotype dataset"""
        #Todo: Zach will figure out exactly what both these lines mean
        #and comment here

        if self.search_term[0] == "*":
            self.query = self.compile_final_query()
        else:
            self.query = self.compile_final_query(where_clause = self.get_where_clause())

        return self.execute(self.query)

class RifSearch(MrnaAssaySearch):
    """Searches for traits with a Gene RIF entry including the search term."""

    DoSearch.search_types['ProbeSet_RIF'] = "RifSearch"

    def get_from_clause(self):
        return ", GeneRIF_BASIC "

    def get_where_clause(self):
        where_clause = """( %s.symbol = GeneRIF_BASIC.symbol and
            MATCH (GeneRIF_BASIC.comment)
            AGAINST ('+%s' IN BOOLEAN MODE)) """ % (self.dataset.type, self.search_term[0])

        return where_clause

    def run(self):
        from_clause = self.get_from_clause()
        where_clause = self.get_where_clause()

        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)

class WikiSearch(MrnaAssaySearch):
    """Searches GeneWiki for traits other people have annotated"""

    DoSearch.search_types['ProbeSet_WIKI'] =  "WikiSearch"

    def get_from_clause(self):
        return ", GeneRIF "

    def get_where_clause(self):
        where_clause = """%s.symbol = GeneRIF.symbol
            and GeneRIF.versionId=0 and GeneRIF.display>0
            and (GeneRIF.comment REGEXP '%s' or GeneRIF.initial = '%s')
                """ % (self.dataset.type,
                       "[[:<:]]"+str(self.search_term[0])+"[[:>:]]",
                       str(self.search_term[0]))
        return where_clause

    def run(self):
        from_clause = self.get_from_clause()
        where_clause = self.get_where_clause()

        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)

class GoSearch(MrnaAssaySearch):
    """Searches for synapse-associated genes listed in the Gene Ontology."""

    DoSearch.search_types['ProbeSet_GO'] =  "GoSearch"

    def get_from_clause(self):
        from_clause = """, db_GeneOntology.term as GOterm,
            db_GeneOntology.association as GOassociation,
            db_GeneOntology.gene_product as GOgene_product """

        return from_clause

    def get_where_clause(self):
        field = 'GOterm.acc'
        go_id = 'GO:' + ('0000000'+self.search_term[0])[-7:]

        statements = ("""%s.symbol=GOgene_product.symbol and
           GOassociation.gene_product_id=GOgene_product.id and
           GOterm.id=GOassociation.term_id""" % (
            escape(self.dataset.type)))

        where_clause = " %s = '%s' and %s " % (field, go_id, statements)

        return where_clause

    def run(self):
        from_clause = self.get_from_clause()
        where_clause = self.get_where_clause()

        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)

#ZS: Not sure what the best way to deal with LRS searches is
class LrsSearch(DoSearch):
    """Searches for genes with a QTL within the given LRS values

    LRS searches can take 3 different forms:
    - LRS > (or <) min/max_LRS
    - LRS=(min_LRS max_LRS)
    - LRS=(min_LRS max_LRS chromosome start_Mb end_Mb)
    where min/max_LRS represent the range of LRS scores and start/end_Mb represent
    the range in megabases on the given chromosome

    """

    for search_key in ('LRS', 'LOD'):
        DoSearch.search_types[search_key] = "LrsSearch"

    def get_from_clause(self):
        #If the user typed, for example "Chr4", the "Chr" substring needs to be removed so that all search elements can be converted to floats
        if len(self.search_term) > 2 and "chr" in self.search_term[2].lower():
            chr_num = self.search_term[2].lower().replace("chr", "")
            self.search_term[2] = chr_num

        self.search_term = [float(value) for value in self.search_term]

        if len(self.search_term) > 2:
            from_clause = ", Geno"
        else:
            from_clause = ""

        return from_clause

    def get_where_clause(self):
        if self.search_operator == "=":
            assert isinstance(self.search_term, (list, tuple))
            lrs_min, lrs_max = self.search_term[:2]
            if self.search_type == "LOD":
                lrs_min = lrs_min*4.61
                lrs_max = lrs_max*4.61

            where_clause = """ %sXRef.LRS > %s and
                             %sXRef.LRS < %s """ % self.mescape(self.dataset.type,
                                                                min(lrs_min, lrs_max),
                                                                self.dataset.type,
                                                                max(lrs_min, lrs_max))

            if len(self.search_term) > 2:
                chr_num = self.search_term[2]
                where_clause += """ and Geno.Chr = %s """ % (chr_num)
                if len(self.search_term) == 5:
                    mb_low, mb_high = self.search_term[3:]
                    where_clause += """ and Geno.Mb > %s and
                                                  Geno.Mb < %s
                                            """ % self.mescape(min(mb_low, mb_high),
                                                               max(mb_low, mb_high))

                where_clause += """ and %sXRef.Locus = Geno.name and
                                                    Geno.SpeciesId = %s
                                                    """ % self.mescape(self.dataset.type,
                                                           self.species_id)
        else:
            # Deal with >, <, >=, and <=
            logger.debug("self.search_term is:", self.search_term)
            lrs_val = self.search_term[0]
            if self.search_type == "LOD":
                lrs_val = lrs_val*4.61

            where_clause = """ %sXRef.LRS %s %s """ % self.mescape(self.dataset.type,
                                                                        self.search_operator,
                                                                        self.search_term[0])

        return where_clause


    def run(self):

        self.from_clause = self.get_from_clause()
        self.where_clause = self.get_where_clause()

        self.query = self.compile_final_query(self.from_clause, self.where_clause)

        return self.execute(self.query)


class MrnaLrsSearch(LrsSearch, MrnaAssaySearch):

    for search_key in ('LRS', 'LOD'):
        DoSearch.search_types['ProbeSet_' + search_key] = "MrnaLrsSearch"

    def run(self):

        self.from_clause = self.get_from_clause()
        self.where_clause = self.get_where_clause()

        self.query = self.compile_final_query(from_clause = self.from_clause, where_clause = self.where_clause)

        return self.execute(self.query)

class PhenotypeLrsSearch(LrsSearch, PhenotypeSearch):

    for search_key in ('LRS', 'LOD'):
        DoSearch.search_types['Publish_' + search_key] = "PhenotypeLrsSearch"

    def run(self):

        self.from_clause = self.get_from_clause()
        self.where_clause = self.get_where_clause()

        self.query = self.compile_final_query(from_clause = self.from_clause, where_clause = self.where_clause)

        return self.execute(self.query)


class CisTransLrsSearch(DoSearch):

    def get_from_clause(self):
        return ", Geno"

    def get_where_clause(self, cis_trans):
        self.search_term = [float(value) for value in self.search_term]
        self.mb_buffer = 5  # default
        if cis_trans == "cis":
            the_operator = "<"
        else:
            the_operator = ">"

        if self.search_operator == "=":
            if len(self.search_term) == 2:
                lrs_min, lrs_max = self.search_term
                #[int(value) for value in self.search_term]

            elif len(self.search_term) == 3:
                lrs_min, lrs_max, self.mb_buffer = self.search_term

            else:
                SomeError

            if self.search_type == "CISLOD" or self.search_type == "TRANSLOD":
                lrs_min = lrs_min * 4.61
                lrs_max = lrs_max * 4.61

            sub_clause = """ %sXRef.LRS > %s and
                %sXRef.LRS < %s  and """  % (
                    escape(self.dataset.type),
                    escape(str(min(lrs_min, lrs_max))),
                    escape(self.dataset.type),
                    escape(str(max(lrs_min, lrs_max)))
                )
        else:
            # Deal with >, <, >=, and <=
            sub_clause = """ %sXRef.LRS %s %s and """  % (
                    escape(self.dataset.type),
                    escape(self.search_operator),
                    escape(self.search_term[0])
                )

        if cis_trans == "cis":
            where_clause = sub_clause + """
                    ABS(%s.Mb-Geno.Mb) %s %s and
                    %sXRef.Locus = Geno.name and
                    Geno.SpeciesId = %s and
                    %s.Chr = Geno.Chr""" % (
                        escape(self.dataset.type),
                        the_operator,
                        escape(str(self.mb_buffer)),
                        escape(self.dataset.type),
                        escape(str(self.species_id)),
                        escape(self.dataset.type)
                        )
        else:
            where_clause = sub_clause + """
                    %sXRef.Locus = Geno.name and
                    Geno.SpeciesId = %s and
                    ((ABS(%s.Mb-Geno.Mb) %s %s and %s.Chr = Geno.Chr) or
                    (%s.Chr != Geno.Chr))""" % (
                        escape(self.dataset.type),
                        escape(str(self.species_id)),
                        escape(self.dataset.type),
                        the_operator,
                        escape(str(self.mb_buffer)),
                        escape(self.dataset.type),
                        escape(self.dataset.type)
                        )

        return where_clause

class CisLrsSearch(CisTransLrsSearch, MrnaAssaySearch):
    """
    Searches for genes on a particular chromosome with a cis-eQTL within the given LRS values

    A cisLRS search can take 3 forms:
    - cisLRS=(min_LRS max_LRS)
    - cisLRS=(min_LRS max_LRS mb_buffer)
    - cisLRS>min_LRS
    where min/max_LRS represent the range of LRS scores and the mb_buffer is the range around
    a particular QTL where its eQTL would be considered "cis". If there is no third parameter,
    mb_buffer will default to 5 megabases.

    A QTL is a cis-eQTL if a gene's expression is regulated by a QTL in roughly the same area
    (where the area is determined by the mb_buffer that the user can choose).

    """

    for search_key in ('LRS', 'LOD'):
        DoSearch.search_types['ProbeSet_CIS'+search_key] = "CisLrsSearch"

    def get_where_clause(self):
        return CisTransLrsSearch.get_where_clause(self, "cis")

    def run(self):
        self.from_clause = self.get_from_clause()
        self.where_clause = self.get_where_clause()

        self.query = self.compile_final_query(self.from_clause, self.where_clause)

        return self.execute(self.query)

class TransLrsSearch(CisTransLrsSearch, MrnaAssaySearch):
    """Searches for genes on a particular chromosome with a cis-eQTL within the given LRS values

    A transLRS search can take 3 forms:
    - transLRS=(min_LRS max_LRS)
    - transLRS=(min_LRS max_LRS mb_buffer)
    - transLRS>min_LRS
    where min/max_LRS represent the range of LRS scores and the mb_buffer is the range around
    a particular QTL where its eQTL would be considered "cis". If there is no third parameter,
    mb_buffer will default to 5 megabases.

    A QTL is a trans-eQTL if a gene's expression is regulated by a QTL in a different location/area
    (where the area is determined by the mb_buffer that the user can choose). Opposite of cis-eQTL.

    """

    for search_key in ('LRS', 'LOD'):
        DoSearch.search_types['ProbeSet_TRANS'+search_key] = "TransLrsSearch"

    def get_where_clause(self):
        return CisTransLrsSearch.get_where_clause(self, "trans")

    def run(self):
        self.from_clause = self.get_from_clause()
        self.where_clause = self.get_where_clause()

        self.query = self.compile_final_query(self.from_clause, self.where_clause)

        return self.execute(self.query)


class MeanSearch(MrnaAssaySearch):
    """Searches for genes expressed within an interval (log2 units) determined by the user"""

    DoSearch.search_types['ProbeSet_MEAN'] = "MeanSearch"

    def get_where_clause(self):
        self.search_term = [float(value) for value in self.search_term]

        if self.search_operator == "=":
            assert isinstance(self.search_term, (list, tuple))
            self.mean_min, self.mean_max = self.search_term[:2]

            where_clause = """ %sXRef.mean > %s and
                             %sXRef.mean < %s """ % self.mescape(self.dataset.type,
                                                                min(self.mean_min, self.mean_max),
                                                                self.dataset.type,
                                                                max(self.mean_min, self.mean_max))
        else:
            # Deal with >, <, >=, and <=
            where_clause = """ %sXRef.mean %s %s """ % self.mescape(self.dataset.type,
                                                                        self.search_operator,
                                                                        self.search_term[0])

        return where_clause

    def run(self):
        self.where_clause = self.get_where_clause()
        logger.debug("where_clause is:", pf(self.where_clause))

        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class RangeSearch(MrnaAssaySearch):
    """Searches for genes with a range of expression varying between two values"""

    DoSearch.search_types['ProbeSet_RANGE'] = "RangeSearch"

    def get_where_clause(self):
        if self.search_operator == "=":
            assert isinstance(self.search_term, (list, tuple))
            self.range_min, self.range_max = self.search_term[:2]
            where_clause = """ (SELECT Pow(2, max(value) -min(value))
                                     FROM ProbeSetData
                                     WHERE ProbeSetData.Id = ProbeSetXRef.dataId) > %s AND
                                    (SELECT Pow(2, max(value) -min(value))
                                     FROM ProbeSetData
                                     WHERE ProbeSetData.Id = ProbeSetXRef.dataId) < %s
                                    """ % self.mescape(min(self.range_min, self.range_max),
                                                       max(self.range_min, self.range_max))
        else:
            # Deal with >, <, >=, and <=
            where_clause = """ (SELECT Pow(2, max(value) -min(value))
                                     FROM ProbeSetData
                                     WHERE ProbeSetData.Id = ProbeSetXRef.dataId) > %s
                                    """ % (escape(self.search_term[0]))

        logger.debug("where_clause is:", pf(where_clause))

        return where_clause

    def run(self):
        self.where_clause = self.get_where_clause()

        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class PositionSearch(DoSearch):
    """Searches for genes/markers located within a specified range on a specified chromosome"""

    for search_key in ('POSITION', 'POS', 'MB'):
        DoSearch.search_types[search_key] = "PositionSearch"

    def get_where_clause(self):
        self.search_term = [float(value) if is_number(value) else value for value in self.search_term]
        chr, self.mb_min, self.mb_max = self.search_term[:3]
        self.chr = str(chr).lower()
        self.get_chr()

        where_clause = """ %s.Chr = %s and
                                %s.Mb > %s and
                                %s.Mb < %s """ % self.mescape(self.dataset.type,
                                                              self.chr,
                                                              self.dataset.type,
                                                              min(self.mb_min, self.mb_max),
                                                              self.dataset.type,
                                                              max(self.mb_min, self.mb_max))


        return where_clause

    def get_chr(self):
        try:
            self.chr = int(self.chr)
        except:
            if 'chr' in self.chr:
                self.chr = self.chr.replace('chr', '')
            else:
                self.chr = self.chr.replace('CHR', '')

    def run(self):

        self.get_where_clause()
        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class MrnaPositionSearch(PositionSearch, MrnaAssaySearch):
    """Searches for genes located within a specified range on a specified chromosome"""

    for search_key in ('POSITION', 'POS', 'MB'):
        DoSearch.search_types['ProbeSet_'+search_key] = "MrnaPositionSearch"

    def run(self):

        self.where_clause = self.get_where_clause()
        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class GenotypePositionSearch(PositionSearch, GenotypeSearch):
    """Searches for genes located within a specified range on a specified chromosome"""

    for search_key in ('POSITION', 'POS', 'MB'):
        DoSearch.search_types['Geno_'+search_key] = "GenotypePositionSearch"

    def run(self):

        self.where_clause = self.get_where_clause()
        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class PvalueSearch(MrnaAssaySearch):
    """Searches for traits with a permutationed p-value between low and high"""

    DoSearch.search_types['ProbeSet_PVALUE'] = "PvalueSearch"

    def run(self):

        self.search_term = [float(value) for value in self.search_term]

        if self.search_operator == "=":
            assert isinstance(self.search_term, (list, tuple))
            self.pvalue_min, self.pvalue_max = self.search_term[:2]
            self.where_clause = """ %sXRef.pValue > %s and %sXRef.pValue < %s
                                    """ % self.mescape(
                                        self.dataset.type,
                                        min(self.pvalue_min, self.pvalue_max),
                                        self.dataset.type,
                                        max(self.pvalue_min, self.pvalue_max))
        else:
            # Deal with >, <, >=, and <=
            self.where_clause = """ %sXRef.pValue %s %s
                                    """ % self.mescape(
                                        self.dataset.type,
                                        self.search_operator,
                                        self.search_term[0])

        logger.debug("where_clause is:", pf(self.where_clause))

        self.query = self.compile_final_query(where_clause = self.where_clause)

        logger.sql(self.query)
        return self.execute(self.query)

class AuthorSearch(PhenotypeSearch):
    """Searches for phenotype traits with specified author(s)"""

    DoSearch.search_types["Publish_NAME"] = "AuthorSearch"

    def run(self):

        self.where_clause = """ Publication.Authors REGEXP "[[:<:]]%s[[:>:]]" and
                                """ % (self.search_term[0])

        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_aliases(symbol, species):
    if species == "mouse":
        symbol_string = symbol.capitalize()
    elif species == "human":
        symbol_string = symbol.upper()
    else:
        return []

    filtered_aliases = []
    response = requests.get("http://gn2.genenetwork.org/gn3/gene/aliases/" + symbol_string)
    if response:
        alias_list = json.loads(response.content)

        seen = set()
        for item in alias_list:
            if item in seen:
                continue
            else:
                filtered_aliases.append(item)
                seen.add(item)

    return filtered_aliases

if __name__ == "__main__":
    ### Usually this will be used as a library, but call it from the command line for testing
    ### And it runs the code below

    import MySQLdb
    import sys

    from base import webqtlConfig
    from base.data_set import create_dataset
    from utility import webqtlUtil
    from db import webqtlDatabaseFunction

    db_conn = MySQLdb.Connect(db=webqtlConfig.DB_NAME,
                              host=webqtlConfig.MYSQL_SERVER,
                              user=webqtlConfig.DB_USER,
                              passwd=webqtlConfig.DB_PASSWD)
    cursor = db_conn.cursor()

    dataset_name = "HC_M2_0606_P"
    dataset = create_dataset(db_conn, dataset_name)

    results = PvalueSearch(['0.005'], '<', dataset, cursor, db_conn).run()

    db_conn.close()
