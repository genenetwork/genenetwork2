import sys
import requests

class TestRegistration(ParametrizedTest):


    def testRegistrationPage(self):
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
