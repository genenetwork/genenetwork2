import datetime
import unittest
from unittest import mock
from gn2.wqflask.show_trait.export_trait_data import dict_to_sorted_list
from gn2.wqflask.show_trait.export_trait_data import cmp_samples
from gn2.wqflask.show_trait.export_trait_data import export_sample_table
from gn2.wqflask.show_trait.export_trait_data import get_export_metadata


class AttributesSetter:
    def __init__(self, obj):
        for key, value in obj.items():
            setattr(self, key, value)


class TestExportTraits(unittest.TestCase):
    """Test methods for exporting traits and metadata"""

    @mock.patch("gn2.wqflask.show_trait.export_trait_data.datetime")
    @mock.patch("gn2.wqflask.show_trait.export_trait_data.create_trait")
    @mock.patch("gn2.wqflask.show_trait.export_trait_data.data_set")
    def test_get_export_metadata(self, data_mock, trait_mock, date_mock):
        """test for exporting metadata with dataset.type=Publish"""
        mock_dataset = AttributesSetter({"type": "Publish",
                                         "name": "HC_M2_0606_P",
                                         "dataset_name": "HC_M2_0606_P"})

        mock_dataset.group = AttributesSetter({"name": "C"})
        data_mock.create_dataset.return_value = mock_dataset

        trait_data = {
            "symbol": "Nr3c1",
            "description_display": "nuclear receptor subfamily 3,group C, member 1 (glucocorticoid receptor); distal 3' UTR",
            "title": "Trait_1 title",

            "authors": "XL_1",
            "journal": ""

        }

        date_mock.datetime.now.return_value = datetime.datetime(
            2022, 8, 8, 19, 2, 31, 628813)
        trait_mock.return_value = AttributesSetter(trait_data)

        results = get_export_metadata({
            "trait_id": "1460303_at",
            "trait_display_name": "1460303_at",
            "dataset": "HC_M2_0606_P",
            "group": "BXD",
        })

        expected = [["Phenotype ID:", "1460303_at"],
                    ["Phenotype URL: ", "http://genenetwork.org/show_trait?trait_id=1460303_at&dataset=HC_M2_0606_P"],
                    ["Group: ", "C"],
                    ["Phenotype: ",
                        'nuclear receptor subfamily 3","group C"," member 1 (glucocorticoid receptor); distal 3\' UTR'],
                    ["Authors: ", "XL_1"],
                    ["Title: ", "Trait_1 title"],
                    ["Journal: ", "N/A"],
                    ["Dataset Link: ", "http://gn1.genenetwork.org/webqtl/main.py?FormID=sharinginfo&InfoPageName=HC_M2_0606_P"],
                    ["Export Date: ", "August 08, 2022"],
                    ["Export Time: ", "19:02 GMT"]]

        self.assertEqual(results, expected)

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
