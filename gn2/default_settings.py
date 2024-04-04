# Default settings file defines a single Flask process for the Python
# webserver running in developer mode with limited console
# output. Copy this file and run it from ./bin/genenetwork2 configfile
#
# Note: these settings are fetched in ./wqflask/utilities/tools.py
# which has support for overriding them through environment variables,
# e.g.
#
#   env LOG_SQL=True USE_REDIS=False ./bin/genenetwork2
#   env LOG_LEVEL=DEBUG ./bin/genenetwork2 ~/gn2_settings.py
#
# Typically you need to set GN2_PROFILE too.
#
# Note also that in the near future we will additionally fetch
# settings from a JSON file
#
# Note: values for False and 0 have to be strings here - otherwise
# Flask won't pick them up
#
# For GNU Guix deployment also check the paths in
#
#  ~/.guix-profile/lib/python3.8/site-packages/genenetwork2-2.0-py2.7.egg/gn2/default_settings.py

import os
import sys

GN_VERSION = "3.12-rc1" # sync up with GN2

SECRET_KEY = ""

# Redis
REDIS_URL = "redis://:@localhost:6379/0"

# gn2-proxy
GN2_PROXY = "http://localhost:8080"

# GN PROXY
GN_PROXY_URL="https://genenetwork.org/gn3-proxy/"

# ---- MySQL

SQL_URI = "mysql://gn2:mysql_password@localhost/db_webqtl_s"
SQL_ALCHEMY_POOL_RECYCLE = 3600
GN_SERVER_URL = "http://localhost:8880/api/" # REST API server
AUTH_SERVER_URL="http://localhost:9094/"
GN2_BASE_URL = "http://genenetwork.org/" # to pick up REST API
GN2_BRANCH_URL = GN2_BASE_URL

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

GITHUB_CLIENT_ID = "UNKNOWN"
GITHUB_CLIENT_SECRET = "UNKNOWN"
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_API_URL = "https://api.github.com/user"

ORCID_CLIENT_ID = "UNKNOWN"
ORCID_CLIENT_SECRET = "UNKNOWN"
ORCID_AUTH_URL = "https://orcid.org/oauth/authorize"
ORCID_TOKEN_URL = "https://orcid.org/oauth/token"

ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = '9200'

SMTP_CONNECT = "localhost"
SMTP_USERNAME = "UNKNOWN"
SMTP_PASSWORD = "UNKNOWN"


# ---- Behavioural settings (defaults) note that logger and log levels can
#      be overridden at the module level and with enviroment settings
WEBSERVER_MODE = 'DEV'     # Python webserver mode (DEBUG|DEV|PROD)
WEBSERVER_BRANDING = None   # Set the branding (nyi)
WEBSERVER_DEPLOY = None     # Deployment specifics (nyi)
WEBSERVER_URL = "http://localhost:" + str(SERVER_PORT) + "/" # external URL

LOG_LEVEL = 'WARNING' # Logger mode (DEBUG|INFO|WARNING|ERROR|CRITICAL)
LOG_LEVEL_DEBUG = '0'       # logger.debugf log level (0-5, 5 = show all)
LOG_SQL = 'False'   # Log SQL/backend and GN_SERVER calls
LOG_SQL_ALCHEMY = 'False'
LOG_BENCH = True      # Log bench marks

USE_REDIS = True      # REDIS caching (note that redis will be phased out)
USE_GN_SERVER = 'False'   # Use GN_SERVER SQL calls
HOME = os.environ['HOME']

# ---- Default locations
# base dir for all static data files
GENENETWORK_FILES = HOME + "/genotype_files"

# ---- Path overrides for Genenetwork - the defaults are normally
#      picked up from Guix or in the HOME directory

# TMPDIR is normally picked up from the environment
# PRIVATE_FILES = HOME+"/gn2_private_data" # private static data files (unused)

# ---- Local path to JS libraries - for development modules (only)
JS_GN_PATH = os.environ['HOME'] + "/genenetwork/javascript"

# ---- GN2 Executables (overwrite for testing only)
# PLINK_COMMAND = str.strip(os.popen("which plink2").read())
# GEMMA_COMMAND = str.strip(os.popen("which gemma").read())
REAPER_COMMAND = os.environ['GN2_PROFILE'] + "/bin/qtlreaper"
CORRELATION_COMMAND = os.environ["GN2_PROFILE"] + "/bin/correlation_rust"
# GEMMA_WRAPPER_COMMAND = str.strip(os.popen("which gemma-wrapper").read())

OAUTH2_CLIENT_ID="0bbfca82-d73f-4bd4-a140-5ae7abb4a64d"
OAUTH2_CLIENT_SECRET="yadabadaboo"

SESSION_TYPE = "redis"
SESSION_PERMANENT = True
SESSION_USE_SIGNER = True


# BEGIN: JSON WEB KEYS #####
JWKS_ROTATION_AGE_DAYS = 7 # Days (from creation) to keep a JWK in use.
JWKS_DELETION_AGE_DAYS = 14 # Days (from creation) to keep a JWK around before deleting it.
# END: JSON WEB KEYS #####
