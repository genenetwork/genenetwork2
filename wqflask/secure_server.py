from __future__ import absolute_import, division, print_function

import time
import sys

from wqflask import app

from flask import Flask, render_template

import redis
Redis = redis.StrictRedis()

# Setup mail
#from flask.ext.mail import Mail
#mail = Mail(app)

from wqflask.model import *

# Create a user to test with
##@app.before_first_request
#def create_user():
#    db.create_all()
#    user_datastore.create_user(email='matt@example.com', password='notebook')
#    db.session.commit()

import logging
file_handler = logging.FileHandler(app.config['LOGFILE'])
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

import logging_tree
logging_tree.printout()

#import sys
#print("At startup, path is:", sys.path)

from werkzeug.contrib.fixers import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app)

#print("app.config is:", app.config)



def check_send_mail_running():
    """Ensure send_mail.py is running before we start the site
    
    It would be really easy to accidentally run the site
    without our mail program running
    This will make sure our mail program is running...or at least recently run...

    """
    error_msg = "Make sure your are running send_mail.py"
    send_mail_ping = Redis.get("send_mail:ping")
    print("send_mail_ping is:", send_mail_ping)
    if not send_mail_ping:
        sys.exit(error_msg)

    last_ping = time.time() - float(send_mail_ping)
    if not (0 < last_ping < 100):
        sys.exit(error_msg)


    print("send_mail.py seems to be running...")


if __name__ == '__main__':
    #create_user()



    check_send_mail_running()


    app.run(host='0.0.0.0',
        port=app.config['SERVER_PORT'],
        use_debugger=False,
        threaded=True,
        use_reloader=True)
