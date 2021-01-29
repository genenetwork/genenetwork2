import unittest
from utility.type_checking import is_float
from utility.type_checking import is_int
from utility.type_checking import is_str
from utility.type_checking import get_float
from utility.type_checking import get_int
from utility.type_checking import get_string


class TestTypeChecking(unittest.TestCase):
    def test_is_float(self):
        floats = [2, 1.2, '3.1']
        not_floats = ["String", None, [], ()]
        for flt in floats:
            results = is_float(flt)
            self.assertTrue(results)
        for nflt in not_floats:
            results = is_float(nflt)
            self.assertFalse(results)

    def test_is_int(self):
        int_values = [1, 1.1]
        not_int_values = ["string", None, [], "1.1"]
        for int_val in int_values:
            results = is_int(int_val)
            self.assertTrue(results)
        for not_int in not_int_values:
            results = is_int(not_int)
            self.assertFalse(results)

    def test_is_str(self):
        string_values = [1, False, [], {}, "string_value"]
        falsey_values = [None]
        for string_val in string_values:
            results = is_str(string_val)
            self.assertTrue(results)
        for non_string in falsey_values:
            results = is_str(non_string)
            self.assertFalse(results)

    def test_get_float(self):
        vars_object = {"min_value": "12"}
        results = get_float(vars_object, "min_value")
        self.assertEqual(results, 12.0)

    def test_get_int(self):
        vars_object = {"lx_value": "1"}
        results = get_int(vars_object, "lx_value")
        self.assertEqual(results, 1)

    def test_get_string(self):
        string_object = {"mx_value": 1}
        results = get_string(string_object, "mx_value")
        self.assertEqual(results, "1")