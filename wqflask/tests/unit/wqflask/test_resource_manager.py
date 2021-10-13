"""Test cases for wqflask/resource_manager.py"""
import unittest

from unittest import mock
from wqflask.resource_manager import get_user_membership


class TestGetUserMembership(unittest.TestCase):
    """Test cases for `get_user_membership`"""

    def setUp(self):
        conn = mock.MagicMock()
        conn.hgetall.return_value = {
            '7fa95d07-0e2d-4bc5-b47c-448fdc1260b2': (
                '{"name": "editors", '
                '"admins": ["8ad942fe-490d-453e-bd37-56f252e41604", "rand"], '
                '"members": ["8ad942fe-490d-453e-bd37-56f252e41603", '
                '"rand"], '
                '"changed_timestamp": "Oct 06 2021 06:39PM", '
                '"created_timestamp": "Oct 06 2021 06:39PM"}')}
        self.conn = conn

    def test_user_is_group_member_only(self):
        """Test that a user is only a group member"""
        self.assertEqual(
            get_user_membership(
                conn=self.conn,
                user_id="8ad942fe-490d-453e-bd37-56f252e41603",
                group_id="7fa95d07-0e2d-4bc5-b47c-448fdc1260b2"),
            {"member": True,
             "admin": False})

    def test_user_is_group_admin_only(self):
        """Test that a user is a group admin only"""
        self.assertEqual(
            get_user_membership(
                conn=self.conn,
                user_id="8ad942fe-490d-453e-bd37-56f252e41604",
                group_id="7fa95d07-0e2d-4bc5-b47c-448fdc1260b2"),
            {"member": False,
             "admin": True})

    def test_user_is_both_group_member_and_admin(self):
        """Test that a user is both an admin and member of a group"""
        self.assertEqual(
            get_user_membership(
                conn=self.conn,
                user_id="rand",
                group_id="7fa95d07-0e2d-4bc5-b47c-448fdc1260b2"),
            {"member": True,
             "admin": True})
