# Tools/paths finder resolves external paths from settings and/or environment
# variables
#
# Currently supported:
#
#   PYLMM_PATH finds the root of the git repository of the pylmm_gn2 tool 

import os
import sys
from wqflask import app

def get_setting(id,default,guess,get_valid_path):
    """
    Resolve a setting from the environment or the global settings in app.config
    """
    # ---- Check whether environment exists
    path = get_valid_path(os.environ.get(id))
    # ---- Check whether setting exists
    setting = app.config.get(id)
    if not path:
        path = get_valid_path(setting)
    # ---- Check whether default exists
    if not path:
        path = get_valid_path(default)
    # ---- Guess directory
    if not path:
        if not setting:
            setting = guess
        path = get_valid_path(guess)
    if not path:
        raise Exception(id+' '+setting+' path unknown or faulty (update settings.py?). '+id+' should point to the root of the git repository')

    return path

def pylmm_command(default=None):
    """
    Return the path to the repository and the python command to call
    """
    def get_valid_path(path):
        """Test for a valid repository"""
        if path:
            sys.stderr.write("Trying PYLMM_PATH in "+path+"\n")
        if path and os.path.isfile(path+'/pylmm_gn2/lmm.py'):
            return path
        else:
            None

    guess = os.environ.get('HOME')+'/pylmm_gn2'
    path = get_setting('PYLMM_PATH',default,guess,get_valid_path)
    pylmm_command = 'python '+path+'/pylmm_gn2/lmm.py'
    return path,pylmm_command

def plink_command(default=None):
    """
    Return the path to the repository and the python command to call
    """
    def get_valid_path(path):
        """Test for a valid repository"""
        if path:
            sys.stderr.write("Trying PLINK_PATH in "+path+"\n")
        if path and os.path.isfile(path+'/plink'):
            return path
        else:
            None

    guess = os.environ.get('HOME')+'/plink'
    path = get_setting('PLINK_PATH',default,guess,get_valid_path)
    plink_command = path+'/plink'
    return path,plink_command

def gemma_command(default=None):
    def get_valid_path(path):
        """Test for a valid repository"""
        if path:
            sys.stderr.write("Trying PLINK_PATH in "+path+"\n")
        if path and os.path.isfile(path+'/plink'):
            return path
        else:
            None

    guess = os.environ.get('HOME')+'/plink'
    path = get_setting('PLINK_PATH',default,guess,get_valid_path)
    gemma_command = path+'/gemma'
    return path, gemma_command