# Tools/paths finder resolves external paths from settings and/or environment
# variables

import os
import sys
import json

from wqflask import app

# Use the standard logger here to avoid a circular dependency
import logging
logger = logging.getLogger(__name__ )

OVERRIDES = {}

def app_set(command_id, value):
    """Set application wide value"""
    app.config.setdefault(command_id,value)
    return value

def get_setting(command_id,guess=None):
    """Resolve a setting from the environment or the global settings in
    app.config, with valid_path is a function checking whether the
    path points to an expected directory and returns the full path to
    the binary command

      guess = os.environ.get('HOME')+'/pylmm'
      valid_path(get_setting('PYLMM_PATH',guess))

    first tries the environment variable in +id+, next gets the Flask
    app setting for the same +id+ and finally does an educated
    +guess+.

    In all, the environment overrides the others, next is the flask
    setting, then the guess. A valid path to the binary command is
    returned. If none is resolved an exception is thrown.

    Note that we do not use the system path. This is on purpose
    because it will mess up controlled (reproducible) deployment. The
    proper way is to either use the GNU Guix defaults as listed in
    etc/default_settings.py or override them yourself by creating a
    different settings.py file (or setting the environment).

    """
    def value(command):
        if command:
            # sys.stderr.write("Found "+command+"\n")
            app_set(command_id,command)
            return command
        else:
            return None

    # ---- Check whether environment exists
    # print("Looking for "+command_id+"\n")
    command = value(os.environ.get(command_id))
    if command is None or command == "":
        command = OVERRIDES.get(command_id) # currently not in use
        if command is None:
            # ---- Check whether setting exists in app
            command = value(app.config.get(command_id))
            if command is None:
                command = value(guess)
                if command is None or command == "":
                    # print command
                    raise Exception(command_id+' setting unknown or faulty (update default_settings.py?).')
    # print("Set "+command_id+"="+str(command))
    return command

def get_setting_bool(id):
    v = get_setting(id)
    if v not in [0,False,'False','FALSE',None]:
      return True
    return False

def get_setting_int(id):
    v = get_setting(id)
    if isinstance(v, str):
        return int(v)
    if v is None:
        return 0
    return v

def valid_bin(bin):
    if os.path.islink(bin) or valid_file(bin):
        return bin
    return None

def valid_file(fn):
    if os.path.isfile(fn):
        return fn
    return None

def valid_path(dir):
    if os.path.isdir(dir):
        return dir
    return None

def js_path(module=None):
    """
    Find the JS module in the two paths
    """
    try_gn   = get_setting("JS_GN_PATH")+"/"+module
    if valid_path(try_gn):
        return try_gn
    try_guix = get_setting("JS_GUIX_PATH")+"/"+module
    if valid_path(try_guix):
        return try_guix
    raise "No JS path found for "+module+" (if not in Guix check JS_GN_PATH)"

def reaper_command(guess=None):
    return get_setting("REAPER_COMMAND",guess)

def gemma_command(guess=None):
    return assert_bin(get_setting("GEMMA_COMMAND",guess))

def gemma_wrapper_command(guess=None):
    return assert_bin(get_setting("GEMMA_WRAPPER_COMMAND",guess))

def plink_command(guess=None):
    return assert_bin(get_setting("PLINK_COMMAND",guess))

def flat_file_exists(subdir):
    base = get_setting("GENENETWORK_FILES")
    return valid_path(base+"/"+subdir)

def flat_files(subdir=None):
    base = get_setting("GENENETWORK_FILES")
    if subdir:
        return assert_dir(base+"/"+subdir)
    return assert_dir(base)

def assert_bin(fn):
    if not valid_bin(fn):
        raise Exception("ERROR: can not find binary "+fn)
    return fn

def assert_dir(dir):
    if not valid_path(dir):
        raise Exception("ERROR: can not find directory "+dir)
    return dir

def assert_writable_dir(dir):
    try:
        fn = dir + "/test.txt"
        fh = open( fn, 'w' )
        fh.write("I am writing this text to the file\n")
        fh.close()
        os.remove(fn)
    except IOError:
        raise Exception('Unable to write test.txt to directory ' + dir)
    return dir

def assert_file(fn):
    if not valid_file(fn):
        raise Exception('Unable to find file '+fn)
    return fn

def mk_dir(dir):
    if not valid_path(dir):
        os.makedirs(dir)
    return assert_dir(dir)

def locate(name, subdir=None):
    """
    Locate a static flat file in the GENENETWORK_FILES environment.

    This function throws an error when the file is not found.
    """
    base = get_setting("GENENETWORK_FILES")
    if subdir:
        base = base+"/"+subdir
    if valid_path(base):
        lookfor = base + "/" + name
        if valid_file(lookfor):
            logger.info("Found: file "+lookfor+"\n")
            return lookfor
        else:
            raise Exception("Can not locate "+lookfor)
    if subdir: sys.stderr.write(subdir)
    raise Exception("Can not locate "+name+" in "+base)

def locate_phewas(name, subdir=None):
    return locate(name,'/phewas/'+subdir)

def locate_ignore_error(name, subdir=None):
    """
    Locate a static flat file in the GENENETWORK_FILES environment.

    This function does not throw an error when the file is not found
    but returns None.
    """
    base = get_setting("GENENETWORK_FILES")
    if subdir:
        base = base+"/"+subdir
    if valid_path(base):
        lookfor = base + "/" + name
        if valid_file(lookfor):
            logger.debug("Found: file "+name+"\n")
            return lookfor
    logger.info("WARNING: file "+name+" not found\n")
    return None

