#!/usr/bin/python


from __future__ import print_function, division

from flask import Flask, g

from MySQLdb import escape_string as escape
from pprint import pformat as pf

import sys
sys.path.append("..")

from dbFunction import webqtlDatabaseFunction


class DoSearch(object):
    """Parent class containing parameters/functions used for all searches"""

    # Used to translate search phrases into classes
    search_types = dict()

    def __init__(self, search_term, search_operator=None, dataset=None):
        self.search_term = search_term
        # Make sure search_operator is something we expect
        assert search_operator in (None, "=", "<", ">", "<=", ">="), "Bad search operator"
        self.search_operator = search_operator
        self.dataset = dataset

        if self.dataset:
            print("self.dataset is boo: ", type(self.dataset), pf(self.dataset))
            print("self.dataset.group is: ", pf(self.dataset.group))
            #Get group information for dataset and the species id
            self.species_id = webqtlDatabaseFunction.retrieve_species_id(self.dataset.group.name)

    def execute(self, query):
        """Executes query and returns results"""
        query = self.normalize_spaces(query)
        print("in do_search query is:", pf(query))
        results = g.db.execute(query, no_parameters=True).fetchall()
        return results

    #def escape(self, stringy):
    #    """Shorter name than self.db_conn.escape_string"""
    #    return escape(str(stringy))

    def mescape(self, *items):
        """Multiple escape"""
        escaped = [escape(str(item)) for item in items]
        print("escaped is:", escaped)
        return tuple(escaped)

    def normalize_spaces(self, stringy):
        """Strips out newlines/extra spaces and replaces them with just spaces"""
        step_one = " ".join(stringy.split())
        return step_one

    @classmethod
    def get_search(cls, search_type):
        print("search_types are:", pf(cls.search_types))

        search_type_string = search_type['dataset_type']
        if 'key' in search_type:
            search_type_string += '_' + search_type['key']

        print("search_type_string is:", search_type_string)

        return cls.search_types[search_type_string]

class QuickMrnaAssaySearch(DoSearch):
    """A general search for mRNA assays"""

    DoSearch.search_types['quick_mrna_assay'] = "QuickMrnaAssaySearch"

    base_query = """SELECT ProbeSet.Name as ProbeSet_Name,
                ProbeSet.Symbol as ProbeSet_Symbol,
                ProbeSet.description as ProbeSet_Description,
                ProbeSet.Chr_num as ProbeSet_Chr_Num,
                ProbeSet.Mb as ProbeSet_Mb,
                ProbeSet.name_num as ProbeSet_name_num
                FROM ProbeSet """

    header_fields = ['',
                     'Record',
                     'Symbol',
                     'Location']

    def run(self):
        """Generates and runs a search for assays across all mRNA expression datasets"""

        print("Running ProbeSetSearch")
        query = self.base_query + """WHERE (MATCH (ProbeSet.Name,
                    ProbeSet.description,
                    ProbeSet.symbol,
                    ProbeSet.alias)
                    AGAINST ('%s' IN BOOLEAN MODE))
                            """ % (escape(self.search_term[0]))

        print("final query is:", pf(query))

        return self.execute(query)


