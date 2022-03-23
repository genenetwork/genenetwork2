"""Tests for wqflask/wqflask/metadata_edits.py"""
import unittest
from unittest import mock

from wqflask import app


class MetadataEditsTest(unittest.TestCase):
    """Test Cases for MetadataEdits"""

    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @mock.patch("wqflask.metadata_edits.get_case_attributes")
    def test_show_case_attributes(self, mock_case_attrs):
        """Test that case attributes are displayed correctly"""
        mock_case_attrs.return_value = {
            "Condition (1)": "",
            "Tissue": "",
            "Age": "Cum sociis natoque penatibus et magnis dis",
            "Condition (4)": "Description A",
            "Condition (5)": "Description B",
        }
        response = self.app.get(
            "/datasets/case-attributes", follow_redirects=True
        ).data.decode()
        self.assertIn(
            "<td>Condition (1)</td><td>No description</td>", response
        )
        self.assertIn("<td>Tissue</td><td>No description</td>", response)
        self.assertIn(
            "<td>Age</td><td>Cum sociis natoque penatibus et magnis dis</td>",
            response,
        )
        self.assertIn("<td>Condition (4)</td><td>Description A</td>", response)
        self.assertIn("<td>Condition (5)</td><td>Description B</td>", response)
