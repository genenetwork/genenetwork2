"""Test chunking"""

import unittest

from utility.chunks import divide_into_chunks


class TestChunks(unittest.TestCase):
    "Test Utility method for chunking"
    def test_divide_into_chunks(self):
        "Check that a list is chunked correctly"
        self.assertEqual(divide_into_chunks([1, 2, 7, 3, 22, 8, 5, 22, 333], 3),
                         [[1, 2, 7], [3, 22, 8], [5, 22, 333]])
        self.assertEqual(divide_into_chunks([1, 2, 7, 3, 22, 8, 5, 22, 333], 4),
                         [[1, 2, 7], [3, 22, 8], [5, 22, 333]])
        self.assertEqual(divide_into_chunks([1, 2, 7, 3, 22, 8, 5, 22, 333], 5),
                         [[1, 2], [7, 3], [22, 8], [5, 22], [333]])
        self.assertEqual(divide_into_chunks([], 5),
                         [[]])
