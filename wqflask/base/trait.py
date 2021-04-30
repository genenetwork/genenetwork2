import requests
import simplejson as json
from wqflask import app

from base import webqtlConfig
from base.webqtlCaseData import webqtlCaseData
from base.data_set import create_dataset
from utility import hmac
from utility.authentication_tools import check_resource_availability
from utility.tools import GN2_BASE_URL
from utility.redis_tools import get_redis_conn, get_resource_id

from utility.db_tools import escape

from flask import g, request, url_for

from utility.logger import getLogger

logger = getLogger(__name__)

Redis = get_redis_conn()


def create_trait(**kw):
    assert bool(kw.get('dataset')) != bool(
        kw.get('dataset_name')), "Needs dataset ob. or name"

    assert bool(kw.get('name')), "Needs trait name"

    if kw.get('dataset_name'):
        if kw.get('dataset_name') != "Temp":
            dataset = create_dataset(kw.get('dataset_name'))
    else:
        dataset = kw.get('dataset')

    if dataset.type == 'Publish':
        permissions = check_resource_availability(
            dataset, kw.get('name'))
    else:
        permissions = check_resource_availability(dataset)

    if permissions['data'] != "no-access":
        the_trait = GeneralTrait(**kw)
        if the_trait.dataset.type != "Temp":
            the_trait = retrieve_trait_info(
                the_trait,
                the_trait.dataset,
                get_qtl_info=kw.get('get_qtl_info'))
        return the_trait
    else:
        return None


class GeneralTrait:
    """
    Trait class defines a trait in webqtl, can be either Microarray,
    Published phenotype, genotype, or user input trait

    """

    def __init__(self, get_qtl_info=False, get_sample_info=True, **kw):
        # xor assertion
        assert bool(kw.get('dataset')) != bool(
            kw.get('dataset_name')), "Needs dataset ob. or name"
        # Trait ID, ProbeSet ID, Published ID, etc.
        self.name = kw.get('name')
        if kw.get('dataset_name'):
            if kw.get('dataset_name') == "Temp":
                temp_group = self.name.split("_")[2]
                self.dataset = create_dataset(
                    dataset_name="Temp",
                    dataset_type="Temp",
                    group_name=temp_group)
            else:
                self.dataset = create_dataset(kw.get('dataset_name'))
        else:
            self.dataset = kw.get('dataset')
        self.cellid = kw.get('cellid')
        self.identification = kw.get('identification', 'un-named trait')
        self.haveinfo = kw.get('haveinfo', False)
        # Blat sequence, available for ProbeSet
        self.sequence = kw.get('sequence')
        self.data = kw.get('data', {})
        self.view = True

        # Sets defaults
        self.locus = None
        self.lrs = None
        self.pvalue = None
        self.mean = None
        self.additive = None
        self.num_overlap = None
        self.strand_probe = None
        self.symbol = None
        self.display_name = self.name

        self.LRS_score_repr = "N/A"
        self.LRS_location_repr = "N/A"

        if kw.get('fullname'):
            name2 = value.split("::")
            if len(name2) == 2:
                self.dataset, self.name = name2
                # self.cellid is set to None above
            elif len(name2) == 3:
                self.dataset, self.name, self.cellid = name2

        # Todo: These two lines are necessary most of the time, but
        # perhaps not all of the time So we could add a simple if
        # statement to short-circuit this if necessary
        if get_sample_info is not False:
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
        for sample_name, sample_data in list(self.data.items()):
            if sample_data.value is not None:
                if not include_variance or sample_data.variance is not None:
                    samples.append(sample_name)
                    vals.append(sample_data.value)
                    the_vars.append(sample_data.variance)
                    sample_aliases.append(sample_data.name2)
        return samples, vals, the_vars, sample_aliases

    @property
    def description_fmt(self):
        """Return a text formated description"""
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
        if isinstance(formatted, bytes):
            formatted = formatted.decode("utf-8")
        return formatted

    @property
    def alias_fmt(self):
        """Return a text formatted alias"""

        alias = 'Not available'
        if getattr(self, "alias", None):
            alias = self.alias.replace(";", " ")
            alias = ", ".join(alias.split())

        return alias

    @property
    def wikidata_alias_fmt(self):
        """Return a text formatted alias"""

        alias = 'Not available'
        if self.symbol:
            human_response = requests.get(
                GN2_BASE_URL + "gn3/gene/aliases/" + self.symbol.upper())
            mouse_response = requests.get(
                GN2_BASE_URL + "gn3/gene/aliases/" + self.symbol.capitalize())
            other_response = requests.get(
                GN2_BASE_URL + "gn3/gene/aliases/" + self.symbol.lower())

            if human_response and mouse_response and other_response:
                alias_list = json.loads(human_response.content) + json.loads(
                    mouse_response.content) + \
                    json.loads(other_response.content)

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
        """Return a text formatted location

        While we're at it we set self.location in case we need it
        later (do we?)

        """

        if self.chr and self.mb:
            self.location = 'Chr %s @ %s Mb' % (self.chr, self.mb)
        elif self.chr:
            self.location = 'Chr %s @ Unknown position' % (self.chr)
        else:
            self.location = 'Not available'

        fmt = self.location
        # XZ: deal with direction
        if self.strand_probe == '+':
            fmt += (' on the plus strand ')
        elif self.strand_probe == '-':
            fmt += (' on the minus strand ')

        return fmt


