import collections
import inspect
import time
from utility.tools import LOG_BENCH

from utility.logger import getLogger
logger = getLogger(__name__ )

class Bench(object):
    entries = collections.OrderedDict()

    def __init__(self, name=None, write_output=LOG_BENCH):
        self.name = name
        self.write_output = write_output

    def __enter__(self):
        if self.write_output:
            if self.name:
                logger.debug("Starting benchmark: %s" % (self.name))
            else:
                logger.debug("Starting benchmark at: %s [%i]" % (inspect.stack()[1][3], inspect.stack()[1][2]))
        self.start_time = time.time()

    def __exit__(self, type, value, traceback):
        time_taken = time.time() - self.start_time
        if self.write_output:
            if self.name:
                name = self.name
            else:
                name = "That"

            logger.info("  %s took: %f seconds" % (name, (time_taken)))

        if self.name:
            Bench.entries[self.name] = Bench.entries.get(self.name, 0) + time_taken

    @classmethod
    def report(cls):
        total_time = sum((time_taken for time_taken in list(cls.entries.values())))
        print("\nTiming report\n")
        for name, time_taken in list(cls.entries.items()):
            percent = int(round((time_taken/total_time) * 100))
            print("[{}%] {}: {}".format(percent, name, time_taken))
        print()

    def reset(cls):
        """Reset the entries"""
        cls.entries = collections.OrderedDict()
