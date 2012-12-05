"""
Parses search terms input by user

Searches take two primary forms:
- search term by itself (ex. "shh" or "brain")
- key / separator / value(s) (ex. "LRS=(9 99 Chr4 122 155)" or "GO:342533")

In the example of "LRS=(9 99 Chr4 122 155)", the key is "LRS", the separator is "=" and the value
is everything within the parentheses.

Both "=" and ":" can be used as separators; in the future, it would also be good to allow no
separator at all (ex. "cisLRS(9 999 10)")

Both square brackets and parentheses can be used interchangeably. Both can also be used to
encapsulate a single value; "cisLRS=[9 999 10)" would
be acceptable.]

"""

from __future__ import print_function, division

import re

from pprint import pformat as pf

def parse(pstring):
    """
    
    returned item serach_term is always a list, even if only one element
    """
    pstring = re.split(r"""(?:(\w+\s*=\s*[\('"\[][^)'"]*[\)\]'"])  |  # LRS=(1 2 3), cisLRS=[4 5 6], etc
                       (\w+\s*[=:\>\<][\w\*]+)  |  # wiki=bar, GO:foobar, etc
                       ([\w\*]+))  # shh, brain, etc """, pstring,
                                                    flags=re.VERBOSE)
    pstring = [item.strip() for item in pstring if item and item.strip()]
    print(pstring)

    items = []

    separators = [re.escape(x) for x in ("<=", ">=", ":", "=", "<", ">")]
    separators = '(%s)' % ("|".join(separators))
    
    print("separators:", separators)

    for item in pstring:
        splat = re.split(separators, item)
        print("splat is:", splat)

        # splat is an array of 1 if no match, otherwise more than 1
        if len(splat) > 1:
            key, separator, value = splat
            if '(' in value or '[' in value:
                assert value.startswith(("(", "[")), "Invalid token"
                assert value.endswith((")", "]")), "Invalid token"
                value = value[1:-1] # Get rid of the parenthesis
                values = re.split(r"""\s+|,""", value)
                value = [value.strip() for value in values if value.strip()]
            else:
                value = [value]
            # : is a synonym for = 
            if separator == ":":
                separator = "="
                
            term = dict(key=key,
                        separator=separator,
                        search_term=value)
        else:
            term = dict(key=None,
                        separator=None,
                        search_term=[item])

        items.append(term)
    print("* items are:", pf(items) + "\n")
    return(items)

if __name__ == '__main__':
    parse("foo=[3 2 1]")
    parse("WIKI=ho*")
    parse("LRS>9")
    parse("LRS>=18")
    parse("NAME='rw williams'")
    parse('NAME="rw williams"')
    parse("foo <= 2")
    parse("cisLRS<20")
    parse("foo=[3 2 1)")
    parse("foo=(3 2 1)")
    parse("shh")
    parse("shh grep")
    parse("LRS=(9 99 Chr4 122 155) cisLRS=(9 999 10)")
    parse("sal1 LRS=(9 99 Chr4 122 155) sal2 cisLRS=(9 999 10)")
    parse("sal1 sal3 LRS=(9 99 Chr4 122 155) wiki=bar sal2 go:foobar cisLRS=(9 999 10)")
    parse("sal1 LRS=(9 99 Chr4 122 155) wiki=bar sal2 go:foobar cisLRS=(9, 999, 10)")