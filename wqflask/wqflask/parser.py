from __future__ import print_function, division

import re

from pprint import pformat as pf

def parse(pstring):
    pstring = re.split(r"""(?:(\w+\s*=\s*\([^)]*\))|(\w+\s*[=:]\w+)|(\w+))""", pstring)
    pstring = [item.strip() for item in pstring if item and item.strip()]
    print(pstring)
    
    items = []
    
    for item in pstring:
        if ":" in item:
            key, seperator, value = item.partition(':')
        elif "=" in item:
            key, seperator, value = item.partition('=')
        else:
            seperator = None
        
        if seperator:
            if '(' in value:
                assert value.startswith("("), "Invalid token"
                assert value.endswith(")"), "Invalid token"
                value = value[1:-1] # Get rid of the parenthesis
                values = re.split(r"""\s+|,""", value)
                value = [value.strip() for value in values if value.strip()]
            term = dict(key=key,
                        seperator=seperator,
                        value=value)
        else:
            term = dict(search_term = item)
            
        items.append(term)
    print(pf(items))
    return(items)
    
if __name__ == '__main__':
    parse("foo=(3 2 1)")
    parse("shh")
    parse("shh grep")
    parse("LRS=(9 99 Chr4 122 155) cisLRS=(9 999 10)")
    parse("sal1 LRS=(9 99 Chr4 122 155) sal2 cisLRS=(9 999 10)")
    parse("sal1 sal3 LRS=(9 99 Chr4 122 155) wiki=bar sal2 go:foobar cisLRS=(9 999 10)")
    parse("sal1 LRS=(9 99 Chr4 122 155) wiki=bar sal2 go:foobar cisLRS=(9, 999, 10)")