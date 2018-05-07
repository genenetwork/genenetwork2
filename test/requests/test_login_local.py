import requests
from wqflask.user_manager import RegisterUser
from parameterized import parameterized
from parametrized_test import ParametrizedTest

login_link_text = '<a id="login_in" href="/n/login">Sign in</a>'
logout_link_text = '<a id="login_out" title="Signed in as Test User." href="/n/logout">Sign out</a>'

class TestLoginLocal(ParametrizedTest):

    def setUp(self):
        super(TestLoginLocal, self).setUp()
        self.login_url = self.gn2_url +"/n/login"
        data = {
            "es_connection": self.es,
            "email_address": "test@user.com",
            "full_name": "Test User",
            "organization": "Test Organisation",
            "password": "test_password",
            "password_confirm": "test_password"
        }
        RegisterUser(data)

    
    @parameterized.expand([
        (
            {
                "email_address": "non@existent.email",
                "password": "doesitmatter?",
                "submit": "Sign in"
            }, login_link_text, "Login should have failed with the wrong user details."),
        (
            {
                "email_address": "test@user.com",
                "password": "test_password",
                "submit": "Sign in"
            }, logout_link_text, "Login should have been successful with correct user details and neither import_collections nor remember_me set"),
        (
            {
                "email_address": "test@user.com",
                "password": "test_password",
                "import_collections": "y",
                "submit": "Sign in"
            }, logout_link_text, "Login should have been successful with correct user details and only import_collections set"),
        (
            {
                "email_address": "test@user.com",
                "password": "test_password",
                "remember_me": "y",
                "submit": "Sign in"
            }, logout_link_text, "Login should have been successful with correct user details and only remember_me set"),
        (
            {
                "email_address": "test@user.com",
                "password": "test_password",
                "remember_me": "y",
                "import_collections": "y",
                "submit": "Sign in"
            }, logout_link_text, "Login should have been successful with correct user details, and both remember_me, and import_collections set")
    ])
    def testLogin(self, data, expected, message):
        result = requests.post(self.login_url, data=data)
        index = result.content.find(expected)
        self.assertTrue(index >= 0, message)
