# Run with something like
#
#   env GN2_PROFILE=/home/wrk/opt/gn-latest ./bin/genenetwork2 ./etc/default_settings.py -c ../test/requests/test-website.py http://localhost:5003
#
# Mostly to pick up the Guix GN2_PROFILE and python modules
from __future__ import print_function
import argparse
from link_checker import check_links
from mapping_tests import check_mapping
from navigation_tests import check_navigation
from main_web_functionality import check_main_web_functionality

print("Mechanical Rob firing up...")

def run_all(args_obj, parser):
    print("")
    print("Running all tests.")
    check_main_web_functionality(args_obj, parser)
    check_links(args_obj, parser)
    check_mapping(args_obj, parser)
    # TODO: Add other functions as they are created.

def print_help(args_obj, parser):
    print(parser.format_help())

def dummy(args_obj, parser):
    print("Not implemented yet.")


desc = """
This is Mechanical-Rob - an automated web server tester for
                         Genenetwork.org
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument("-d", "--database", metavar="DB", type=str
                    , default="db_webqtl_s"
                    , help="Use database (default db_webqtl_s)")

parser.add_argument("host", metavar="HOST", type=str
                    , default="http://localhost:5003"
                    , help="The url to the web server")

parser.add_argument("-a", "--all", dest="accumulate", action="store_const"
                    , const=run_all, default=print_help
                    , help="Runs all tests.")

parser.add_argument("-l", "--link-checker", dest="accumulate"
                    , action='store_const', const=check_links, default=print_help
                    , help="Checks for dead links.")

parser.add_argument("-f", "--main-functionality", dest="accumulate"
                    , action='store_const', const=check_main_web_functionality
                    , default=print_help
                    , help="Checks for main web functionality.")

parser.add_argument("-m", "--mapping", dest="accumulate"
                    , action="store_const", const=check_mapping, default=print_help
                    , help="Checks for mapping.")

parser.add_argument("-n", "--navigation", dest="accumulate"
                    , action="store_const", const=check_navigation, default=print_help
                    , help="Checks for navigation.")

# parser.add_argument("-s", "--skip-broken", dest="accumulate"
#                     , action="store_const", const=dummy, default=print_help
#                     , help="Skip tests that are known to be broken.")

args = parser.parse_args()
# print("The arguments object: ", args)

args.accumulate(args, parser)
