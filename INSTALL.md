# INSTALL Genenetwork2 (GN2)

## Fetch GN2 from github

Clone the repository (currently ~800Mb) to local

    git clone git@github.com:genenetwork2/genenetwork2.git

## Dependencies

GN2 requires

* redis
* mysql

## Required python modules

Install the following python modules:

* Flask
* pyyaml
* redis
* qtlreaper
* numarray
* pp
* Flask-SQLAlchemy

## Set up local file settings.py

```python
LOGFILE = """/tmp/flask_gn_log"""

#This is needed because Flask turns key errors into a
#400 bad request response with no exception/log
TRAP_BAD_REQUEST_ERRORS = True

DB_URI = """mysql://gn2:password@localhost/db_webqtl"""
SQLALCHEMY_DATABASE_URI = 'mysql://gn2:password@localhost/db_webqtl'

# http://pythonhosted.org/Flask-Security/configuration.html
SECURITY_CONFIRMABLE = True
SECURITY_TRACKABLE = True
SECURITY_REGISTERABLE = True
SECURITY_RECOVERABLE = True

SECURITY_EMAIL_SENDER = "no-reply@genenetwork.org"
SECURITY_POST_LOGIN_VIEW = "/thank_you"
SQLALCHEMY_POOL_RECYCLE = 3600

SERVER_PORT = 5051

SECRET_HMAC_CODE = '*'
```

```sh
   export WQFLASK_SETTINGS=$HOME/settings.py
   source /home/pjotr/ve27/bin/activate  
   cd genenetwork2/wqflask
   python ./runserver.py

   or

   python ./secure_server.py
```
