from __future__ import absolute_import, print_function, division

class HeatMapobject):

    def __init__(self, start_vars):
    
        trait_db_list = [trait.strip() for trait in start_vars['trait_list'].split(',')]
        helper_functions.get_trait_db_obs(trait_db_list)
        