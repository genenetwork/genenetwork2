"""Tests for wqflask/base/data_set.py"""

import unittest
from unittest import mock

from wqflask import app
from base.data_set import DatasetType


GEN_MENU_JSON = """
{
  "datasets": {
    "human": {
      "HLC": {
        "Liver mRNA": [
          [
            "320",
            "HLC_0311",
            "GSE9588 Human Liver Normal (Mar11) Both Sexes"
          ]
        ],
        "Phenotypes": [
          [
            "635",
            "HLCPublish",
            "HLC Published Phenotypes"
          ]
        ]
      }
    },
    "mouse": {
      "BXD": {
        "Genotypes": [
          [
            "600",
            "BXDGeno",
            "BXD Genotypes"
          ]
        ],
        "Hippocampus mRNA": [
          [
            "112",
            "HC_M2_0606_P",
            "Hippocampus Consortium M430v2 (Jun06) PDNN"
          ]
        ],
        "Phenotypes": [
          [
            "602",
            "BXDPublish",
            "BXD Published Phenotypes"
          ]
        ]
      }
    }
  },
  "groups": {
    "human": [
      [
        "HLC",
        "Liver: Normal Gene Expression with Genotypes (Merck)",
        "Family:None"
      ]
    ],
    "mouse": [
      [
        "BXD",
        "BXD",
        "Family:None"
      ]
    ]
  },
  "species": [
    [
      "human",
      "Human"
    ],
    [
      "mouse",
      "Mouse"
    ]
  ],
  "types": {
    "human": {
      "HLC": [
        [
          "Phenotypes",
          "Traits and Cofactors",
          "Phenotypes"
        ],
        [
          "Liver mRNA",
          "Liver mRNA",
          "Molecular Trait Datasets"
        ]
      ]
    },
    "mouse": {
      "BXD": [
        [
          "Phenotypes",
          "Traits and Cofactors",
          "Phenotypes"
        ],
        [
          "Genotypes",
          "DNA Markers and SNPs",
          "Genotypes"
        ],
        [
          "Hippocampus mRNA",
          "Hippocampus mRNA",
          "Molecular Trait Datasets"
        ]
      ]
    }
  }
}
"""


