"MrnaAssayDataSet class ..."

import codecs


from .dataset import DataSet
from .utils import geno_mrna_confidentiality
from gn2.wqflask.database import database_connection
from gn2.utility.tools import get_setting

class MrnaAssayDataSet(DataSet):
    '''
    An mRNA Assay is a quantitative assessment (assay) associated with an mRNA trait

    This used to be called ProbeSet, but that term only refers specifically to the Affymetrix
    platform and is far too specific.

    '''

    def setup(self):
        # Fields in the database table
        self.search_fields = ['Name',
                              'Description',
                              'Probe_Target_Description',
                              'Symbol',
                              'Alias',
                              'GenbankId',
                              'UniGeneId',
                              'RefSeq_TranscriptId']

        # Find out what display_fields is
        self.display_fields = ['name', 'symbol',
                               'description', 'probe_target_description',
                               'chr', 'mb',
                               'alias', 'geneid',
                               'genbankid', 'unigeneid',
                               'omim', 'refseq_transcriptid',
                               'blatseq', 'targetseq',
                               'chipid', 'comments',
                               'strand_probe', 'strand_gene',
                               'proteinid', 'uniprotid',
                               'probe_set_target_region',
                               'probe_set_specificity',
                               'probe_set_blat_score',
                               'probe_set_blat_mb_start',
                               'probe_set_blat_mb_end',
                               'probe_set_strand',
                               'probe_set_note_by_rw',
                               'flag']

        # Fields displayed in the search results table header
        self.header_fields = ['Index',
                              'Record',
                              'Symbol',
                              'Description',
                              'Location',
                              'Mean',
                              'Max LRS',
                              'Max LRS Location',
                              'Additive Effect']

        # Todo: Obsolete or rename this field
        self.type = 'ProbeSet'
        self.query_for_group = """
SELECT InbredSet.Name, InbredSet.Id, InbredSet.GeneticType, InbredSet.InbredSetCode
FROM InbredSet, ProbeSetFreeze, ProbeFreeze WHERE ProbeFreeze.InbredSetId = InbredSet.Id AND
ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId AND ProbeSetFreeze.Name = %s"""

    def check_confidentiality(self):
        return geno_mrna_confidentiality(self)

    def get_trait_info(self, trait_list=None, species=''):

        #  Note: setting trait_list to [] is probably not a great idea.
        if not trait_list:
            trait_list = []
        with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
            for this_trait in trait_list:

                if not this_trait.haveinfo:
                    this_trait.retrieveInfo(QTL=1)

                if not this_trait.symbol:
                    this_trait.symbol = "N/A"

                # XZ, 12/08/2008: description
                # XZ, 06/05/2009: Rob asked to add probe target description
                description_string = str(
                    str(this_trait.description).strip(codecs.BOM_UTF8), 'utf-8')
                target_string = str(
                    str(this_trait.probe_target_description).strip(codecs.BOM_UTF8), 'utf-8')

                if len(description_string) > 1 and description_string != 'None':
                    description_display = description_string
                else:
                    description_display = this_trait.symbol

                if (len(description_display) > 1 and description_display != 'N/A'
                        and len(target_string) > 1 and target_string != 'None'):
                    description_display = description_display + '; ' + target_string.strip()

                # Save it for the jinja2 template
                this_trait.description_display = description_display

                if this_trait.chr and this_trait.mb:
                    this_trait.location_repr = 'Chr%s: %.6f' % (
                        this_trait.chr, float(this_trait.mb))

                # Get mean expression value
                cursor.execute(
                    "SELECT ProbeSetXRef.mean FROM "
                    "ProbeSetXRef, ProbeSet WHERE "
                    "ProbeSetXRef.ProbeSetFreezeId = %s "
                    "AND ProbeSet.Id = ProbeSetXRef.ProbeSetId "
                    "AND ProbeSet.Name = %s",
                    (str(this_trait.dataset.id), this_trait.name,)
                )
                result = cursor.fetchone()

                mean = result[0] if result else 0

                if mean:
                    this_trait.mean = "%2.3f" % mean

                # LRS and its location
                this_trait.LRS_score_repr = 'N/A'
                this_trait.LRS_location_repr = 'N/A'

                # Max LRS and its Locus location
                if this_trait.lrs and this_trait.locus:
                    cursor.execute(
                        "SELECT Geno.Chr, Geno.Mb FROM "
                        "Geno, Species WHERE "
                        "Species.Name = %s AND "
                        "Geno.Name = %s AND "
                        "Geno.SpeciesId = Species.Id",
                        (species, this_trait.locus,)
                    )
                    if result := cursor.fetchone():
                        lrs_chr, lrs_mb = result
                        this_trait.LRS_score_repr = '%3.1f' % this_trait.lrs
                        this_trait.LRS_location_repr = 'Chr%s: %.6f' % (
                            lrs_chr, float(lrs_mb))

        return trait_list

    def retrieve_sample_data(self, trait):
        with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT Strain.Name, ProbeSetData.value, "
                "ProbeSetSE.error, NStrain.count, "
                "Strain.Name2 FROM (ProbeSetData, "
                "ProbeSetFreeze, Strain, ProbeSet, "
                "ProbeSetXRef) LEFT JOIN ProbeSetSE ON "
                "(ProbeSetSE.DataId = ProbeSetData.Id AND "
                "ProbeSetSE.StrainId = ProbeSetData.StrainId) "
                "LEFT JOIN NStrain ON "
                "(NStrain.DataId = ProbeSetData.Id AND "
                "NStrain.StrainId = ProbeSetData.StrainId) "
                "WHERE ProbeSet.Name = %s AND "
                "ProbeSetXRef.ProbeSetId = ProbeSet.Id "
                "AND ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id "
                "AND ProbeSetFreeze.Name = %s AND "
                "ProbeSetXRef.DataId = ProbeSetData.Id "
                "AND ProbeSetData.StrainId = Strain.Id "
                "ORDER BY Strain.Name",
                (trait, self.name,)
            )
            return cursor.fetchall()

    def retrieve_genes(self, column_name):
        with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
            cursor.execute(
                f"SELECT ProbeSet.Name, ProbeSet.{column_name} "
                "FROM ProbeSet,ProbeSetXRef WHERE "
                "ProbeSetXRef.ProbeSetFreezeId = %s "
                "AND ProbeSetXRef.ProbeSetId=ProbeSet.Id",
                (str(self.id),))
            return dict(cursor.fetchall())
