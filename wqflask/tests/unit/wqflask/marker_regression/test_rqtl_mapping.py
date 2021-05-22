import unittest
from unittest import mock
from wqflask.marker_regression.rqtl_mapping import run_rqtl

class AttributeSetter:
    def __init__(self, obj):
        for key, val in obj.items():
            setattr(self, key, val)

class MockGroup(AttributeSetter):
    def get_samplelist(self):
        return None

class TestRqtlMapping(unittest.TestCase):

    @mock.patch("wqflask.marker_regression.rqtl_mapping.process_rqtl_results")
    @mock.patch("wqflask.marker_regression.rqtl_mapping.process_perm_results")
    @mock.patch("wqflask.marker_regression.rqtl_mapping.requests.post")
    @mock.patch("wqflask.marker_regression.rqtl_mapping.locate")
    @mock.patch("wqflask.marker_regression.rqtl_mapping.write_phenotype_file")
    def test_run_rqtl_with_perm(self, mock_write_pheno_file, mock_locate, mock_post, mock_process_perm, mock_process_rqtl):
        """Test for run_rqtl with permutations > 0"""
        dataset_group = MockGroup(
            {"name": "GP1", "genofile": "file_geno"})

        dataset = AttributeSetter({"group": dataset_group})

        mock_write_pheno_file.return_value = "pheno_filename"
        mock_locate.return_value = "geno_filename"

        mock_post.return_value = "output_filename"

        mock_process_perm.return_value = [[], 3, 4]
        mock_process_rqtl.return_value = []

        results = run_rqtl(trait_name="the_trait", vals=[], samples=[],
        dataset=dataset, mapping_scale="cM", model="normal", method="hk",
        num_perm=5, perm_strata_list=[], do_control="false", control_marker="",
        manhattan_plot=True, cofactors="")

        mock_write_pheno_file.assert_called_once()
        mock_locate.assert_called_once()
        mock_post.assert_called_once()
        mock_process_perm.assert_called_once()
        mock_process_rqtl.assert_called_once()
        self.assertEqual(results, ([], 3, 4, []))