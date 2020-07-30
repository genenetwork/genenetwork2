#! /bin/bash
#
# PLEASE DO NOT CHANGE THIS FILE - copy it elsewhere to run
#
# Run with GN2_PROFILE and SERVER_PORT overrides, e.g.
#
#   env GN2_PROFILE=/usr/local/guix-profiles/gn-latest SERVER_PORT=5010 scripts/run_debug.sh

[ -z $GN2_PROFILE ] && export GN2_PROFILE=/usr/local/guix-profiles/gn-latest
[ -z $SERVER_PORT ] && export SERVER_PORT=5010

echo Running on port $SERVER_PORT from $GN2_PROFILE 

cwd=`pwd`
echo Running source from $cwd

mkdir -p ~/tmp

env TMPDIR=~/tmp WEBSERVER_MODE=DEBUG LOG_LEVEL=DEBUG GENENETWORK_FILES=/export/data/genenetwork/genotype_files/ SQL_URI=mysql://webqtlout:webqtlout@localhost/db_webqtl ./bin/genenetwork2 etc/default_settings.py -gunicorn-dev 

