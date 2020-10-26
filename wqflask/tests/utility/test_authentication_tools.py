"""Tests for authentication tools"""
import unittest
from unittest import mock

from utility.authentication_tools import check_resource_availability
from utility.authentication_tools import add_new_resource


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
        return "Jane"


class TestUserSession:
    """Mock user session"""
    @property
    def user_session(self):
        """Mock user session. Mocks Flask.g.user_session object"""
        return TestUser()


def mock_add_resource(resource_ob, update=False):
    return resource_ob


class TestCheckResourceAvailability(unittest.TestCase):
    """Test methods related to checking the resource availability"""
    @mock.patch('utility.authentication_tools.add_new_resource')
    @mock.patch('utility.authentication_tools.Redis')
    @mock.patch('utility.authentication_tools.g', mock.Mock())
    @mock.patch('utility.authentication_tools.get_resource_id')
    def test_check_resource_availability_default_mask(
            self,
            resource_id_mock,
            redis_mock,
            add_new_resource_mock):
        """Test the resource availability with default mask"""
        resource_id_mock.return_value = 1
        redis_mock.smembers.return_value = []
        test_dataset = mock.MagicMock()
        type(test_dataset).type = mock.PropertyMock(return_value="Test")
        add_new_resource_mock.return_value = {"default_mask": 2}
        self.assertEqual(check_resource_availability(test_dataset), 2)

    @mock.patch('utility.authentication_tools.requests.get')
    @mock.patch('utility.authentication_tools.add_new_resource')
    @mock.patch('utility.authentication_tools.Redis')
    @mock.patch('utility.authentication_tools.g', TestUserSession())
    @mock.patch('utility.authentication_tools.get_resource_id')
    def test_check_resource_availability_non_default_mask(
            self,
            resource_id_mock,
            redis_mock,
            add_new_resource_mock,
            requests_mock):
        """Test the resource availability with default mask"""
        resource_id_mock.return_value = 1
        redis_mock.smembers.return_value = []
        add_new_resource_mock.return_value = {"default_mask": 2}
        requests_mock.return_value = TestResponse()
        test_dataset = mock.MagicMock()
        type(test_dataset).type = mock.PropertyMock(return_value="Test")
        self.assertEqual(check_resource_availability(test_dataset),
                         ['foo'])

    @mock.patch('utility.authentication_tools.webqtlConfig.SUPER_PRIVILEGES',
                "SUPERUSER")
    @mock.patch('utility.authentication_tools.requests.get')
    @mock.patch('utility.authentication_tools.add_new_resource')
    @mock.patch('utility.authentication_tools.Redis')
    @mock.patch('utility.authentication_tools.g', TestUserSession())
    @mock.patch('utility.authentication_tools.get_resource_id')
    def test_check_resource_availability_of_super_user(
            self,
            resource_id_mock,
            redis_mock,
            add_new_resource_mock,
            requests_mock):
        """Test the resource availability if the user is the super user"""
        resource_id_mock.return_value = 1
        redis_mock.smembers.return_value = ["Jane"]
        add_new_resource_mock.return_value = {"default_mask": 2}
        requests_mock.return_value = TestResponse()
        test_dataset = mock.MagicMock()
        type(test_dataset).type = mock.PropertyMock(return_value="Test")
        self.assertEqual(check_resource_availability(test_dataset),
                         "SUPERUSER")

    @mock.patch('utility.authentication_tools.webqtlConfig.DEFAULT_PRIVILEGES',
                "John Doe")
    def test_check_resource_availability_string_dataset(self):
        """Test the resource availability if the dataset is a string"""
        self.assertEqual(check_resource_availability("Test"),
                         "John Doe")

    @mock.patch('utility.authentication_tools.webqtlConfig.DEFAULT_PRIVILEGES',
                "John Doe")
    def test_check_resource_availability_temp(self):
        """Test the resource availability if the dataset is a string"""
        test_dataset = mock.MagicMock()
        type(test_dataset).type = mock.PropertyMock(return_value="Temp")
        self.assertEqual(check_resource_availability(test_dataset),
                         "John Doe")


class TestAddNewResource(unittest.TestCase):
    """Test cases for add_new_resource method"""
    @mock.patch('utility.authentication_tools.webqtlConfig.DEFAULT_PRIVILEGES',
                "John Doe")
    @mock.patch('utility.authentication_tools.add_resource', mock_add_resource)
    @mock.patch('utility.authentication_tools.get_group_code')
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

    @mock.patch('utility.authentication_tools.webqtlConfig.DEFAULT_PRIVILEGES',
                "John Doe")
    @mock.patch('utility.authentication_tools.add_resource', mock_add_resource)
    @mock.patch('utility.authentication_tools.get_group_code')
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

    @mock.patch('utility.authentication_tools.webqtlConfig.DEFAULT_PRIVILEGES',
                "John Doe")
    @mock.patch('utility.authentication_tools.add_resource', mock_add_resource)
    @mock.patch('utility.authentication_tools.get_group_code')
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