def tempdir():
    """
    Get UNIX TMPDIR by default
    """
    return valid_path(get_setting("TMPDIR","/tmp"))

BLUE  = '\033[94m'
GREEN = '\033[92m'
BOLD  = '\033[1m'
ENDC  = '\033[0m'

def show_settings():
    from utility.tools import LOG_LEVEL

    print("Set global log level to "+BLUE+LOG_LEVEL+ENDC)
    log_level = getattr(logging, LOG_LEVEL.upper())
    logging.basicConfig(level=log_level)

    logger.info(OVERRIDES)
    logger.info(BLUE+"Mr. Mojo Risin 2"+ENDC)
    print "runserver.py: ****** Webserver configuration - k,v pairs from app.config ******"
    keylist = app.config.keys()
    keylist.sort()
    for k in keylist:
        try:
            print("%s: %s%s%s%s" % (k,BLUE,BOLD,get_setting(k),ENDC))
        except:
            print("%s: %s%s%s%s" % (k,GREEN,BOLD,app.config[k],ENDC))


# Cached values
GN_VERSION         = get_setting('GN_VERSION')
HOME               = get_setting('HOME')
WEBSERVER_MODE     = get_setting('WEBSERVER_MODE')
GN_SERVER_URL      = get_setting('GN_SERVER_URL')
SERVER_PORT        = get_setting_int('SERVER_PORT')
SQL_URI            = get_setting('SQL_URI')
LOG_LEVEL          = get_setting('LOG_LEVEL')
LOG_LEVEL_DEBUG    = get_setting_int('LOG_LEVEL_DEBUG')
LOG_SQL            = get_setting_bool('LOG_SQL')
LOG_SQL_ALCHEMY    = get_setting_bool('LOG_SQL_ALCHEMY')
LOG_BENCH          = get_setting_bool('LOG_BENCH')
LOG_FORMAT         = "%(message)s"    # not yet in use
USE_REDIS          = get_setting_bool('USE_REDIS')
USE_GN_SERVER      = get_setting_bool('USE_GN_SERVER')

GENENETWORK_FILES  = get_setting('GENENETWORK_FILES')
JS_GUIX_PATH       = get_setting('JS_GUIX_PATH')
assert_dir(JS_GUIX_PATH)
JS_GN_PATH         = get_setting('JS_GN_PATH')
# assert_dir(JS_GN_PATH)

GITHUB_CLIENT_ID = get_setting('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = get_setting('GITHUB_CLIENT_SECRET')
GITHUB_AUTH_URL = None
if GITHUB_CLIENT_ID != 'UNKNOWN' and GITHUB_CLIENT_SECRET:
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize?client_id=" + \
                      GITHUB_CLIENT_ID+"&client_secret="+GITHUB_CLIENT_SECRET
    GITHUB_API_URL = get_setting('GITHUB_API_URL')

ORCID_CLIENT_ID = get_setting('ORCID_CLIENT_ID')
ORCID_CLIENT_SECRET = get_setting('ORCID_CLIENT_SECRET')
ORCID_AUTH_URL = None
if ORCID_CLIENT_ID != 'UNKNOWN' and ORCID_CLIENT_SECRET:
    ORCID_AUTH_URL = "https://sandbox.orcid.org/oauth/authorize?response_type=code&scope=/authenticate&show_login=true&client_id=" + \
                      ORCID_CLIENT_ID+"&client_secret="+ORCID_CLIENT_SECRET
    ORCID_TOKEN_URL = get_setting('ORCID_TOKEN_URL')

ELASTICSEARCH_HOST = get_setting('ELASTICSEARCH_HOST')
ELASTICSEARCH_PORT = get_setting('ELASTICSEARCH_PORT')
import utility.elasticsearch_tools as es
es.test_elasticsearch_connection()

SMTP_CONNECT = get_setting('SMTP_CONNECT')
SMTP_USERNAME = get_setting('SMTP_USERNAME')
SMTP_PASSWORD = get_setting('SMTP_PASSWORD')

REAPER_COMMAND     = app_set("REAPER_COMMAND",reaper_command())
GEMMA_COMMAND      = app_set("GEMMA_COMMAND",gemma_command())
assert(GEMMA_COMMAND is not None)
PLINK_COMMAND      = app_set("PLINK_COMMAND",plink_command())
GEMMA_WRAPPER_COMMAND = gemma_wrapper_command()
TEMPDIR            = tempdir() # defaults to UNIX TMPDIR
assert_dir(TEMPDIR)

# ---- Handle specific JS modules
JS_GUIX_PATH = get_setting("JS_GUIX_PATH")
assert_dir(JS_GUIX_PATH)
assert_dir(JS_GUIX_PATH+'/cytoscape-panzoom')
CSS_PATH = "UNKNOWN"
# assert_dir(JS_PATH)
JS_TWITTER_POST_FETCHER_PATH = get_setting("JS_TWITTER_POST_FETCHER_PATH",js_path("Twitter-Post-Fetcher"))
assert_dir(JS_TWITTER_POST_FETCHER_PATH)
assert_file(JS_TWITTER_POST_FETCHER_PATH+"/js/twitterFetcher_min.js")
JS_CYTOSCAPE_PATH = get_setting("JS_CYTOSCAPE_PATH",js_path("cytoscape"))
assert_dir(JS_CYTOSCAPE_PATH)
assert_file(JS_CYTOSCAPE_PATH+'/cytoscape.min.js')

# assert_file(PHEWAS_FILES+"/auwerx/PheWAS_pval_EMMA_norm.RData")