class MrnaAssaySearch(DoSearch):
    """A search within an expression dataset, including mRNA, protein, SNP, but not phenotype or metabolites"""

    DoSearch.search_types['ProbeSet'] = "MrnaAssaySearch"

    base_query = """SELECT ProbeSet.Name as TNAME,
                0 as thistable,
                ProbeSetXRef.Mean as TMEAN,
                ProbeSetXRef.LRS as TLRS,
                ProbeSetXRef.PVALUE as TPVALUE,
                ProbeSet.Chr_num as TCHR_NUM,
                ProbeSet.Mb as TMB,
                ProbeSet.Symbol as TSYMBOL,
                ProbeSet.name_num as TNAME_NUM
                FROM ProbeSetXRef, ProbeSet """

    header_fields = ['',
                     'Record',
                     'Symbol',
                     'Description',
                     'Location',
                     'Mean',
                     'Max LRS',
                     'Max LRS Location',
                     'Additive Effect']

    def get_where_clause(self):
        where_clause = """(MATCH (ProbeSet.Name,
                    ProbeSet.description,
                    ProbeSet.symbol,
                    alias,
                    GenbankId,
                    UniGeneId,
                    Probe_Target_Description)
                    AGAINST ('%s' IN BOOLEAN MODE))
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    and ProbeSetXRef.ProbeSetFreezeId = %s
                            """ % (escape(self.search_term[0]),
                            escape(str(self.dataset.id)))

        return where_clause

    def compile_final_query(self, from_clause = '', where_clause = ''):
        """Generates the final query string"""

        from_clause = self.normalize_spaces(from_clause)

        query = (self.base_query +
            """%s
                WHERE %s
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    and ProbeSetXRef.ProbeSetFreezeId = %s
                            """ % (escape(from_clause),
                                    where_clause,
                                    escape(str(self.dataset.id))))

        #print("query is:", pf(query))

        return query

    def run_combined(self, from_clause = '', where_clause = ''):
        """Generates and runs a combined search of an mRNA expression dataset"""

        print("Running ProbeSetSearch")
        #query = self.base_query + from_clause + " WHERE " + where_clause

        from_clause = self.normalize_spaces(from_clause)

        query = (self.base_query +
            """%s
                WHERE %s
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    and ProbeSetXRef.ProbeSetFreezeId = %s
                            """ % (escape(from_clause),
                                    where_clause,
                                    escape(str(self.dataset.id))))

        print("final query is:", pf(query))

        return self.execute(query)

    def run(self):
        """Generates and runs a simple search of an mRNA expression dataset"""

        print("Running ProbeSetSearch")
        where_clause = self.get_where_clause()
        query = self.base_query + "WHERE " + where_clause

        #print("final query is:", pf(query))

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

    header_fields = ['',
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
            search_term = "[[:<:]]" + self.search_term[0] + "[[:>:]]"

        # This adds a clause to the query that matches the search term
        # against each field in the search_fields tuple
        fields_clause_list = []
        for field in self.search_fields:
            fields_clause_list.append('''%s REGEXP "%s"''' % (field, search_term))
        fields_clause = "(%s) " % ' OR '.join(fields_clause_list)

        return fields_clause

    def compile_final_query(self, from_clause = '', where_clause = ''):
        """Generates the final query string"""

        from_clause = self.normalize_spaces(from_clause)

        query = (self.base_query +
                """%s
                    WHERE %s
                    and PublishXRef.InbredSetId = %s
                    and PublishXRef.PhenotypeId = Phenotype.Id
                    and PublishXRef.PublicationId = Publication.Id
                    and PublishFreeze.Id = %s""" % (
                        from_clause,
                        where_clause,
                        escape(str(self.dataset.group.id)),
                        escape(str(self.dataset.id))))

        print("query is:", pf(query))

        return query

    def run_combined(self, from_clause, where_clause):
        """Generates and runs a combined search of an phenotype dataset"""

        print("Running PhenotypeSearch")

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

        print("final query is:", pf(query))

        
        return self.execute(query)

    def run(self):
        """Generates and runs a simple search of a phenotype dataset"""

        query = self.compile_final_query(where_clause = self.get_where_clause())

        return self.execute(query)

class QuickPhenotypeSearch(PhenotypeSearch):
    """A search across all phenotype datasets"""

    DoSearch.search_types['quick_phenotype'] = "QuickPhenotypeSearch"

    base_query = """SELECT Species.Name as Species_Name,
                PublishFreeze.FullName as Dataset_Name,
                PublishFreeze.Name,
                PublishXRef.Id,
                PublishFreeze.createtime as thistable,
                Publication.PubMed_ID as Publication_PubMed_ID,
                Phenotype.Post_publication_description as Phenotype_Name
                FROM Phenotype,
                    PublishFreeze,
                    Publication,
                    PublishXRef,
                    InbredSet,
                    Species """

    search_fields = ('Phenotype.Post_publication_description',
                    'Phenotype.Pre_publication_description',
                    'Phenotype.Pre_publication_abbreviation',
                    'Phenotype.Post_publication_abbreviation',
                    'Phenotype.Lab_code',
                    'Publication.PubMed_ID',
                    'Publication.Abstract',
                    'Publication.Title',
                    'Publication.Authors')

    def compile_final_query(self, where_clause = ''):
        """Generates the final query string"""

        query = (self.base_query +
                 """WHERE %s
                    PublishXRef.PhenotypeId = Phenotype.Id and
                    PublishXRef.PublicationId = Publication.Id and
                    PublishXRef.InbredSetId = InbredSet.Id and
                    InbredSet.SpeciesId = Species.Id""" % where_clause)

        print("query is:", pf(query))

        return query

    def run(self):
        """Generates and runs a search across all phenotype datasets"""

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

    header_fields = ['',
                     'Record',
                     'Location']

    def get_where_clause(self):
        """Generate clause for part of the WHERE portion of query"""

        # This adds a clause to the query that matches the search term
        # against each field in search_fields (above)
        fields_clause = []

        if "'" not in self.search_term[0]:
            self.search_term = "[[:<:]]" + self.search_term[0] + "[[:>:]]"

        for field in self.search_fields:
            fields_clause.append('''%s REGEXP "%s"''' % ("%s.%s" % self.mescape(self.dataset.type,
                                                                               field),
                                                                               self.search_term))
        print("hello ;where_clause is:", pf(fields_clause))
        fields_clause = "(%s) " % ' OR '.join(fields_clause)

        return fields_clause

    def compile_final_query(self, from_clause = '', where_clause = ''):
        """Generates the final query string"""

        from_clause = self.normalize_spaces(from_clause)

        query = (self.base_query +
                """WHERE %s
                    and Geno.Id = GenoXRef.GenoId
                    and GenoXRef.GenoFreezeId = GenoFreeze.Id
                    and GenoFreeze.Id = %s"""% (where_clause,
                                            escape(str(self.dataset.id))))

        print("query is:", pf(query))

        return query

    def run(self):
        """Generates and runs a simple search of a genotype dataset"""
        #Todo: Zach will figure out exactly what both these lines mean
        #and comment here

        self.query = self.compile_final_query(where_clause = self.get_where_clause())

        return self.execute(self.query)

class RifSearch(MrnaAssaySearch):
    """Searches for traits with a Gene RIF entry including the search term."""

    DoSearch.search_types['ProbeSet_RIF'] = "RifSearch"

    def get_where_clause(self):
        where_clause = """( %s.symbol = GeneRIF_BASIC.symbol and
            MATCH (GeneRIF_BASIC.comment)
            AGAINST ('+%s' IN BOOLEAN MODE)) """ % (self.dataset.type, self.search_term[0])

        return where_clause

    def run(self):
        where_clause = self.get_where_clause()

        from_clause = ", GeneRIF_BASIC "
        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)

