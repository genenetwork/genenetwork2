import unittest
from unittest import mock
from wqflask.correlation.correlation_functions import get_trait_symbol_and_tissue_values
from wqflask.correlation.correlation_functions import cal_zero_order_corr_for_tiss


class TestCorrelationFunctions(unittest.TestCase):
    
    @mock.patch("wqflask.correlation.correlation_functions.MrnaAssayTissueData")
    def test_get_trait_symbol_and_tissue_values(self, mock_class):
        """test for getting trait symbol and tissue_values"""
        mock_class_instance = mock_class.return_value
        mock_class_instance.gene_symbols = ["k1", "k2", "k3"]
        mock_class_instance.get_symbol_values_pairs.return_value = {
            "k1": ["v1", "v2", "v3"], "k2": ["v2", "v3"], "k3": ["k3"]}
        results = get_trait_symbol_and_tissue_values(
            symbol_list=["k1", "k2", "k3"])
        mock_class.assert_called_with(gene_symbols=['k1', 'k2', 'k3'])
        self.assertEqual({"k1": ["v1", "v2", "v3"], "k2": [
                         "v2", "v3"], "k3": ["k3"]}, results)
