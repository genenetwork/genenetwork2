from pprint import pformat as pf


class Bunch(object):
    """Like a dictionary but using object notation"""
    def __init__(self,  **kw):
            self.__dict__ = kw

    def __repr__(self):
        return pf(self.__dict__)


