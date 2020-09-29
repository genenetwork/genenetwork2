"""Test cases for some methods in collect.py"""

import unittest
from unittest import mock

from flask import Flask
from wqflask.collect import process_traits

app = Flask(__name__)


class MockSession:
    """Helper class for mocking wqflask.collect.g.user_session.logged_in"""
    def __init__(self, is_logged_in=False):
        self.is_logged_in = is_logged_in

    @property
    def logged_in(self):
        return self.is_logged_in


class MockFlaskG:
    """Helper class for mocking wqflask.collect.g.user_session"""
    def __init__(self, is_logged_in=False):
        self.is_logged_in = is_logged_in

    @property
    def user_session(self):
        if self.is_logged_in:
            return MockSession(is_logged_in=True)
        return MockSession()


class TestCollect(unittest.TestCase):

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @mock.patch("wqflask.collect.g", MockFlaskG())
    def test_process_traits_with_bytestring(self):
        """
        Test that the correct traits are returned when the user is logged
        out and bytes are used.
        """
        self.assertEqual(process_traits(
            b'1452452_at:HC_M2_0606_P:163d04f7db7c9e110de6,'
            b'1452447_at:HC_M2_0606_P:eeece8fceb67072debea,'
            b'1451401_a_at:HC_M2_0606_P:a043d23b3b3906d8318e,'
            b'1429252_at:HC_M2_0606_P:6fa378b349bc9180e8f5'),
            set(['1429252_at:HC_M2_0606_P',
                 '1451401_a_at:HC_M2_0606_P',
                 '1452447_at:HC_M2_0606_P',
                 '1452452_at:HC_M2_0606_P']))

    @mock.patch("wqflask.collect.g", MockFlaskG())
    def test_process_traits_with_normal_string(self):
        """
        Test that the correct traits are returned when the user is logged
        out and a normal string is used.
        """
        self.assertEqual(process_traits(
            '1452452_at:HC_M2_0606_P:163d04f7db7c9e110de6,'
            '1452447_at:HC_M2_0606_P:eeece8fceb67072debea,'
            '1451401_a_at:HC_M2_0606_P:a043d23b3b3906d8318e,'
            '1429252_at:HC_M2_0606_P:6fa378b349bc9180e8f5'),
            set(['1429252_at:HC_M2_0606_P',
                 '1451401_a_at:HC_M2_0606_P',
                 '1452447_at:HC_M2_0606_P',
                 '1452452_at:HC_M2_0606_P']))
