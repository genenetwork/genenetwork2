from pprint import pformat as pf

# Todo: Move these out of __init__

class Bunch(object):
    """Like a dictionary but using object notation"""
    def __init__(self,  **kw):
            self.__dict__ = kw

    def __repr__(self):
        return pf(self.__dict__)


class Struct(object):
    '''The recursive class for building and representing objects with.

    From http://stackoverflow.com/a/6573827/1175849

    '''

    def __init__(self, obj):
        for k, v in obj.iteritems():
            if isinstance(v, dict):
                setattr(self, k, Struct(v))
            else:
                setattr(self, k, v)

    def __getitem__(self, val):
        return self.__dict__[val]

    def __repr__(self):
        return '{%s}' % str(', '.join('%s : %s' % (k, repr(v)) for
            (k, v) in self.__dict__.iteritems()))


