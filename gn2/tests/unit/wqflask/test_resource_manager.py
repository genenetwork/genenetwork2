"""Test cases for wqflask/resource_manager.py"""
import json
import unittest

from unittest import mock
from gn3.authentication import get_user_membership
from gn3.authentication import get_highest_user_access_role
from gn3.authentication import DataRole
from gn3.authentication import AdminRole


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


class TestCheckUserAccessRole(unittest.TestCase):
    """Test cases for `get_highest_user_access_role`"""

    def test_edit_access(self, requests_mock):
        """Test that the right access roles are set"""
        response = mock.PropertyMock(return_value=json.dumps(
            {
                'data': ['no-access', 'view', 'edit', ],
                'metadata': ['no-access', 'view', 'edit', ],
                'admin': ['not-admin', 'edit-access', ],
            }
        ))
        type(requests_mock.return_value).content = response
        self.assertEqual(get_highest_user_access_role(
            resource_id="0196d92e1665091f202f",
            user_id="8ad942fe-490d-453e-bd37"),
            {"data": DataRole.EDIT,
             "metadata": DataRole.EDIT,
             "admin": AdminRole.EDIT_ACCESS})

    def test_no_access(self, requests_mock):
        response = mock.PropertyMock(return_value=json.dumps(
            {
                'data': ['no-access', ],
                'metadata': ['no-access', ],
                'admin': ['not-admin', ],
            }
        ))
        type(requests_mock.return_value).content = response
        self.assertEqual(get_highest_user_access_role(
            resource_id="0196d92e1665091f202f",
            user_id=""),
            {"data": DataRole.NO_ACCESS,
             "metadata": DataRole.NO_ACCESS,
             "admin": AdminRole.NOT_ADMIN})
