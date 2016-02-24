# Call external program

import os
import sys
import subprocess

def shell(command):
    if not subprocess.call(command, shell=True):
        raise Exception("ERROR: failed on "+command)