class TestDataSetTypes(unittest.TestCase):
    """Tests for the DataSetType class"""

    def setUp(self):
        self.test_dataset = """
            {
                "AD-cases-controls-MyersGeno": "Geno",
                "AD-cases-controls-MyersPublish": "Publish",
                "AKXDGeno": "Geno",
                "AXBXAGeno": "Geno",
                "AXBXAPublish": "Publish",
                "Aging-Brain-UCIPublish": "Publish",
                "All Phenotypes": "Publish",
                "B139_K_1206_M": "ProbeSet",
                "B139_K_1206_R": "ProbeSet"
            }
            """
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_data_set_type(self):
        """Test that DatasetType returns correctly if the Redis Instance is not empty
        and the name variable exists in the dictionary

        """
        with app.app_context():
            redis_mock = mock.Mock()
            redis_mock.get.return_value = self.test_dataset
            self.assertEqual(DatasetType(redis_mock)
                             ("All Phenotypes"), "Publish")
            redis_mock.get.assert_called_once_with("dataset_structure")

    @mock.patch('base.data_set.requests.get')
    def test_data_set_type_with_empty_redis(self, request_mock):
        """Test that DatasetType returns correctly if the Redis Instance is empty and
        the name variable exists in the dictionary

        """
        with app.app_context():
            request_mock.return_value.content = GEN_MENU_JSON
            redis_mock = mock.Mock()
            redis_mock.get.return_value = None
            data_set = DatasetType(redis_mock)
            self.assertEqual(data_set("BXDGeno"), "Geno")
            self.assertEqual(data_set("BXDPublish"), "Publish")
            self.assertEqual(data_set("HLC_0311"), "ProbeSet")

            redis_mock.set.assert_called_once_with(
                "dataset_structure",
                ('{"HLC_0311": "ProbeSet", '
                 '"HLCPublish": "Publish", '
                 '"BXDGeno": "Geno", '
                 '"HC_M2_0606_P": "ProbeSet", '
                 '"BXDPublish": "Publish"}'))

    @unittest.skip("Too complicated")
    @mock.patch('base.data_set.g')
    def test_set_dataset_key_mrna(self, db_mock):
        with app.app_context():
            db_mock.db.execute.return_value.fetchone.return_value = [1, 2, 3]
            redis_mock = mock.Mock()
            redis_mock.get.return_value = self.test_dataset
            data_set = DatasetType(redis_mock)
            data_set.set_dataset_key("mrna_expr", "Test")
            self.assertEqual(data_set("Test"), "ProbeSet")
            redis_mock.set.assert_called_once_with(
                "dataset_structure",
                ('{"AD-cases-controls-MyersGeno": "Geno", '
                 '"AD-cases-controls-MyersPublish": "Publish", '
                 '"AKXDGeno": "Geno", '
                 '"AXBXAGeno": "Geno", '
                 '"AXBXAPublish": "Publish", '
                 '"Aging-Brain-UCIPublish": "Publish", '
                 '"All Phenotypes": "Publish", '
                 '"B139_K_1206_M": "ProbeSet", '
                 '"B139_K_1206_R": "ProbeSet", '
                 '"Test": "ProbeSet"}'))
            db_mock.db.execute.assert_called_once_with(
                ("SELECT ProbeSetFreeze.Id FROM ProbeSetFreeze "
                 + "WHERE ProbeSetFreeze.Name = \"Test\" ")
            )

    @unittest.skip("Too complicated")
    @mock.patch('base.data_set.g')
    def test_set_dataset_key_pheno(self, db_mock):
        with app.app_context():
            db_mock.db.execute.return_value.fetchone.return_value = [1, 2, 3]
            redis_mock = mock.Mock()
            redis_mock.get.return_value = self.test_dataset
            data_set = DatasetType(redis_mock)
            data_set.set_dataset_key("pheno", "Test")
            self.assertEqual(data_set("Test"), "Publish")
            redis_mock.set.assert_called_once_with(
                "dataset_structure",
                ('{"AD-cases-controls-MyersGeno": "Geno", '
                 '"AD-cases-controls-MyersPublish": "Publish", '
                 '"AKXDGeno": "Geno", '
                 '"AXBXAGeno": "Geno", '
                 '"AXBXAPublish": "Publish", '
                 '"Aging-Brain-UCIPublish": "Publish", '
                 '"All Phenotypes": "Publish", '
                 '"B139_K_1206_M": "ProbeSet", '
                 '"B139_K_1206_R": "ProbeSet", '
                 '"Test": "Publish"}'))
            db_mock.db.execute.assert_called_with(
                ("SELECT InfoFiles.GN_AccesionId "
                 "FROM InfoFiles, PublishFreeze, InbredSet "
                 "WHERE InbredSet.Name = 'Test' AND "
                 "PublishFreeze.InbredSetId = InbredSet.Id AND "
                 "InfoFiles.InfoPageName = PublishFreeze.Name")
            )

    @unittest.skip("Too complicated")
    @mock.patch('base.data_set.g')
    def test_set_dataset_other_pheno(self, db_mock):
        with app.app_context():
            db_mock.db.execute.return_value.fetchone.return_value = [1, 2, 3]
            redis_mock = mock.Mock()
            redis_mock.get.return_value = self.test_dataset
            data_set = DatasetType(redis_mock)
            data_set.set_dataset_key("other_pheno", "Test")
            self.assertEqual(data_set("Test"), "Publish")

            redis_mock.set.assert_called_once_with(
                "dataset_structure",
                ('{"AD-cases-controls-MyersGeno": "Geno", '
                 '"AD-cases-controls-MyersPublish": "Publish", '
                 '"AKXDGeno": "Geno", '
                 '"AXBXAGeno": "Geno", '
                 '"AXBXAPublish": "Publish", '
                 '"Aging-Brain-UCIPublish": "Publish", '
                 '"All Phenotypes": "Publish", '
                 '"B139_K_1206_M": "ProbeSet", '
                 '"B139_K_1206_R": "ProbeSet", '
                 '"Test": "Publish"}'))

            db_mock.db.execute.assert_called_with(
                ("SELECT PublishFreeze.Name "
                 + "FROM PublishFreeze, InbredSet "
                 + "WHERE InbredSet.Name = 'Test' AND "
                 "PublishFreeze.InbredSetId = InbredSet.Id")
            )

    @unittest.skip("Too complicated")
    @mock.patch('base.data_set.g')
    def test_set_dataset_geno(self, db_mock):
        with app.app_context():
            db_mock.db.execute.return_value.fetchone.return_value = [1, 2, 3]
            redis_mock = mock.Mock()
            redis_mock.get.return_value = self.test_dataset
            data_set = DatasetType(redis_mock)
            data_set.set_dataset_key("geno", "Test")
            self.assertEqual(data_set("Test"), "Geno")
            redis_mock.set.assert_called_once_with(
                "dataset_structure",
                ('{"AD-cases-controls-MyersGeno": "Geno", '
                 '"AD-cases-controls-MyersPublish": "Publish", '
                 '"AKXDGeno": "Geno", '
                 '"AXBXAGeno": "Geno", '
                 '"AXBXAPublish": "Publish", '
                 '"Aging-Brain-UCIPublish": "Publish", '
                 '"All Phenotypes": "Publish", '
                 '"B139_K_1206_M": "ProbeSet", '
                 '"B139_K_1206_R": "ProbeSet", '
                 '"Test": "Geno"}'))

            db_mock.db.execute.assert_called_with(
                ("SELECT GenoFreeze.Id FROM "
                 "GenoFreeze WHERE GenoFreeze.Name = \"Test\" "))
