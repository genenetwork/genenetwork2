import logging
import unittest
from wqflask import app
from utility.elasticsearch_tools import get_elasticsearch_connection, get_user_by_unique_column
from elasticsearch import Elasticsearch, TransportError

class ParametrizedTest(unittest.TestCase):

    def __init__(self, methodName='runTest', gn2_url="http://localhost:5003", es_url="localhost:9200"):
        super(ParametrizedTest, self).__init__(methodName=methodName)
        self.gn2_url = gn2_url
        self.es_url = es_url

    def setUp(self):
        self.es = get_elasticsearch_connection()
        self.es_cleanup = []

        es_logger = logging.getLogger("elasticsearch")
        es_logger.setLevel(app.config.get("LOG_LEVEL"))
        es_logger.addHandler(
            logging.FileHandler("/tmp/es_TestRegistrationInfo.log"))
        es_trace_logger = logging.getLogger("elasticsearch.trace")
        es_trace_logger.addHandler(
            logging.FileHandler("/tmp/es_TestRegistrationTrace.log"))

    def tearDown(self):
        from time import sleep
        self.es.delete_by_query(
            index="users"
            , doc_type="local"
            , body={"query":{"match":{"email_address":"test@user.com"}}})
        sleep(1)
