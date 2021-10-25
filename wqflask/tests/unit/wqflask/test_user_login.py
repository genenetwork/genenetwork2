"""Test cases for some methods in login.py"""

import unittest
from wqflask.user_login import encode_password


class TestUserLogin(unittest.TestCase):
    def test_encode_password(self):
        """
        Test encode password
        """
        pass_gen_fields = {
            "salt": "salt",
            "hashfunc": "sha1",
            "iterations": 4096,
            "keylength": 20,
        }
        self.assertEqual(
            encode_password(pass_gen_fields,
                            "password").get("password"),
            '4b007901b765489abead49d926f721d065a429c1')
