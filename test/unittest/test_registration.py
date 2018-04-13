# Run test with something like
#
# env GN2_PROFILE=~/opt/gn-latest GENENETWORK_FILES=$HOME/gn2_data ./bin/genenetwork2 ./etc/default_settings.py -c ../test/unittest/test_registration.py
#

import unittest
import mock.es_double as es
from wqflask.user_manager import RegisterUser

class TestRegisterUser(unittest.TestCase):
    def setUp(self):
        self.es = es.ESDouble()

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
        self.assertEqual(len(result.errors), 0, "Errors were not expected")

if __name__ == "__main__":
    unittest.main()
