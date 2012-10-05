from __future__ import print_function, division

import re


def parse(pstring):
    pstring = re.split(r"""(?:(\w+\s*=\s*\([^)]*\))|(\w+\s*[=:]\w+))""", pstring)
    pstring = [item.strip() for item in pstring if item and item.strip()]
    print(pstring)
    for item in pstring:
        
    
parse("foo=(3 2 1)")
parse("LRS=(9 99 Chr4 122 155) cisLRS=(9 999 10)")
parse("sal1 LRS=(9 99 Chr4 122 155) sal2 cisLRS=(9 999 10)")
parse("sal1 LRS=(9 99 Chr4 122 155) wiki=bar sal2 go:foobar cisLRS=(9 999 10)")