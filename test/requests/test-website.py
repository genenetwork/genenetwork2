# Run with something like
#
#   env GN2_PROFILE=/home/wrk/opt/gn-latest ./bin/genenetwork2 ./etc/default_settings.py -c ../test/requests/test-website.py http://localhost:5003
#
# Mostly to pick up the Guix GN2_PROFILE and python modules

import requests as req
import sys

print "Mechanical Rob firing up..."

if len(sys.argv)<1:
    raise "Problem with arguments"

url = sys.argv[1]
print url

r = req.get(url)

print r
