from __future__ import absolute_import, division, print_function

import string
import resource
import codecs
import requests

import redis
Redis = redis.StrictRedis()

from base import webqtlConfig
from base.webqtlCaseData import webqtlCaseData
from base.data_set import create_dataset
from db import webqtlDatabaseFunction
from utility import webqtlUtil

from wqflask import app

import simplejson as json
from MySQLdb import escape_string as escape
from pprint import pformat as pf

from flask import Flask, g, request, url_for

from utility.logger import getLogger
logger = getLogger(__name__ )

from wqflask import user_manager

class GeneralTrait(object):
    """
    Trait class defines a trait in webqtl, can be either Microarray,
    Published phenotype, genotype, or user input trait

    """

    def __init__(self, get_qtl_info=False, get_sample_info=True, **kw):
        # xor assertion
        assert bool(kw.get('dataset')) != bool(kw.get('dataset_name')), "Needs dataset ob. or name";
        self.name = kw.get('name')                 # Trait ID, ProbeSet ID, Published ID, etc.
        if kw.get('dataset_name'):
            if kw.get('dataset_name') == "Temp":
                temp_group = self.name.split("_")[2]
                self.dataset = create_dataset(dataset_name = "Temp", dataset_type = "Temp", group_name = temp_group)
            else:
                self.dataset = create_dataset(kw.get('dataset_name'))
        else:
            self.dataset = kw.get('dataset')
        self.cellid = kw.get('cellid')
        self.identification = kw.get('identification', 'un-named trait')
        self.haveinfo = kw.get('haveinfo', False)
        self.sequence = kw.get('sequence')         # Blat sequence, available for ProbeSet
        self.data = kw.get('data', {})

        # Sets defaults
        self.locus = None
        self.lrs = None
        self.pvalue = None
        self.mean = None
        self.additive = None
        self.num_overlap = None
        self.strand_probe = None
        self.symbol = None

        self.LRS_score_repr = "N/A"
        self.LRS_location_repr = "N/A"

        if kw.get('fullname'):
            name2 = value.split("::")
            if len(name2) == 2:
                self.dataset, self.name = name2
                # self.cellid is set to None above
            elif len(name2) == 3:
                self.dataset, self.name, self.cellid = name2

        # Todo: These two lines are necessary most of the time, but perhaps not all of the time
        # So we could add a simple if statement to short-circuit this if necessary
        if self.dataset.type != "Temp":
            self = retrieve_trait_info(self, self.dataset, get_qtl_info=get_qtl_info)
        if get_sample_info != False:
            self = retrieve_sample_data(self, self.dataset)

    def export_informative(self, include_variance=0):
        """
        export informative sample
        mostly used in qtl regression

        """
        samples = []
        vals = []
        the_vars = []
        sample_aliases = []
        for sample_name, sample_data in self.data.items():
            if sample_data.value != None:
                if not include_variance or sample_data.variance != None:
                    samples.append(sample_name)
                    vals.append(sample_data.value)
                    the_vars.append(sample_data.variance)
                    sample_aliases.append(sample_data.name2)
        return  samples, vals, the_vars, sample_aliases

    @property
    def description_fmt(self):
        '''Return a text formated description'''
        if self.dataset.type == 'ProbeSet':
            if self.description:
                formatted = self.description
                if self.probe_target_description:
                    formatted += "; " + self.probe_target_description
            else:
                formatted = "Not available"
        elif self.dataset.type == 'Publish':
            if self.confidential:
                formatted = self.pre_publication_description
            else:
                formatted = self.post_publication_description
        else:
            formatted = "Not available"
        return formatted

    @property
    def alias_fmt(self):
        '''Return a text formatted alias'''

        alias = 'Not available'
        if self.alias:
            alias = string.replace(self.alias, ";", " ")
            alias = string.join(string.split(alias), ", ")

        return alias

    @property
    def wikidata_alias_fmt(self):
        '''Return a text formatted alias'''

        alias = 'Not available'
        if self.symbol:
            human_response = requests.get("http://gn2.genenetwork.org/gn3/gene/aliases/" + self.symbol.upper())
            mouse_response = requests.get("http://gn2.genenetwork.org/gn3/gene/aliases/" + self.symbol.capitalize())
            other_response = requests.get("http://gn2.genenetwork.org/gn3/gene/aliases/" + self.symbol.lower())
            alias_list = json.loads(human_response.content) + json.loads(mouse_response.content) + json.loads(other_response.content)

            filtered_aliases = []
            seen = set()
            for item in alias_list:
                if item in seen:
                    continue
                else:
                    filtered_aliases.append(item)
                    seen.add(item)
            alias = "; ".join(filtered_aliases)

        return alias


    @property
    def location_fmt(self):
        '''Return a text formatted location

        While we're at it we set self.location in case we need it later (do we?)

        '''

        if self.chr and self.mb:
            self.location = 'Chr %s @ %s Mb'  % (self.chr,self.mb)
        elif self.chr:
            self.location = 'Chr %s @ Unknown position' % (self.chr)
        else:
            self.location = 'Not available'

        fmt = self.location
        ##XZ: deal with direction
        if self.strand_probe == '+':
            fmt += (' on the plus strand ')
        elif self.strand_probe == '-':
            fmt += (' on the minus strand ')

        return fmt
        
