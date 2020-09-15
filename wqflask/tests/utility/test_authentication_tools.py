"""Tests for authentication tools"""
import unittest
import mock

from utility.authentication_tools import check_resource_availability


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


class TestCheckResourceAvailability(unittest.TestCase):
    """Test methods related to checking the resource availability"""
    @mock.patch('utility.authentication_tools.add_new_resource')
    @mock.patch('utility.authentication_tools.Redis')
    @mock.patch('utility.authentication_tools.g')
    @mock.patch('utility.authentication_tools.get_resource_id')
    def test_check_resource_availability_default_mask(
            self,
            resource_id_mock,
            g_mock,
            redis_mock,
            add_new_resource_mock):
        """Test the resource availability with default mask"""
        resource_id_mock.return_value = 1
        g_mock.return_value = mock.Mock()
        redis_mock.smembers.return_value = []
        test_dataset = mock.MagicMock()
        type(test_dataset).type = mock.PropertyMock(return_value="Test")
        add_new_resource_mock.return_value = {"default_mask": 2}
        self.assertEqual(check_resource_availability(test_dataset), 2)

    @mock.patch('utility.authentication_tools.requests.get')
    @mock.patch('utility.authentication_tools.add_new_resource')
    @mock.patch('utility.authentication_tools.Redis')
    @mock.patch('utility.authentication_tools.g')
    @mock.patch('utility.authentication_tools.get_resource_id')
    def test_check_resource_availability_non_default_mask(
            self,
            resource_id_mock,
            g_mock,
            redis_mock,
            add_new_resource_mock,
            requests_mock):
        """Test the resource availability with default mask"""
        resource_id_mock.return_value = 1
        g_mock.return_value = mock.Mock()
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
