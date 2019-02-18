# Starts the webserver with the ./bin/genenetwork2 command
#
# This uses Werkzeug WSGI, see ./run_gunicorn.py for the alternative
#
# Please note, running with host set externally below combined with
# debug mode is a security risk unless you have a firewall setup, e.g.
#
# /sbin/iptables -A INPUT -p tcp -i eth0 -s ! 71.236.239.43 --dport 5003 -j DROP

from wqflask import app

import logging
import utility.logger
logger = utility.logger.getLogger(__name__ )

import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

BLUE  = '\033[94m'
GREEN = '\033[92m'
BOLD  = '\033[1m'
ENDC  = '\033[0m'

from utility.startup_config import app_config

app_config()

werkzeug_logger = logging.getLogger('werkzeug')

from utility.tools import WEBSERVER_MODE, SERVER_PORT

if WEBSERVER_MODE == 'DEBUG':
    app.run(host='0.0.0.0',
            port=SERVER_PORT,
            debug=True,
            use_debugger=False,
            threaded=False,
            processes=0,
            use_reloader=True)
elif WEBSERVER_MODE == 'DEV':
    werkzeug_logger.setLevel(logging.WARNING)
    app.run(host='0.0.0.0',
            port=SERVER_PORT,
            debug=False,
            use_debugger=False,
            threaded=False,
            processes=0,
            use_reloader=True)
else: # staging/production modes
    app.run(host='0.0.0.0',
            port=SERVER_PORT,
            debug=False,
            use_debugger=False,
            threaded=True,
            processes=0,
            use_reloader=True)
