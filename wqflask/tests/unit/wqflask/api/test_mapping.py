import unittest
from unittest import mock
from wqflask.api.mapping import initialize_parameters
from wqflask.api.mapping import do_mapping_for_api


class AttributeSetter:
    def __init__(self, obj):
        for key, value in obj.items():
            setattr(self, key, value)


class MockGroup(AttributeSetter):
    def get_marker(self):
        self.markers = []


class TestMapping(unittest.TestCase):

    def test_initialize_parameters(self):
        expected_results = {
            "format": "json",
            "limit_to": False,
            "mapping_method": "gemma",
            "maf": 0.01,
            "use_loco": True,
            "num_perm": 0,
            "perm_check": False
        }

        results = initialize_parameters(
            start_vars={}, dataset={}, this_trait={})
        self.assertEqual(results, expected_results)

        start_vars = {
            "format": "F1",
            "limit_to": "1",
            "mapping_method": "rqtl",
            "control_marker": True,
            "pair_scan": "true",
            "interval_mapping": "true",
            "use_loco": "true",
            "num_perm": "14"

        }

        results_2 = initialize_parameters(
            start_vars=start_vars, dataset={}, this_trait={})
        expected_results = {
            "format": "F1",
            "limit_to": 1,
            "mapping_method": "gemma",
            "maf": 0.01,
            "use_loco": True,
            "num_perm": 14,
            "perm_check": "ON"
        }

        self.assertEqual(results_2, expected_results)

    @mock.patch("wqflask.api.mapping.rqtl_mapping.run_rqtl")
    @mock.patch("wqflask.api.mapping.gemma_mapping.run_gemma")
    @mock.patch("wqflask.api.mapping.initialize_parameters")
    @mock.patch("wqflask.api.mapping.retrieve_sample_data")
    @mock.patch("wqflask.api.mapping.create_trait")
    @mock.patch("wqflask.api.mapping.data_set.create_dataset")
    def test_do_mapping_for_api(self, mock_create_dataset, mock_trait, mock_retrieve_sample, mock_param, run_gemma, run_rqtl_geno):
        start_vars = {
            "db": "Temp",
            "trait_id": "dewf3232rff2",
            "format": "F1",
            "mapping_method": "gemma",
            "use_loco": True

        }
        sampleList = ["S1", "S2", "S3", "S4"]
        samplelist = ["S1", "S2", "S4"]
        dataset = AttributeSetter({"group": samplelist})
        this_trait = AttributeSetter({})
        trait_data = AttributeSetter({
            "data": {
                "item1": AttributeSetter({"name": "S1", "value": "S1_value"}),
                "item2": AttributeSetter({"name": "S2", "value": "S2_value"}),
                "item3": AttributeSetter({"name": "S3", "value": "S3_value"}),

            }
        })
        trait = AttributeSetter({
            "data": trait_data
        })

        dataset.return_value = dataset
        mock_trait.return_value = this_trait

        mock_retrieve_sample.return_value = trait
        mock_param.return_value = {
            "format": "F1",
            "limit_to": False,
            "mapping_method": "gemma",
            "maf": 0.01,
            "use_loco": "True",
            "num_perm": 14,
            "perm_check": "ON"
        }

        run_gemma.return_value = ["results"]
        results = do_mapping_for_api(start_vars=start_vars)
        self.assertEqual(results, ("results", None))
