"""Test Core Stats"""

import unittest

from utility.corestats import Stats


class TestChunks(unittest.TestCase):
    "Test Utility method for chunking"

    def setUp(self):
        self.stat_test = Stats((x for x in range(1, 11)))

    def test_stats_sum(self):
        """ Test sequence sum """
        self.assertEqual(self.stat_test.sum(), 55)
        self.stat_test = Stats([])
        self.assertEqual(self.stat_test.sum(), None)

    def test_stats_count(self):
        """ Test sequence count """
        self.assertEqual(self.stat_test.count(), 10)
        self.stat_test = Stats([])
        self.assertEqual(self.stat_test.count(), 0)

    def test_stats_min(self):
        """ Test min value in sequence"""
        self.assertEqual(self.stat_test.min(), 1)
        self.stat_test = Stats([])
        self.assertEqual(self.stat_test.min(), None)

    def test_stats_max(self):
        """ Test max value in sequence """
        self.assertEqual(self.stat_test.max(), 10)
        self.stat_test = Stats([])
        self.assertEqual(self.stat_test.max(), None)

    def test_stats_avg(self):
        """ Test avg of sequence """
        self.assertEqual(self.stat_test.avg(), 5.5)
        self.stat_test = Stats([])
        self.assertEqual(self.stat_test.avg(), None)

    def test_stats_stdev(self):
        """ Test standard deviation of sequence """
        self.assertEqual(self.stat_test.stdev(), 3.0276503540974917)
        self.stat_test = Stats([])
        self.assertEqual(self.stat_test.stdev(), None)

    def test_stats_percentile(self):
        """ Test percentile of sequence """
        self.assertEqual(self.stat_test.percentile(20), 3.0)
        self.assertEqual(self.stat_test.percentile(101), None)
        self.stat_test = Stats([])
        self.assertEqual(self.stat_test.percentile(20), None)
