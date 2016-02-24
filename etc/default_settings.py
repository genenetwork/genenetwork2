import os
import sys

LOGFILE = "/tmp/genenetwork2.log"

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

# Path overrides for Genenetwork
GENENETWORK_FILES = "../../gn2_data"
PYLMM_COMMAND = str.strip(os.popen("which pylmm_redis").read())
PLINK_COMMAND = str.strip(os.popen("which plink2").read())
GEMMA_COMMAND = str.strip(os.popen("which gemma").read())
