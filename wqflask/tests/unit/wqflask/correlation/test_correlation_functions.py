"""module contains tests for correlation functions"""

import unittest
from unittest import mock

from wqflask.correlation.correlation_functions import get_trait_symbol_and_tissue_values
from wqflask.correlation.correlation_functions import cal_zero_order_corr_for_tiss


class TestCorrelationFunctions(unittest.TestCase):
    """test for correlation helper functions"""

    @mock.patch("wqflask.correlation.correlation_functions.compute_corr_coeff_p_value")
    def test_tissue_corr_computation(self, mock_tiss_corr_computation):
        """test for cal_zero_order_corr_for_tiss"""

        primary_values = [9.288, 9.313, 8.988, 9.660, 8.21]
        target_values = [9.586, 8.498, 9.362, 8.820, 8.786]

        mock_tiss_corr_computation.return_value = (0.51, 0.7)

        results = cal_zero_order_corr_for_tiss(primary_values, target_values)
        mock_tiss_corr_computation.assert_called_once_with(
            primary_values=primary_values, target_values=target_values,
            corr_method="pearson")

        self.assertEqual(len(results), 3)

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
