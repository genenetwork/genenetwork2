import urllib.request
import urllib.error
import urllib.parse
import re

from MySQLdb.cursors import DictCursor
from wqflask.database import database_connection
from utility.tools import get_setting


class InfoPage:
    def __init__(self, start_vars):
        self.info = None
        self.gn_accession_id = None
        if 'gn_accession_id' in start_vars:
            self.gn_accession_id = start_vars['gn_accession_id']
        self.info_page_name = start_vars['info_page_name']

        self.get_info()
        self.get_datasets_list()

    def get_info(self, create=False):
        query_base = (
            "SELECT InfoPageName AS info_page_name, "
            "GN_AccesionId AS accession_id, "
            "Species.MenuName AS menu_name, "
            "Species.TaxonomyId AS taxonomy_id, "
            "Tissue.Name AS tissue_name, "
            "InbredSet.Name AS group_name, "
            "GeneChip.GeneChipName AS gene_chip_name, "
            "GeneChip.GeoPlatform AS geo_platform, "
            "AvgMethod.Name AS avg_method_name, "
            "Datasets.DatasetName AS dataset_name, "
            "Datasets.GeoSeries AS geo_series, "
            "Datasets.PublicationTitle AS publication_title, "
            "DatasetStatus.DatasetStatusName AS dataset_status_name, "
            "Datasets.Summary AS dataset_summary, "
            "Datasets.AboutCases AS about_cases, "
            "Datasets.AboutTissue AS about_tissue, "
            "Datasets.AboutDataProcessing AS about_data_processing, "
            "Datasets.Acknowledgment AS acknowledgement, "
            "Datasets.ExperimentDesign AS experiment_design, "
            "Datasets.Contributors AS contributors, "
            "Datasets.Citation AS citation, "
            "Datasets.Notes AS notes, "
            "Investigators.FirstName AS investigator_firstname, "
            "Investigators.LastName AS investigator_lastname, "
            "Investigators.Address AS investigator_address, "
            "Investigators.City AS investigator_city, "
            "Investigators.State AS investigator_state, "
            "Investigators.ZipCode AS investigator_zipcode, "
            "Investigators.Country AS investigator_country, "
            "Investigators.Phone AS investigator_phone, "
            "Investigators.Email AS investigator_email, "
            "Investigators.Url AS investigator_url, "
            "Organizations.OrganizationName AS organization_name, "
            "InvestigatorId AS investigator_id, "
            "DatasetId AS dataset_id, "
            "DatasetStatusId AS dataset_status_id, "
            "Datasets.AboutPlatform AS about_platform, "
            "InfoFileTitle AS info_file_title, "
            "Specifics AS specifics"
            "FROM InfoFiles "
            "LEFT JOIN Species USING (SpeciesId) "
            "LEFT JOIN Tissue USING (TissueId) "
            "LEFT JOIN InbredSet USING (InbredSetId) "
            "LEFT JOIN GeneChip USING (GeneChipId) "
            "LEFT JOIN AvgMethod USING (AvgMethodId) "
            "LEFT JOIN Datasets USING (DatasetId) "
            "LEFT JOIN Investigators USING (InvestigatorId) "
            "LEFT JOIN Organizations USING (OrganizationId) "
            "LEFT JOIN DatasetStatus USING (DatasetStatusId) WHERE "
        )
        if not all([self.gn_accession_id, self.info_page_name]):
            raise ValueError('No correct parameter found')

        results = {}
        with database_connection(get_setting("SQL_URI")) as conn, conn.cursor(DictCursor) as cursor:
            if self.gn_accession_id:
                cursor.execute(f"{query_base}GN_AccesionId = %s",
                               (self.gn_accession_id,))
            elif self.info_page_name:
                cursor.execute(f"{query_base}InfoPageName = %s",
                               (self.info_page_name,))
            if (results := cursor.fetchone()):
                self.info = results
        if ((not results or len(results) < 1)
            and self.info_page_name and create):
            return self.get_info()
        if not self.gn_accession_id and self.info:
            self.gn_accession_id = self.info['accession_id']
        if not self.info_page_name and self.info:
            self.info_page_name = self.info['info_page_name']

    def get_datasets_list(self):
        self.filelist = []
        try:
            response = urllib.request.urlopen(
                "https://files.genenetwork.org/current/GN%s" % self.gn_accession_id)
            data = response.read()

            matches = re.findall(r"<tr>.+?</tr>", data, re.DOTALL)
            for i, match in enumerate(matches):
                if i == 0:
                    continue
                cells = re.findall(r"<td.+?>.+?</td>", match, re.DOTALL)
                full_filename = re.search(
                    r"<a href=\"(.+?)\"", cells[1], re.DOTALL).group(1).strip()
                filename = full_filename.split("/")[-1]
                filesize = re.search(r">(.+?)<", cells[2]).group(1).strip()
                filedate = "N/A"  # ZS: Since we can't get it for now

                self.filelist.append([filename, filedate, filesize])
        except Exception as e:
            pass
