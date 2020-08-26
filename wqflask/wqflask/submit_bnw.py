from base.trait import GeneralTrait
from base import data_set
from utility import helper_functions

import utility.logger
logger = utility.logger.getLogger(__name__ )

def get_bnw_input(start_vars):
    logger.debug("BNW VARS:", start_vars)
