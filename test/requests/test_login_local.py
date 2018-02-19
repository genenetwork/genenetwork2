import requests
from wqflask import user_manager
from parametrized_test import ParametrizedTest

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
        user_manager.basic_info = lambda : { "basic_info": "basic" }
        user_manager.RegisterUser(data)

    def testLoginNonRegisteredUser(self):
        data = {
            "email_address": "non@existent.email",
            "password": "doesitmatter?"
        }
        result = requests.post(self.login_url, data=data)
        self.assertEqual(result.url, self.login_url, "")

    def testLoginWithRegisteredUserBothRememberMeAndImportCollectionsFalse(self):
        data = {
            "email_address": "test@user.com",
            "password": "test_password"
        }
        result = requests.post(self.login_url, data=data)
        self.assertEqual(
            result.url
            , self.gn2_url+"/?import_collections=false"
            , "Login should have been successful")

    def testLoginWithRegisteredUserImportCollectionsTrueAndRememberMeFalse(self):
        data = {
            "email_address": "test@user.com",
            "password": "test_password",
            "import_collections": "y"
        }
        result = requests.post(self.login_url, data=data)
        self.assertEqual(
            result.url
            , self.gn2_url+"/?import_collections=true"
            , "Login should have been successful")

    def testLoginWithRegisteredUserImportCollectionsFalseAndRememberMeTrue(self):
        data = {
            "email_address": "test@user.com",
            "password": "test_password",
            "remember_me": "y"
        }
        result = requests.post(self.login_url, data=data)
        self.assertEqual(
            result.url
            , self.gn2_url+"/?import_collections=false"
            , "Login should have been successful")

    def testLoginWithRegisteredUserBothImportCollectionsAndRememberMeTrue(self):
        data = {
            "email_address": "test@user.com",
            "password": "test_password",
            "remember_me": "y",
            "import_collections": "y"
        }
        result = requests.post(self.login_url, data=data)
        self.assertEqual(
            result.url
            , self.gn2_url+"/?import_collections=true"
            , "Login should have been successful")


def main(gn2, es):
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(TestLoginLocal(methodName="testLoginNonRegisteredUser", gn2_url=gn2, es_url=es))
    suite.addTest(TestLoginLocal(methodName="testLoginWithRegisteredUserBothRememberMeAndImportCollectionsFalse", gn2_url=gn2, es_url=es))
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        raise Exception("Required arguments missing")
    else:
        main(sys.argv[1], sys.argv[2])
