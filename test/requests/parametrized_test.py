import logging
import unittest
from elasticsearch import Elasticsearch, TransportError

class ParametrizedTest(unittest.TestCase):

    def __init__(self, methodName='runTest', gn2_url="http://localhost:5003", es_url="localhost:9200"):
        super(ParametrizedTest, self).__init__(methodName=methodName)
        self.gn2_url = gn2_url
        self.es_url = es_url

    def setUp(self):
        self.es = Elasticsearch([self.es_url])
        self.es_cleanup = []

        es_logger = logging.getLogger("elasticsearch")
        es_logger.addHandler(
            logging.FileHandler("/tmp/es_TestRegistrationInfo.log"))
        es_trace_logger = logging.getLogger("elasticsearch.trace")
        es_trace_logger.addHandler(
            logging.FileHandler("/tmp/es_TestRegistrationTrace.log"))

    def tearDown(self):
        self.es.delete_by_query(
            index="users"
            , doc_type="local"
            , body={"query":{"match":{"email_address":"test@user.com"}}})
