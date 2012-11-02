#!/usr/bin/python


from __future__ import print_function, division

from pprint import pformat as pf


class DoSearch(object):
    """Parent class containing parameters/functions used for all searches"""
    
    # Used to translate search phrases into classes
    search_types = dict()
    
    def __init__(self, search_term, dataset, cursor, db_conn):
        self.search_term = search_term
        self.dataset = dataset
        self.db_conn = db_conn
        self.cursor = cursor

    def execute(self, query):
        """Executes query and returns results"""
        query = self.normalize_spaces(query)
        print("in do_search query is:", pf(query))
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return results

    def escape(self, stringy):
        """Shorter name than self.db_conn.escape_string"""
        return self.db_conn.escape_string(str(stringy))

    def normalize_spaces(self, stringy):
        """Strips out newlines/extra spaces and replaces them with just spaces"""
        step_one = " ".join(stringy.split())
        return step_one
        
    @classmethod
    def get_search(cls, search_type):
        return cls.search_types[search_type]


class ProbeSetSearch(DoSearch):
    """A search within an mRNA expression dataset"""
    
    DoSearch.search_types['ProbeSet'] = "ProbeSetSearch"
    
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

    def compile_final_query(self, from_clause, where_clause):
        """Generates the final query string"""
        
        from_clause = self.normalize_spaces(from_clause)

        query = (self.base_query +
            """%s
                WHERE %s
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    and ProbeSetXRef.ProbeSetFreezeId = %s
                            """ % (self.escape(from_clause),
                                    where_clause,
                                    self.escape(self.dataset.id)))        

        print("query is:", pf(query))
        
        return query

    def run(self):
        """Generates and runs a simple search of an mRNA expression dataset"""
        
        print("Running ProbeSetSearch")
        query = (self.base_query +
                """WHERE (MATCH (ProbeSet.Name,
                    ProbeSet.description,
                    ProbeSet.symbol,
                    alias,
                    GenbankId,
                    UniGeneId,
                    Probe_Target_Description)
                    AGAINST ('%s' IN BOOLEAN MODE)) 
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    and ProbeSetXRef.ProbeSetFreezeId = %s  
                            """ % (self.escape(self.search_term),
                            self.escape(self.dataset.id)))

        print("final query is:", pf(query))

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
    
    def get_where_clause(self):
        """Generate clause for WHERE portion of query"""

        #Todo: Zach will figure out exactly what both these lines mean
        #and comment here
        if "'" not in self.search_term:
            search_term = "[[:<:]]" + self.search_term + "[[:>:]]"

        # This adds a clause to the query that matches the search term
        # against each field in the search_fields tuple
        where_clause = []
        for field in self.search_fields:
            where_clause.append('''%s REGEXP "%s"''' % (field, search_term))
        where_clause = "(%s)" % ' OR '.join(where_clause)
        
        return where_clause

    def run(self):
        """Generates and runs a simple search of a phenotype dataset"""

        #Get group information for dataset
        self.dataset.get_group()

        query = (self.base_query +
                """WHERE %s and
                    PublishXRef.InbredSetId = %s and
                    PublishXRef.PhenotypeId = Phenotype.Id and
                    PublishXRef.PublicationId = Publication.Id and
                    PublishFreeze.Id = %s""" % (
                        self.get_where_clause(),
                        self.escape(self.dataset.group_id),
                        self.escape(self.dataset.id)))

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

    def get_where_clause(self):
        """Generate clause for WHERE portion of query"""

        # This adds a clause to the query that matches the search term
        # against each field in search_fields (above)
        where_clause = []
        for field in self.search_fields:
            where_clause.append('''%s REGEXP "%s"''' % ("%s.%s" % (self.dataset.type, field),
                                                                self.search_term))
        where_clause = "(%s)" % ' OR '.join(where_clause)

        return where_clause

    def run(self):
        """Generates and runs a simple search of a genotype dataset"""
        #Todo: Zach will figure out exactly what both these lines mean
        #and comment here
        if "'" not in self.search_term:
            search_term = "[[:<:]]" + self.search_term + "[[:>:]]"

        query = (self.base_query +
                """WHERE %s and
                    Geno.Id = GenoXRef.GenoId and
                    GenoXRef.GenoFreezeId = GenoFreeze.Id and
                    GenoFreeze.Id = %s"""% (
                        self.get_where_clause(),
                        self.escape(self.dataset.id)))

        return self.execute(query)

