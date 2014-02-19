import sys

import utilities

def main(argv):
    config = utilities.get_config(argv[1])
    print config.items('config')

if __name__ == "__main__":
    print "command line arguments: %s" % sys.argv
    main(sys.argv)
    print "exit successfully"
