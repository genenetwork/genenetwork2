
"""module contains for processing gn3 wgcna data"""
from unittest import TestCase

from gn2.wqflask.wgcna.gn3_wgcna import process_wgcna_data


class DataProcessingTests(TestCase):
    """class contains data processing tests"""

    def test_data_processing(self):
        """test for parsing data for datatable"""
        output = {
            "input": {
                "sample_names": ["BXD1", "BXD2", "BXD3", "BXD4", "BXD5", "BXD6"],

            },
            "output": {
                "ModEigens": {
                    "MEturquoise": [
                        0.0646677768085351,
                        0.137200224277058,
                        0.63451113720732,
                        -0.544002665501479,
                        -0.489487590361863,
                        0.197111117570427
                    ],
                    "MEgrey": [
                        0.213,
                        0.214,
                        0.3141,
                        -0.545,
                        -0.423,
                        0.156,
                    ]
                }}}

        row_data = [['BXD1', 0.065, 0.213],
                    ['BXD2', 0.137, 0.214],
                    ['BXD3', 0.635, 0.314],
                    ['BXD4', -0.544, -0.545],
                    ['BXD5', -0.489, -0.423],
                    ['BXD6', 0.197, 0.156]]

        expected_results = {
            "col_names": ["sample_names", "MEturquoise", "MEgrey"],
            "mod_dataset": row_data
        }

        self.assertEqual(process_wgcna_data(output), expected_results)
