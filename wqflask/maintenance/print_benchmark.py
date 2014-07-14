#!/usr/bin/python

from __future__ import absolute_import, print_function, division

import time

from pprint import pformat as pf


class TheCounter(object):
    Counters = {}
    
    def __init__(self):
        start_time = time.time()
        for counter in range(170000):
            self.print_it(counter)
        self.time_took = time.time() - start_time
        TheCounter.Counters[self.__class__.__name__] = self.time_took        

class PrintAll(TheCounter): 
    def print_it(self, counter):
        print(counter)
        
class PrintSome(TheCounter):
    def print_it(self, counter):
        if counter % 1000 == 0:
            print(counter)
            
class PrintNone(TheCounter):
    def print_it(self, counter):
        pass
    
    
def new_main():
    print("Running new_main")
    tests = [PrintAll, PrintSome, PrintNone]
    for test in tests:
        test()
        
    print(pf(TheCounter.Counters))

if __name__ == '__main__':
    new_main()