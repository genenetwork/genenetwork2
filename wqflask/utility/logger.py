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
import string
from inspect import isfunction
from pprint import pformat as pf
from inspect import stack
import datetime

from utility.tools import LOG_LEVEL, LOG_LEVEL_DEBUG, LOG_SQL

class GNLogger:
    """A logger class with some additional functionality, such as
    multiple parameter logging, SQL logging, timing, colors, and lazy
    functions.

    """

    def __init__(self,name):
        self.logger = logging.getLogger(name)

    def setLevel(self,value):
        """Set the undelying log level"""
        self.logger.setLevel(value)

    def debug(self,*args):
        """Call logging.debug for multiple args. Use (lazy) debugf and
level=num to filter on LOG_LEVEL_DEBUG.

        """
        self.collect(self.logger.debug,*args)

    def debug20(self,*args):
        """Call logging.debug for multiple args. Use level=num to filter on
LOG_LEVEL_DEBUG (NYI).

        """
        if level <= LOG_LEVEL_DEBUG:
            if self.logger.getEffectiveLevel() < 20:
                self.collect(self.logger.debug,*args)

    def info(self,*args):
        """Call logging.info for multiple args"""
        self.collect(self.logger.info,*args)

    def warning(self,*args):
        """Call logging.warning for multiple args"""
        self.collect(self.logger.warning,*args)
        # self.logger.warning(self.collect(*args))

    def error(self,*args):
        """Call logging.error for multiple args"""
        now = datetime.datetime.utcnow()
        time_str = now.strftime('%H:%M:%S UTC %Y%m%d')
        l = [time_str]+list(args)
        self.collect(self.logger.error,*l)

    def infof(self,*args):
        """Call logging.info for multiple args lazily"""
        # only evaluate function when logging
        if self.logger.getEffectiveLevel() < 30:
            self.collectf(self.logger.debug,*args)

    def debugf(self,level=0,*args):
        """Call logging.debug for multiple args lazily and handle
        LOG_LEVEL_DEBUG correctly

        """
        # only evaluate function when logging
        if level <= LOG_LEVEL_DEBUG:
            if self.logger.getEffectiveLevel() < 20:
                self.collectf(self.logger.debug,*args)

    def sql(self, sqlcommand, fun = None):
        """Log SQL command, optionally invoking a timed fun"""
        if LOG_SQL:
            caller = stack()[1][3]
            if caller in ['fetchone','fetch1','fetchall']:
                caller = stack()[2][3]
            self.info(caller,sqlcommand)
        if fun:
            result = fun(sqlcommand)
            if LOG_SQL:
                self.info(result)
            return result

    def collect(self,fun,*args):
        """Collect arguments and use fun to output"""
        out = "."+stack()[2][3]
        for a in args:
            if len(out)>1:
                out += ": "
            if isinstance(a, str):
                out = out + a
            else:
                out = out + pf(a,width=160)
        fun(out)

    def collectf(self,fun,*args):
        """Collect arguments and use fun to output one by one"""
        out = "."+stack()[2][3]
        for a in args:
            if len(out)>1:
                out += ": "
                if isfunction(a):
                    out += a()
                else:
                    if isinstance(a, str):
                        out = out + a
                    else:
                        out = out + pf(a,width=160)
        fun(out)

# Get the module logger. You can override log levels at the
# module level
def getLogger(name, level = None):
    gnlogger = GNLogger(name)
    logger = gnlogger.logger

    if level:
        logger.setLevel(level)
    else:
        logger.setLevel(LOG_LEVEL)

    logger.info("Log level of "+name+" set to "+logging.getLevelName(logger.getEffectiveLevel()))
    return gnlogger
