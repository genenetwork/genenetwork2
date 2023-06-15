"""Functions used in setting up configurations."""
import os # replace os.path with pathlib.Path
import sys
import logging

from flask import current_app

logger = logging.getLogger(__name__)

def override_from_envvars(app):
    """
    Override `app` configuration values with those in the enviroment variables with the same names.
    """
    configs = dict((key, value.strip()) for key,value in
                   ((key, os.environ.get(key)) for key in app.config.keys())
                   if value is not None and value != "")
    app.config.update(**configs)
    return app

def get_setting(app, setting_id, guess=None):
    """Resolve a setting from the `app`."""
    setting = app.config.get(setting_id, guess or "")
    if setting is None or setting == "":
        raise Exception(
            f"{setting_id} setting unknown or faulty "
            "(update default_settings.py?).")
    return setting

def get_setting_bool(app, setting_id):
    v = get_setting(app, setting_id)
    if v not in [0, False, 'False', 'FALSE', None]:
        return True
    return False


def get_setting_int(app, setting_id):
    val = get_setting(app, setting_id)
    if isinstance(val, str):
        return int(val)
    if val is None:
        return 0
    return val

def valid_bin(path):
    if os.path.islink(path) or valid_file(path):
        return path
    return None

def valid_file(path):
    if os.path.isfile(path):
        return path
    return None

def valid_path(path):
    if os.path.isdir(path):
        return path
    return None

def flat_file_exists(app, subdir):
    base = get_setting(app, "GENENETWORK_FILES")
    return valid_path(base + "/" + subdir)

def flat_files(app, subdir=None):
    base = get_setting(app, "GENENETWORK_FILES")
    if subdir:
        return assert_dir(base + "/" + subdir)
    return assert_dir(base)

def assert_bin(fn):
    if not valid_bin(fn):
        raise Exception("ERROR: can not find binary " + fn)
    return fn


def assert_dir(the_dir):
    if not valid_path(the_dir):
        raise FileNotFoundError(f"ERROR: can not find directory '{the_dir}'")
    return the_dir

def assert_writable_dir(path):
    try:
        fn = path + "/test.txt"
        fh = open(fn, 'w')
        fh.write("I am writing this text to the file\n")
        fh.close()
        os.remove(fn)
    except IOError:
        raise Exception(f"Unable to write test.txt to directory {path}")
    return path

def assert_file(fn):
    if not valid_file(fn):
        raise FileNotFoundError(f"Unable to find file '{fn}'")
    return fn

def mk_dir(path):
    if not valid_path(path):
        os.makedirs(path)
    return assert_dir(path)

def locate(app, name, subdir=None):
    """
    Locate a static flat file in the GENENETWORK_FILES environment.

    This function throws an error when the file is not found.
    """
    base = get_setting(app, "GENENETWORK_FILES")
    if subdir:
        base = base + "/" + subdir
    if valid_path(base):
        lookfor = base + "/" + name
        if valid_file(lookfor):
            return lookfor
        else:
            raise Exception("Can not locate " + lookfor)
    if subdir:
        sys.stderr.write(subdir)
    raise Exception("Can not locate " + name + " in " + base)

def locate_ignore_error(app, name, subdir=None):
    """
    Locate a static flat file in the GENENETWORK_FILES environment.

    This function does not throw an error when the file is not found
    but returns None.
    """
    base = get_setting(app, "GENENETWORK_FILES")
    if subdir:
        base = base + "/" + subdir
    if valid_path(base):
        lookfor = base + "/" + name
        if valid_file(lookfor):
            return lookfor
    return None

def tempdir(app):
    """Retrieve the configured temporary directory or `/tmp`."""
    return valid_path(get_setting(app, "TMPDIR", "/tmp"))

def show_settings(app):
    """Print out the application configurations."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'
    app = app or current_app
    LOG_LEVEL = app.config.get("LOG_LEVEL")

    print(("Set global log level to " + BLUE + LOG_LEVEL + ENDC),
          file=sys.stderr)
    log_level = getattr(logging, LOG_LEVEL.upper())
    logging.basicConfig(level=log_level)

    logger.info(BLUE + "Mr. Mojo Risin 2" + ENDC)
    keylist = list(app.config.keys())
    print("runserver.py: ****** Webserver configuration - k,v pairs from app.config ******",
          file=sys.stderr)
    keylist.sort()
    for k in keylist:
        try:
            print(("%s: %s%s%s%s" % (k, BLUE, BOLD, get_setting(app, k), ENDC)),
                  file=sys.stderr)
        except:
            print(("%s: %s%s%s%s" % (k, GREEN, BOLD, app.config[k], ENDC)),
                  file=sys.stderr)
