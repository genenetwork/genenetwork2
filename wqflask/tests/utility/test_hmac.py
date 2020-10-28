# -*- coding: utf-8 -*-
"""Test hmac utility functions"""

import unittest
from unittest import mock

from utility.hmac import data_hmac
from utility.hmac import url_for_hmac
from utility.hmac import hmac_creation


class TestHmacUtil(unittest.TestCase):
    """Test Utility method for hmac creation"""

    @mock.patch("utility.hmac.app.config", {'SECRET_HMAC_CODE': "secret"})
    def test_hmac_creation(self):
        """Test hmac creation with a utf-8 string"""
        self.assertEqual(hmac_creation("ファイ"), "7410466338cfe109e946")

    @mock.patch("utility.hmac.app.config",
                {'SECRET_HMAC_CODE': ('\x08\xdf\xfa\x93N\x80'
                                      '\xd9\\H@\\\x9f`\x98d^'
                                      '\xb4a;\xc6OM\x946a\xbc'
                                      '\xfc\x80:*\xebc')})
    def test_hmac_creation_with_cookie(self):
        """Test hmac creation with a cookie"""
        cookie = "3f4c1dbf-5b56-4260-87d6-f35445bda37e:af4fcf5eace9e7c864ce"
        uuid_, _, signature = cookie.partition(":")
        self.assertEqual(
            hmac_creation(uuid_),
            "af4fcf5eace9e7c864ce")

    @mock.patch("utility.hmac.app.config", {'SECRET_HMAC_CODE': "secret"})
    def test_data_hmac(self):
        """Test data_hmac fn with a utf-8 string"""
        self.assertEqual(data_hmac("ファイ"), "ファイ:7410466338cfe109e946")

    @mock.patch("utility.hmac.app.config", {'SECRET_HMAC_CODE': "secret"})
    @mock.patch("utility.hmac.url_for")
    def test_url_for_hmac_with_plain_url(self, mock_url):
        """Test url_for_hmac without params"""
        mock_url.return_value = "https://mock_url.com/ファイ/"
        self.assertEqual(url_for_hmac("ファイ"),
                         "https://mock_url.com/ファイ/?hm=05bc39e659b1948f41e7")

    @mock.patch("utility.hmac.app.config", {'SECRET_HMAC_CODE': "secret"})
    @mock.patch("utility.hmac.url_for")
    def test_url_for_hmac_with_param_in_url(self, mock_url):
        """Test url_for_hmac with params"""
        mock_url.return_value = "https://mock_url.com/?ファイ=1"
        self.assertEqual(url_for_hmac("ファイ"),
                         "https://mock_url.com/?ファイ=1&hm=4709c1708270644aed79")
