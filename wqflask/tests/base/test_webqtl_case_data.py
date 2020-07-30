"""Tests for wqflask/base/webqtlCaseData.py"""
import unittest

from wqflask import app  # Required because of utility.tools in webqtlCaseData.py
from base.webqtlCaseData import webqtlCaseData

class TestWebqtlCaseData(unittest.TestCase):
    """Tests for WebqtlCaseData class"""

    def setUp(self):
        self.w = webqtlCaseData(name="Test",
                           value=0,
                           variance=0.0,
                           num_cases=10,
                           name2="Test2")

    def test_webqtl_case_data_repr(self):
        self.assertEqual(
            repr(self.w),
            "<webqtlCaseData> value=0.000 variance=0.000 ndata=10 name=Test name2=Test2"
        )

    def test_class_outlier(self):
        self.assertEqual(self.w.class_outlier, "")

    def test_display_value(self):
        self.assertEqual(self.w.display_value, "0.000")
        self.w.value = None
        self.assertEqual(self.w.display_value, "x")

    def test_display_variance(self):
        self.assertEqual(self.w.display_variance, "0.000")
        self.w.variance = None
        self.assertEqual(self.w.display_variance, "x")

    def test_display_num_cases(self):
        self.assertEqual(self.w.display_num_cases, "10")
        self.w.num_cases = None
        self.assertEqual(self.w.display_num_cases, "x")