def retrieve_sample_data(trait, dataset, samplelist=None):
    if samplelist is None:
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
                    trait.data[all_samples_ordered[i]] = webqtlCaseData(
                        all_samples_ordered[i], float(item))
                except:
                    pass
        else:
            for item in results:
                name, value, variance, num_cases, name2 = item
                if not samplelist or (samplelist and name in samplelist):
                    # name, value, variance, num_cases)
                    trait.data[name] = webqtlCaseData(*item)
    return trait


@app.route("/trait/get_sample_data")
def get_sample_data():
    params = request.args
    trait = params['trait']
    dataset = params['dataset']

    trait_ob = create_trait(name=trait, dataset_name=dataset)
    if trait_ob:
        trait_dict = {}
        trait_dict['name'] = trait
        trait_dict['db'] = dataset
        trait_dict['type'] = trait_ob.dataset.type
        trait_dict['group'] = trait_ob.dataset.group.name
        trait_dict['tissue'] = trait_ob.dataset.tissue
        trait_dict['species'] = trait_ob.dataset.group.species
        trait_dict['url'] = url_for(
            'show_trait_page', trait_id=trait, dataset=dataset)
        if trait_ob.dataset.type == "ProbeSet":
            trait_dict['symbol'] = trait_ob.symbol
            trait_dict['location'] = trait_ob.location_repr
            trait_dict['description'] = trait_ob.description_display
        elif trait_ob.dataset.type == "Publish":
            trait_dict['description'] = trait_ob.description_display
            if trait_ob.pubmed_id:
                trait_dict['pubmed_link'] = trait_ob.pubmed_link
            trait_dict['pubmed_text'] = trait_ob.pubmed_text
        else:
            trait_dict['location'] = trait_ob.location_repr

        return json.dumps([trait_dict, {key: value.value for
                                        key, value in list(
                                            trait_ob.data.items())}])
    else:
        return None


def jsonable(trait):
    """Return a dict suitable for using as json

    Actual turning into json doesn't happen here though"""

    dataset = create_dataset(dataset_name=trait.dataset.name,
                             dataset_type=trait.dataset.type,
                             group_name=trait.dataset.group.name)

    if dataset.type == "ProbeSet":
        return dict(name=trait.name,
                    symbol=trait.symbol,
                    dataset=dataset.name,
                    dataset_name=dataset.shortname,
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
                        dataset_name=dataset.shortname,
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
                        dataset_name=dataset.shortname,
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
                    dataset_name=dataset.shortname,
                    location=trait.location_repr
                    )
    elif dataset.name == "Temp":
        return dict(name=trait.name,
                    dataset="Temp",
                    dataset_name="Temp")
    else:
        return dict()


