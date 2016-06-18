# Default settings file defines a single Flask process for the Python
# webserver running in developer mode with limited console
# output. Copy this file and run it from ./bin/genenetwork2 configfile
#
# Note that these settings are fetched in ./wqflask/utilities/tools.py
# which has support for overriding them through environment variables,
# e.g.
#
#   env LOG_SQL=True USE_REDIS=False ./bin/genenetwork2

import os
import sys

HOME=os.environ['HOME']
LOGFILE = HOME+"/genenetwork2.log"

# This is needed because Flask turns key errors into a
# 400 bad request response with no exception/log
TRAP_BAD_REQUEST_ERRORS = True

DB_URI = "mysql://gn2:mysql_password@localhost/db_webqtl_s"
SQLALCHEMY_DATABASE_URI = 'mysql://gn2:mysql_password@localhost/db_webqtl_s'

# http://pythonhosted.org/Flask-Security/configuration.html
SECURITY_CONFIRMABLE = True
SECURITY_TRACKABLE = True
SECURITY_REGISTERABLE = True
SECURITY_RECOVERABLE = True
SECURITY_EMAIL_SENDER = "no-reply@genenetwork.org"
SECURITY_POST_LOGIN_VIEW = "/thank_you"
SQLALCHEMY_POOL_RECYCLE = 3600

SERVER_PORT = 5003
SECRET_HMAC_CODE = '\x08\xdf\xfa\x93N\x80\xd9\\H@\\\x9f`\x98d^\xb4a;\xc6OM\x946a\xbc\xfc\x80:*\xebc'

# Behavioural settings (defaults) note that logger and log levels can
# be overridden at the module level and with enviroment settings
WEBSERVER_MODE  = 'DEV'     # Python webserver mode (DEBUG|DEV|PROD)
LOG_LEVEL       = 'WARNING' # Logger mode (DEBUG|INFO|WARNING|ERROR|CRITICAL)
DEBUG_LOG_LEVEL = 1         # Debug log level (0-5)
USE_REDIS       = True      # REDIS caching (note that redis will be phased out)
LOG_SQL         = 'False'   # Log SQL/backend calls

# Path overrides for Genenetwork
GENENETWORK_FILES = HOME+"/gn2_data"
PYLMM_COMMAND = str.strip(os.popen("which pylmm_redis").read())
PLINK_COMMAND = str.strip(os.popen("which plink2").read())
GEMMA_COMMAND = str.strip(os.popen("which gemma").read())
