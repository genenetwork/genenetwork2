# GeneNetwork logger
#
# The standard python logging module is very good. This logger adds a
# few facilities on top of that. Main one being that it picks up
# settings for log levels (global and by module) and (potentially)
# offers some fine grained log levels for the standard levels.
#
# All behaviour is defined here.  Global settings (defined in
# default_settings.py).
#
# To use logging and settings put this at the top of a module:
#
#   import utility.logger
#   logger = utility.logger.getLogger(__name__ )
#
# To override global behaviour set the LOG_LEVEL in default_settings.py
# or use an environment variable, e.g.
#
#    env LOG_LEVEL=INFO ./bin/genenetwork2
#
# To override log level for a module replace that with, for example,
#
#   import logging
#   import utility.logger
#   logger = utility.logger.getLogger(__name__,level=logging.DEBUG)
#
# We'll add more overrides soon.

import logging
from utility.tools import LOG_LEVEL

# Get the module logger. You can override log levels at the
# module level
def getLogger(name, level = None):
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    else:
        logger.setLevel(LOG_LEVEL)

    logger.debug("Log "+name+" at level "+logging.getLevelName(logger.getEffectiveLevel()))
    return logger
