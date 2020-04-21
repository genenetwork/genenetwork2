import sys
import requests
from parametrized_test import ParametrizedTest

class TestRegistration(ParametrizedTest):

    def tearDown(self):
        for item in self.es_cleanup:
            self.es.delete(index="users", doc_type="local", id=item["_id"])

    def testRegistrationPage(self):
        if self.es.ping():
            data = {
                "email_address": "test@user.com",
                "full_name": "Test User",
                "organization": "Test Organisation",
                "password": "test_password",
                "password_confirm": "test_password"
            }
            requests.post(self.gn2_url+"/n/register", data)
            response = self.es.search(
                index="users"
                , doc_type="local"
                , body={
                    "query": {"match": {"email_address": "test@user.com"}}})
            self.assertEqual(len(response["hits"]["hits"]), 1)
        else:
            self.skipTest("The elasticsearch server is down")

def main(gn2, es):
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(TestRegistration(methodName="testRegistrationPage", gn2_url=gn2, es_url=es))
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise Exception("Required arguments missing")
    else:
        main(sys.argv[1], sys.argv[2])
