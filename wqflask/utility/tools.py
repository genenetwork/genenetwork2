# Tools/paths finder resolves external paths from settings and/or environment
# variables

import os
import sys
import json
from typing import Any, Optional

from flask import Flask

# Use the standard logger here to avoid a circular dependency
import logging
logger = logging.getLogger(__name__)


def app_set(app: Flask, command_id: str, value: Any) -> Any:
    """Set application wide value"""
    app.config.setdefault(command_id, value)
    return value


def get_setting(app: Flask, command_id: str, guess: Optional[Any] = None) -> Any:
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
            app_set(app, command_id, command)
            return command
        else:
            return app.config.get(command_id)

    # ---- Check whether environment exists
    # print("Looking for "+command_id+"\n")
    command = value(os.environ.get(command_id))
    if command is None or command == "":
        # ---- Check whether setting exists in app
        command = value(app.config.get(command_id))
        if command is None:
            command = value(guess)
            if command is None or command == "":
                # print command
                raise Exception(
                    command_id + ' setting unknown or faulty (update default_settings.py?).')
    # print("Set "+command_id+"="+str(command))
    return command


def get_setting_bool(app, id):
    v = get_setting(app, id)
    if v not in [0, False, 'False', 'FALSE', None]:
        return True
    return False


def get_setting_int(app, id):
    v = get_setting(app, id)
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


def js_path(app, module=None):
    """
    Find the JS module in the two paths
    """
    try_gn = get_setting(app, "JS_GN_PATH") + "/" + module
    if valid_path(try_gn):
        return try_gn
    try_guix = get_setting(app, "JS_GUIX_PATH") + "/" + module
    if valid_path(try_guix):
        return try_guix
    raise "No JS path found for " + module + \
        " (if not in Guix check JS_GN_PATH)"


def reaper_command(app, guess=None):
    return get_setting(app, "REAPER_COMMAND", guess)


def gemma_command(app, guess=None):
    return assert_bin(get_setting(app, "GEMMA_COMMAND", guess))


def gemma_wrapper_command(app, guess=None):
    return assert_bin(get_setting(app, "GEMMA_WRAPPER_COMMAND", guess))


def plink_command(app, guess=None):
    return assert_bin(get_setting(app, "PLINK_COMMAND", guess))


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


def assert_writable_dir(dir):
    try:
        fn = dir + "/test.txt"
        fh = open(fn, 'w')
        fh.write("I am writing this text to the file\n")
        fh.close()
        os.remove(fn)
    except IOError:
        raise Exception('Unable to write test.txt to directory ' + dir)
    return dir


def assert_file(fn):
    if not valid_file(fn):
        raise FileNotFoundError(f"Unable to find file '{fn}'")
    return fn


def mk_dir(dir):
    if not valid_path(dir):
        os.makedirs(dir)
    return assert_dir(dir)


def locate(app: Flask, name: str, subdir=None) -> str:
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


def locate_phewas(app: Flask, name, subdir=None):
    return locate(app, name, '/phewas/' + subdir)


def locate_ignore_error(app: Flask, name, subdir=None):
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


def tempdir(app: Flask) -> str:
    """
    Get UNIX TMPDIR by default
    """
    return valid_path(get_setting(app, "TMPDIR", "/tmp"))


BLUE = '\033[94m'
GREEN = '\033[92m'
BOLD = '\033[1m'
ENDC = '\033[0m'


def show_settings(app: Flask) -> None:
    LOG_LEVEL = get_setting(app, "LOG_LEVEL")

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


