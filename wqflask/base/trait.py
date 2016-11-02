from __future__ import absolute_import, division, print_function

import string
import resource
import codecs

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from base.webqtlCaseData import webqtlCaseData
from base.data_set import create_dataset
from db import webqtlDatabaseFunction
from utility import webqtlUtil

from wqflask import app

import simplejson as json
from MySQLdb import escape_string as escape
from pprint import pformat as pf

from flask import Flask, g, request

from utility.logger import getLogger
logger = getLogger(__name__ )

def print_mem(stage=""):
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("{}: {}".format(stage, mem/1024))

class GeneralTrait(object):
    """
    Trait class defines a trait in webqtl, can be either Microarray,
    Published phenotype, genotype, or user input trait

    """

    def __init__(self, get_qtl_info=False, get_sample_info=True, **kw):
        # xor assertion
        assert bool(kw.get('dataset')) != bool(kw.get('dataset_name')), "Needs dataset ob. or name";
        if kw.get('dataset_name'):
            self.dataset = create_dataset(kw.get('dataset_name'))
            #print(" in GeneralTrait created dataset:", self.dataset)
        else:
            self.dataset = kw.get('dataset')
        self.name = kw.get('name')                 # Trait ID, ProbeSet ID, Published ID, etc.
        #print("THE NAME IS:", self.name)
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
        self.num_overlap = None
        self.strand_probe = None
        self.symbol = None

        if kw.get('fullname'):
            name2 = value.split("::")
            if len(name2) == 2:
                self.dataset, self.name = name2
                # self.cellid is set to None above
            elif len(name2) == 3:
                self.dataset, self.name, self.cellid = name2

        # Todo: These two lines are necessary most of the time, but perhaps not all of the time
        # So we could add a simple if statement to short-circuit this if necessary
        self.retrieve_info(get_qtl_info=get_qtl_info)
        if get_sample_info != False:
            self.retrieve_sample_data()


    def jsonable(self):
        """Return a dict suitable for using as json

        Actual turning into json doesn't happen here though"""

        if self.dataset.type == "ProbeSet":
            return dict(name=self.name,
                        symbol=self.symbol,
                        dataset=self.dataset.name,
                        description=self.description_display,
                        mean=self.mean,
                        location=self.location_repr,
                        lrs_score=self.LRS_score_repr,
                        lrs_location=self.LRS_location_repr,
                        additive=self.additive
                        )
        elif self.dataset.type == "Publish":
            if self.pubmed_id:
                return dict(name=self.name,
                            dataset=self.dataset.name,
                            description=self.description_display,
                            authors=self.authors,
                            pubmed_text=self.pubmed_text,
                            pubmed_link=self.pubmed_link,
                            lrs_score=self.LRS_score_repr,
                            lrs_location=self.LRS_location_repr,
                            additive=self.additive
                            )
            else:
                return dict(name=self.name,
                            dataset=self.dataset.name,
                            description=self.description_display,
                            authors=self.authors,
                            pubmed_text=self.pubmed_text,
                            lrs_score=self.LRS_score_repr,
                            lrs_location=self.LRS_location_repr,
                            additive=self.additive
                            )
        elif self.dataset.type == "Geno":
            return dict(name=self.name,
                        dataset=self.dataset.name,
                        location=self.location_repr
                        )
        else:
            return dict()

    def jsonable_table_row(self, index, search_type):
        """Return a list suitable for json and intended to be displayed in a table

        Actual turning into json doesn't happen here though"""

        if self.dataset.type == "ProbeSet":
            if self.mean == "":
                mean = "N/A"
            else:
                mean = "%.3f" % round(float(self.additive), 2)
            if self.additive == "":
                additive = "N/A"
            else:
                additive = "%.3f" % round(float(self.additive), 2)
            return ['<input type="checkbox" name="searchResult" class="checkbox trait_checkbox" style="transform: scale(1.5);" value="{{ data_hmac(\'{}:{}\'.format(' + str(self.name) + ',' + self.dataset.name + ')) }}">',
                    index,
                    '<a href="/show_trait?trait_id='+str(self.name)+'&dataset='+self.dataset.name+'">'+str(self.name)+'</a>',
                    self.symbol,
                    self.description_display,
                    self.location_repr,
                    mean, 
                    self.LRS_score_repr,
                    self.LRS_location_repr,
                    additive]
        elif self.dataset.type == "Publish":
            if self.additive == "":
                additive = "N/A"
            else:
                additive = "%.2f" % round(float(self.additive), 2)
            if self.pubmed_id:
                return ['<input type="checkbox" name="searchResult" class="checkbox trait_checkbox" style="transform: scale(1.5);" value="{{ data_hmac(\'{}:{}\'.format(' + str(self.name) + ',' + self.dataset.name + ')) }}">',
                        index,
                        '<a href="/show_trait?trait_id='+str(self.name)+'&dataset='+self.dataset.name+'">'+str(self.name)+'</a>',
                        self.description_display,
                        self.authors,
                        '<a href="' + self.pubmed_link + '">' + self.pubmed_text + '</href>',
                        self.LRS_score_repr,
                        self.LRS_location_repr,
                        additive]
            else:
                return ['<input type="checkbox" name="searchResult" class="checkbox trait_checkbox" style="transform: scale(1.5);" value="{{ data_hmac(\'{}:{}\'.format(' + str(self.name) + ',' + self.dataset.name + ')) }}">',
                        index,
                        '<a href="/show_trait?trait_id='+str(self.name)+'&dataset='+self.dataset.name+'">'+str(self.name)+'</a>',
                        self.description_display,
                        self.authors,
                        self.pubmed_text,
                        self.LRS_score_repr,
                        self.LRS_location_repr,
                        additive]
        elif self.dataset.type == "Geno":
            return ['<input type="checkbox" name="searchResult" class="checkbox trait_checkbox" style="transform: scale(1.5);" value="{{ data_hmac(\'{}:{}\'.format(' + str(self.name) + ',' + self.dataset.name + ')) }}">',
                    index,
                    '<a href="/show_trait?trait_id='+str(self.name)+'&dataset='+self.dataset.name+'">'+str(self.name)+'</a>',
                    self.location_repr]
        else:
            return dict()

    def get_name(self):
        stringy = ""
        if self.dataset and self.name:
            stringy = "%s::%s" % (self.dataset, self.name)
            if self.cellid:
                stringy += "::" + self.cellid
        else:
            stringy = self.description
        return stringy


    def get_given_name(self):
        """
         when user enter a trait or GN generate a trait, user want show the name
         not the name that generated by GN randomly, the two follow function are
         used to give the real name and the database. displayName() will show the
         database also, getGivenName() just show the name.
         For other trait, displayName() as same as getName(), getGivenName() as
         same as self.name

         Hongqiang 11/29/07

        """
        stringy = self.name
        if self.dataset and self.name:
            desc = self.dataset.get_desc()
            if desc:
                #desc = self.handle_pca(desc)
                stringy = desc
        return stringy


    def display_name(self):
        stringy = ""
        if self.dataset and self.name:
            desc = self.dataset.get_desc()
            #desc = self.handle_pca(desc)
            if desc:
                #desc = self.handle_pca(desc)
                #stringy = desc
                #if desc.__contains__('PCA'):
                #    desc = desc[desc.rindex(':')+1:].strip()
                #else:
                #    desc = desc[:desc.index('entered')].strip()
                #desc = self.handle_pca(desc)
                stringy = "%s::%s" % (self.dataset, desc)
            else:
                stringy = "%s::%s" % (self.dataset, self.name)
                if self.cellid:
                    stringy += "::" + self.cellid
        else:
            stringy = self.description

        return stringy


    #def __str__(self):
    #       #return "%s %s" % (self.getName(), self.group)
    #       return self.getName()
    #__str__ = getName
    #__repr__ = __str__

    def export_data(self, samplelist, the_type="val"):
        """
        export data according to samplelist
        mostly used in calculating correlation

        """
        result = []
        for sample in samplelist:
            if self.data.has_key(sample):
                if the_type=='val':
                    result.append(self.data[sample].val)
                elif the_type=='var':
                    result.append(self.data[sample].var)
                elif the_type=='N':
                    result.append(self.data[sample].N)
                else:
                    raise KeyError, `the_type`+' the_type is incorrect.'
            else:
                result.append(None)
        return result

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


    #
    # In ProbeSet, there are maybe several annotations match one sequence
    # so we need use sequence(BlatSeq) as the identification, when we update
    # one annotation, we update the others who match the sequence also.
    #
    # Hongqiang Li, 3/3/2008
    #
    #def getSequence(self):
    #    assert self.cursor
    #    if self.dataset.type == 'ProbeSet':
    #        self.cursor.execute('''
    #                        SELECT
    #                                ProbeSet.BlatSeq
    #                        FROM
    #                                ProbeSet, ProbeSetFreeze, ProbeSetXRef
    #                        WHERE
    #                                ProbeSet.Id=ProbeSetXRef.ProbeSetId and
    #                                ProbeSetFreeze.Id = ProbeSetXRef.ProbSetFreezeId and
    #                                ProbeSet.Name = %s
    #                                ProbeSetFreeze.Name = %s
    #                ''', self.name, self.dataset.name)
    #        #self.cursor.execute(query)
    #        results = self.fetchone()
    #
    #        return results[0]



    def retrieve_sample_data(self, samplelist=None):
        if samplelist == None:
            samplelist = []

        results = self.dataset.retrieve_sample_data(self.name)

        # Todo: is this necessary? If not remove
        self.data.clear()

        all_samples_ordered = self.dataset.group.all_samples_ordered()

        if results:
            for item in results:
                name, value, variance, num_cases, name2 = item
                if not samplelist or (samplelist and name in samplelist):
                    self.data[name] = webqtlCaseData(*item)   #name, value, variance, num_cases)

    def retrieve_info(self, get_qtl_info=False):
        assert self.dataset, "Dataset doesn't exist"
        if self.dataset.type == 'Publish':
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
                    """ % (self.name, self.dataset.id)

            logger.sql(query)
            trait_info = g.db.execute(query).fetchone()


        #XZ, 05/08/2009: Xiaodong add this block to use ProbeSet.Id to find the probeset instead of just using ProbeSet.Name
        #XZ, 05/08/2009: to avoid the problem of same probeset name from different platforms.
        elif self.dataset.type == 'ProbeSet':
            display_fields_string = ', ProbeSet.'.join(self.dataset.display_fields)
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
                           escape(self.dataset.name),
                           escape(str(self.name)))
            logger.sql(query)
            trait_info = g.db.execute(query).fetchone()
        #XZ, 05/08/2009: We also should use Geno.Id to find marker instead of just using Geno.Name
        # to avoid the problem of same marker name from different species.
        elif self.dataset.type == 'Geno':
            display_fields_string = string.join(self.dataset.display_fields,',Geno.')
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
                           escape(self.dataset.name),
                           escape(self.name))
            logger.sql(query)
            trait_info = g.db.execute(query).fetchone()
        else: #Temp type
            query = """SELECT %s FROM %s WHERE Name = %s"""
            logger.sql(query)
            trait_info = g.db.execute(query,
                                      (string.join(self.dataset.display_fields,','),
                                                   self.dataset.type, self.name)).fetchone()
        if trait_info:
            self.haveinfo = True

            #XZ: assign SQL query result to trait attributes.
            for i, field in enumerate(self.dataset.display_fields):
                holder = trait_info[i]
                if isinstance(trait_info[i], basestring):
                    holder = unicode(trait_info[i], "utf8", "ignore")
                setattr(self, field, holder)

            if self.dataset.type == 'Publish':
                self.confidential = 0
                if self.pre_publication_description and not self.pubmed_id:
                    self.confidential = 1

                description = self.post_publication_description

                #If the dataset is confidential and the user has access to confidential
                #phenotype traits, then display the pre-publication description instead
                #of the post-publication description
                if self.confidential:
                    self.description_display = self.pre_publication_description

                    #if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(
                    #        privilege=self.dataset.privilege,
                    #        userName=self.dataset.userName,
                    #        authorized_users=self.authorized_users):
                    #
                    #    description = self.pre_publication_description
                else:
                    if description:
                        self.description_display = description.strip()
                    else:
                        self.description_display = ""

                if not self.year.isdigit():
                    self.pubmed_text = "N/A"
                else:
                    self.pubmed_text = self.year

                if self.pubmed_id:
                    self.pubmed_link = webqtlConfig.PUBMEDLINK_URL % self.pubmed_id


            self.homologeneid = None
            if self.dataset.type == 'ProbeSet' and self.dataset.group:
                if self.geneid:
                    #XZ, 05/26/2010: From time to time, this query get error message because some geneid values in database are not number.
                    #XZ: So I have to test if geneid is number before execute the query.
                    #XZ: The geneid values in database should be cleaned up.
                    #try:
                    #    float(self.geneid)
                    #    geneidIsNumber = True
                    #except ValueError:
                    #    geneidIsNumber = False
                    #if geneidIsNumber:
                    query = """
                            SELECT
                                    HomologeneId
                            FROM
                                    Homologene, Species, InbredSet
                            WHERE
                                    Homologene.GeneId ='%s' AND
                                    InbredSet.Name = '%s' AND
                                    InbredSet.SpeciesId = Species.Id AND
                                    Species.TaxonomyId = Homologene.TaxonomyId
                            """ % (escape(str(self.geneid)), escape(self.dataset.group.name))
                    logger.sql(query)
                    result = g.db.execute(query).fetchone()
                    #else:
                    #    result = None

                    if result:
                        self.homologeneid = result[0]

                description_string = unicode(str(self.description).strip(codecs.BOM_UTF8), 'utf-8')
                target_string = unicode(str(self.probe_target_description).strip(codecs.BOM_UTF8), 'utf-8')

                if len(description_string) > 1 and description_string != 'None':
                    description_display = description_string
                else:
                    description_display = self.symbol

                if (len(description_display) > 1 and description_display != 'N/A' and
                        len(target_string) > 1 and target_string != 'None'):
                    description_display = description_display + '; ' + target_string.strip()

                # Save it for the jinja2 template
                self.description_display = description_display

                #XZ: trait_location_value is used for sorting
                self.location_repr = 'N/A'
                trait_location_value = 1000000

                if self.chr and self.mb:
                    #Checks if the chromosome number can be cast to an int (i.e. isn't "X" or "Y")
                    #This is so we can convert the location to a number used for sorting
                    trait_location_value = convert_location_to_value(self.chr, self.mb)
                     #try:
                    #    trait_location_value = int(self.chr)*1000 + self.mb
                    #except ValueError:
                    #    if self.chr.upper() == 'X':
                    #        trait_location_value = 20*1000 + self.mb
                    #    else:
                    #        trait_location_value = (ord(str(self.chr).upper()[0])*1000 +
                    #                               self.mb)

                    #ZS: Put this in function currently called "convert_location_to_value"
                    self.location_repr = 'Chr%s: %.6f' % (self.chr, float(self.mb))
                    self.location_value = trait_location_value

            elif self.dataset.type == "Geno":
                self.location_repr = 'N/A'
                trait_location_value = 1000000

                if self.chr and self.mb:
                    #Checks if the chromosome number can be cast to an int (i.e. isn't "X" or "Y")
                    #This is so we can convert the location to a number used for sorting
                    trait_location_value = convert_location_to_value(self.chr, self.mb)

                    #ZS: Put this in function currently called "convert_location_to_value"
                    self.location_repr = 'Chr%s: %.6f' % (self.chr, float(self.mb))
                    self.location_value = trait_location_value

            if get_qtl_info:
                #LRS and its location
                self.LRS_score_repr = "N/A"
                self.LRS_score_value = 0
                self.LRS_location_repr = "N/A"
                self.LRS_location_value = 1000000
                if self.dataset.type == 'ProbeSet' and not self.cellid:
                    query = """
                            SELECT
                                    ProbeSetXRef.Locus, ProbeSetXRef.LRS, ProbeSetXRef.pValue, ProbeSetXRef.mean, ProbeSetXRef.additive
                            FROM
                                    ProbeSetXRef, ProbeSet
                            WHERE
                                    ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                    ProbeSet.Name = "{}" AND
                                    ProbeSetXRef.ProbeSetFreezeId ={}
                            """.format(self.name, self.dataset.id)
                    logger.sql(query)
                    trait_qtl = g.db.execute(query).fetchone()
                    if trait_qtl:
                        self.locus, self.lrs, self.pvalue, self.mean, self.additive = trait_qtl
                        if self.locus:
                            query = """
                                select Geno.Chr, Geno.Mb from Geno, Species
                                where Species.Name = '{}' and
                                Geno.Name = '{}' and
                                Geno.SpeciesId = Species.Id
                                """.format(self.dataset.group.species, self.locus)
                            logger.sql(query)
                            result = g.db.execute(query).fetchone()
                            if result:
                                self.locus_chr = result[0]
                                self.locus_mb = result[1]
                            else:
                                self.locus = self.locus_chr = self.locus_mb = self.additive = ""
                        else:
                            self.locus = self.locus_chr = self.locus_mb = self.additive = ""
                    else:
                        self.locus = self.locus_chr = self.locus_mb = self.lrs = self.pvalue = self.mean = self.additive = ""


                if self.dataset.type == 'Publish':
                    query = """
                            SELECT
                                    PublishXRef.Locus, PublishXRef.LRS, PublishXRef.additive
                            FROM
                                    PublishXRef, PublishFreeze
                            WHERE
                                    PublishXRef.Id = %s AND
                                    PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                                    PublishFreeze.Id =%s
                    """ % (self.name, self.dataset.id)
                    logger.sql(query)
                    trait_qtl = g.db.execute(query).fetchone()
                    if trait_qtl:
                        self.locus, self.lrs, self.additive = trait_qtl
                        if self.locus:
                            query = """
                                select Geno.Chr, Geno.Mb from Geno, Species
                                where Species.Name = '{}' and
                                Geno.Name = '{}' and
                                Geno.SpeciesId = Species.Id
                                """.format(self.dataset.group.species, self.locus)
                            logger.sql(query)
                            result = g.db.execute(query).fetchone()
                            if result:
                                self.locus_chr = result[0]
                                self.locus_mb = result[1]
                            else:
                                self.locus = self.locus_chr = self.locus_mb = self.additive = ""
                        else:
                            self.locus = self.locus_chr = self.locus_mb = self.additive = ""
                    else:
                        self.locus = self.lrs = self.additive = ""

                if (self.dataset.type == 'Publish' or self.dataset.type == "ProbeSet") and self.locus_chr != "" and self.locus_mb != "":
                    #XZ: LRS_location_value is used for sorting
                    try:
                        LRS_location_value = int(self.locus_chr)*1000 + float(self.locus_mb)
                    except:
                        if self.locus_chr.upper() == 'X':
                            LRS_location_value = 20*1000 + float(self.locus_mb)
                        else:
                            LRS_location_value = ord(str(self.locus_chr).upper()[0])*1000 + float(self.locus_mb)

                    self.LRS_location_repr = LRS_location_repr = 'Chr%s: %.6f' % (self.locus_chr, float(self.locus_mb))
                    if self.lrs != "":
                        self.LRS_score_repr = LRS_score_repr = '%3.1f' % self.lrs
                        self.LRS_score_value = LRS_score_value = self.lrs
        else:
            raise KeyError, `self.name`+' information is not found in the database.'

    def genHTML(self, formName = "", dispFromDatabase=0, privilege="guest", userName="Guest", authorized_users=""):
        if not self.haveinfo:
            self.retrieveInfo()

        if self.dataset.type == 'Publish':
            PubMedLink = ""
            if self.pubmed_id:
                PubMedLink = HT.Href(text="PubMed %d : " % self.pubmed_id,
                target = "_blank", url = webqtlConfig.PUBMEDLINK_URL % self.pubmed_id)
            else:
                PubMedLink = HT.Span("Unpublished : ", Class="fs15")

            if formName:
                setDescription2 = HT.Href(url="javascript:showDatabase3('%s','%s','%s','')" %
                (formName, self.dataset.name, self.name), Class = "fs14")
            else:
                setDescription2 = HT.Href(url="javascript:showDatabase2('%s','%s','')" %
                (self.dataset.name,self.name), Class = "fs14")

            if self.confidential and not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=privilege, userName=userName, authorized_users=authorized_users):
                setDescription2.append('RecordID/%s - %s' % (self.name, self.pre_publication_description))
            else:
                setDescription2.append('RecordID/%s - %s' % (self.name, self.post_publication_description))

            #XZ 03/26/2011: Xiaodong comment out the following two lins as Rob asked. Need to check with Rob why in PublishXRef table, there are few row whose Sequence > 1.
            #if self.sequence > 1:
            #       setDescription2.append(' btach %d' % self.sequence)
            if self.authors:
                a1 = string.split(self.authors,',')[0]
                while a1[0] == '"' or a1[0] == "'" :
                    a1 = a1[1:]
                setDescription2.append(' by ')
                setDescription2.append(HT.Italic('%s, and colleagues' % a1))
            setDescription = HT.Span(PubMedLink, setDescription2)

        elif self.dataset.type == 'Temp':
            setDescription = HT.Href(text="%s" % (self.description),url="javascript:showDatabase2\
            ('%s','%s','')" % (self.dataset.name,self.name), Class = "fs14")
            setDescription = HT.Span(setDescription)

        elif self.dataset.type == 'Geno': # Genome DB only available for single search
            if formName:
                setDescription = HT.Href(text="Locus %s [Chr %s @ %s Mb]" % (self.name,self.chr,\
        '%2.3f' % self.mb),url="javascript:showDatabase3('%s','%s','%s','')" % \
        (formName, self.dataset.name, self.name), Class = "fs14")
            else:
                setDescription = HT.Href(text="Locus %s [Chr %s @ %s Mb]" % (self.name,self.chr,\
        '%2.3f' % self.mb),url="javascript:showDatabase2('%s','%s','')" % \
        (self.dataset.name,self.name), Class = "fs14")

            setDescription = HT.Span(setDescription)

        else:
            if self.cellid:
                if formName:
                    setDescription = HT.Href(text="ProbeSet/%s/%s" % (self.name, self.cellid),url=\
            "javascript:showDatabase3('%s','%s','%s','%s')" % (formName, self.dataset.name,self.name,self.cellid), \
            Class = "fs14")
                else:
                    setDescription = HT.Href(text="ProbeSet/%s/%s" % (self.name,self.cellid),url=\
            "javascript:showDatabase2('%s','%s','%s')" % (self.dataset.name,self.name,self.cellid), \
            Class = "fs14")
            else:
                if formName:
                    setDescription = HT.Href(text="ProbeSet/%s" % self.name, url=\
            "javascript:showDatabase3('%s','%s','%s','')" % (formName, self.dataset.name,self.name), \
            Class = "fs14")
                else:
                    setDescription = HT.Href(text="ProbeSet/%s" % self.name, url=\
            "javascript:showDatabase2('%s','%s','')" % (self.dataset.name,self.name), \
            Class = "fs14")
            if self.symbol and self.chr and self.mb:
                setDescription.append(' [')
                setDescription.append(HT.Italic('%s' % self.symbol,Class="cdg fwb"))
                setDescription.append(' on Chr %s @ %s Mb]' % (self.chr,self.mb))
            if self.description:
                setDescription.append(': %s' % self.description)
            if self.probe_target_description:
                setDescription.append('; %s' % self.probe_target_description)
            setDescription = HT.Span(setDescription)

        if self.dataset.type != 'Temp' and dispFromDatabase:
            setDescription.append( ' --- FROM : ')
            setDescription.append(self.dataset.genHTML(Class='cori'))
        return setDescription

    @property
    def name_header_fmt(self):
        '''Return a human-readable name for use in page header'''
        if self.dataset.type == 'ProbeSet':
            return self.symbol
        elif self.dataset.type == 'Geno':
            return self.name
        elif self.dataset.type == 'Publish':
            return self.post_publication_abbreviation
        else:
            return "unnamed"

    @property
    def description_fmt(self):
        '''Return a text formated description'''
        if self.dataset.type == 'ProbeSet':
            if self.description:
                formatted = self.description
                if self.probe_target_description:
                    formatted += "; " + self.probe_target_description
        elif self.dataset.type == 'Publish':
            if self.confidential:
                formatted = self.pre_publication_description
            else:
                formatted = self.post_publication_description
        else:
            formatted = "Not available"
        return formatted.capitalize()

    @property
    def alias_fmt(self):
        '''Return a text formatted alias'''
        if self.alias:
            alias = string.replace(self.alias, ";", " ")
            alias = string.join(string.split(alias), ", ")
        else:
            alias = 'Not available'

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


    def get_database(self):
        """
        Returns the database, and the url referring to the database if it exists

        We're going to to return two values here, and we don't want to have to call this twice from
        the template. So it's not a property called from the template, but instead is called from the view

        """
        if self.cellid:
            query = """ select ProbeFreeze.Name from ProbeFreeze, ProbeSetFreeze where
                            ProbeFreeze.Id =
                            ProbeSetFreeze.ProbeFreezeId AND
                            ProbeSetFreeze.Id = %d""" % thisTrait.dataset.id
            logger.sql(query)
            probeDBName = g.db.execute(query).fetchone()[0]
            return dict(name = probeDBName,
                        url = None)
        else:
            return dict(name = self.dataset.fullname,
                        url = webqtlConfig.INFOPAGEHREF % self.dataset.name)

    def calculate_correlation(self, values, method):
        """Calculate the correlation value and p value according to the method specified"""

        #ZS: This takes the list of values of the trait our selected trait is being correlated against and removes the values of the samples our trait has no value for
        #There's probably a better way of dealing with this, but I'll have to ask Christian
        updated_raw_values = []
        updated_values = []
        for i in range(len(values)):
            if values[i] != "None":
                updated_raw_values.append(self.raw_values[i])
                updated_values.append(values[i])

        self.raw_values = updated_raw_values
        values = updated_values

        if method == METHOD_SAMPLE_PEARSON or method == METHOD_LIT or method == METHOD_TISSUE_PEARSON:
            corr, nOverlap = webqtlUtil.calCorrelation(self.raw_values, values, len(values))
        else:
            corr, nOverlap = webqtlUtil.calCorrelationRank(self.raw_values, values, len(values))

        self.correlation = corr
        self.overlap = nOverlap

        if self.overlap < 3:
            self.p_value = 1.0
        else:
            #ZS - This is probably the wrong way to deal with this. Correlation values of 1.0 definitely exist (the trait correlated against itself), so zero division needs to br prevented.
            if abs(self.correlation) >= 1.0:
                self.p_value = 0.0
            else:
                ZValue = 0.5*log((1.0+self.correlation)/(1.0-self.correlation))
                ZValue = ZValue*sqrt(self.overlap-3)
                self.p_value = 2.0*(1.0 - reaper.normp(abs(ZValue)))

def convert_location_to_value(chromosome, mb):
    try:
        location_value = int(chromosome)*1000 + float(mb)
    except ValueError:
        if chromosome.upper() == 'X':
            location_value = 20*1000 + float(mb)
        else:
            location_value = (ord(str(chromosome).upper()[0])*1000 +
                              float(mb))

    return location_value

@app.route("/trait/get_sample_data")
def get_sample_data():
    params = request.args
    trait = params['trait']
    dataset = params['dataset']

    trait_ob = GeneralTrait(name=trait, dataset_name=dataset)

    return json.dumps([trait, {key: value.value for key, value in trait_ob.data.iteritems() }])

    #jsonable_sample_data = {}
    #for sample in trait_ob.data.iteritems():
    #    jsonable_sample_data[sample] = trait_ob.data[sample].value
    #
    #return jsonable_sample_data
