# Default settings file defines a single Flask process for the Python
# webserver running in developer mode with limited console
# output. Copy this file and run it from ./bin/genenetwork2 configfile
#
# Note that these settings are fetched in ./wqflask/utilities/tools.py
# which has support for overriding them through environment variables,
# e.g.
#
#   env LOG_SQL=True USE_REDIS=False ./bin/genenetwork2
#   env LOG_LEVEL=DEBUG ./bin/genenetwork2 ~/gn2_settings.py
#
# Note also that in the near future we will additionally fetch
# settings from a JSON file
#
# Note that values for False and 0 have to be strings here - otherwise
# Flask won't pick them up

import os
import sys

SQL_URI = "mysql://gn2:mysql_password@localhost/db_webqtl_s"
SQLALCHEMY_DATABASE_URI = 'mysql://gn2:mysql_password@localhost/db_webqtl_s'
SQLALCHEMY_POOL_RECYCLE = 3600
GN_SERVER_URL = "http://localhost:8880/"

# ---- Flask configuration (see website)
TRAP_BAD_REQUEST_ERRORS = True
SECURITY_CONFIRMABLE = True
SECURITY_TRACKABLE = True
SECURITY_REGISTERABLE = True
SECURITY_RECOVERABLE = True
SECURITY_EMAIL_SENDER = "no-reply@genenetwork.org"
SECURITY_POST_LOGIN_VIEW = "/thank_you"

SERVER_PORT = 5003
SECRET_HMAC_CODE = '\x08\xdf\xfa\x93N\x80\xd9\\H@\\\x9f`\x98d^\xb4a;\xc6OM\x946a\xbc\xfc\x80:*\xebc'

# ---- Behavioural settings (defaults) note that logger and log levels can
#      be overridden at the module level and with enviroment settings
WEBSERVER_MODE  = 'DEV'     # Python webserver mode (DEBUG|DEV|PROD)
WEBSERVER_BRANDING = None   # Set the branding (nyi)
WEBSERVER_DEPLOY = None     # Deployment specifics (nyi)

LOG_LEVEL       = 'WARNING' # Logger mode (DEBUG|INFO|WARNING|ERROR|CRITICAL)
LOG_LEVEL_DEBUG = '0'       # logger.debugf log level (0-5, 5 = show all)
LOG_SQL         = 'False'   # Log SQL/backend and GN_SERVER calls
LOG_SQLALCHEMY  = 'False'
LOG_BENCH       = True      # Log bench marks

USE_REDIS       = True      # REDIS caching (note that redis will be phased out)
USE_GN_SERVER   = 'False'   # Use GN_SERVER SQL calls

# ---- Path overrides for Genenetwork
# TMPDIR is normally picked up from the environment
HOME=os.environ['HOME']
LOGFILE = HOME+"/genenetwork2.log"
GENENETWORK_FILES = HOME+"/gn2_data"  # base dir for all static data files
LOCAL_PRIVATE_FILES = HOME+"/gn2_private_data" # private static data files

# ---- GN2 Executables
PYLMM_COMMAND = str.strip(os.popen("which pylmm_redis").read())
PLINK_COMMAND = str.strip(os.popen("which plink2").read())
GEMMA_COMMAND = str.strip(os.popen("which gemma").read())


BIODALLIANCE_PATH = os.environ['HOME']+"/dalliance"
