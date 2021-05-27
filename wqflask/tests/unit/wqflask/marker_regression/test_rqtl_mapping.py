import unittest
from unittest import mock
from dataclasses import dataclass

from wqflask.marker_regression.rqtl_mapping import run_rqtl

@dataclass
class MockGroup:
    name: str
    genofile: str

@dataclass
class MockDataset:
    group: MockGroup

class TestRqtlMapping(unittest.TestCase):
    """Tests for functions in rqtl_mapping.py"""
    @mock.patch("wqflask.marker_regression.rqtl_mapping.requests.post")
    @mock.patch("wqflask.marker_regression.rqtl_mapping.locate")
    @mock.patch("wqflask.marker_regression.rqtl_mapping.write_phenotype_file")
    def test_run_rqtl_with_perm(self, mock_write_pheno_file, mock_locate, mock_post):
        """Test for run_rqtl with permutations > 0"""
        dataset_group = MockGroup("GP1", "file_geno")
        dataset = MockDataset(dataset_group)

        mock_write_pheno_file.return_value = "pheno_filename"
        mock_locate.return_value = "geno_filename"
        mock_post.return_value = mock.Mock(ok=True)
        mock_post.return_value.json.return_value = {"perm_results": [],
                                                    "suggestive": 3,
                                                    "significant": 4,
                                                    "results" : []}

        results = run_rqtl(trait_name="the_trait", vals=[], samples=[],
        dataset=dataset, mapping_scale="cM", model="normal", method="hk",
        num_perm=5, perm_strata_list=[], do_control="false", control_marker="",
        manhattan_plot=True, cofactors="")

        mock_write_pheno_file.assert_called_once()
        mock_locate.assert_called_once()
        mock_post.assert_called_once()

        self.assertEqual(results, ([], 3, 4, []))
