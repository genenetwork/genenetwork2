# Call external program

import os
import sys
import subprocess

def shell(command):
    if subprocess.call(command, shell=True) != 0:
        raise Exception("ERROR: failed on "+command)
