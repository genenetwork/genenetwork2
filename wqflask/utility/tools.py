# Tools/paths finder resolves external paths from settings and/or environment
# variables
#
# Currently supported:
#
#   PYLMM_PATH finds the root of the git repository of the pylmm_gn2 tool 

import os

def get_setting():
    """
    Resolve a setting from the environment or the global settings in app.config
    """
    pass
    
def pylmm_command(default=None):
    def get_valid_path(path):
        if path and os.path.isfile(path+'/lmm.py'):
            return path
        else:
            None

    # ---- Check whether environment exists
    path = get_valid_path(os.environ['PYLMM_PATH'])
    # ---- Check whether setting exists
    if not path:
        path = get_valid_path(app.config.get('PYLMM_PATH'))
    # ---- Check whether default exists
    if not path:
        path = get_valid_path(default)
    home = get_valid_path(os.environ['HOME']+'/pylmm_gn2')
    if not path:
        path = get_valid_path(home)
    if not path:
        raise Exception('PYLMM_PATH '+home+' unknown or faulty (add PYLMM_PATH to settings.py)')
    pylmm_command = 'python '+path+'/lmm.py'
    return path,pylmm_command