class RifSearch(ProbeSetSearch):
    """Searches for traits with a Gene RIF entry including the search term."""
    
    DoSearch.search_types['RIF'] = "RifSearch"

    def run(self):
        where_clause = """( %s.symbol = GeneRIF_BASIC.symbol and
            MATCH (GeneRIF_BASIC.comment)
            AGAINST ('+%s' IN BOOLEAN MODE)) """ % (self.dataset.type, self.search_term)

        from_clause = ", GeneRIF_BASIC "
        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)

class WikiSearch(ProbeSetSearch):
    """Searches GeneWiki for traits other people have annotated"""
    
    DoSearch.search_types['WIKI'] =  "WikiSearch"
    
    def run(self):
        where_clause = """%s.symbol = GeneRIF.symbol
            and GeneRIF.versionId=0 and GeneRIF.display>0
            and (GeneRIF.comment REGEXP '%s' or GeneRIF.initial = '%s')
                """ % (self.dataset.type, "[[:<:]]"+self.search_term+"[[:>:]]", self.search_term)

        from_clause = ", GeneRIF "
        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)

class GoSearch(ProbeSetSearch):
    """Searches for synapse-associated genes listed in the Gene Ontology."""

    DoSearch.search_types['GO'] =  "GoSearch"

    def run(self):
        field = 'GOterm.acc'
        go_id = 'GO:' + ('0000000'+self.search_term)[-7:]

        statements = ("""%s.symbol=GOgene_product.symbol and
           GOassociation.gene_product_id=GOgene_product.id and
           GOterm.id=GOassociation.term_id""" % (
            self.db_conn.escape_string(self.dataset.type)))

        where_clause = " %s = '%s' and %s " % (field, go_id, statements)

        from_clause = """ , db_GeneOntology.term as GOterm,
            db_GeneOntology.association as GOassociation,
            db_GeneOntology.gene_product as GOgene_product """
            
        query = self.compile_final_query(from_clause, where_clause)

        return self.execute(query)


if __name__ == "__main__":
    ### Usually this will be used as a library, but call it from the command line for testing
    ### And it runs the code below

    import MySQLdb
    import sys
    sys.path.append("/home/zas1024/gene/wqflask")
    print("Path is:", sys.path)


    from base import webqtlConfig
    from base.webqtlDataset import webqtlDataset
    from base.templatePage import templatePage
    from utility import webqtlUtil
    from dbFunction import webqtlDatabaseFunction

    db_conn = MySQLdb.Connect(db=webqtlConfig.DB_NAME,
                              host=webqtlConfig.MYSQL_SERVER,
                              user=webqtlConfig.DB_USER,
                              passwd=webqtlConfig.DB_PASSWD)
    cursor = db_conn.cursor()

    dataset_name = "HC_M2_0606_P"
    dataset = webqtlDataset(dataset_name, cursor)

    #results = ProbeSetSearch("salt", dataset, cursor, db_conn).run()
    #results = RifSearch("diabetes", dataset, cursor, db_conn).run()
    results = WikiSearch("nicotine", dataset, cursor, db_conn).run()
    #results = PhenotypeSearch("brain", dataset, cursor, db_conn).run()
    #results = GenotypeSearch("rs13475699", dataset, cursor, db_conn).run()
    #results = GoSearch("0045202", dataset, cursor, db_conn).run()
    
    print("results are:", pf(results))