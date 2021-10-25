"""Test cases for some methods in user_session.py"""

import unittest
from wqflask.user_session import verify_cookie


class TestUserSession(unittest.TestCase):
    def test_verify_cookie(self):
        """
        Test cookie verification
        """
        self.assertEqual(
            "3f4c1dbf-5b56-4260-87d6-f35445bda37e",
            verify_cookie(("3f4c1dbf-5b56-4260-87d6-"
                           "f35445bda37e:af4fcf5eace9e7c864ce")))