def set_mandatory_settings(app: Flask) -> Flask:
    """Set the mandatory settings then return the `app` object."""
    # Cached values
    app.config["GN_VERSION"] = get_setting(app, 'GN_VERSION')
    app.config["HOME"] = get_setting(app, 'HOME')
    app.config["SERVER_PORT"] = get_setting(app, 'SERVER_PORT')
    app.config["WEBSERVER_MODE"] = get_setting(app, 'WEBSERVER_MODE')
    app.config["GN2_BASE_URL"] = get_setting(app, 'GN2_BASE_URL')
    app.config["GN2_BRANCH_URL"] = get_setting(app, 'GN2_BRANCH_URL')
    app.config["GN_SERVER_URL"] = get_setting(app, 'GN_SERVER_URL')
    app.config["GN_PROXY_URL"] = get_setting(app, 'GN_PROXY_URL')
    app.config["GN3_LOCAL_URL"] = get_setting(app, 'GN3_LOCAL_URL')
    app.config["SERVER_PORT"] = get_setting_int(app, 'SERVER_PORT')
    app.config["SQL_URI"] = get_setting(app, 'SQL_URI')
    app.config["LOG_LEVEL"] = get_setting(app, 'LOG_LEVEL')
    app.config["LOG_LEVEL_DEBUG"] = get_setting_int(app, 'LOG_LEVEL_DEBUG')
    app.config["LOG_SQL"] = get_setting_bool(app, 'LOG_SQL')
    app.config["LOG_SQL_ALCHEMY"] = get_setting_bool(app, 'LOG_SQL_ALCHEMY')
    app.config["LOG_BENCH"] = get_setting_bool(app, 'LOG_BENCH')
    app.config["LOG_FORMAT"] = "%(message)s"    # not yet in use
    app.config["USE_REDIS"] = get_setting_bool(app, 'USE_REDIS')
    app.config["REDIS_URL"] = get_setting(app, 'REDIS_URL')
    app.config["USE_GN_SERVER"] = get_setting_bool(app, 'USE_GN_SERVER')

    app.config["GENENETWORK_FILES"] = get_setting(app, 'GENENETWORK_FILES')
    app.config["JS_GUIX_PATH"] = assert_dir(get_setting(app, 'JS_GUIX_PATH'))
    app.config["JS_GN_PATH"] = get_setting(app, 'JS_GN_PATH')
    # assert_dir(JS_GN_PATH)

    app.config["GITHUB_CLIENT_ID"] = get_setting(app, 'GITHUB_CLIENT_ID')
    app.config["GITHUB_CLIENT_SECRET"] = get_setting(app, 'GITHUB_CLIENT_SECRET')
    app.config["GITHUB_AUTH_URL"] = ""
    if app.config["GITHUB_CLIENT_ID"] != 'UNKNOWN' and app.config["GITHUB_CLIENT_SECRET"]:
        app.config["GITHUB_AUTH_URL"] = "https://github.com/login/oauth/authorize?client_id=" + \
                          app.config["GITHUB_CLIENT_ID"] + "&client_secret=" + \
                          app.config["GITHUB_CLIENT_SECRET"]
        app.config["GITHUB_API_URL"] = get_setting(app, 'GITHUB_API_URL')

    app.config["ORCID_CLIENT_ID"] = get_setting(app, 'ORCID_CLIENT_ID')
    app.config["ORCID_CLIENT_SECRET"] = get_setting(app, 'ORCID_CLIENT_SECRET')
    app.config["ORCID_AUTH_URL"] = None
    if app.config["ORCID_CLIENT_ID"] != 'UNKNOWN' and app.config["ORCID_CLIENT_SECRET"]:
        app.config["ORCID_AUTH_URL"] = "https://orcid.org/oauth/authorize" + \
            "?response_type=code&scope=/authenticate&show_login=true" + \
            "&client_id=" + \
            app.config["ORCID_CLIENT_ID"] + "&client_secret=" + \
            app.config["ORCID_CLIENT_SECRET"] + "&redirect_uri=" + \
            app.config["GN2_BRANCH_URL"] + "n/login/orcid_oauth2"
        app.config["ORCID_TOKEN_URL"] = get_setting(app, 'ORCID_TOKEN_URL')


    app.config["SMTP_CONNECT"] = get_setting(app, 'SMTP_CONNECT')
    app.config["SMTP_USERNAME"] = get_setting(app, 'SMTP_USERNAME')
    app.config["SMTP_PASSWORD"] = get_setting(app, 'SMTP_PASSWORD')

    app.config["REAPER_COMMAND"] = app_set(app, "REAPER_COMMAND", reaper_command(app))
    app.config["GEMMA_COMMAND"] = app_set(app, "GEMMA_COMMAND", gemma_command(app))
    assert(app.config["GEMMA_COMMAND"] is not None)
    app.config["PLINK_COMMAND"] = app_set(app, "PLINK_COMMAND", plink_command(app))
    app.config["GEMMA_WRAPPER_COMMAND"] = gemma_wrapper_command(app)
    app.config["TEMPDIR"] = assert_dir(tempdir(app))  # defaults to UNIX TMPDIR

    # ---- Handle specific JS modules
    app.config["JS_GUIX_PATH"] = assert_dir(get_setting(app, "JS_GUIX_PATH"))
    assert_dir(app.config["JS_GUIX_PATH"] + '/cytoscape-panzoom')

    app.config["CSS_PATH"] = app.config["JS_GUIX_PATH"]  # The CSS is bundled together with the JS
    # assert_dir(JS_PATH)

    app.config["JS_TWITTER_POST_FETCHER_PATH"] = assert_dir(get_setting(
        app,
        "JS_TWITTER_POST_FETCHER_PATH",
        js_path(app, "javascript-twitter-post-fetcher")))
    assert_file(app.config["JS_TWITTER_POST_FETCHER_PATH"] + "/js/twitterFetcher_min.js")

    app.config["JS_CYTOSCAPE_PATH"] = assert_dir(get_setting(app, "JS_CYTOSCAPE_PATH", js_path(app, "cytoscape")))
    assert_file(app.config["JS_CYTOSCAPE_PATH"] + '/cytoscape.min.js')

    # assert_file(PHEWAS_FILES+"/auwerx/PheWAS_pval_EMMA_norm.RData")

    app.config["OAUTH2_CLIENT_ID"] = get_setting(app, 'OAUTH2_CLIENT_ID')
    app.config["OAUTH2_CLIENT_SECRET"] = get_setting(app, 'OAUTH2_CLIENT_SECRET')
    return app
