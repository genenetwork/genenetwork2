# Tools/paths finder resolves external paths from settings and/or environment
# variables
#
# Currently supported:
#
#   PYLMM_PATH finds the root of the git repository of the pylmm_gn2 tool 

import os
import sys
from wqflask import app

def get_setting(id,default,guess,find_path):
    """Resolve a setting from the environment or the global settings in
    app.config, with get_valid_path is a function checking whether the
    path points to an expected directory an returns the full path e.g.

      guess = os.environ.get('HOME')+'/pylmm'
      get_setting('PYLMM_PATH',default,guess,get_valid_path)

    first tries the environment variable in +id+, next gets the Flask
    app setting for the same +id+, next tries the path passed in with
    +default+ and finally does an educated +guess+.

    In all, the environment overrides the others, next is the flask
    setting, then the default and finally the guess (which is
    $HOME/repo). A valid path is returned. If none is resolved an
    exception is thrown.

    Note that we do not use the system path. This is on purpose
    because it will mess up controlled (reproducible) deployment. The
    proper way is to either use the GNU Guix defaults as listed in
    etc/default_settings.py or override them yourself by creating a
    different settings.py file (or setting the environment).

    """
    # ---- Check whether environment exists
    path = find_path(os.environ.get(id))
    # ---- Check whether setting exists
    setting = app.config.get(id)
    if not path:
        path = find_path(setting)
    # ---- Check whether default exists
    if not path:
        path = find_path(default)
    # ---- Guess directory
    if not path:
        guess = os.environ.get('HOME')+guess
        if not setting:
            setting = guess
        path = find_path(guess)
    if not path:
        raise Exception(id+' '+setting+' path unknown or faulty (update settings.py?). '+id+' should point to the path')
    return path

def find_command(command,id1,default,guess):
    def find_path(path):
        """Test for a valid repository"""
        if path:
            sys.stderr.write("Trying "+id1+" in "+path+"\n")
        binary = str.split(command)[0]
        if path and os.path.isfile(path+'/'+binary):
            return path
        else:
            None

    path = get_setting(id1,default,guess,find_path)
    binary = path+'/'+command
    sys.stderr.write("Found "+binary+"\n")
    return path,binary

def pylmm_command(default=None):
    return find_command('pylmm_gn2/lmm.py',"PYLMM_PATH",default,'/pylmm2')

def gemma_command(default=None):
    return find_command('gemma',"GEMMA_PATH",default,'/gemma')

def plink_command(default=None):
    return find_command('plink2',"PLINK_PATH",default,'/plink')
