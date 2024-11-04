"""Debug utilities"""
import logging
from flask import current_app

__this_module_name__ = __name__


# pylint: disable=invalid-name
def getLogger(name: str):
    """Return a logger"""
    return (
        logging.getLogger(name)
        if not bool(current_app)
        else current_app.logger)

def __pk__(*args):
    """Format log entry"""
    value = args[-1]
    title_vals = " => ".join(args[0:-1])
    logger = getLogger(__this_module_name__)
    logger.debug("%s: %s", title_vals, value)
    return value