def retrieve_trait_info(trait, dataset, get_qtl_info=False):
    assert dataset, "Dataset doesn't exist"

    resource_id = get_resource_id(dataset, trait.name)
    if dataset.type == 'Publish':
        the_url = "http://localhost:8080/run-action?resource={}&user={}&branch=data&action=view".format(
            resource_id, g.user_session.user_id)
    else:
        the_url = "http://localhost:8080/run-action?resource={}&user={}&branch=data&action=view&trait={}".format(
            resource_id, g.user_session.user_id, trait.name)

    try:
        response = requests.get(the_url).content
        trait_info = json.loads(response)
    except:  # ZS: I'm assuming the trait is viewable if the try fails for some reason; it should never reach this point unless the user has privileges, since that's dealt with in create_trait
        if dataset.type == 'Publish':
            query = """
                    SELECT
                            PublishXRef.Id, InbredSet.InbredSetCode, Publication.PubMed_ID,
                            CAST(Phenotype.Pre_publication_description AS BINARY),
                            CAST(Phenotype.Post_publication_description AS BINARY),
                            CAST(Phenotype.Original_description AS BINARY),
                            CAST(Phenotype.Pre_publication_abbreviation AS BINARY),
                            CAST(Phenotype.Post_publication_abbreviation AS BINARY), PublishXRef.mean,
                            Phenotype.Lab_code, Phenotype.Submitter, Phenotype.Owner, Phenotype.Authorized_Users,
                            CAST(Publication.Authors AS BINARY), CAST(Publication.Title AS BINARY), CAST(Publication.Abstract AS BINARY),
                            CAST(Publication.Journal AS BINARY), Publication.Volume, Publication.Pages,
                            Publication.Month, Publication.Year, PublishXRef.Sequence,
                            Phenotype.Units, PublishXRef.comments
                    FROM
                            PublishXRef, Publication, Phenotype, PublishFreeze, InbredSet
                    WHERE
                            PublishXRef.Id = %s AND
                            Phenotype.Id = PublishXRef.PhenotypeId AND
                            Publication.Id = PublishXRef.PublicationId AND
                            PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                            PublishXRef.InbredSetId = InbredSet.Id AND
                            PublishFreeze.Id = %s
                    """ % (trait.name, dataset.id)

            logger.sql(query)
            trait_info = g.db.execute(query).fetchone()

        # XZ, 05/08/2009: Xiaodong add this block to use ProbeSet.Id to find the probeset instead of just using ProbeSet.Name
        # XZ, 05/08/2009: to avoid the problem of same probeset name from different platforms.
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
        # XZ, 05/08/2009: We also should use Geno.Id to find marker instead of just using Geno.Name
        # to avoid the problem of same marker name from different species.
        elif dataset.type == 'Geno':
            display_fields_string = ',Geno.'.join(dataset.display_fields)
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
        else:  # Temp type
            query = """SELECT %s FROM %s WHERE Name = %s"""
            logger.sql(query)
            trait_info = g.db.execute(query,
                                      ','.join(dataset.display_fields),
                                      dataset.type, trait.name).fetchone()

    if trait_info:
        trait.haveinfo = True
        for i, field in enumerate(dataset.display_fields):
            holder = trait_info[i]
            if isinstance(holder, bytes):
                holder = holder.decode("utf-8", errors="ignore")
            setattr(trait, field, holder)

        if dataset.type == 'Publish':
            if trait.group_code:
                trait.display_name = trait.group_code + "_" + str(trait.name)

            trait.confidential = 0
            if trait.pre_publication_description and not trait.pubmed_id:
                trait.confidential = 1

            description = trait.post_publication_description

            # If the dataset is confidential and the user has access to confidential
            # phenotype traits, then display the pre-publication description instead
            # of the post-publication description
            trait.description_display = "N/A"
            if not trait.pubmed_id:
                trait.abbreviation = trait.pre_publication_abbreviation
                if trait.pre_publication_description:
                    trait.description_display = trait.pre_publication_description
            else:
                trait.abbreviation = trait.post_publication_abbreviation
                if description:
                    trait.description_display = description.strip()

            if not trait.year.isdigit():
                trait.pubmed_text = "N/A"
            else:
                trait.pubmed_text = trait.year

            if trait.pubmed_id:
                trait.pubmed_link = webqtlConfig.PUBMEDLINK_URL % trait.pubmed_id

        if dataset.type == 'ProbeSet' and dataset.group:
            description_string = trait.description
            target_string = trait.probe_target_description

            if str(description_string or "") != "" and description_string != 'None':
                description_display = description_string
            else:
                description_display = trait.symbol

            if (str(description_display or "") != ""
                and description_display != 'N/A'
                    and str(target_string or "") != "" and target_string != 'None'):
                description_display = description_display + '; ' + target_string.strip()

            # Save it for the jinja2 template
            trait.description_display = description_display

            trait.location_repr = 'N/A'
            if trait.chr and trait.mb:
                trait.location_repr = 'Chr%s: %.6f' % (
                    trait.chr, float(trait.mb))

        elif dataset.type == "Geno":
            trait.location_repr = 'N/A'
            if trait.chr and trait.mb:
                trait.location_repr = 'Chr%s: %.6f' % (
                    trait.chr, float(trait.mb))

        if get_qtl_info:
            # LRS and its location
            trait.LRS_score_repr = "N/A"
            trait.LRS_location_repr = "N/A"
            trait.locus = trait.locus_chr = trait.locus_mb = trait.lrs = trait.pvalue = trait.additive = ""
            if dataset.type == 'ProbeSet' and not trait.cellid:
                trait.mean = ""
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
            if (dataset.type == 'Publish' or dataset.type == "ProbeSet") and str(trait.locus_chr or "") != "" and str(trait.locus_mb or "") != "":
                trait.LRS_location_repr = LRS_location_repr = 'Chr%s: %.6f' % (
                    trait.locus_chr, float(trait.locus_mb))
                if str(trait.lrs or "") != "":
                    trait.LRS_score_repr = LRS_score_repr = '%3.1f' % trait.lrs
    else:
        raise KeyError(repr(trait.name)
                       + ' information is not found in the database.')
    return trait
