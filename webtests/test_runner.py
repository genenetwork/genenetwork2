from __future__ import absolute_import, division, print_function

import unittest
import doctest
import glob

#tests = ("correlation_test",
#         "correlation_matrix_test",
#         "marker_regression_test")


def main():
    tests = glob.glob("*_test.py")
    
    suite = unittest.TestSuite()
    
    for testname in tests:
        test = testname.rsplit(".", 1)[0]
        print("Test is:", test)
        mod = __import__(test)
        suite.addTest(doctest.DocTestSuite(mod))
        
    runner = unittest.TextTestRunner()
    runner.run(suite)
    
if __name__ == '__main__':
    main()