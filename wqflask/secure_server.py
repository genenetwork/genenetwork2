from __future__ import print_function, division, absolute_import

from wqflask import app

from flask import Flask, render_template

# Setup mail
from flask.ext.mail import Mail
mail = Mail(app)

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

import sys
print("At startup, path is:", sys.path)


########
def tracefunc(frame, event, arg, indent=[0]):
    if event == "call":
        indent[0] += 2
        print("-" * indent[0] + "> call function", frame.f_code.co_name)
    elif event == "return":
        print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
        indent[0] -= 2
    return tracefunc

import sys
sys.settrace(tracefunc)
##############

#print("app.config is:", app.config)

if __name__ == '__main__':
    #create_user()
    app.run(host='0.0.0.0',
        port=app.config['SERVER_PORT'],
        use_debugger=False,
        threaded=True,
        use_reloader=True)
