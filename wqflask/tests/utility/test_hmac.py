# -*- coding: utf-8 -*-
"""Test hmac utility functions"""

import unittest
import mock

from utility.hmac import data_hmac
from utility.hmac import url_for_hmac
from utility.hmac import hmac_creation


class TestHmacUtil(unittest.TestCase):
    """Test Utility method for hmac creation"""

    def test_hmac_creation(self):
        """Test hmac creation with a utf-8 string"""
        self.assertEqual(hmac_creation("ファイ"), "21fa1d935bbbb07a7875")

    def test_data_hmac(self):
        """Test data_hmac fn with a utf-8 string"""
        self.assertEqual(data_hmac("ファイ"), "ファイ:21fa1d935bbbb07a7875")

    @mock.patch("utility.hmac.url_for")
    def test_url_for_hmac_with_plain_url(self, mock_url):
        """Test url_for_hmac without params"""
        mock_url.return_value = "https://mock_url.com/ファイ/"
        self.assertEqual(url_for_hmac("ファイ"),
                         "https://mock_url.com/ファイ/?hm=a62896a50d9ffcff7deb")

    @mock.patch("utility.hmac.url_for")
    def test_url_for_hmac_with_param_in_url(self, mock_url):
        """Test url_for_hmac with params"""
        mock_url.return_value = "https://mock_url.com/?ファイ=1"
        self.assertEqual(url_for_hmac("ファイ"),
                         "https://mock_url.com/?ファイ=1&hm=b2128fb28bc32da3b5b7")