class WikiSearch(MrnaAssaySearch):
    """Searches GeneWiki for traits other people have annotated"""

    DoSearch.search_types['ProbeSet_WIKI'] =  "WikiSearch"

    def get_where_clause(self):
        where_clause = """%s.symbol = GeneRIF.symbol
            and GeneRIF.versionId=0 and GeneRIF.display>0
            and (GeneRIF.comment REGEXP '%s' or GeneRIF.initial = '%s')
                """ % (self.dataset.type,
                       "[[:<:]]"+str(self.search_term[0])+"[[:>:]]",
                       str(self.search_term[0])) 
        return where_clause

    def run(self):
        #where_clause = """%s.symbol = GeneRIF.symbol
        #    and GeneRIF.versionId=0 and GeneRIF.display>0
        #    and (GeneRIF.comment REGEXP '%s' or GeneRIF.initial = '%s')
        #        """ % (self.dataset.type,
        #               "[[:<:]]"+str(self.search_term[0])+"[[:>:]]",
        #               str(self.search_term[0]))

        where_clause = self.get_where_clause()

        from_clause = ", GeneRIF "
        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)

class GoSearch(MrnaAssaySearch):
    """Searches for synapse-associated genes listed in the Gene Ontology."""

    DoSearch.search_types['ProbeSet_GO'] =  "GoSearch"

    def run(self):
        field = 'GOterm.acc'
        go_id = 'GO:' + ('0000000'+self.search_term[0])[-7:]

        statements = ("""%s.symbol=GOgene_product.symbol and
           GOassociation.gene_product_id=GOgene_product.id and
           GOterm.id=GOassociation.term_id""" % (
            escape(self.dataset.type)))

        where_clause = " %s = '%s' and %s " % (field, go_id, statements)

        from_clause = """ , db_GeneOntology.term as GOterm,
            db_GeneOntology.association as GOassociation,
            db_GeneOntology.gene_product as GOgene_product """

        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)

