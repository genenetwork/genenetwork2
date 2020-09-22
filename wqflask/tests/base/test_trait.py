# -*- coding: utf-8 -*-
"""Tests wqflask/base/trait.py"""
import unittest
import mock

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
    def test_retrieve_trait_info_with_empty_dataset(self):
        """Test that an exception is raised when dataset is empty"""
        with self.assertRaises(AssertionError):
            retrieve_trait_info(trait=mock.MagicMock(),
                                dataset={})

    @mock.patch('base.trait.requests.get')
    @mock.patch('base.trait.g')
    def test_retrieve_trait_info_with_empty_trait_info(self,
                                                       g_mock,
                                                       requests_mock):
        """Empty trait info"""
        requests_mock.return_value = TestNilResponse()
        with self.assertRaises(KeyError):
            retrieve_trait_info(trait=mock.MagicMock(),
                                dataset=mock.MagicMock())

    @mock.patch('base.trait.requests.get')
    @mock.patch('base.trait.g')
    def test_retrieve_trait_info_with_non_empty_trait_info(self,
                                                           g_mock,
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
    @mock.patch('base.trait.g')
    def test_retrieve_trait_info_utf8_parsing(self,
                                              g_mock,
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
                         "ファイルを画面毎に見て行くには、次のコマンドを使います。".decode('utf-8'))
        self.assertEqual(test_trait.authors,
                         "Jane Doe かいと".decode('utf-8'))
