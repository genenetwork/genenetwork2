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
        self.assertEqual(str(test_obj), "name = test\nvalue = 1\n")
        self.assertEqual(
            repr(test_obj), "contents = ['a']\nname = test\nvalue = 1\n")
        self.assertEqual(len(test_obj), 2)
        self.assertEqual(test_obj["value"], 1)
        test_obj["test"] = 1
        self.assertEqual(test_obj["test"], 1)

    def test_get_attribute(self):
        "Test that getattr works"
        test_obj = GeneralObject("a", name="test", value=1)
        self.assertEqual(getattr(test_obj, "value", None), 1)
        self.assertEqual(getattr(test_obj, "non-existent", None), None)

    def test_object_comparisons(self):
        "Test that 2 objects of the same length are equal"
        test_obj1 = GeneralObject("a", name="test", value=1)
        test_obj2 = GeneralObject("b", name="test2", value=2)
        test_obj3 = GeneralObject("a", name="test", x=1, y=2)
        self.assertTrue(test_obj1 == test_obj2)
        self.assertFalse(test_obj1 == test_obj3)
