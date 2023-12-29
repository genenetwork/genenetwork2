"""Tests for wqflask/base/data_set.py"""

import unittest
from unittest import mock
from dataclasses import dataclass
from gn3.monads import MonadicDict

from gn2.wqflask import app
from gn2.base.data_set import DatasetType
from gn2.base.data_set.dataset import DataSet

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

class MockPhenotypeDataset(DataSet):
    def setup(self):
        self.type = "Publish"
        self.query_for_group = ""
        self.group = ""


    def check_confidentiality(self):
        pass

    def retrieve_other_names(self):
        pass

@dataclass
class MockGroup:
    name = "Group"

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
            cursor_mock = mock.Mock()
            redis_mock.get.return_value = self.test_dataset
            self.assertEqual(DatasetType(redis_mock)
                             ("All Phenotypes", redis_mock, cursor_mock), "Publish")
            redis_mock.get.assert_called_once_with("dataset_structure")

    @mock.patch('base.data_set.datasettype.requests.get')
    def test_data_set_type_with_empty_redis(self, request_mock):
        """Test that DatasetType returns correctly if the Redis Instance is empty and
        the name variable exists in the dictionary

        """
        with app.app_context():
            request_mock.return_value.content = GEN_MENU_JSON
            redis_mock = mock.Mock()
            cursor_mock = mock.Mock()
            redis_mock.get.return_value = None
            data_set = DatasetType(redis_mock)
            self.assertEqual(data_set("BXDGeno", redis_mock, cursor_mock),
                             "Geno")
            self.assertEqual(data_set("BXDPublish", redis_mock, cursor_mock),
                             "Publish")
            self.assertEqual(data_set("HLC_0311", redis_mock, cursor_mock),
                             "ProbeSet")

            redis_mock.set.assert_called_once_with(
                "dataset_structure",
                ('{"HLC_0311": "ProbeSet", '
                 '"HLCPublish": "Publish", '
                 '"BXDGeno": "Geno", '
                 '"HC_M2_0606_P": "ProbeSet", '
                 '"BXDPublish": "Publish"}'))


class TestDatasetAccessionId(unittest.TestCase):
    """Tests for the DataSetType class"""

    @mock.patch("base.data_set.dataset.query_sql")
    @mock.patch("base.data_set.dataset.DatasetGroup")
    def test_get_accession_id(self, mock_dataset_group, mock_query_sql):
        def mock_fn():
            yield MonadicDict({"accession_id": 7})
        mock_dataset_group.return_value = MockGroup()
        mock_query_sql.return_value = mock_fn()
        sample_dataset = MockPhenotypeDataset(
            name="BXD-LongevityPublish",
            get_samplelist=False,
            group_name="BXD",
            redis_conn=mock.Mock()
        )
        sample_dataset\
            .accession_id\
            .bind(lambda x: self.assertEqual(7, x))

    @mock.patch("base.data_set.dataset.query_sql")
    @mock.patch("base.data_set.dataset.DatasetGroup")
    def test_get_accession_id_empty_return(self, mock_dataset_group,
                                           mock_query_sql):
        mock_dataset_group.return_value = MockGroup()
        mock_query_sql.return_value = None
        sample_dataset = MockPhenotypeDataset(
            name="BXD-LongevityPublish",
            get_samplelist=False,
            group_name="BXD",
            redis_conn=mock.Mock()
        )
        sample_dataset\
            .accession_id\
            .bind(lambda x: self.assertNone(x))
