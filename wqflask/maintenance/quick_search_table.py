from __future__ import print_function, division, absolute_import

"""
Results will be returned for each of several trait types: mRNA assays, phenotypes, genotypes, and
(maybe later) genes

For each trait type, the results for each species should be given; for example, have a "Mouse" tab
with the mouse traits in a table inside it

This table will then list each trait, its dataset, and several columns determined by its trait type
(phenotype, genotype, etc)

"""


import sys
sys.path.append("../../..")

import simplejson as json

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base

from pprint import pformat as pf

import zach_settings as settings

Engine = sa.create_engine(settings.SQLALCHEMY_DATABASE_URI,
                       #encoding='utf-8',
                       #client_encoding='utf-8',
                       #echo="debug",
                       )

Session = scoped_session(sessionmaker(bind=Engine)) #, extension=VersionedListener()))

Base = declarative_base(bind=Engine)
Metadata = sa.MetaData()
Metadata.bind = Engine

class PublishXRef(Base):
    __tablename__ = 'PublishXRef'
    
    Id = sa.Column(sa.Integer, primary_key=True)
    InbredSetId = sa.Column(sa.Integer, primary_key=True)
    PhenotypeId = sa.Column(sa.Integer)
    PublicationId = sa.Column(sa.Integer)
    DataId = sa.Column(sa.Integer)
    Locus = sa.Column(sa.Text)
    LRS = sa.Column(sa.Float)
    additive = sa.Column(sa.Float)
    Sequence = sa.Column(sa.Integer)
    comments = sa.Column(sa.Text)
    
    @classmethod
    def run(cls):
        conn = Engine.connect()
        counter = 0
        for ps in page_query(Session.query(cls)):   #all()
            values = {}
            values['table_name'] = cls.__tablename__
            values['the_key'] = json.dumps([ps.Id, ps.InbredSetId])
            values['terms'] = cls.get_unique_terms(ps.Id, ps.InbredSetId)
            print("terms is:", values['terms'])
            values['result_fields'] = cls.get_result_fields(ps.Id, ps.InbredSetId)
            ins = QuickSearch.insert().values(**values)
            conn.execute(ins)
            counter += 1
            print("Done:", counter)
            
    @staticmethod
    def get_unique_terms(publishxref_id, inbredset_id):
        results = Session.query(
                "pre_publication_description",
                "post_publication_description",
                "pre_publication_abbreviation",
                "post_publication_abbreviation",
                "publication_title"
            ).from_statement(
                "SELECT Phenotype.Pre_publication_description as pre_publication_description, "
                "Phenotype.Post_publication_description as post_publication_description, "
                "Phenotype.Pre_publication_abbreviation as pre_publication_abbreviation, "
                "Phenotype.Post_publication_abbreviation as post_publication_abbreviation, "
                "Publication.Title as publication_title "
                "FROM Phenotype, Publication, PublishXRef "
                "WHERE PublishXRef.Id = :publishxref_id and "
                "PublishXRef.InbredSetId = :inbredset_id and "
                "PublishXRef.PhenotypeId = Phenotype.Id and "
                "PublishXRef.PublicationId = Publication.Id ").params(publishxref_id=publishxref_id,
                                                            inbredset_id=inbredset_id).all()

        unique = set()
        for item in results[0]:
            #print("locals:", locals())
            if not item:
                continue
            for token in item.split():
                if token.startswith(('(','[')):
                    token = token[1:]
                if token.endswith((')', ']')):
                    token = token[:-1]
                if token.endswith(';'):
                    token = token[:-1]
                if len(token) > 2:
                    try:
                        # This hopefully ensures that the token is utf-8
                        token = token.encode('utf-8')
                        print(" ->", token)
                    except UnicodeDecodeError:
                        print("\n-- UDE \n")
                        # Can't get it into utf-8, we won't use it
                        continue 

                    unique.add(token)
        print("\nUnique terms are: {}\n".format(unique))
        return " ".join(unique)            

    @staticmethod
    def get_result_fields(publishxref_id, inbredset_id):
        results = Session.query(
                "phenotype_id",
                "species",
                "group_name",
                "description",
                "lrs",
                "publication_id",
                "pubmed_id",
                "year",
                "authors"
            ).from_statement(
                "SELECT PublishXRef.PhenotypeId as phenotype_id, "
                "Species.Name as species, "
                "InbredSet.Name as group_name, "
                "Phenotype.Original_description as description, "
                "PublishXRef.LRS as lrs, "
                "PublishXRef.PublicationId as publication_id, "
                "Publication.PubMed_ID"
                "Publication.Year as year, "
                "Publication.Authors as authors "
                "FROM PublishXRef, "
                "Phenotype, "
                "Publication, "
                "InbredSet, "
                "Species "
                "WHERE PublishXRef.Id = :publishxref_id and "
                "PublishXRef.InbredSetId = :inbredset_id and "
                "PublishXRef.PhenotypeId = Phenotype.Id and "
                "PublishXRef.PublicationId = Publication.Id and "
                "InbredSet.Id = :inbredset_id and "
                "Species.Id = InbredSet.SpeciesId ").params(publishxref_id=publishxref_id,
                                                            inbredset_id=inbredset_id).all()                
                #"InbredSet.SpeciesId = Species.Id and "
                #"Geno.SpeciesId = Species.Id and "
                #"Geno.Name = PublishXRef.Locus ").params(publishxref_id=publishxref_id,
                #                                            inbredset_id=inbredset_id).all()
        for result in results:
            print("****", result)

        assert len(set(result for result in results)) == 1, "Different results or no results"

        print("results are:", results)
        result = results[0]
        result = row2dict(result)
        try:
            json_results = json.dumps(result, sort_keys=True)
        except UnicodeDecodeError:
            print("\n\nTrying to massage unicode\n\n")
            for key, value in result.iteritems():
                print("\tkey is:", key)
                print("\tvalue is:", value)
                if isinstance(value, basestring):
                    result[key] = value.decode('utf-8', errors='ignore')
            json_results = json.dumps(result, sort_keys=True)

        return json_results

