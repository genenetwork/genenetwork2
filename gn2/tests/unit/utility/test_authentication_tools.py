"""Tests for authentication tools"""
import unittest
from unittest import mock

from gn2.utility.authentication_tools import add_new_resource


class TestResponse:
    """Mock Test Response after a request"""
    @property
    def content(self):
        """Mock the content from Requests.get(params).content"""
        return '["foo"]'


class TestUser:
    """Mock user"""
    @property
    def user_id(self):
        """Mockes user id. Used in Flask.g.user_session.user_id"""
        return b"Jane"

user_id = b"Jane"


class TestUserSession:
    """Mock user session"""
    @property
    def user_session(self):
        """Mock user session. Mocks Flask.g.user_session object"""
        return TestUser()


def mock_add_resource(resource_ob, update=False):
    return resource_ob


class TestAddNewResource(unittest.TestCase):
    """Test cases for add_new_resource method"""
    @mock.patch('gn2.utility.authentication_tools.webqtlConfig.DEFAULT_PRIVILEGES',
                "John Doe")
    @mock.patch('gn2.utility.authentication_tools.add_resource', mock_add_resource)
    @mock.patch('gn2.utility.authentication_tools.get_group_code')
    def test_add_new_resource_if_publish_datatype(self, group_code_mock):
        """Test add_new_resource if dataset type is 'publish'"""
        group_code_mock.return_value = "Test"
        test_dataset = mock.MagicMock()
        type(test_dataset).type = mock.PropertyMock(return_value="Publish")
        type(test_dataset).id = mock.PropertyMock(return_value=10)
        expected_value = {
            "owner_id": "none",
            "default_mask": "John Doe",
            "group_masks": {},
            "name": "Test_None",
            "data": {
                "dataset": 10,
                "trait": None
            },
            "type": "dataset-publish"
        }
        self.assertEqual(add_new_resource(test_dataset),
                         expected_value)

    @mock.patch('gn2.utility.authentication_tools.webqtlConfig.DEFAULT_PRIVILEGES',
                "John Doe")
    @mock.patch('gn2.utility.authentication_tools.add_resource', mock_add_resource)
    @mock.patch('gn2.utility.authentication_tools.get_group_code')
    def test_add_new_resource_if_geno_datatype(self, group_code_mock):
        """Test add_new_resource if dataset type is 'geno'"""
        group_code_mock.return_value = "Test"
        test_dataset = mock.MagicMock()
        type(test_dataset).name = mock.PropertyMock(return_value="Geno")
        type(test_dataset).type = mock.PropertyMock(return_value="Geno")
        type(test_dataset).id = mock.PropertyMock(return_value=20)
        expected_value = {
            "owner_id": "none",
            "default_mask": "John Doe",
            "group_masks": {},
            "name": "Geno",
            "data": {
                "dataset": 20,
            },
            "type": "dataset-geno"
        }
        self.assertEqual(add_new_resource(test_dataset),
                         expected_value)

    @mock.patch('gn2.utility.authentication_tools.webqtlConfig.DEFAULT_PRIVILEGES',
                "John Doe")
    @mock.patch('gn2.utility.authentication_tools.add_resource', mock_add_resource)
    @mock.patch('gn2.utility.authentication_tools.get_group_code')
    def test_add_new_resource_if_other_datatype(self, group_code_mock):
        """Test add_new_resource if dataset type is not 'geno' or 'publish'"""
        group_code_mock.return_value = "Test"
        test_dataset = mock.MagicMock()
        type(test_dataset).name = mock.PropertyMock(return_value="Geno")
        type(test_dataset).type = mock.PropertyMock(return_value="other")
        type(test_dataset).id = mock.PropertyMock(return_value=20)
        expected_value = {
            "owner_id": "none",
            "default_mask": "John Doe",
            "group_masks": {},
            "name": "Geno",
            "data": {
                "dataset": 20,
            },
            "type": "dataset-probeset"
        }
        self.assertEqual(add_new_resource(test_dataset),
                         expected_value)
