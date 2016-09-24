# Tools/paths finder resolves external paths from settings and/or environment
# variables

import os
import sys

from wqflask import app

# Use the standard logger here to avoid a circular dependency
import logging
logger = logging.getLogger(__name__ )

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
            return command
        else:
            return None

    # ---- Check whether environment exists
    logger.debug("Looking for "+command_id+"\n")
    command = value(os.environ.get(command_id))
    if command is None or command == "":
        # ---- Check whether setting exists in app
        command = value(app.config.get(command_id))
        if command is None:
            command = value(guess)
            if command is None or command == "":
                print command
                raise Exception(command_id+' setting unknown or faulty (update default_settings.py?).')
    logger.debug("Set "+command_id+"="+str(command))
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

def pylmm_command(guess=None):
    return valid_bin(get_setting("PYLMM_COMMAND",guess))

def gemma_command(guess=None):
    return valid_bin(get_setting("GEMMA_COMMAND",guess))

def plink_command(guess=None):
    return valid_bin(get_setting("PLINK_COMMAND",guess))

def flat_files(subdir=None):
    base = get_setting("GENENETWORK_FILES")
    if subdir:
        return assert_dir(base+"/"+subdir)
    return assert_dir(base)

def assert_dir(dir):
    if not valid_path(dir):
        raise Exception("ERROR: can not find directory "+dir)
    return dir

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

    logger.info(BLUE+"Mr. Mojo Risin 2"+ENDC)
    print "runserver.py: ****** The webserver has the following configuration ******"
    keylist = app.config.keys()
    keylist.sort()
    for k in keylist:
        try:
            print("%s %s%s%s%s" % (k,BLUE,BOLD,get_setting(k),ENDC))
        except:
            print("%s %s%s%s%s" % (k,GREEN,BOLD,app.config[k],ENDC))


# Cached values
WEBSERVER_MODE     = get_setting('WEBSERVER_MODE')
GN_SERVER_URL      = get_setting('GN_SERVER_URL')
SQL_URI            = get_setting('SQL_URI')
LOG_LEVEL          = get_setting('LOG_LEVEL')
LOG_LEVEL_DEBUG    = get_setting_int('LOG_LEVEL_DEBUG')
LOG_SQL            = get_setting_bool('LOG_SQL')
LOG_SQLALCHEMY     = get_setting_bool('LOG_SQLALCHEMY')
LOG_BENCH          = get_setting_bool('LOG_BENCH')
LOG_FORMAT         = "%(message)s"    # not yet in use
USE_REDIS          = get_setting_bool('USE_REDIS')
USE_GN_SERVER      = get_setting_bool('USE_GN_SERVER')
GENENETWORK_FILES  = get_setting_bool('GENENETWORK_FILES')

PYLMM_COMMAND      = pylmm_command()
GEMMA_COMMAND      = gemma_command()
PLINK_COMMAND      = plink_command()
TEMPDIR            = tempdir()