#ZS: Not sure what the best way to deal with LRS searches is
class LrsSearch(MrnaAssaySearch):
    """Searches for genes with a QTL within the given LRS values

    LRS searches can take 3 different forms:
    - LRS > (or <) min/max_LRS
    - LRS=(min_LRS max_LRS)
    - LRS=(min_LRS max_LRS chromosome start_Mb end_Mb)
    where min/max_LRS represent the range of LRS scores and start/end_Mb represent
    the range in megabases on the given chromosome

    """

    DoSearch.search_types['LRS'] = 'LrsSearch'

    def get_from_clause(self):
        if self.search_operator == "=":
            return ", Geno"
        else:
            return ""

    def get_where_clause(self):
        self.search_term = [float(value) for value in self.search_term]

        if self.search_operator == "=":
            assert isinstance(self.search_term, (list, tuple))
            self.lrs_min, self.lrs_max = self.search_term[:2]

            self.sub_clause = """ %sXRef.LRS > %s and
                             %sXRef.LRS < %s and """ % self.mescape(self.dataset.type,
                                                                min(self.lrs_min, self.lrs_max),
                                                                self.dataset.type,
                                                                max(self.lrs_min, self.lrs_max))

            if len(self.search_term) > 2:
                self.chr_num = self.search_term[2]
                self.sub_clause += """ Geno.Chr = %s and """ % (self.chr_num)
                if len(self.search_term) == 5:
                    self.mb_low, self.mb_high = self.search_term[3:]
                    self.sub_clause += """ Geno.Mb > %s and
                                                  Geno.Mb < %s and
                                            """ % self.mescape(min(self.mb_low, self.mb_high),
                                                               max(self.mb_low, self.mb_high))
            print("self.sub_clause is:", pf(self.sub_clause))

            #%s.Chr = Geno.Chr
            where_clause = self.sub_clause + """ %sXRef.Locus = Geno.name and
                                                    Geno.SpeciesId = %s
                                                    """ % self.mescape(self.dataset.type,
                                                           self.species_id)
        else:
            # Deal with >, <, >=, and <=
            print("self.search_term is:", self.search_term)
            self.sub_clause = """ %sXRef.LRS %s %s """ % self.mescape(self.dataset.type,
                                                                        self.search_operator,
                                                                        self.search_term[0])
            where_clause = self.sub_clause
        

        return where_clause

    def get_final_query(self):
        self.from_clause = self.get_from_clause()
        self.where_clause = self.get_where_clause()
        self.query = self.compile_final_query(self.from_clause, self.where_clause)

        return self.query

    def run(self):

        self.from_clause = self.get_from_clause()
        self.where_clause = self.get_where_clause()

        self.query = self.compile_final_query(self.from_clause, self.where_clause)

        return self.execute(self.query)


class CisTransLrsSearch(LrsSearch):

    def real_run(self, the_operator):
        #if isinstance(self.search_term, basestring):
        #    self.search_term = [self.search_term]
        print("self.search_term is:", self.search_term)
        self.search_term = [float(value) for value in self.search_term]
        self.mb_buffer = 5  # default

        self.from_clause = ", Geno "

        if self.search_operator == "=":
            if len(self.search_term) == 2:
                self.lrs_min, self.lrs_max = self.search_term
                #[int(value) for value in self.search_term]

            elif len(self.search_term) == 3:
                self.lrs_min, self.lrs_max, self.mb_buffer = self.search_term

            else:
                SomeError

            self.sub_clause = """ %sXRef.LRS > %s and
                %sXRef.LRS < %s  and """  % (
                    escape(self.dataset.type),
                    escape(min(self.lrs_min, self.lrs_max)),
                    escape(self.dataset.type),
                    escape(max(self.lrs_min, self.lrs_max))
                )
        else:
            # Deal with >, <, >=, and <=
            self.sub_clause = """ %sXRef.LRS %s %s and """  % (
                    escape(self.dataset.type),
                    escape(self.search_operator),
                    escape(self.search_term[0])
                )

        self.where_clause = self.sub_clause + """
                ABS(%s.Mb-Geno.Mb) %s %s and
                %sXRef.Locus = Geno.name and
                Geno.SpeciesId = %s and
                %s.Chr = Geno.Chr""" % (
                    escape(self.dataset.type),
                    the_operator,
                    escape(self.mb_buffer),
                    escape(self.dataset.type),
                    escape(self.species_id),
                    escape(self.dataset.type)
                    )

        print("where_clause is:", pf(self.where_clause))

        self.query = self.compile_final_query(self.from_clause, self.where_clause)

        return self.execute(self.query)


