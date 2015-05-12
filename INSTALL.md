# INSTALL Genenetwork2 (GN2)

## Use a Docker image

A Docker image can be generated from
[here](https://github.com/lomereiter/gn2-docker).

## Fetch GN2 from github

Clone the repository (currently ~800Mb) to local

    git clone git@github.com:genenetwork2/genenetwork2.git

## Dependencies

GN2 requires

* python
* redis-server
* mysql-server

## Required python modules

Install the following python modules (it is probably wise to use a local
Python with environment for this)

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
# Use a working copy of python
export python=$HOME/ve27/bin/python
export WQFLASK_SETTINGS=$HOME/settings.py
source /home/pjotr/ve27/bin/activate  
cd genenetwork2/wqflask
$python ./runserver.py

or

$python ./secure_server.py
```

## Running tools

### pylmm

To run pylmm check out the repository at https://github.com/genenetwork/pylmm_gn2.

Next update the setting.py file to point at the tree

GN2 can locate PYLMM through PYLMM_PATH in setting.py (or in ENV)

    PYLMM_PATH = '/home/test/opensource/python/pylmm_gn2/pylmm_gn2'

## Other information

Check also the ./misc/ directory for settings