import unittest

from base.GeneralObject import GeneralObject


class TestGeneralObjectTests(unittest.TestCase):
    """
    Test the GeneralObject base class
    """

    def test_object_contents(self):
        """Test whether base contents are stored properly"""
        test_obj = GeneralObject("a", "b", "c")
        self.assertEqual("abc", ''.join(test_obj.contents))

    def test_object_dict(self):
        """Test whether the base class is printed properly"""
        test_obj = GeneralObject("a", name="test", value=1)
        self.assertEqual(str(test_obj), "value = 1\nname = test\n")
        self.assertEqual(
            repr(test_obj), "value = 1\nname = test\ncontents = ['a']\n")
