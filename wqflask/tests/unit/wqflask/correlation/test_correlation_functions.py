"""module contains tests for correlation functions"""

import unittest
from unittest import mock

from wqflask.correlation.correlation_functions import get_trait_symbol_and_tissue_values
from wqflask.correlation.correlation_functions import cal_zero_order_corr_for_tiss


def test_tissue_corr_computation(mocker):
    """Test for cal_zero_order_corr_for_tiss"""
    primary_values = [9.288, 9.313, 8.988, 9.660, 8.21]
    target_values = [9.586, 8.498, 9.362, 8.820, 8.786]
    _m = mocker.patch(("wqflask.correlation.correlation_functions."
                       "compute_corr_coeff_p_value"),
                      return_value=(0.51, 0.7))
    results = cal_zero_order_corr_for_tiss(primary_values, target_values)
    _m.assert_called_once_with(
        primary_values=primary_values, target_values=target_values,
        corr_method="pearson")
    assert len(results) == 3
