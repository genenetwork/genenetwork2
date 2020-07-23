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
        self.assertEqual(len(test_obj), 0)

    def test_object_dict(self):
        """Test whether the base class is printed properly"""
        test_obj = GeneralObject("a", name="test", value=1)
        self.assertEqual(str(test_obj), "value = 1\nname = test\n")
        self.assertEqual(
            repr(test_obj), "value = 1\nname = test\ncontents = ['a']\n")
        self.assertEqual(len(test_obj), 2)
        self.assertEqual(getattr(test_obj, "value"), 1)
        self.assertEqual(test_obj["value"], 1)
        test_obj["test"] = 1
        self.assertEqual(test_obj["test"], 1)
