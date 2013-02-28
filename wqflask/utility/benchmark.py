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

        time_took = time.time() - self.start_time
        print("  %s took: %f seconds" % (name, (time_took)))
        
        if self.name:
            Bench.entries[self.name] = time_took

    @classmethod
    def report(cls):
        total_time = sum((time_took for time_took in cls.entries.itervalues()))
        print("\nTiming report\n")
        for name, time_took in cls.entries.iteritems():
            percent = int(round((time_took/total_time) * 100))
            print("[{}%] {}: {}".format(percent, name, time_took))
        print()
        
        # Reset the entries after reporting
        cls.entries = collections.OrderedDict()