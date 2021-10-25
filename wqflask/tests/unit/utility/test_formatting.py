import unittest
from utility.formatting import numify, commify


class TestFormatting(unittest.TestCase):
    """Test formatting numbers by numifying or commifying"""

    def test_numify(self):
        "Test that a number is correctly converted to a English readable string"
        self.assertEqual(numify(1, 'item', 'items'),
                         'one item')
        self.assertEqual(numify(2, 'book'), 'two')
        self.assertEqual(numify(2, 'book', 'books'), 'two books')
        self.assertEqual(numify(0, 'book', 'books'), 'zero books')
        self.assertEqual(numify(0), 'zero')
        self.assertEqual(numify(5), 'five')
        self.assertEqual(numify(14, 'book', 'books'), '14 books')
        self.assertEqual(numify(999, 'book', 'books'), '999 books')
        self.assertEqual(numify(1000000, 'book', 'books'), '1,000,000 books')
        self.assertEqual(numify(1956), '1956')

    def test_commify(self):
        "Test that commas are added correctly"
        self.assertEqual(commify(1), '1')
        self.assertEqual(commify(123), '123')
        self.assertEqual(commify(1234), '1234')
        self.assertEqual(commify(12345), '12,345')
        self.assertEqual(commify(1234567890), '1,234,567,890')
        self.assertEqual(commify(123.0), '123.0')
        self.assertEqual(commify(1234.5), '1234.5')
        self.assertEqual(commify(1234.56789), '1234.56789')
        self.assertEqual(commify(123456.789), '123,456.789')
        self.assertEqual(commify(None), None)
