import requests
from wqflask import user_manager
from utility.elasticsearch_tools import get_user_by_unique_column
from parameterized import parameterized
from parametrized_test import ParametrizedTest

passwork_reset_link = ''
forgot_password_page = None

class TestForgotPassword(ParametrizedTest):

    def setUp(self):
        super(TestForgotPassword, self).setUp()
        self.forgot_password_url = self.gn2_url+"/n/forgot_password_submit"
        def send_email(to_addr, msg, fromaddr="no-reply@genenetwork.org"):
            print("CALLING: send_email_mock()")
            email_data = {
                "to_addr": to_addr
                , "msg": msg
                , "fromaddr": from_addr}

        data = {
            "es_connection": self.es,
            "email_address": "test@user.com",
            "full_name": "Test User",
            "organization": "Test Organisation",
            "password": "test_password",
            "password_confirm": "test_password"
        }
        user_manager.basic_info = lambda : { "basic_info": "basic" }
        user_manager.RegisterUser(data)

    def testWithoutEmail(self):
        data = {"email_address": ""}
        error_notification = '<div class="alert alert-danger">You MUST provide an email</div>'
        result = requests.post(self.forgot_password_url, data=data)
        self.assertEqual(result.url, self.gn2_url+"/n/forgot_password")
        self.assertTrue(
            result.content.find(error_notification) >= 0
            , "Error message should be displayed but was not")

    def testWithNonExistingEmail(self):
        # Monkey patching doesn't work, so simply test that getting by email
        # returns the correct data
        user = get_user_by_unique_column(self.es, "email_address", "non-existent@domain.com")
        self.assertTrue(user is None, "Should not find non-existent user")

    def testWithExistingEmail(self):
        # Monkey patching doesn't work, so simply test that getting by email
        # returns the correct data
        user = get_user_by_unique_column(self.es, "email_address", "test@user.com")
        self.assertTrue(user is not None, "Should find user")
