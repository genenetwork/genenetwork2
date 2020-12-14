import unittest
from unittest import mock
from wqflask import app
from collections import OrderedDict
from wqflask.api.correlation import init_corr_params
from wqflask.api.correlation import convert_to_mouse_gene_id
from wqflask.api.correlation import do_literature_correlation_for_all_traits
from wqflask.api.correlation import get_sample_r_and_p_values
from wqflask.api.correlation import calculate_results


class AttributeSetter:
    def __init__(self, obj):
        for k, v in obj.items():
            setattr(self, k, v)


class MockDataset(AttributeSetter):
    def get_trait_data(self):
        return None

    def retrieve_genes(self, id=None):
        return {
            "TT-1": "GH-1",
            "TT-2": "GH-2",
            "TT-3": "GH-3"

        }


class TestCorrelations(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_init_corr_params(self):
        start_vars = {
            "return_count": "3",
            "type": "T1",
            "method": "spearman"
        }

        corr_params_results = init_corr_params(start_vars=start_vars)
        expected_results = {
            "return_count": 3,
            "type": "T1",
            "method": "spearman"
        }

        self.assertEqual(corr_params_results, expected_results)

    @mock.patch("wqflask.api.correlation.g")
    def test_convert_to_mouse_gene_id(self, mock_db):

        results = convert_to_mouse_gene_id(species="Other", gene_id="")
        self.assertEqual(results, None)

        rat_species_results = convert_to_mouse_gene_id(
            species="rat", gene_id="GH1")

        mock_db.db.execute.return_value.fetchone.side_effect = [
            AttributeSetter({"mouse": "MG-1"}), AttributeSetter({"mouse": "MG-2"})]

        self.assertEqual(convert_to_mouse_gene_id(
            species="mouse", gene_id="MG-4"), "MG-4")
        self.assertEqual(convert_to_mouse_gene_id(
            species="rat", gene_id="R1"), "MG-1")
        self.assertEqual(convert_to_mouse_gene_id(
            species="human", gene_id="H1"), "MG-2")

    @mock.patch("wqflask.api.correlation.g")
    @mock.patch("wqflask.api.correlation.convert_to_mouse_gene_id")
    def test_do_literature_correlation_for_all_traits(self, mock_convert_to_mouse_geneid, mock_db):
        mock_convert_to_mouse_geneid.side_effect = [
            "MG-1", "MG-2;", "MG-3", "MG-4"]

        trait_geneid_dict = {
            "TT-1": "GH-1",
            "TT-2": "GH-2",
            "TT-3": "GH-3"

        }
        mock_db.db.execute.return_value.fetchone.side_effect = [AttributeSetter(
            {"value": "V1"}), AttributeSetter({"value": "V2"}), AttributeSetter({"value": "V3"})]

        this_trait = AttributeSetter({"geneid": "GH-1"})

        target_dataset = AttributeSetter(
            {"group": AttributeSetter({"species": "rat"})})
        results = do_literature_correlation_for_all_traits(
            this_trait=this_trait, target_dataset=target_dataset, trait_geneid_dict=trait_geneid_dict, corr_params={})

        expected_results = {'TT-1': ['GH-1', 0],
                            'TT-2': ['GH-2', 'V1'], 'TT-3': ['GH-3', 'V2']}
        self.assertEqual(results, expected_results)

    @mock.patch("wqflask.api.correlation.corr_result_helpers.normalize_values")
    def test_get_sample_r_and_p_values(self, mock_normalize):

        group = AttributeSetter(
            {"samplelist": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]})
        target_dataset = AttributeSetter({"group": group})

        target_vals = [3.4, 6.2, 4.1, 3.4, 1.2, 5.6]
        trait_data = {"S1": AttributeSetter({"value": 2.3}), "S2": AttributeSetter({"value": 1.1}), 
        "S3": AttributeSetter(
            {"value": 6.3}), "S4": AttributeSetter({"value": 3.6}), "S5": AttributeSetter({"value": 4.1}), 
        "S6": AttributeSetter({"value": 5.0})}
        this_trait = AttributeSetter({"data": trait_data})
        mock_normalize.return_value = ([2.3, 1.1, 6.3, 3.6, 4.1, 5.0],
                                       [3.4, 6.2, 4.1, 3.4, 1.2, 5.6], 6)
        mock_normalize.side_effect = [([2.3, 1.1, 6.3, 3.6, 4.1, 5.0],
                                       [3.4, 6.2, 4.1, 3.4, 1.2, 5.6], 6),
                                      ([2.3, 1.1, 6.3, 3.6, 4.1, 5.0],
                                       [3.4, 6.2, 4.1, 3.4, 1.2, 5.6], 6),
                                      ([2.3, 1.1, 1.4], [3.4, 6.2, 4.1], 3)]

        results_pearsonr = get_sample_r_and_p_values(this_trait=this_trait, this_dataset={
        }, target_vals=target_vals, target_dataset=target_dataset, type="pearson")
        results_spearmanr = get_sample_r_and_p_values(this_trait=this_trait, this_dataset={
        }, target_vals=target_vals, target_dataset=target_dataset, type="spearman")
        results_num_overlap = get_sample_r_and_p_values(this_trait=this_trait, this_dataset={
        }, target_vals=target_vals, target_dataset=target_dataset, type="pearson")
        expected_pearsonr = [-0.21618688834430866, 0.680771605997119, 6]
        expected_spearmanr = [-0.11595420713048969, 0.826848213385815, 6]
        for i, val in enumerate(expected_pearsonr):
            self.assertAlmostEqual(val, results_pearsonr[i],4)
        for i, val in enumerate(expected_spearmanr):
            self.assertAlmostEqual(val, results_spearmanr[i],4)
        self.assertEqual(results_num_overlap, None)

    @mock.patch("wqflask.api.correlation.do_literature_correlation_for_all_traits")
    def test_calculate_results(self, literature_correlation):

        literature_correlation.return_value = {
            'TT-1': ['GH-1', 0], 'TT-2': ['GH-2', 3], 'TT-3': ['GH-3', 1]}

        this_dataset = MockDataset(
            {"group": AttributeSetter({"species": "rat"})})
        target_dataset = MockDataset(
            {"group": AttributeSetter({"species": "rat"})})
        this_trait = AttributeSetter({"geneid": "GH-1"})
        corr_params = {"type": "literature"}
        sorted_results = calculate_results(
            this_trait=this_trait, this_dataset=this_dataset, target_dataset=target_dataset, corr_params=corr_params)
        expected_results = {'TT-2': ['GH-2', 3],
                            'TT-3': ['GH-3', 1], 'TT-1': ['GH-1', 0]}

        self.assertTrue(isinstance(sorted_results, OrderedDict))
        self.assertEqual(dict(sorted_results), expected_results)
