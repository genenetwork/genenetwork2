# -*- coding: utf-8 -*-
"""Tests wqflask/base/trait.py"""
import unittest
from unittest import mock

from wqflask import app
from base.trait import GeneralTrait
from base.trait import retrieve_trait_info


class TestResponse:
    """Mock Test Response after a request"""
    @property
    def content(self):
        """Mock the content from Requests.get(params).content"""
        return "[1, 2, 3, 4]"


class TestNilResponse:
    """Mock Test Response after a request"""
    @property
    def content(self):
        """Mock the content from Requests.get(params).content"""
        return "{}"


class MockTrait(GeneralTrait):
    @property
    def wikidata_alias_fmt(self):
        return "Mock alias"


class TestRetrieveTraitInfo(unittest.TestCase):
    """Tests for 'retrieve_trait_info'"""

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_retrieve_trait_info_with_empty_dataset(self):
        """Test that an exception is raised when dataset is empty"""
        with self.assertRaises(AssertionError):
            retrieve_trait_info(trait=mock.MagicMock(),
                                dataset={})

    @mock.patch('base.trait.requests.get')
    @mock.patch('base.trait.g', mock.Mock())
    def test_retrieve_trait_info_with_empty_trait_info(self,
                                                       requests_mock):
        """Empty trait info"""
        requests_mock.return_value = TestNilResponse()
        with self.assertRaises(KeyError):
            retrieve_trait_info(trait=mock.MagicMock(),
                                dataset=mock.MagicMock())

    @mock.patch('base.trait.requests.get')
    @mock.patch('base.trait.g', mock.Mock())
    def test_retrieve_trait_info_with_non_empty_trait_info(self,
                                                           requests_mock):
        """Test that attributes are set"""
        mock_dataset = mock.MagicMock()
        requests_mock.return_value = TestResponse()
        type(mock_dataset).display_fields = mock.PropertyMock(
            return_value=["a", "b", "c", "d"])
        test_trait = retrieve_trait_info(trait=MockTrait(dataset=mock_dataset),
                                         dataset=mock_dataset)
        self.assertEqual(test_trait.a, 1)
        self.assertEqual(test_trait.b, 2)
        self.assertEqual(test_trait.c, 3)
        self.assertEqual(test_trait.d, 4)

    @mock.patch('base.trait.requests.get')
    @mock.patch('base.trait.g', mock.Mock())
    def test_retrieve_trait_info_utf8_parsing(self,
                                              requests_mock):
        """Test that utf-8 strings are parsed correctly"""
        utf_8_string = "test_string"
        mock_dataset = mock.MagicMock()
        requests_mock.return_value = TestResponse()
        type(mock_dataset).display_fields = mock.PropertyMock(
            return_value=["a", "b", "c", "d"])
        type(mock_dataset).type = 'Publish'

        mock_trait = MockTrait(
            dataset=mock_dataset,
            pre_publication_description=utf_8_string
        )
        trait_attrs = {
            "group_code": "test_code",
            "pre_publication_description": "test_pre_pub",
            "pre_publication_abbreviation": "ファイルを画面毎に見て行くには、次のコマンドを使います。",
            "post_publication_description": None,
            "pubmed_id": None,
            'year': "2020",
            "authors": "Jane Doe かいと",
        }
        for key, val in list(trait_attrs.items()):
            setattr(mock_trait, key, val)
        test_trait = retrieve_trait_info(trait=mock_trait,
                                         dataset=mock_dataset)
        self.assertEqual(test_trait.abbreviation,
                         "ファイルを画面毎に見て行くには、次のコマンドを使います。")
        self.assertEqual(test_trait.authors,
                         "Jane Doe かいと")

    @mock.patch('base.trait.requests.get')
    @mock.patch('base.trait.g')
    @mock.patch('base.trait.get_resource_id')
    def test_retrieve_trait_info_with_non_empty_lrs(self,
                                                    resource_id_mock,
                                                    g_mock,
                                                    requests_mock):
        """Test retrieve trait info when lrs has a value"""
        resource_id_mock.return_value = 1
        g_mock.db.execute.return_value.fetchone = mock.Mock()
        g_mock.db.execute.return_value.fetchone.side_effect = [
            [1, 2, 3, 4],  # trait_info = g.db.execute(query).fetchone()
            [1, 2.37, 3, 4, 5],  # trait_qtl = g.db.execute(query).fetchone()
            [2.7333, 2.1204]  # trait_info = g.db.execute(query).fetchone()
        ]
        requests_mock.return_value = None

        mock_dataset = mock.MagicMock()
        type(mock_dataset).display_fields = mock.PropertyMock(
            return_value=["a", "b", "c", "d"])
        type(mock_dataset).type = "ProbeSet"
        type(mock_dataset).name = "RandomName"

        mock_trait = MockTrait(
            dataset=mock_dataset,
            pre_publication_description="test_string"
        )
        trait_attrs = {
            "description": "some description",
            "probe_target_description": "some description",
            "cellid": False,
            "chr": 2.733,
            "mb": 2.1204
        }

        for key, val in list(trait_attrs.items()):
            setattr(mock_trait, key, val)
        test_trait = retrieve_trait_info(trait=mock_trait,
                                         dataset=mock_dataset,
                                         get_qtl_info=True)
        self.assertEqual(test_trait.LRS_score_repr,
                         "2.4")

    @mock.patch('base.trait.requests.get')
    @mock.patch('base.trait.g')
    @mock.patch('base.trait.get_resource_id')
    def test_retrieve_trait_info_with_empty_lrs_field(self,
                                                      resource_id_mock,
                                                      g_mock,
                                                      requests_mock):
        """Test retrieve trait info with empty lrs field"""
        resource_id_mock.return_value = 1
        g_mock.db.execute.return_value.fetchone = mock.Mock()
        g_mock.db.execute.return_value.fetchone.side_effect = [
            [1, 2, 3, 4],  # trait_info = g.db.execute(query).fetchone()
            [1, None, 3, 4, 5],  # trait_qtl = g.db.execute(query).fetchone()
            [2, 3]  # trait_info = g.db.execute(query).fetchone()
        ]
        requests_mock.return_value = None

        mock_dataset = mock.MagicMock()
        type(mock_dataset).display_fields = mock.PropertyMock(
            return_value=["a", "b", "c", "d"])
        type(mock_dataset).type = "ProbeSet"
        type(mock_dataset).name = "RandomName"

        mock_trait = MockTrait(
            dataset=mock_dataset,
            pre_publication_description="test_string"
        )
        trait_attrs = {
            "description": "some description",
            "probe_target_description": "some description",
            "cellid": False,
            "chr": 2.733,
            "mb": 2.1204
        }

        for key, val in list(trait_attrs.items()):
            setattr(mock_trait, key, val)
        test_trait = retrieve_trait_info(trait=mock_trait,
                                         dataset=mock_dataset,
                                         get_qtl_info=True)
        self.assertEqual(test_trait.LRS_score_repr,
                         "N/A")
        self.assertEqual(test_trait.LRS_location_repr,
                         "Chr2: 3.000000")

    @mock.patch('base.trait.requests.get')
    @mock.patch('base.trait.g')
    @mock.patch('base.trait.get_resource_id')
    def test_retrieve_trait_info_with_empty_chr_field(self,
                                                      resource_id_mock,
                                                      g_mock,
                                                      requests_mock):
        """Test retrieve trait info with empty chr field"""
        resource_id_mock.return_value = 1
        g_mock.db.execute.return_value.fetchone = mock.Mock()
        g_mock.db.execute.return_value.fetchone.side_effect = [
            [1, 2, 3, 4],  # trait_info = g.db.execute(query).fetchone()
            [1, 2, 3, 4, 5],  # trait_qtl = g.db.execute(query).fetchone()
            [None, 3]  # trait_info = g.db.execute(query).fetchone()
        ]

        requests_mock.return_value = None

        mock_dataset = mock.MagicMock()
        type(mock_dataset).display_fields = mock.PropertyMock(
            return_value=["a", "b", "c", "d"])
        type(mock_dataset).type = "ProbeSet"
        type(mock_dataset).name = "RandomName"

        mock_trait = MockTrait(
            dataset=mock_dataset,
            pre_publication_description="test_string"
        )
        trait_attrs = {
            "description": "some description",
            "probe_target_description": "some description",
            "cellid": False,
            "chr": 2.733,
            "mb": 2.1204
        }

        for key, val in list(trait_attrs.items()):
            setattr(mock_trait, key, val)
        test_trait = retrieve_trait_info(trait=mock_trait,
                                         dataset=mock_dataset,
                                         get_qtl_info=True)
        self.assertEqual(test_trait.LRS_score_repr,
                         "N/A")
        self.assertEqual(test_trait.LRS_location_repr,
                         "N/A")
