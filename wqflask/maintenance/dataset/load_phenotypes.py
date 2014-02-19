import sys

import utilities

def main(argv):
    config = utilities.get_config(argv[1])
    print "config:"
    for item in config.items('config'):
        print "\t%s" % (str(item))

if __name__ == "__main__":
    print "command line arguments:\n\t%s" % sys.argv
    main(sys.argv)
    print "exit successfully"
