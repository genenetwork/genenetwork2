"GenotypeDataSet class ..."

from .dataset import DataSet
from utility import webqtlUtil
from db import webqtlDatabaseFunction
from .utils import geno_mrna_confidentiality
from wqflask.database import database_connection

class GenotypeDataSet(DataSet):

    def setup(self):
        # Fields in the database table
        self.search_fields = ['Name',
                              'Chr']

        # Find out what display_fields is
        self.display_fields = ['name',
                               'chr',
                               'mb',
                               'source2',
                               'sequence']

        # Fields displayed in the search results table header
        self.header_fields = ['Index',
                              'ID',
                              'Location']

        # Todo: Obsolete or rename this field
        self.type = 'Geno'
        self.query_for_group = """
SELECT InbredSet.Name, InbredSet.Id, InbredSet.GeneticType, InbredSet.InbredSetCode
FROM InbredSet, GenoFreeze WHERE GenoFreeze.InbredSetId = InbredSet.Id AND
GenoFreeze.Name = %s"""

    def check_confidentiality(self):
        return geno_mrna_confidentiality(self)

    def get_trait_info(self, trait_list, species=None):
        for this_trait in trait_list:
            if not this_trait.haveinfo:
                this_trait.retrieveInfo()

            if this_trait.chr and this_trait.mb:
                this_trait.location_repr = 'Chr%s: %.6f' % (
                    this_trait.chr, float(this_trait.mb))

    def retrieve_sample_data(self, trait):
        results = []
        with database_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT Strain.Name, GenoData.value, "
                "GenoSE.error, 'N/A', Strain.Name2 "
                "FROM (GenoData, GenoFreeze, Strain, Geno, "
                "GenoXRef) LEFT JOIN GenoSE ON "
                "(GenoSE.DataId = GenoData.Id AND "
                "GenoSE.StrainId = GenoData.StrainId) "
                "WHERE Geno.SpeciesId = %s AND "
                "Geno.Name = %s AND GenoXRef.GenoId = Geno.Id "
                "AND GenoXRef.GenoFreezeId = GenoFreeze.Id "
                "AND GenoFreeze.Name = %s AND "
                "GenoXRef.DataId = GenoData.Id "
                "AND GenoData.StrainId = Strain.Id "
                "ORDER BY Strain.Name",
                (webqtlDatabaseFunction.retrieve_species_id(self.group.name),
                 trait, self.name,))
            results = list(cursor.fetchall())

        if self.group.name in webqtlUtil.ParInfo:
            f1_1, f1_2, ref, nonref = webqtlUtil.ParInfo[self.group.name]
            results.append([f1_1, 0, None, "N/A", f1_1])
            results.append([f1_2, 0, None, "N/A", f1_2])
            results.append([ref, -1, None, "N/A", ref])
            results.append([nonref, 1, None, "N/A", nonref])

        return results