class CisLrsSearch(CisTransLrsSearch):
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

    DoSearch.search_types['CISLRS'] = "CisLrsSearch"

    def run(self):
        return self.real_run("<")

class TransLrsSearch(CisTransLrsSearch):
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

    DoSearch.search_types['TRANSLRS'] = "TransLrsSearch"

    def run(self):
        return self.real_run(">")


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

    def get_final_query(self):
        self.where_clause = self.get_where_clause()
        print("where_clause is:", pf(self.where_clause))

        self.query = self.compile_final_query(where_clause = self.where_clause)
        
        return self.query

    def run(self):

        #self.search_term = [float(value) for value in self.search_term]
        #
        #if self.search_operator == "=":
        #    assert isinstance(self.search_term, (list, tuple))
        #    self.mean_min, self.mean_max = self.search_term[:2]
        #
        #    self.where_clause = """ %sXRef.mean > %s and
        #                     %sXRef.mean < %s """ % self.mescape(self.dataset.type,
        #                                                        min(self.mean_min, self.mean_max),
        #                                                        self.dataset.type,
        #                                                        max(self.mean_min, self.mean_max))
        #else:
        #    # Deal with >, <, >=, and <=
        #    self.where_clause = """ %sXRef.mean %s %s """ % self.mescape(self.dataset.type,
        #                                                                self.search_operator,
        #                                                                self.search_term[0])

        self.where_clause = self.get_where_clause()
        print("where_clause is:", pf(self.where_clause))

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

        print("where_clause is:", pf(where_clause))

        return where_clause

    def run(self):

        #self.search_term = [float(value) for value in self.search_term]
        # 
        #if self.search_operator == "=":
        #    assert isinstance(self.search_term, (list, tuple))
        #    self.range_min, self.range_max = self.search_term[:2]
        #    self.where_clause = """ (SELECT Pow(2, max(value) -min(value))
        #                             FROM ProbeSetData
        #                             WHERE ProbeSetData.Id = ProbeSetXRef.dataId) > %s AND
        #                            (SELECT Pow(2, max(value) -min(value))
        #                             FROM ProbeSetData
        #                             WHERE ProbeSetData.Id = ProbeSetXRef.dataId) < %s
        #                            """ % self.mescape(min(self.range_min, self.range_max),
        #                                               max(self.range_min, self.range_max))
        #else:
        #    # Deal with >, <, >=, and <=
        #    self.where_clause = """ (SELECT Pow(2, max(value) -min(value))
        #                             FROM ProbeSetData
        #                             WHERE ProbeSetData.Id = ProbeSetXRef.dataId) > %s
        #                            """ % (escape(self.search_term[0]))
        
        self.where_clause = self.get_where_clause()

        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class PositionSearch(DoSearch):
    """Searches for genes/markers located within a specified range on a specified chromosome"""

    for search_key in ('POSITION', 'POS', 'MB'):
        DoSearch.search_types[search_key] = "PositionSearch"

    def get_where_clause(self):
        where_clause = """ %s.Chr = %s and
                                %s.Mb > %s and
                                %s.Mb < %s """ % self.mescape(self.dataset.type,
                                                              self.chr,
                                                              self.dataset.type,
                                                              min(self.mb_min, self.mb_max),
                                                              self.dataset.type,
                                                              max(self.mb_min, self.mb_max))


        return where_clause

    def setup(self):
        self.search_term = [float(value) if is_number(value) else value for value in self.search_term]
        self.chr, self.mb_min, self.mb_max = self.search_term[:3]
        self.get_chr()
        self.where_clause = self.get_where_clause()

    def get_chr(self):
        try:
            self.chr = int(self.chr)
        except: 
            self.chr = int(self.chr.replace('chr', ''))

    def run(self):

        self.setup()
        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class MrnaPositionSearch(PositionSearch, MrnaAssaySearch):
    """Searches for genes located within a specified range on a specified chromosome"""

    for search_key in ('POSITION', 'POS', 'MB'):
        DoSearch.search_types['ProbeSet_'+search_key] = "MrnaPositionSearch"

    def run(self):

        self.setup()
        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class GenotypePositionSearch(PositionSearch, GenotypeSearch):
    """Searches for genes located within a specified range on a specified chromosome"""

    for search_key in ('POSITION', 'POS', 'MB'):
        DoSearch.search_types['Geno_'+search_key] = "GenotypePositionSearch"

    def run(self):

        self.setup()
        self.query = self.compile_final_query(where_clause = self.where_clause)

        return self.execute(self.query)

