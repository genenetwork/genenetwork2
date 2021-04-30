import http.client
import urllib.request
import urllib.error
import urllib.parse
import re

from flask import Flask, g

from utility.logger import getLogger
logger = getLogger(__name__)


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
        query_base = ("SELECT InfoPageName, GN_AccesionId, Species.MenuName, Species.TaxonomyId, Tissue.Name, InbredSet.Name, " +
                      "GeneChip.GeneChipName, GeneChip.GeoPlatform, AvgMethod.Name, Datasets.DatasetName, Datasets.GeoSeries, " +
                      "Datasets.PublicationTitle, DatasetStatus.DatasetStatusName, Datasets.Summary, Datasets.AboutCases, " +
                      "Datasets.AboutTissue, Datasets.AboutDataProcessing, Datasets.Acknowledgment, Datasets.ExperimentDesign, " +
                      "Datasets.Contributors, Datasets.Citation, Datasets.Notes, Investigators.FirstName, Investigators.LastName, " +
                      "Investigators.Address, Investigators.City, Investigators.State, Investigators.ZipCode, Investigators.Country, " +
                      "Investigators.Phone, Investigators.Email, Investigators.Url, Organizations.OrganizationName, " +
                      "InvestigatorId, DatasetId, DatasetStatusId, Datasets.AboutPlatform, InfoFileTitle, Specifics " +
                      "FROM InfoFiles " +
                      "LEFT JOIN Species USING (SpeciesId) " +
                      "LEFT JOIN Tissue USING (TissueId) " +
                      "LEFT JOIN InbredSet USING (InbredSetId) " +
                      "LEFT JOIN GeneChip USING (GeneChipId) " +
                      "LEFT JOIN AvgMethod USING (AvgMethodId) " +
                      "LEFT JOIN Datasets USING (DatasetId) " +
                      "LEFT JOIN Investigators USING (InvestigatorId) " +
                      "LEFT JOIN Organizations USING (OrganizationId) " +
                      "LEFT JOIN DatasetStatus USING (DatasetStatusId) WHERE ")

        if self.gn_accession_id:
            final_query = query_base + \
                "GN_AccesionId = {}".format(self.gn_accession_id)
            results = g.db.execute(final_query).fetchone()
            if self.info_page_name and not results:
                final_query = query_base + \
                    "InfoPageName={}".format(self.info_page_name)
        elif self.info_page_name:
            final_query = query_base + \
                "InfoPageName={}".format(self.info_page_name)
            results = g.db.execute(final_query).fetchone()
        else:
            raise 'No correct parameter found'

        if results:
            self.info = process_query_results(results)

        if (not results or len(results) < 1) and self.info_page_name and create:
            insert_sql = "INSERT INTO InfoFiles SET InfoFiles.InfoPageName={}".format(
                self.info_page_name)
            return self.get_info()

        if not self.gn_accession_id and self.info:
            self.gn_accession_id = self.info['accession_id']
        if not self.info_page_name and self.info:
            self.info_page_name = self.info['info_page_name']

    def get_datasets_list(self):
        self.filelist = []
        try:
            response = urllib.request.urlopen(
                "http://datafiles.genenetwork.org/download/GN%s" % self.gn_accession_id)
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


def process_query_results(results):
    info_ob = {
        'info_page_name': results[0],
        'accession_id': results[1],
        'menu_name': results[2],
        'taxonomy_id': results[3],
        'tissue_name': results[4],
        'group_name': results[5],
        'gene_chip_name': results[6],
        'geo_platform': results[7],
        'avg_method_name': results[8],
        'dataset_name': results[9],
        'geo_series': results[10],
        'publication_title': results[11],
        'dataset_status_name': results[12],
        'dataset_summary': results[13],
        'about_cases': results[14],
        'about_tissue': results[15],
        'about_data_processing': results[16],
        'acknowledgement': results[17],
        'experiment_design': results[18],
        'contributors': results[19],
        'citation': results[20],
        'notes': results[21],
        'investigator_firstname': results[22],
        'investigator_lastname': results[23],
        'investigator_address': results[24],
        'investigator_city': results[25],
        'investigator_state': results[26],
        'investigator_zipcode': results[27],
        'investigator_country': results[28],
        'investigator_phone': results[29],
        'investigator_email': results[30],
        'investigator_url': results[31],
        'organization_name': results[32],
        'investigator_id': results[33],
        'dataset_id': results[34],
        'dataset_status_is': results[35],
        'about_platform': results[36],
        'info_file_title': results[37],
        'specifics': results[38]
    }

    return info_ob
