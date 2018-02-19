import sys
from test_login_local import TestLoginLocal
from test_registration import TestRegistration
from unittest import TestSuite, TextTestRunner, TestLoader

test_cases = [
    TestLoginLocal,
    TestRegistration
]

def suite(gn2_url, es_url):
    the_suite = TestSuite()
    for case in test_cases:
        the_suite.addTests(initTest(case, gn2_url, es_url))
    return the_suite

def initTest(klass, gn2_url, es_url):
    loader = TestLoader()
    methodNames = loader.getTestCaseNames(klass)
    return [klass(mname, gn2_url, es_url) for mname in methodNames]

def main(gn2_url, es_url):
    runner = TextTestRunner()
    runner.run(suite(gn2_url, es_url))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise Exception("Required arguments missing:\n\tTry running `run-integration-test.py <gn2-url> <es-url>`")
    else:
        main(sys.argv[1], sys.argv[2])
