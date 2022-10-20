import unittest
from unittest import mock
from wqflask.correlation.show_corr_results import get_header_fields


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
