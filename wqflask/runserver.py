# Starts the webserver with the ./bin/genenetwork2 command
#
# Please note, running with host set externally below combined with
# debug mode is a security risk unless you have a firewall setup, e.g.
#
# /sbin/iptables -A INPUT -p tcp -i eth0 -s ! 71.236.239.43 --dport 5003 -j DROP

from wqflask import app

import logging
import utility.logger
logger = utility.logger.getLogger(__name__ )

BLUE  = '\033[94m'
GREEN = '\033[92m'
BOLD  = '\033[1m'
ENDC  = '\033[0m'

import os
app.config['SECRET_KEY'] = os.urandom(24)

from utility.tools import WEBSERVER_MODE,get_setting_int,get_setting

port = get_setting_int("SERVER_PORT")

print("GN2 API server URL is ["+BLUE+get_setting("GN_SERVER_URL")+ENDC+"]")

import requests
page = requests.get(get_setting("GN_SERVER_URL"))
if page.status_code != 200:
    raise Exception("API server not found!")

print("GN2 is running. Visit %s[http://localhost:%s/%s](%s)" % (BLUE,str(port),ENDC,get_setting("WEBSERVER_URL")))

werkzeug_logger = logging.getLogger('werkzeug')

if WEBSERVER_MODE == 'DEBUG':
    app.run(host='0.0.0.0',
            port=port,
            debug=True,
            use_debugger=False,
            threaded=False,
            processes=0,
            use_reloader=True)
elif WEBSERVER_MODE == 'DEV':
    werkzeug_logger.setLevel(logging.WARNING)
    app.run(host='0.0.0.0',
            port=port,
            debug=False,
            use_debugger=False,
            threaded=False,
            processes=0,
            use_reloader=True)
else: # staging/production modes
    app.run(host='0.0.0.0',
            port=port,
            debug=False,
            use_debugger=False,
            threaded=True,
            processes=8,
            use_reloader=True)