class PvalueSearch(MrnaAssaySearch):
    """Searches for traits with a permutationed p-value between low and high"""

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

        print("where_clause is:", pf(self.where_clause))

        self.query = self.compile_final_query(where_clause = self.where_clause)

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

if __name__ == "__main__":
    ### Usually this will be used as a library, but call it from the command line for testing
    ### And it runs the code below

    import MySQLdb
    import sys

    from base import webqtlConfig
    from base.data_set import create_dataset
    from base.templatePage import templatePage
    from utility import webqtlUtil
    from dbFunction import webqtlDatabaseFunction

    db_conn = MySQLdb.Connect(db=webqtlConfig.DB_NAME,
                              host=webqtlConfig.MYSQL_SERVER,
                              user=webqtlConfig.DB_USER,
                              passwd=webqtlConfig.DB_PASSWD)
    cursor = db_conn.cursor()

    dataset_name = "HC_M2_0606_P"
    dataset = create_dataset(db_conn, dataset_name)

    #cursor.execute("""
    #            SELECT ProbeSet.Name as TNAME, 0 as thistable,
    #            ProbeSetXRef.Mean as TMEAN, ProbeSetXRef.LRS as TLRS,
    #            ProbeSetXRef.PVALUE as TPVALUE, ProbeSet.Chr_num as TCHR_NUM,
    #            ProbeSet.Mb as TMB, ProbeSet.Symbol as TSYMBOL,
    #            ProbeSet.name_num as TNAME_NUM
    #            FROM ProbeSetXRef, ProbeSet, Geno
    #            WHERE ProbeSetXRef.LRS > 99.0 and
    #            ABS(ProbeSet.Mb-Geno.Mb) < 5 and
    #            ProbeSetXRef.Locus = Geno.name and
    #            Geno.SpeciesId = 1 and
    #            ProbeSet.Chr = Geno.Chr and
    #            ProbeSet.Id = ProbeSetXRef.ProbeSetId and
    #            ProbeSetXRef.ProbeSetFreezeId = 112""")

    #print(pf(cursor.fetchall()))
    #results = ProbeSetSearch("shh", None, dataset, cursor, db_conn).run()
    results = PvalueSearch(['0.005'], '<', dataset, cursor, db_conn).run()
    #results = RifSearch("diabetes", dataset, cursor, db_conn).run()
    #results = WikiSearch("nicotine", dataset, cursor, db_conn).run()
    #results = CisLrsSearch(['99'], '>', dataset, cursor, db_conn).run() # cisLRS > 99
    #results = LrsSearch('99', '>', dataset, cursor, db_conn).run()
    #results = TransLrsSearch(['9', '999', '10'], dataset, cursor, db_conn).run()
    #results = PhenotypeSearch("brain", dataset, cursor, db_conn).run()
    #results = GenotypeSearch("rs13475699", dataset, cursor, db_conn).run()
    #results = GoSearch("0045202", dataset, cursor, db_conn).run()

    print("results are:", pf(results))
