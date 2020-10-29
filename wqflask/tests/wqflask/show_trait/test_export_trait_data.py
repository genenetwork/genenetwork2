import unittest
from unittest import mock
from wqflask.show_trait.export_trait_data import dict_to_sorted_list
from wqflask.show_trait.export_trait_data import cmp_samples
from wqflask.show_trait.export_trait_data import export_sample_table

class TestExportTraits(unittest.TestCase):
    """Test methods related to converting dict to sortedlist"""
    @mock.patch("wqflask.show_trait.export_trait_data.dict_to_sorted_list")
    @mock.patch("wqflask.show_trait.export_trait_data.get_export_metadata")
    def test_export_sample_table(self, exp_metadata, dict_list):
        """test for  exporting sample table"""
        targs_obj = {
            "export_data": """{
                "primary_samples": [
                    {
                        "other": "germanotta",
                        "name": "Sauroniops"
                    }
                ],
                "other_samples": [
                    {
                        "se": 1,
                        "num_cases": 4,
                        "value": 6,
                        "name": 3
                    }
                ]
            }""",
            "trait_display_name": "Hair_color",
            "trait_id": "23177fdc-312e-4084-ad0c-f3eae785fff5",
            "dataset": {
            }
        }
        exp_metadata.return_value = [["Phenotype ID:0a2be192-57f5-400b-bbbd-0cf50135995f"], ['Group:gp1'], ["Phenotype:p1"], [
            "Authors:N/A"], ["Title:research1"], ["Journal:N/A"], ["Dataset Link: http://gn1.genenetwork.org/webqtl/main.py?FormID=sharinginfo&InfoPageName=name1"], []]
        expected = ('Hair_color',
                    [['Phenotype ID:0a2be192-57f5-400b-bbbd-0cf50135995f'],
                     ['Group:gp1'],
                     ['Phenotype:p1'],
                     ['Authors:N/A'],
                     ['Title:research1'],
                     ['Journal:N/A'],
                     ['Dataset Link: '
                      'http://gn1.genenetwork.org/webqtl/main.py?FormID=sharinginfo&InfoPageName=name1'],
                     [],
                     ['Sauroniops', 'germanotta'],
                     [3, 6, 1, 4]])

        dict_list.side_effect = [['Sauroniops', 'germanotta'], [3, 6, 1, 4]]

        self.assertEqual(export_sample_table(targs_obj), expected)
        exp_metadata.assert_called_with("23177fdc-312e-4084-ad0c-f3eae785fff5", {})
        self.assertEqual(dict_list.call_count, 2)

    def test_dict_to_sortedlist(self):
        """test for conversion of dict to sorted list"""
        sample1 = {
            "other": "exp1",
            "name": "exp2"
        }
        sample2 = {
            "se": 1,
            "num_cases": 4,
            "value": 6,
            "name": 3

        }
        rever = {
            "name": 3,
            "value": 6,
            "num_cases": 4,
            "se": 1
        }
        oneItem = {
            "item1": "one"
        }

        self.assertEqual(["exp2", "exp1"], dict_to_sorted_list(sample1))
        self.assertEqual([3, 6, 1, 4], dict_to_sorted_list(sample2))
        self.assertEqual([3, 6, 1, 4], dict_to_sorted_list(rever))
        self.assertEqual(["one"], dict_to_sorted_list(oneItem))
        """test that the func returns the values not the keys"""
        self.assertFalse(["other", "name"] == dict_to_sorted_list(sample1))

    def test_cmp_samples(self):
        """test for comparing samples function"""
        sampleA = [
            [
                ("value", "other"),
                ("name", "test_name")
            ]
        ]
        sampleB = [
            [
                ("value", "other"),
                ("unknown", "test_name")
            ]
        ]
        sampleC = [
            [("other", "value"),
             ("name", "value")
             ],
            [
                ("name", "value"),
                ("value", "name")
            ],
            [
                ("other", "value"),
                ("name", "value"
                 )],
            [
                ("name", "name1"),
                ("se", "valuex")
            ],
            [(
                "value", "name1"),
                ("se", "valuex")
             ],
            [(
                "other", "name1"),
                ("se", "valuex"
                 )
             ],
            [(
                "name", "name_val"),
                ("num_cases", "num_val")
             ],
            [(
                "other_a", "val_a"),
                ("other_b", "val"
                 )
             ]
        ]
        results = [cmp_samples(val[0], val[1]) for val in sampleA]
        resultB = [cmp_samples(val[0], val[1]) for val in sampleB]
        resultC = [cmp_samples(val[0], val[1]) for val in sampleC]

        self.assertEqual(1, *results)
        self.assertEqual(-1, *resultB)
        self.assertEqual([1, -1, 1, -1, -1, 1, -1, -1], resultC)
