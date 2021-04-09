import unittest
from unittest import mock
from wqflask.correlation.show_corr_results import get_header_fields
from wqflask.correlation.show_corr_results import generate_corr_json


class AttributeSetter:
    def __init__(self, trait_obj):
        for key, value in trait_obj.items():
            setattr(self, key, value)


class TestShowCorrResults(unittest.TestCase):
    def test_get_header_fields(self):
        expected = [
            ['Index',
             'Record',
             'Symbol',
             'Description',
             'Location',
             'Mean',
             'Sample rho',
             'N',
             'Sample p(rho)',
             'Lit rho',
             'Tissue rho',
             'Tissue p(rho)',
             'Max LRS',
             'Max LRS Location',
             'Additive Effect'],

            ['Index',
             'ID',
             'Location',
             'Sample r',
             'N',
             'Sample p(r)']

        ]
        result1 = get_header_fields("ProbeSet", "spearman")
        result2 = get_header_fields("Other", "Other")
        self.assertEqual(result1, expected[0])
        self.assertEqual(result2, expected[1])

    @mock.patch("wqflask.correlation.show_corr_results.hmac.data_hmac")
    def test_generate_corr_json(self, mock_data_hmac):
        mock_data_hmac.return_value = "hajsdiau"

        dataset = AttributeSetter({"name": "the_name"})
        this_trait = AttributeSetter(
            {"name": "trait_test", "dataset": dataset})
        target_dataset = AttributeSetter({"type": "Publish"})
        corr_trait_1 = AttributeSetter({
            "name": "trait_1",
            "dataset": AttributeSetter({"name": "dataset_1"}),
            "view": True,
            "abbreviation": "T1",
            "description_display": "Trait I description",
            "authors": "JM J,JYEW",
            "pubmed_id": "34n4nn31hn43",
            "pubmed_text": "2016",
            "pubmed_link": "https://www.load",
            "lod_score": "",
            "mean": "",
            "LRS_location_repr": "BXBS",
            "additive": "",
            "sample_r": 10.5,
            "num_overlap": 2,
            "sample_p": 5




        })
        corr_results = [corr_trait_1]

        dataset_type_other = {
            "location": "cx-3-4",
            "sample_4": 12.32,
            "num_overlap": 3,
            "sample_p": 10.34
        }

        expected_results = '[{"index": 1, "trait_id": "trait_1", "dataset": "dataset_1", "hmac": "hajsdiau", "abbreviation_display": "T1", "description": "Trait I description", "mean": "N/A", "authors_display": "JM J,JYEW", "additive": "N/A", "pubmed_id": "34n4nn31hn43", "year": "2016", "lod_score": "N/A", "lrs_location": "BXBS", "sample_r": "10.500", "num_overlap": 2, "sample_p": "5.000e+00"}]'

        results1 = generate_corr_json(corr_results=corr_results, this_trait=this_trait,
                                      dataset=dataset, target_dataset=target_dataset, for_api=True)
        self.assertEqual(expected_results, results1)

    def test_generate_corr_json_view_false(self):
        trait = AttributeSetter({"view": False})
        corr_results = [trait]
        this_trait = AttributeSetter({"name": "trait_test"})
        dataset = AttributeSetter({"name": "the_name"})

        results_where_view_is_false = generate_corr_json(
            corr_results=corr_results, this_trait=this_trait, dataset={}, target_dataset={}, for_api=False)
        self.assertEqual(results_where_view_is_false, "[]")
