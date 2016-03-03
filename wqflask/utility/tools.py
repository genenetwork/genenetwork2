# Tools/paths finder resolves external paths from settings and/or environment
# variables

import os
import sys
from wqflask import app


def get_setting(command_id,guess=None):
    """Resolve a setting from the environment or the global settings in
    app.config, with get_valid_path is a function checking whether the
    path points to an expected directory and returns the full path to
    the binary command

      guess = os.environ.get('HOME')+'/pylmm'
      get_setting('PYLMM_PATH',guess)

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
            sys.stderr.write("Found path "+command+"\n")
            return command
        else:
            return None
    
    # ---- Check whether environment exists
    sys.stderr.write("Looking for "+command_id+"\n")
    command = value(os.environ.get(command_id))
    if not command:
        # ---- Check whether setting exists in app
        command = value(app.config.get(command_id))
        if not command:
            command = value(guess)
            if not command:
                raise Exception(command_id+' path unknown or faulty (update settings.py?). '+command_id+' should point to the path')
    return command

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
            print("Found: file "+lookfor+"\n")
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
            print("Found: file "+name+"\n")
            return lookfor
    sys.stderr.write("WARNING: file "+name+" not found\n")
    return None

def tempdir():
    return valid_path(get_setting("TEMPDIR","/tmp"))

    
# Cached values
PYLMM_COMMAND = pylmm_command()
GEMMA_COMMAND = gemma_command()
PLINK_COMMAND = plink_command()
FLAT_FILES    = flat_files()
TEMPDIR       = tempdir()
