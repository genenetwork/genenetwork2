"PhenotypeDataSet class ..."

from .dataset import DataSet
from base import webqtlConfig
from utility.tools import get_setting
from wqflask.database import database_connection

class PhenotypeDataSet(DataSet):

    def setup(self):
        # Fields in the database table
        self.search_fields = ['Phenotype.Post_publication_description',
                              'Phenotype.Pre_publication_description',
                              'Phenotype.Pre_publication_abbreviation',
                              'Phenotype.Post_publication_abbreviation',
                              'PublishXRef.mean',
                              'Phenotype.Lab_code',
                              'Publication.PubMed_ID',
                              'Publication.Abstract',
                              'Publication.Title',
                              'Publication.Authors',
                              'PublishXRef.Id']

        # Figure out what display_fields is
        self.display_fields = ['name', 'group_code',
                               'pubmed_id',
                               'pre_publication_description',
                               'post_publication_description',
                               'original_description',
                               'pre_publication_abbreviation',
                               'post_publication_abbreviation',
                               'mean',
                               'lab_code',
                               'submitter', 'owner',
                               'authorized_users',
                               'authors', 'title',
                               'abstract', 'journal',
                               'volume', 'pages',
                               'month', 'year',
                               'sequence', 'units', 'comments']

        # Fields displayed in the search results table header
        self.header_fields = ['Index',
                              'Record',
                              'Description',
                              'Authors',
                              'Year',
                              'Max LRS',
                              'Max LRS Location',
                              'Additive Effect']

        self.type = 'Publish'
        self.query_for_group = """
SELECT InbredSet.Name, InbredSet.Id, InbredSet.GeneticType, InbredSet.InbredSetCode FROM InbredSet, PublishFreeze WHERE PublishFreeze.InbredSetId = InbredSet.Id AND PublishFreeze.Name = %s"""

    def check_confidentiality(self):
        # (Urgently?) Need to write this
        pass

    def get_trait_info(self, trait_list, species=''):
        for this_trait in trait_list:

            if not this_trait.haveinfo:
                this_trait.retrieve_info(get_qtl_info=True)

            description = this_trait.post_publication_description

            # If the dataset is confidential and the user has access to confidential
            # phenotype traits, then display the pre-publication description instead
            # of the post-publication description
            if this_trait.confidential:
                this_trait.description_display = ""
                continue   # for now, because no authorization features

                if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(
                        privilege=self.privilege,
                        userName=self.userName,
                        authorized_users=this_trait.authorized_users):

                    description = this_trait.pre_publication_description

            if len(description) > 0:
                this_trait.description_display = description.strip()
            else:
                this_trait.description_display = ""

            if not this_trait.year.isdigit():
                this_trait.pubmed_text = "N/A"
            else:
                this_trait.pubmed_text = this_trait.year

            if this_trait.pubmed_id:
                this_trait.pubmed_link = webqtlConfig.PUBMEDLINK_URL % this_trait.pubmed_id

            # LRS and its location
            this_trait.LRS_score_repr = "N/A"
            this_trait.LRS_location_repr = "N/A"

            if this_trait.lrs:
                with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT Geno.Chr, Geno.Mb FROM "
                        "Geno, Species WHERE "
                        "Species.Name = %s AND "
                        "Geno.Name = %s AND "
                        "Geno.SpeciesId = Species.Id",
                        (species, this_trait.locus,)
                    )
                    if result := cursor.fetchone():
                        if result[0] and result[1]:
                            LRS_Chr, LRS_Mb = result[0], result[1]
                            this_trait.LRS_score_repr = LRS_score_repr = '%3.1f' % this_trait.lrs
                            this_trait.LRS_location_repr = LRS_location_repr = 'Chr%s: %.6f' % (
                                LRS_Chr, float(LRS_Mb))

    def retrieve_sample_data(self, trait):
        with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
            cursor.execute(
            "SELECT Strain.Name, PublishData.value, "
                "PublishSE.error, NStrain.count, "
                "Strain.Name2 FROM (PublishData, Strain, "
                "PublishXRef, PublishFreeze) LEFT JOIN "
                "PublishSE ON "
                "(PublishSE.DataId = PublishData.Id "
                "AND PublishSE.StrainId = PublishData.StrainId) "
                "LEFT JOIN NStrain ON "
                "(NStrain.DataId = PublishData.Id AND "
                "NStrain.StrainId = PublishData.StrainId) "
                "WHERE PublishXRef.InbredSetId = PublishFreeze.InbredSetId "
                "AND PublishData.Id = PublishXRef.DataId AND "
                "PublishXRef.Id = %s AND PublishFreeze.Id = %s "
                "AND PublishData.StrainId = Strain.Id "
                "ORDER BY Strain.Name", (trait, self.id))
            return cursor.fetchall()
