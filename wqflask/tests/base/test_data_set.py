"""Tests for wqflask/base/data_set.py"""

import unittest
import mock

from wqflask import app
from data import gen_menu_json
from base.data_set import DatasetType


class TestDataSetTypes(unittest.TestCase):
    """Tests for the DataSetType class"""

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @mock.patch('base.data_set.g')
    def test_data_set_type(self, db_mock):
        """Test that DatasetType returns correctly if the Redis Instance is not empty
        and the name variable exists in the dictionary

        """
        with app.app_context():
            db_mock.get = mock.Mock()
            redis_mock = mock.Mock()
            redis_mock.get.return_value = """
            {
                "AD-cases-controls-MyersGeno": "Geno",
                "AD-cases-controls-MyersPublish": "Publish",
                "AKXDGeno": "Geno",
                "AXBXAGeno": "Geno",
                "AXBXAPublish": "Publish",
                "Aging-Brain-UCIPublish": "Publish",
                "All Phenotypes": "Publish",
                "B139_K_1206_M": "ProbeSet",
                "B139_K_1206_R": "ProbeSet"
            }
            """
            self.assertEqual(DatasetType(redis_mock)
                             ("All Phenotypes"), "Publish")

    @mock.patch('base.data_set.requests.get')
    def test_data_set_type_with_empty_redis(self, request_mock):
        """Test that DatasetType returns correctly if the Redis Instance is empty and
        the name variable exists in the dictionary

        """
        with app.app_context():
            request_mock.return_value.content = gen_menu_json
            redis_mock = mock.Mock()
            redis_mock.get.return_value = None
            data_set = DatasetType(redis_mock)
            self.assertEqual(data_set("BXDGeno"), "Geno")
            self.assertEqual(data_set("BXDPublish"), "Publish")
            self.assertEqual(data_set("HLC_0311"), "ProbeSet")
