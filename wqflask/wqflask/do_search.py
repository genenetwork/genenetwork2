#!/usr/bin/python


from __future__ import print_function, division

from pprint import pformat as pf


class DoSearch(object):
    def __init__(self, search_term, dataset, cursor, db_conn):
        self.search_term = search_term
        self.dataset = dataset
        self.db_conn = db_conn
        self.cursor = cursor
        
    def execute(self, query):
        query = self.normalize_spaces(query)
        print("query is:", pf(query))
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return results
    
    def escape(self, stringy):
        """Shorter name than self.db_conn.escape_string"""
        return self.db_conn.escape_string(str(stringy))
    
    def normalize_spaces(self, stringy):
        """Strips out newlines  extra spaces and replaces them with just spaces"""
        step_one = " ".join(stringy.split())
        return step_one

        
        
class ProbeSetSearch(DoSearch):
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
    
    def run(self):
        
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
                            self.escape(dataset.id)))
        
        return self.execute(query)


class PhenotypeSearch(DoSearch):
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
                
    def run(self):
        #Todo: Zach will figure out exactly what both these lines mean
        #and comment here
        if "'" not in self.search_term:
            search_term = "[[:<:]]" + self.search_term + "[[:>:]]"

        where_clause = []
        for field in self.search_fields:
            where_clause.append('''%s REGEXP "%s"''' % (field, search_term))
            
        where_clause = "(%s)" % ' OR '.join(where_clause)
        
        #Get group information for dataset
        self.dataset.get_group()
        
        print("before query where clause is:", where_clause)
        
        query = (self.base_query +
                """WHERE %s and
                    PublishXRef.InbredSetId = %s and
                    PublishXRef.PhenotypeId = Phenotype.Id and
                    PublishXRef.PublicationId = Publication.Id and
                    PublishFreeze.Id = %s""" % (
                        where_clause,
                        self.escape(self.dataset.group_id),
                        self.escape(self.dataset.id)))



        return self.execute(query)

       
class GenotypeSearch(DoSearch):
    def __init__(self):
       pass
    
class GoSearch(ProbeSetSearch):
    """searches for synapse-associated genes listed in the Gene Ontology."""
    
    def run(self):
        field = 'GOterm.acc'
        go_id = 'GO:' + ('0000000'+self.search_term)[-7:]
        
        statements = ("""%s.symbol=GOgene_product.symbol and
           GOassociation.gene_product_id=GOgene_product.id and
           GOterm.id=GOassociation.term_id""" % (
            self.db_conn.escape_string(self.dataset.type)))
            
        clause_item = " %s = '%s' and %s " % (field, go_id, statements)
        
        gene_ontology_from_table = """ , db_GeneOntology.term as GOterm,
            db_GeneOntology.association as GOassociation,
            db_GeneOntology.gene_product as GOgene_product """
        
        gene_ontology_from_table = self.normalize_spaces(gene_ontology_from_table)
        #gene_ontology_from_table = " ".join(gene_ontology_from_table.splitlines())
        
        query = (self.base_query + 
            """%s
                WHERE %s 
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    and ProbeSetXRef.ProbeSetFreezeId = %s  
                            """ % (self.db_conn.escape_string(gene_ontology_from_table),
                                    clause_item,
                                    self.db_conn.escape_string(str(self.dataset.id))))
        
        return self.execute(query)
        


if __name__ == "__main__":
    
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
    #results = PhenotypeSearch("brain", dataset, cursor, db_conn).run()
    
    results = GoSearch("0045202", dataset, cursor, db_conn).run()
    print("results are:", pf(results))