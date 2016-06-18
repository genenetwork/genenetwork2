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
# To override log level for a module replace that with, for example,
#
#   import logging
#   import utility.logger
#   logger = utility.logger.getLogger(__name__,level=logging.DEBUG)
#
# We'll add more overrides soon.

import logging

from utility.tools import LOG_LEVEL

print("Set global log level to "+LOG_LEVEL)

log_level = getattr(logging, LOG_LEVEL.upper())
logging.basicConfig(level=log_level)

# Get the module logger. You can override log levels at the
# module level
def getLogger(name, level = None):
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    return logger
