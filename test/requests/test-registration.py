import sys
import unittest
import requests
import logging
from elasticsearch import Elasticsearch, TransportError
#from utility.tools import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT

GN2_SERVER = None
ES_SERVER = None

class TestRegistration(unittest.TestCase):
    

    def setUp(self):
        self.url = GN2_SERVER+"/n/register"
        self.es = Elasticsearch([ES_SERVER])
        self.es_cleanup = []

        es_logger = logging.getLogger("elasticsearch")
        es_logger.addHandler(
            logging.FileHandler("/tmp/es_TestRegistrationInfo.log"))
        es_trace_logger = logging.getLogger("elasticsearch.trace")
        es_trace_logger.addHandler(
            logging.FileHandler("/tmp/es_TestRegistrationTrace.log"))

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
            requests.post(self.url, data)
            response = self.es.search(
                index="users"
                , doc_type="local"
                , body={
                    "query": {"match": {"email_address": "test@user.com"}}})
            self.assertEqual(len(response["hits"]["hits"]), 1)
            self.es_cleanup.append(response["hits"]["hits"][0])
        else:
            self.skipTest("The elasticsearch server is down")

def main():
    suite = unittest.TestSuite()
    suite.addTest(TestRegistration("testRegistrationPage"))
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == "__main__":
    GN2_SERVER = sys.argv[1]
    ES_SERVER = sys.argv[2]
    main()