def retrieve_sample_data(trait, dataset, samplelist=None):
    if samplelist == None:
        samplelist = []

    if dataset.type == "Temp":
        results = Redis.get(trait.name).split()
    else:
        results = dataset.retrieve_sample_data(trait.name)

    # Todo: is this necessary? If not remove
    trait.data.clear()

    if results:
        if dataset.type == "Temp":
            all_samples_ordered = dataset.group.all_samples_ordered()
            for i, item in enumerate(results):
                try:
                    trait.data[all_samples_ordered[i]] = webqtlCaseData(all_samples_ordered[i], float(item))
                except:
                    pass
        else:
            for item in results:
                name, value, variance, num_cases, name2 = item
                if not samplelist or (samplelist and name in samplelist):
                    trait.data[name] = webqtlCaseData(*item)   #name, value, variance, num_cases)
    return trait

@app.route("/trait/get_sample_data")
def get_sample_data():
    params = request.args
    trait = params['trait']
    dataset = params['dataset']

    trait_ob = GeneralTrait(name=trait, dataset_name=dataset)

    trait_dict = {}
    trait_dict['name'] = trait
    trait_dict['db'] = dataset
    trait_dict['type'] = trait_ob.dataset.type
    trait_dict['group'] = trait_ob.dataset.group.name
    trait_dict['tissue'] = trait_ob.dataset.tissue
    trait_dict['species'] = trait_ob.dataset.group.species
    trait_dict['url'] = url_for('show_trait_page', trait_id = trait, dataset = dataset)
    trait_dict['description'] = trait_ob.description_display
    if trait_ob.dataset.type == "ProbeSet":
        trait_dict['symbol'] = trait_ob.symbol
        trait_dict['location'] = trait_ob.location_repr
    elif trait_ob.dataset.type == "Publish":
        if trait_ob.pubmed_id:
            trait_dict['pubmed_link'] = trait_ob.pubmed_link
        trait_dict['pubmed_text'] = trait_ob.pubmed_text

    return json.dumps([trait_dict, {key: value.value for key, value in trait_ob.data.iteritems() }])
    
def jsonable(trait):
    """Return a dict suitable for using as json

    Actual turning into json doesn't happen here though"""

    dataset = create_dataset(dataset_name = trait.dataset.name, dataset_type = trait.dataset.type, group_name = trait.dataset.group.name)
    
    if dataset.type == "ProbeSet":
        return dict(name=trait.name,
                    symbol=trait.symbol,
                    dataset=dataset.name,
                    dataset_name = dataset.shortname,
                    description=trait.description_display,
                    mean=trait.mean,
                    location=trait.location_repr,
                    lrs_score=trait.LRS_score_repr,
                    lrs_location=trait.LRS_location_repr,
                    additive=trait.additive
                    )
    elif dataset.type == "Publish":
        if trait.pubmed_id:
            return dict(name=trait.name,
                        dataset=dataset.name,
                        dataset_name = dataset.shortname,
                        description=trait.description_display,
                        abbreviation=trait.abbreviation,
                        authors=trait.authors,
                        pubmed_text=trait.pubmed_text,
                        pubmed_link=trait.pubmed_link,
                        lrs_score=trait.LRS_score_repr,
                        lrs_location=trait.LRS_location_repr,
                        additive=trait.additive
                        )
        else:
            return dict(name=trait.name,
                        dataset=dataset.name,
                        dataset_name = dataset.shortname,
                        description=trait.description_display,
                        abbreviation=trait.abbreviation,
                        authors=trait.authors,
                        pubmed_text=trait.pubmed_text,
                        lrs_score=trait.LRS_score_repr,
                        lrs_location=trait.LRS_location_repr,
                        additive=trait.additive
                        )
    elif dataset.type == "Geno":
        return dict(name=trait.name,
                    dataset=dataset.name,
                    dataset_name = dataset.shortname,
                    location=trait.location_repr
                    )
    else:
        return dict()

