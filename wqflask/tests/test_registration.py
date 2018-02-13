import unittest
import es_double
import wqflask.user_manager
from wqflask.user_manager import RegisterUser

class TestRegisterUser(unittest.TestCase):
    def setUp(self):
        # Mock elasticsearch
        self.es = es_double.ESDouble()

        # Patch method
        wqflask.user_manager.basic_info = lambda : {"basic_info": "some info"}

    def tearDown(self):
        self.es = None

    def testRegisterUserWithNoData(self):
        data = {}
        result = RegisterUser(data)
        self.assertNotEqual(len(result.errors), 0, "Data was not provided. Error was expected")

    def testRegisterUserWithNoEmail(self):
        data = {
            "email_address": ""
            , "full_name": "A.N. Other"
            , "organization": "Some Organisation"
            , "password": "testing"
            , "password_confirm": "testing"
            , "es_connection": self.es
        }

        result = RegisterUser(data)
        self.assertNotEqual(len(result.errors), 0, "Email not provided. Error was expected")

    def testRegisterUserWithNoName(self):
        data = {
            "email_address": "user@example.com"
            , "full_name": ""
            , "organization": "Some Organisation"
            , "password": "testing"
            , "password_confirm": "testing"
            , "es_connection": self.es
        }

        result = RegisterUser(data)
        self.assertNotEqual(len(result.errors), 0, "Name not provided. Error was expected")

    def testRegisterUserWithNoOrganisation(self):
        data = {
            "email_address": "user@example.com"
            , "full_name": "A.N. Other"
            , "organization": ""
            , "password": "testing"
            , "password_confirm": "testing"
            , "es_connection": self.es
        }
        
        result = RegisterUser(data)
        self.assertEqual(len(result.errors), 0, "Organisation not provided. Error not expected")

    def testRegisterUserWithShortOrganisation(self):
        data = {
            "email_address": "user@example.com"
            , "full_name": "A.N. Other"
            , "organization": "SO"
            , "password": "testing"
            , "password_confirm": "testing"
            , "es_connection": self.es
        }
        
        result = RegisterUser(data)
        self.assertNotEqual(len(result.errors), 0, "Organisation name too short. Error expected")

    def testRegisterUserWithNoPassword(self):
        data = {
            "email_address": "user@example.com"
            , "full_name": "A.N. Other"
            , "organization": "Some Organisation"
            , "password": None
            , "password_confirm": None
            , "es_connection": self.es
        }

        result = RegisterUser(data)
        self.assertNotEqual(len(result.errors), 0, "Password not provided. Error was expected")

    def testRegisterUserWithNonMatchingPasswords(self):
        data = {
            "email_address": "user@example.com"
            , "full_name": "A.N. Other"
            , "organization": "Some Organisation"
            , "password": "testing"
            , "password_confirm": "stilltesting"
            , "es_connection": self.es
        }

        result = RegisterUser(data)
        self.assertNotEqual(len(result.errors), 0, "Password mismatch. Error was expected")

    def testRegisterUserWithCorrectData(self):
        data = {
            "email_address": "user@example.com"
            , "full_name": "A.N. Other"
            , "organization": "Some Organisation"
            , "password": "testing"
            , "password_confirm": "testing"
            , "es_connection": self.es
        }
        result = RegisterUser(data)
        self.assertEqual(len(result.errors), 0, "All data items provided. Errors were not expected")

if __name__ == "__main__":
    unittest.main()
