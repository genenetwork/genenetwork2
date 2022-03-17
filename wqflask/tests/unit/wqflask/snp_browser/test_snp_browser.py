import unittest
from unittest import mock
from wqflask import app
from wqflask.snp_browser.snp_browser import get_gene_id
from wqflask.snp_browser.snp_browser import get_gene_id_name_dict
from wqflask.snp_browser.snp_browser import check_if_in_gene
from wqflask.snp_browser.snp_browser import get_browser_sample_lists
from wqflask.snp_browser.snp_browser import get_header_list


class TestSnpBrowser(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_get_header_list(self):
        empty_columns = {"snp_source": "false", "conservation_score": "true", "gene_name": "false",
                         "transcript": "false", "exon": "false", "domain_2": "true", "function": "false", "function_details": "true"}
        strains = {"mouse": ["S1", "S2", "S3", "S4", "S5"], "rat": []}
        expected_results = ([['Index', 'SNP ID', 'Chr', 'Mb', 'Alleles', 'ConScore',
                              'Domain 1', 'Domain 2', 'Details'],
                             ['S1', 'S2', 'S3', 'S4', 'S5']], 5,
                            ['index', 'snp_name', 'chr', 'mb_formatted', 'alleles',
                             'conservation_score', 'domain_1', 'domain_2',
                             'function_details', 'S1', 'S2', 'S3', 'S4', 'S5'])

        results_with_snp = get_header_list(
            variant_type="SNP", strains=strains, species="Mouse", empty_columns=empty_columns)
        results_with_indel = get_header_list(
            variant_type="InDel", strains=strains, species="rat", empty_columns=[])
        expected_results_with_indel = (
            ['Index', 'ID', 'Type', 'InDel Chr', 'Mb Start',
             'Mb End', 'Strand', 'Size', 'Sequence', 'Source'], 0,
            ['index', 'indel_name', 'indel_type', 'indel_chr', 'indel_mb_s',
             'indel_mb_e', 'indel_strand', 'indel_size', 'indel_sequence', 'source_name'])

        self.assertEqual(expected_results, results_with_snp)
        self.assertEqual(expected_results_with_indel, results_with_indel)

    @mock.patch("wqflask.snp_browser.snp_browser.database_connection")
    def test_get_gene_id(self, mock_db):
        db_query_value = ("SELECT geneId FROM GeneList WHERE "
                          "SpeciesId = %s AND geneSymbol = %s")
        conn = mock.MagicMock()
        mock_db.return_value.__enter__.return_value = conn
        with conn.cursor() as cursor:
            cursor.fetchone.return_value = (("517d729f-aa13-4413"
                                             "-a885-40a3f7ff768a"),)

            results = get_gene_id(
                species_id="c9c0f59e-1259-4cba-91e6-831ef1a99c83",
                gene_name="INSR")
            cursor.execute.assert_called_once_with(
                db_query_value,
                ("c9c0f59e-1259-4cba-91e6-831ef1a99c83",
                 "INSR"))
            self.assertEqual(results,
                             "517d729f-aa13-4413-a885-40a3f7ff768a")

    @mock.patch("wqflask.snp_browser.snp_browser.database_connection")
    def test_gene_id_name_dict(self, mock_db):
        no_gene_names = []
        conn = mock.MagicMock()
        mock_db.return_value.__enter__.return_value = conn
        with conn.cursor() as cursor:
            cursor.fetchall.side_effect = [
                [],
                [("fsdf43-fseferger-f22", "GH1"),
                 ("1sdf43-fsewferger-f22", "GH2"),
                 ("fwdj43-fstferger-f22", "GH3")]]
            self.assertEqual("", get_gene_id_name_dict(
                species_id="fregb343bui43g4",
                gene_name_list=no_gene_names))
            gene_name_list = ["GH1", "GH2", "GH3"]
            no_results = get_gene_id_name_dict(
                species_id="ret3-32rf32", gene_name_list=gene_name_list)
            results_found = get_gene_id_name_dict(
                species_id="ret3-32rf32", gene_name_list=gene_name_list)
            expected_found = {'GH1': 'fsdf43-fseferger-f22',
                              'GH2': '1sdf43-fsewferger-f22',
                              'GH3': 'fwdj43-fstferger-f22'}
            db_query_value = (
                "SELECT geneId, geneSymbol FROM GeneList WHERE "
                "SpeciesId = %s AND geneSymbol in (%s, %s, %s)")
            cursor.execute.assert_called_with(
                db_query_value, ("ret3-32rf32", "GH1", "GH2", "GH3"))
            self.assertEqual(results_found, expected_found)
            self.assertEqual(no_results, {})

    @mock.patch("wqflask.snp_browser.snp_browser.database_connection")
    def test_check_if_in_gene(self, mock_db):
        conn = mock.MagicMock()
        mock_db.return_value.__enter__.return_value = conn
        with conn.cursor() as cursor:
            cursor.fetchone.side_effect = [
                ("fsdf-232sdf-sdf", "GHA"), ""]
            results_found = check_if_in_gene(
                species_id="517d729f-aa13-4413-a885-40a3f7ff768a",
                chr_="CH1", mb=12.09)
            self.assertEqual(results_found, ["fsdf-232sdf-sdf", "GHA"])
            db_query_value = (
                "SELECT geneId, geneSymbol FROM GeneList "
                "WHERE SpeciesId = %s AND chromosome = %s "
                "AND (txStart < %s AND txEnd > %s)")
            gene_not_found = check_if_in_gene(
                species_id="517d729f-aa13-4413-a885-40a3f7ff768a",
                chr_="CH1", mb=12.09)
            cursor.execute.assert_has_calls(
                [mock.call(db_query_value,
                           ("517d729f-aa13-4413-a885-40a3f7ff768a",
                            "CH1", 12.09, 12.09)),
                 mock.call(db_query_value,
                           ("517d729f-aa13-4413-a885-40a3f7ff768a",
                            "CH1", 12.09, 12.09))])
            self.assertEqual(gene_not_found, "")

    @mock.patch("wqflask.snp_browser.snp_browser.database_connection")
    def test_get_browser_sample_lists(self, mock_db):
        conn = mock.MagicMock()
        mock_db.return_value.__enter__.return_value = conn
        with conn.cursor() as cursor:
            cursor.execute.return_value.fetchall.return_value = []
            results = get_browser_sample_lists(species_id="12")
            self.assertEqual(results, {'mouse': [], 'rat': []})