def jsonable_table_row(trait, dataset_name, index):
    """Return a list suitable for json and intended to be displayed in a table

    Actual turning into json doesn't happen here though"""

    dataset = create_dataset(dataset_name)
    
    if dataset.type == "ProbeSet":
        if trait.mean == "":
            mean = "N/A"
        else:
            mean = "%.3f" % round(float(trait.mean), 2)
        if trait.additive == "":
            additive = "N/A"
        else:
            additive = "%.3f" % round(float(trait.additive), 2)
        return ['<input type="checkbox" name="searchResult" class="checkbox trait_checkbox" value="' + user_manager.data_hmac('{}:{}'.format(str(trait.name), dataset.name)) + '">',
                index,
                '<a href="/show_trait?trait_id='+str(trait.name)+'&dataset='+dataset.name+'">'+str(trait.name)+'</a>',
                trait.symbol,
                trait.description_display,
                trait.location_repr,
                mean, 
                trait.LRS_score_repr,
                trait.LRS_location_repr,
                additive]
    elif dataset.type == "Publish":
        if trait.additive == "":
            additive = "N/A"
        else:
            additive = "%.2f" % round(float(trait.additive), 2)
        if trait.pubmed_id:
            return ['<input type="checkbox" name="searchResult" class="checkbox trait_checkbox" value="' + user_manager.data_hmac('{}:{}'.format(str(trait.name), dataset.name)) + '">',
                    index,
                    '<a href="/show_trait?trait_id='+str(trait.name)+'&dataset='+dataset.name+'">'+str(trait.name)+'</a>',
                    trait.description_display,
                    trait.authors,
                    '<a href="' + trait.pubmed_link + '">' + trait.pubmed_text + '</href>',
                    trait.LRS_score_repr,
                    trait.LRS_location_repr,
                    additive]
        else:
            return ['<input type="checkbox" name="searchResult" class="checkbox trait_checkbox" value="' + user_manager.data_hmac('{}:{}'.format(str(trait.name), dataset.name)) + '">',
                    index,
                    '<a href="/show_trait?trait_id='+str(trait.name)+'&dataset='+dataset.name+'">'+str(trait.name)+'</a>',
                    trait.description_display,
                    trait.authors,
                    trait.pubmed_text,
                    trait.LRS_score_repr,
                    trait.LRS_location_repr,
                    additive]
    elif dataset.type == "Geno":
        return ['<input type="checkbox" name="searchResult" class="checkbox trait_checkbox" value="' + user_manager.data_hmac('{}:{}'.format(str(trait.name), dataset.name)) + '">',
                index,
                '<a href="/show_trait?trait_id='+str(trait.name)+'&dataset='+dataset.name+'">'+str(trait.name)+'</a>',
                trait.location_repr]
    else:
        return dict()

