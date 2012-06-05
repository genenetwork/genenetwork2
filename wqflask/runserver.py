from wqflask import app

# Please note, running with host set externally below combined with debug mode
# is a big security no-no
# Unless you have a firewall setup
#
# Something like /sbin/iptables -A INPUT -p tcp -i eth0 -s ! 71.236.239.43 --dport 5000 -j DROP
# should do the trick
#
# You'll probably have to firewall the main port and the
#
# For more info see: http://www.cyberciti.biz/faq/iptables-block-port/

import logging
logging.basicConfig(filename="/tmp/flask_gn_log", level=logging.INFO)

_log = logging.getLogger("search")
_ch = logging.StreamHandler()
_log.addHandler(_ch)

app.run(host='0.0.0.0',
        use_debugger=False,
        use_reloader=True)