class GenoXRef(Base):
    __tablename__ = 'GenoXRef'
    
    GenoFreezeId = sa.Column(sa.Integer, primary_key=True)
    GenoId = sa.Column(sa.Integer, primary_key=True)
    DataId = sa.Column(sa.Integer)
    cM = sa.Column(sa.Float)
    Used_for_mapping = sa.Column(sa.Text)

    @classmethod
    def run(cls):
        conn = Engine.connect()
        counter = 0
        for item in page_query(Session.query(cls)):   #all()
            values = {}
            values['table_name'] = cls.__tablename__
            values['the_key'] = json.dumps([item.GenoId, item.GenoFreezeId])
            values['terms'] = cls.get_unique_terms(item.GenoId)
            print("terms is:", values['terms'])
            if values['terms']:
                values['result_fields'] = cls.get_result_fields(item.GenoId, item.GenoFreezeId)
                ins = QuickSearch.insert().values(**values)
                conn.execute(ins)
            counter += 1
            print("Done:", counter)
    
    @staticmethod
    def get_unique_terms(geno_id):
        print("geno_id: ", geno_id)
        results = Session.query(
                "name",
                "marker_name"
            ).from_statement(
                "SELECT Geno.Name as name, "
                "Geno.Marker_Name as marker_name "
                "FROM Geno "
                "WHERE Geno.Id = :geno_id ").params(geno_id=geno_id).all()
        
        print("results: ", pf(results))
        
        unique = set()
        if len(results):
            for item in results[0]:
                #print("locals:", locals())
                if not item:
                    continue
                for token in item.split():
                    if len(token) > 2:
                        try:
                            # This hopefully ensures that the token is utf-8
                            token = token.encode('utf-8')
                            print(" ->", token)
                        except UnicodeDecodeError:
                            print("\n-- UDE \n")
                            # Can't get it into utf-8, we won't use it
                            continue 
                        
                        unique.add(token)
        print("\nUnique terms are: {}\n".format(unique))
        return " ".join(unique)


    @staticmethod
    def get_result_fields(geno_id, dataset_id):
        results = Session.query(
                "name",
                "marker_name",
                "group_name",
                "species",
                "dataset",
                "dataset_name",
                "chr", "mb",
                "source"
            ).from_statement(
                "SELECT Geno.Name as name, "
                "Geno.Marker_Name as marker_name, "
                "InbredSet.Name as group_name, "
                "Species.Name as species, "
                "GenoFreeze.Name as dataset, "
                "GenoFreeze.FullName as dataset_name, "
                "Geno.Chr as chr, "
                "Geno.Mb as mb, "
                "Geno.Source as source "
                "FROM Geno, "
                "GenoXRef, "
                "GenoFreeze, "
                "InbredSet, "
                "Species "
                "WHERE Geno.Id = :geno_id and "
                "GenoXRef.GenoId = Geno.Id and "
                "GenoFreeze.Id = :dataset_id and "
                "GenoXRef.GenoFreezeId = GenoFreeze.Id and "
                "InbredSet.Id = GenoFreeze.InbredSetId and "
                "InbredSet.SpeciesId = Species.Id ").params(geno_id=geno_id,
                                                                    dataset_id=dataset_id).all()
        for result in results:
            print(result)
        assert len(set(result for result in results)) == 1, "Different results"
        
        print("results are:", results)
        result = results[0]
        result = row2dict(result)
        try:
            json_results = json.dumps(result, sort_keys=True)
        except UnicodeDecodeError:
            print("\n\nTrying to massage unicode\n\n")
            for key, value in result.iteritems():
                print("\tkey is:", key)
                print("\tvalue is:", value)
                if isinstance(value, basestring):
                    result[key] = value.decode('utf-8', errors='ignore')
            json_results = json.dumps(result, sort_keys=True)

        return json_results    

