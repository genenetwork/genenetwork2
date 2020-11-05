import unittest
import re
from unittest import mock
from wqflask.show_trait.SampleList import natural_sort


class TestSampleList(unittest.TestCase):
    def test_natural_sort(self):
        "Sort the list into natural alphanumeric order."

        characters_list = ["z", "f", "q", "s", "t", "a", "g"]
        names_list = ["temp1", "publish", "Sample", "Dataset"]

        natural_sort(characters_list)
        natural_sort(names_list)

        self.assertEqual(characters_list, ["a", "f", "g", "q", "s", "t", "z"])
        self.assertEqual(names_list, ["Dataset", "Sample", "publish", "temp1"])
