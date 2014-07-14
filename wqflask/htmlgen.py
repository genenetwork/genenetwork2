from __future__ import absolute_import, division, print_function

class HTMLgen(object):
    """A redefined HT until we manage to completely eliminate it"""
    def __getattr__(self, name):
        return ""

    def Item(self, *args, **kw):
        print("This way of generating html is obsolete!")
        return "foo"

    Href = Span = TD = Blockquote = Image = Item

HTMLgen2 = HTMLgen()