class ProbeSetXRef(Base):
    __tablename__ = 'ProbeSetXRef'
    
    ProbeSetFreezeId = sa.Column(sa.Integer, primary_key=True)
    ProbeSetId = sa.Column(sa.Integer, primary_key=True)
    DataId = sa.Column(sa.Integer, unique=True)
    Locus_old = sa.Column(sa.Text)
    LRS_old = sa.Column(sa.Float)
    pValue_old = sa.Column(sa.Float)
    mean = sa.Column(sa.Float)
    se = sa.Column(sa.Float)
    Locus = sa.Column(sa.Text)
    LRS = sa.Column(sa.Float)
    pValue = sa.Column(sa.Float)
    additive = sa.Column(sa.Float)
    h2 = sa.Column(sa.Float)

    @classmethod
    def run(cls):
        conn = Engine.connect()
        counter = 0
        for ps in page_query(Session.query(cls)):   #all()
            values = {}
            values['table_name'] = cls.__tablename__
            values['the_key'] = json.dumps([ps.ProbeSetId, ps.ProbeSetFreezeId])
            values['terms'] = cls.get_unique_terms(ps.ProbeSetId)
            print("terms is:", values['terms'])
            #values['species'] = get_species("ProbeSet", ps.Id)
            values['result_fields'] = cls.get_result_fields(ps.ProbeSetId, ps.ProbeSetFreezeId)
            ins = QuickSearch.insert().values(**values)
            conn.execute(ins)
            counter += 1
            print("Done:", counter)
    
    @staticmethod
    def get_unique_terms(probeset_id):
        results = Session.query(
                "name",
                "symbol",
                "description",
                "alias"
            ).from_statement(
                "SELECT ProbeSet.Name as name, "
                "ProbeSet.Symbol as symbol, "
                "ProbeSet.description as description, "
                "ProbeSet.alias as alias "
                "FROM ProbeSet "
                "WHERE ProbeSet.Id = :probeset_id ").params(probeset_id=probeset_id).all()
        
        unique = set()
        for item in results[0]:
            #print("locals:", locals())
            if not item:
                continue
            for token in item.split():
                if token.startswith(('(','[')):
                    token = token[1:]
                if token.endswith((')', ']')):
                    token = token[:-1]
                if token.endswith(';'):
                    token = token[:-1]
                if len(token) > 2:
                    try:
                        # This hopefully ensures that the token is utf-8
                        token = token.encode('utf-8')
                        print(" ->", token)
                    except UnicodeDecodeError:
                        print("\n-- UDE \n")
                        # Can't get it into utf-8, we won't use it
                        continue 
                    
                    unique.add(token)
        print("\nUnique terms are: {}\n".format(unique))
        return " ".join(unique)


    @staticmethod
    def get_result_fields(probeset_id, dataset_id):
        results = Session.query(
                "name",
                "species",
                "group_name",
                "dataset",
                "dataset_name",
                "symbol",
                "description",
                "chr", "mb",
                "lrs", "mean",
                "genbank_id",
                "gene_id",
                "chip_id",
                "chip_name"
            ).from_statement(
                "SELECT ProbeSet.Name as name, "
                "Species.Name as species, "
                "InbredSet.Name as group_name, "
                "ProbeSetFreeze.Name as dataset, "
                "ProbeSetFreeze.FullName as dataset_name, "
                "ProbeSet.Symbol as symbol, "
                "ProbeSet.description as description, "
                "ProbeSet.Chr as chr, "
                "ProbeSet.Mb as mb, "
                "ProbeSetXRef.LRS as lrs, "
                "ProbeSetXRef.mean as mean, "
                "ProbeSet.GenbankId as genbank_id, "
                "ProbeSet.GeneId as gene_id, "
                "ProbeSet.ChipId as chip_id, "
                "GeneChip.Name as chip_name "
                "FROM ProbeSet, "
                "ProbeSetXRef, "
                "ProbeSetFreeze, "
                "ProbeFreeze, "
                "InbredSet, "
                "Species, "
                "GeneChip "
                "WHERE ProbeSetXRef.ProbeSetId = :probeset_id and "
                "ProbeSetXRef.ProbeSetFreezeId = :dataset_id and "
                "ProbeSetXRef.ProbeSetId = ProbeSet.Id and "
                "ProbeSet.ChipId = GeneChip.Id and "
                "ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id and "
                "ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and "
                "ProbeFreeze.InbredSetId = InbredSet.Id and "
                "InbredSet.SpeciesId = Species.Id ").params(probeset_id=probeset_id,
                                                                    dataset_id=dataset_id).all()
        for result in results:
            print(result)
        assert len(set(result for result in results)) == 1, "Different results"
        
        print("results are:", results)
        result = results[0]
        result = row2dict(result)
        try:
            json_results = json.dumps(result, sort_keys=True)
        except UnicodeDecodeError:
            print("\n\nTrying to massage unicode\n\n")
            for key, value in result.iteritems():
                print("\tkey is:", key)
                print("\tvalue is:", value)
                if isinstance(value, basestring):
                    result[key] = value.decode('utf-8', errors='ignore')
            json_results = json.dumps(result, sort_keys=True)

        return json_results    


QuickSearch = sa.Table("QuickSearch", Metadata,
        sa.Column('table_name', sa.String(15),
                  primary_key=True, nullable=False, autoincrement=False), # table that item is inserted from
        sa.Column('the_key', sa.String(30),
                  primary_key=True, nullable=False, autoincrement=False), # key in database table
        sa.Column('terms', sa.Text), # terms to compare search string with
        sa.Column('result_fields', sa.Text)  # json
                    )

QuickSearch.drop(Engine, checkfirst=True)
Metadata.create_all(Engine)


def row2dict(row):
    """http://stackoverflow.com/a/2848519/1175849"""
    return dict(zip(row.keys(), row))


def page_query(q):
    """http://stackoverflow.com/a/1217947/1175849"""
    offset = 0
    while True:
        r = False
        for elem in q.limit(1000).offset(offset):
           r = True
           yield elem
        offset += 1000
        if not r:
            break


def main():
    GenoXRef.run()
    ProbeSetXRef.run()
    PublishXRef.run()

if __name__ == "__main__":
    main()