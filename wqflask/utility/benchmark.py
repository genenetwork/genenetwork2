from __future__ import print_function, division, absolute_import

import collections
import inspect
import time


class Bench(object):
    entries = collections.OrderedDict()
    
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        if self.name:
            print("Starting benchmark: %s" % (self.name))
        else:
            print("Starting benchmark at: %s [%i]" % (inspect.stack()[1][3], inspect.stack()[1][2]))
        self.start_time = time.time()

    def __exit__(self, type, value, traceback):
        if self.name:
            name = self.name
        else:
            name = "That"

        time_taken = time.time() - self.start_time
        print("  %s took: %f seconds" % (name, (time_taken)))
        
        if self.name:
            Bench.entries[self.name] = Bench.entries.get(self.name, 0) + time_taken
            

    @classmethod
    def report(cls):
        total_time = sum((time_taken for time_taken in cls.entries.itervalues()))
        print("\nTiming report\n")
        for name, time_taken in cls.entries.iteritems():
            percent = int(round((time_taken/total_time) * 100))
            print("[{}%] {}: {}".format(percent, name, time_taken))
        print()
        
    def reset(cls):
        """Reset the entries"""
        cls.entries = collections.OrderedDict()