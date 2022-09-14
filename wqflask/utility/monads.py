"""Monadic utilities

This module is a collection of monadic utilities for use in
GeneNetwork. It includes:

* MonadicDict - monadic version of the built-in dictionary
* MonadicDictCursor - monadic version of MySQLdb.cursors.DictCursor
  that returns a MonadicDict instead of the built-in dictionary
"""

from collections import UserDict
from functools import partial

from MySQLdb.cursors import DictCursor
from pymonad.maybe import Just, Nothing

class MonadicDict(UserDict):
    """
    Monadic version of the built-in dictionary.

    Keys in this dictionary can be any python object, but values must
    be monadic values.
    """
    def __init__(self, d, convert=True):
        """
        Initialize monadic dictionary.

        If convert is False, values in dictionary d must be
        monadic. If convert is True, values in dictionary d are
        converted to monadic values.
        """
        if convert:
            super().__init__({key:(Nothing if value is None else Just(value))
                              for key, value in d.items()})
        else:
            super().__init__(d)
    def __getitem__(self, key):
        """
        Get key from dictionary.

        If key exists in the dictionary, return a Just value. Else,
        return Nothing.
        """
        try:
            return Just(self.data[key])
        except KeyError:
            return Nothing
    def __setitem__(self, key, value):
        """
        Set key in dictionary.

        value must be a monadic value---either Nothing or a Just
        value. If value is a Just value, set it in the dictionary. If
        value is Nothing, do nothing.
        """
        value.bind(partial(super().__setitem__, key))
    def __delitem__(self, key):
        """
        Delete key from dictionary.

        If key exists in the dictionary, delete it. Else, do nothing.
        """
        try:
            super().__delitem__(key)
        except KeyError:
            pass

class MonadicDictCursor(DictCursor):
    """
    Monadic version of MySQLdb.cursors.DictCursor.

    Monadic version of MySQLdb.cursors.DictCursor that returns a
    MonadicDict instead of the built-in dictionary.
    """
    def fetchone(self):
        return MonadicDict(super().fetchone())
    def fetchmany(self, size=None):
        return [MonadicDict(row) for row in super().fetchmany(size=size)]
    def fetchall(self):
        return [MonadicDict(row) for row in super().fetchall()]