def retrieve_trait_info(trait, dataset, get_qtl_info=False):
    assert dataset, "Dataset doesn't exist"
    
    if dataset.type == 'Publish':
        query = """
                SELECT
                        PublishXRef.Id, Publication.PubMed_ID,
                        Phenotype.Pre_publication_description, Phenotype.Post_publication_description, Phenotype.Original_description,
                        Phenotype.Pre_publication_abbreviation, Phenotype.Post_publication_abbreviation,
                        Phenotype.Lab_code, Phenotype.Submitter, Phenotype.Owner, Phenotype.Authorized_Users,
                        Publication.Authors, Publication.Title, Publication.Abstract,
                        Publication.Journal, Publication.Volume, Publication.Pages,
                        Publication.Month, Publication.Year, PublishXRef.Sequence,
                        Phenotype.Units, PublishXRef.comments
                FROM
                        PublishXRef, Publication, Phenotype, PublishFreeze
                WHERE
                        PublishXRef.Id = %s AND
                        Phenotype.Id = PublishXRef.PhenotypeId AND
                        Publication.Id = PublishXRef.PublicationId AND
                        PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                        PublishFreeze.Id = %s
                """ % (trait.name, dataset.id)

        logger.sql(query)
        trait_info = g.db.execute(query).fetchone()


    #XZ, 05/08/2009: Xiaodong add this block to use ProbeSet.Id to find the probeset instead of just using ProbeSet.Name
    #XZ, 05/08/2009: to avoid the problem of same probeset name from different platforms.
    elif dataset.type == 'ProbeSet':
        display_fields_string = ', ProbeSet.'.join(dataset.display_fields)
        display_fields_string = 'ProbeSet.' + display_fields_string
        query = """
                SELECT %s
                FROM ProbeSet, ProbeSetFreeze, ProbeSetXRef
                WHERE
                        ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                        ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                        ProbeSetFreeze.Name = '%s' AND
                        ProbeSet.Name = '%s'
                """ % (escape(display_fields_string),
                       escape(dataset.name),
                       escape(str(trait.name)))
        logger.sql(query)
        trait_info = g.db.execute(query).fetchone()
    #XZ, 05/08/2009: We also should use Geno.Id to find marker instead of just using Geno.Name
    # to avoid the problem of same marker name from different species.
    elif dataset.type == 'Geno':
        display_fields_string = string.join(dataset.display_fields,',Geno.')
        display_fields_string = 'Geno.' + display_fields_string
        query = """
                SELECT %s
                FROM Geno, GenoFreeze, GenoXRef
                WHERE
                        GenoXRef.GenoFreezeId = GenoFreeze.Id AND
                        GenoXRef.GenoId = Geno.Id AND
                        GenoFreeze.Name = '%s' AND
                        Geno.Name = '%s'
                """ % (escape(display_fields_string),
                       escape(dataset.name),
                       escape(trait.name))
        logger.sql(query)
        trait_info = g.db.execute(query).fetchone()
    else: #Temp type
        query = """SELECT %s FROM %s WHERE Name = %s"""
        logger.sql(query)
        trait_info = g.db.execute(query,
                                  (string.join(dataset.display_fields,','),
                                               dataset.type, trait.name)).fetchone()
    if trait_info:
        trait.haveinfo = True

        #XZ: assign SQL query result to trait attributes.
        for i, field in enumerate(dataset.display_fields):
            holder = trait_info[i]
            # if isinstance(trait_info[i], basestring):
            #     logger.debug("HOLDER:", holder)
            #     logger.debug("HOLDER2:", holder.decode(encoding='latin1'))
            #     holder = unicode(trait_info[i], "utf-8", "ignore")
            setattr(trait, field, holder)

        if dataset.type == 'Publish':
            trait.confidential = 0
            if trait.pre_publication_description and not trait.pubmed_id:
                trait.confidential = 1

            description = trait.post_publication_description

            #If the dataset is confidential and the user has access to confidential
            #phenotype traits, then display the pre-publication description instead
            #of the post-publication description
            if trait.confidential:
                trait.abbreviation = trait.pre_publication_abbreviation
                trait.description_display = trait.pre_publication_description

                #if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(
                #        privilege=self.dataset.privilege,
                #        userName=self.dataset.userName,
                #        authorized_users=self.authorized_users):
                #
                #    description = self.pre_publication_description
            else:
                trait.abbreviation = trait.post_publication_abbreviation
                if description:
                    trait.description_display = description.strip()
                else:
                    trait.description_display = ""

            if not trait.year.isdigit():
                trait.pubmed_text = "N/A"
            else:
                trait.pubmed_text = trait.year

            if trait.pubmed_id:
                trait.pubmed_link = webqtlConfig.PUBMEDLINK_URL % trait.pubmed_id

        if dataset.type == 'ProbeSet' and dataset.group:
            description_string = unicode(str(trait.description).strip(codecs.BOM_UTF8), 'utf-8')
            target_string = unicode(str(trait.probe_target_description).strip(codecs.BOM_UTF8), 'utf-8')

            if len(description_string) > 1 and description_string != 'None':
                description_display = description_string
            else:
                description_display = trait.symbol

            if (len(description_display) > 1 and description_display != 'N/A' and
                    len(target_string) > 1 and target_string != 'None'):
                description_display = description_display + '; ' + target_string.strip()

            # Save it for the jinja2 template
            trait.description_display = description_display

            trait.location_repr = 'N/A'
            if trait.chr and trait.mb:
                trait.location_repr = 'Chr%s: %.6f' % (trait.chr, float(trait.mb))

        elif dataset.type == "Geno":
            trait.location_repr = 'N/A'
            if trait.chr and trait.mb:
                trait.location_repr = 'Chr%s: %.6f' % (trait.chr, float(trait.mb))

        if get_qtl_info:
            #LRS and its location
            trait.LRS_score_repr = "N/A"
            trait.LRS_location_repr = "N/A"
            if dataset.type == 'ProbeSet' and not trait.cellid:
                query = """
                        SELECT
                                ProbeSetXRef.Locus, ProbeSetXRef.LRS, ProbeSetXRef.pValue, ProbeSetXRef.mean, ProbeSetXRef.additive
                        FROM
                                ProbeSetXRef, ProbeSet
                        WHERE
                                ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                ProbeSet.Name = "{}" AND
                                ProbeSetXRef.ProbeSetFreezeId ={}
                        """.format(trait.name, dataset.id)
                logger.sql(query)
                trait_qtl = g.db.execute(query).fetchone()
                if trait_qtl:
                    trait.locus, trait.lrs, trait.pvalue, trait.mean, trait.additive = trait_qtl
                    if trait.locus:
                        query = """
                            select Geno.Chr, Geno.Mb from Geno, Species
                            where Species.Name = '{}' and
                            Geno.Name = '{}' and
                            Geno.SpeciesId = Species.Id
                            """.format(dataset.group.species, trait.locus)
                        logger.sql(query)
                        result = g.db.execute(query).fetchone()
                        if result:
                            trait.locus_chr = result[0]
                            trait.locus_mb = result[1]
                        else:
                            trait.locus = trait.locus_chr = trait.locus_mb = trait.additive = ""
                    else:
                        trait.locus = trait.locus_chr = trait.locus_mb = trait.additive = ""
                else:
                    trait.locus = trait.locus_chr = trait.locus_mb = trait.lrs = trait.pvalue = trait.mean = trait.additive = ""


            if dataset.type == 'Publish':
                query = """
                        SELECT
                                PublishXRef.Locus, PublishXRef.LRS, PublishXRef.additive
                        FROM
                                PublishXRef, PublishFreeze
                        WHERE
                                PublishXRef.Id = %s AND
                                PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                                PublishFreeze.Id =%s
                """ % (trait.name, dataset.id)
                logger.sql(query)
                trait_qtl = g.db.execute(query).fetchone()
                if trait_qtl:
                    trait.locus, trait.lrs, trait.additive = trait_qtl
                    if trait.locus:
                        query = """
                            select Geno.Chr, Geno.Mb from Geno, Species
                            where Species.Name = '{}' and
                            Geno.Name = '{}' and
                            Geno.SpeciesId = Species.Id
                            """.format(dataset.group.species, trait.locus)
                        logger.sql(query)
                        result = g.db.execute(query).fetchone()
                        if result:
                            trait.locus_chr = result[0]
                            trait.locus_mb = result[1]
                        else:
                            trait.locus = trait.locus_chr = trait.locus_mb = trait.additive = ""
                    else:
                        trait.locus = trait.locus_chr = trait.locus_mb = trait.additive = ""
                else:
                    trait.locus = trait.lrs = trait.additive = ""

            if (dataset.type == 'Publish' or dataset.type == "ProbeSet") and trait.locus_chr != "" and trait.locus_mb != "":
                trait.LRS_location_repr = LRS_location_repr = 'Chr%s: %.6f' % (trait.locus_chr, float(trait.locus_mb))
                if trait.lrs != "":
                    trait.LRS_score_repr = LRS_score_repr = '%3.1f' % trait.lrs
    else:
        raise KeyError, `trait.name`+' information is not found in the database.'
        
    return trait